"""The §5 observation model: closed, immutable, UTC, with the §5.4/§5 invariants."""

import json
import math
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.canon.models import (
    MAX_PAYLOAD_DEPTH,
    AcceptedVia,
    CanonicalObservation,
    CanonicalQuantity,
    DeltaVerdict,
    EntryMode,
    Informant,
    InformantRole,
    NotComparableReason,
    QualityState,
    QualityVerdict,
    RejectionReason,
    ReportedValue,
    SourceStatus,
    SuspicionReason,
    UnitResolution,
)
from tests.conftest import make_capture

# Which exception an immutable container raises is the container's business; the
# contract is only that the mutation is refused (§5 write-once).
MUTATION_REFUSED = (TypeError, AttributeError)


def _nested_payload(levels: int) -> dict[str, object]:
    """A chain of `levels` nested mappings, innermost empty."""
    payload: dict[str, object] = {}
    current = payload
    for _ in range(levels - 1):
        nested: dict[str, object] = {}
        current["n"] = nested
        current = nested
    return payload


def test_effective_time_is_normalised_to_utc():
    # Arrange / Act
    capture = make_capture(
        effective_time=datetime(2026, 6, 12, 11, 20, tzinfo=timezone(timedelta(hours=3)))
    )

    # Assert — 11:20 at +03:00 is 08:20 UTC (§2.6)
    assert capture.effective_time.tzinfo is UTC
    assert capture.effective_time.hour == 8
    assert capture.effective_time.minute == 20


def test_a_naive_datetime_is_refused():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_capture(effective_time=datetime(2026, 6, 12, 8, 20))


def test_patient_reported_entry_requires_an_informant():
    # Arrange / Act / Assert — §5.4: this is not optional
    with pytest.raises(ValidationError):
        make_capture(entry_mode=EntryMode.patient_reported, informant=None)


def test_patient_reported_entry_with_an_informant_is_accepted():
    # Arrange / Act
    capture = make_capture(
        entry_mode=EntryMode.patient_reported,
        informant=Informant(role=InformantRole.medicine_manager, person_id="MM-17"),
    )

    # Assert
    assert capture.informant is not None
    assert capture.informant.role is InformantRole.medicine_manager


def test_absent_reason_is_set_instead_of_a_value_never_alongside_one():
    # Arrange / Act / Assert — §5: absence with a stated reason is not a value
    with pytest.raises(ValidationError):
        make_capture(
            as_reported=ReportedValue(value="5.5", unit="mmol/L"),
            absent_reason="not_done",
        )


def test_the_model_is_closed_to_undeclared_fields():
    # Arrange / Act / Assert — the §4.2 closed-contract discipline, applied to captures
    with pytest.raises(ValidationError):
        make_capture(ward="north")


def test_the_model_is_immutable():
    # Arrange
    capture = make_capture()

    # Act / Assert — observations are write-once (§5); the model makes it literal
    with pytest.raises(ValidationError):
        capture.observable = "pulse"  # type: ignore[misc]


def test_capture_collections_are_immutable_in_place():
    # Arrange
    capture = make_capture(
        context_flags=["home"],
        raw_payload={"details": {"source": "meter"}, "readings": ["5.5"]},
    )

    # Act / Assert
    with pytest.raises(MUTATION_REFUSED):
        capture.context_flags[0] = "clinic"
    with pytest.raises(MUTATION_REFUSED):
        capture.context_flags.append("clinic")
    with pytest.raises(MUTATION_REFUSED):
        capture.raw_payload["details"] = {"source": "manual"}
    with pytest.raises(MUTATION_REFUSED):
        capture.raw_payload["details"]["source"] = "manual"
    with pytest.raises(MUTATION_REFUSED):
        capture.raw_payload["readings"].append("6.0")

    # Assert — nested payload data remains write-once as well
    assert capture.context_flags == ("home",)
    assert capture.raw_payload["details"]["source"] == "meter"
    assert capture.raw_payload["readings"] == ("5.5",)


def test_a_capture_without_a_payload_still_holds_a_frozen_one():
    # Arrange / Act — the default routes through the same validator as a supplied
    # payload, so the field's type does not depend on whether a caller passed one
    capture = make_capture()

    # Act / Assert
    with pytest.raises(MUTATION_REFUSED):
        capture.raw_payload["injected"] = "value"

    # Assert
    assert capture.raw_payload == {}


def test_a_frozen_payload_serialises_to_json():
    # Arrange
    capture = make_capture(
        context_flags=["home"],
        raw_payload={"device": {"serial": "BP-17"}, "readings": ["5.5", "5.6"]},
    )

    # Act — the frozen containers are not JSON types; serialisation thaws them
    payload = json.loads(capture.model_dump_json())

    # Assert
    assert payload["context_flags"] == ["home"]
    assert payload["raw_payload"] == {"device": {"serial": "BP-17"}, "readings": ["5.5", "5.6"]}


def test_raw_payload_rejects_a_cyclic_container():
    # Arrange
    raw_payload: dict[str, object] = {}
    raw_payload["self"] = raw_payload

    # Act / Assert
    with pytest.raises(ValidationError):
        make_capture(raw_payload=raw_payload)


def test_raw_payload_accepts_nesting_at_the_depth_cap():
    # Arrange / Act
    capture = make_capture(raw_payload=_nested_payload(MAX_PAYLOAD_DEPTH))

    # Assert
    assert "n" in capture.raw_payload


def test_raw_payload_rejects_nesting_past_the_depth_cap():
    # Arrange / Act / Assert — an uncapped recursion would raise RecursionError and
    # escape the validation channel; the cap makes it an ordinary rejection
    with pytest.raises(ValidationError):
        make_capture(raw_payload=_nested_payload(MAX_PAYLOAD_DEPTH + 1))


@pytest.mark.parametrize(
    "raw_payload",
    [
        pytest.param({1: "meter"}, id="non_string_top_level_key"),
        pytest.param({"details": {1: "meter"}}, id="non_string_nested_key"),
        pytest.param({"value": Decimal("5.5")}, id="decimal_value"),
        pytest.param({"values": {1, 2}}, id="set_value"),
        pytest.param({"value": object()}, id="arbitrary_object"),
        pytest.param({"value": math.nan}, id="nan_value"),
        pytest.param({"value": math.inf}, id="infinity"),
    ],
)
def test_raw_payload_rejects_values_outside_json_shapes(raw_payload):
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_capture(raw_payload=raw_payload)


def test_an_accepted_verdict_must_carry_how_it_got_there():
    # Arrange / Act / Assert — §6.2: accepted_via is not optional
    with pytest.raises(ValidationError):
        QualityVerdict(state=QualityState.accepted, unit_resolution=UnitResolution.explicit)


def test_a_rejected_verdict_must_name_why():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        QualityVerdict(state=QualityState.rejected, unit_resolution=UnitResolution.explicit)


def test_a_flagged_verdict_must_name_what_is_suspected():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.needs_repeat_or_verification,
            unit_resolution=UnitResolution.explicit,
        )


def test_a_consistent_rejected_verdict_is_accepted():
    # Arrange / Act
    verdict = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=UnitResolution.ambiguous,
        rejection_reasons=[RejectionReason.unit_ambiguous],
    )

    # Assert
    assert verdict.state is QualityState.rejected
    assert verdict.accepted_via is None


def test_a_rejected_verdict_cannot_carry_accepted_via():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.rejected,
            unit_resolution=UnitResolution.explicit,
            accepted_via=AcceptedVia.clinician_verified,
            rejection_reasons=[RejectionReason.parse_failure],
        )


def test_a_consistent_flagged_verdict_is_accepted():
    # Arrange / Act
    verdict = QualityVerdict(
        state=QualityState.needs_repeat_or_verification,
        unit_resolution=UnitResolution.explicit,
        suspicions=[SuspicionReason.delta_exceeded],
    )

    # Assert
    assert verdict.suspicions == (SuspicionReason.delta_exceeded,)


def test_a_flagged_verdict_cannot_carry_rejection_reasons():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.needs_repeat_or_verification,
            unit_resolution=UnitResolution.explicit,
            rejection_reasons=[RejectionReason.parse_failure],
            suspicions=[SuspicionReason.delta_exceeded],
        )


def test_accepted_via_unremarkable_round_trips():
    # Arrange / Act
    verdict = QualityVerdict(
        state=QualityState.accepted,
        unit_resolution=UnitResolution.explicit,
        accepted_via=AcceptedVia.unremarkable,
    )

    # Assert
    assert verdict.accepted_via is AcceptedVia.unremarkable


@pytest.mark.parametrize(
    "quality_state",
    [QualityState.accepted, QualityState.clinically_exceptional_accepted],
)
def test_an_accepted_family_verdict_cannot_carry_rejection_reasons(quality_state):
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=quality_state,
            unit_resolution=UnitResolution.explicit,
            accepted_via=AcceptedVia.unremarkable,
            rejection_reasons=[RejectionReason.parse_failure],
        )


@pytest.mark.parametrize(
    "unit_resolution", [UnitResolution.explicit, UnitResolution.inferred_from_code]
)
def test_a_resolved_verdict_cannot_carry_a_unit_ambiguous_rejection(unit_resolution):
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.rejected,
            unit_resolution=unit_resolution,
            rejection_reasons=[RejectionReason.unit_ambiguous],
        )


def test_verdict_reason_lists_are_stored_as_immutable_collections():
    # Arrange — reasons arrive as lists, from callers and from JSON alike
    verdict = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=UnitResolution.explicit,
        rejection_reasons=[RejectionReason.parse_failure],
        suspicions=[SuspicionReason.delta_exceeded],
    )

    # Act / Assert — a verdict is a record; §8.2 reads these reasons, so they
    # cannot be edited after the fact
    with pytest.raises(MUTATION_REFUSED):
        verdict.rejection_reasons[0] = RejectionReason.unit_ambiguous
    with pytest.raises(MUTATION_REFUSED):
        verdict.suspicions[0] = SuspicionReason.unit_changed_from_prior

    # Assert
    assert verdict.rejection_reasons == (RejectionReason.parse_failure,)
    assert verdict.suspicions == (SuspicionReason.delta_exceeded,)


@pytest.mark.parametrize(
    ("quality_state", "accepted_via"),
    [
        (QualityState.accepted, AcceptedVia.unremarkable),
        (QualityState.clinically_exceptional_accepted, AcceptedVia.clinician_verified),
    ],
)
def test_an_accepted_observation_must_carry_a_canonical_value(quality_state, accepted_via):
    # Arrange
    capture = make_capture()
    quality = QualityVerdict(
        state=quality_state,
        unit_resolution=UnitResolution.explicit,
        accepted_via=accepted_via,
    )

    # Act / Assert — §6.3 as a type invariant, not a convention: nothing accepted
    # reaches the engine without a canonical value
    with pytest.raises(ValidationError):
        CanonicalObservation(**capture.model_dump(), canonical=None, quality=quality)


@pytest.mark.parametrize(
    ("quality_state", "accepted_via"),
    [
        (QualityState.accepted, AcceptedVia.unremarkable),
        (QualityState.clinically_exceptional_accepted, AcceptedVia.clinician_verified),
    ],
)
def test_an_accepted_observation_with_a_canonical_value_is_accepted(quality_state, accepted_via):
    # Arrange
    capture = make_capture(
        context_flags=["home_visit"],
        raw_payload={
            "device": {"serial": "BP-17"},
            "readings": ["5.5", "5.6"],
            "temperature_c": 36.5,
        },
    )
    quality = QualityVerdict(
        state=quality_state,
        unit_resolution=UnitResolution.explicit,
        accepted_via=accepted_via,
    )
    canonical = CanonicalQuantity(value=Decimal("5.5"), ucum="mmol/L")
    capture_dump = capture.model_dump()

    # Act
    observation = CanonicalObservation(**capture_dump, canonical=canonical, quality=quality)

    # Assert
    assert observation.canonical == canonical
    assert observation.quality.state is quality_state
    assert capture_dump["context_flags"] == ("home_visit",)
    assert capture_dump["raw_payload"] == {
        "device": {"serial": "BP-17"},
        "readings": ["5.5", "5.6"],
        "temperature_c": 36.5,
    }
    assert observation.context_flags == ("home_visit",)
    assert observation.raw_payload["device"]["serial"] == "BP-17"
    assert observation.raw_payload["readings"] == ("5.5", "5.6")


def test_ambiguous_unit_resolution_cannot_produce_an_accepted_verdict():
    # Arrange / Act / Assert — ambiguous units are a hard failure (§6.3)
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.accepted,
            unit_resolution=UnitResolution.ambiguous,
            accepted_via=AcceptedVia.unremarkable,
        )


@pytest.mark.parametrize(
    "rejection_reason",
    [RejectionReason.mapping_unusable, RejectionReason.source_status_unusable],
)
def test_a_refusal_before_unit_resolution_records_no_resolution_outcome(rejection_reason):
    # Arrange / Act — §6.3: the three values are outcomes, and these two refusals
    # happen before resolution runs, so there is no outcome to name
    verdict = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=None,
        rejection_reasons=[rejection_reason],
    )

    # Assert
    assert verdict.unit_resolution is None
    assert verdict.rejection_reasons == (rejection_reason,)


@pytest.mark.parametrize(
    "rejection_reasons",
    [
        pytest.param([RejectionReason.parse_failure], id="parse_failure"),
        pytest.param([RejectionReason.unit_ambiguous], id="unit_ambiguous"),
        pytest.param([RejectionReason.missing_required_context], id="missing_context"),
        pytest.param([RejectionReason.outside_physiologic_envelope], id="outside_envelope"),
        pytest.param(
            [RejectionReason.mapping_unusable, RejectionReason.parse_failure],
            id="a_pre_resolution_reason_mixed_with_a_later_one",
        ),
    ],
)
def test_a_refusal_after_unit_resolution_must_record_its_outcome(rejection_reasons):
    # Arrange / Act / Assert — a unit resolves whether or not the value parses, the
    # context is complete, or the result is plausible, so silence here would hand
    # §11.9's missing-unit rate a failure that never happened
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.rejected,
            unit_resolution=None,
            rejection_reasons=rejection_reasons,
        )


@pytest.mark.parametrize(
    "rejection_reason",
    [RejectionReason.mapping_unusable, RejectionReason.source_status_unusable],
)
def test_a_refusal_before_unit_resolution_cannot_record_an_outcome(rejection_reason):
    # Arrange / Act / Assert — the other direction of the same equivalence: claiming
    # a resolution that never ran misleads the same §11.9 counters
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.rejected,
            unit_resolution=UnitResolution.explicit,
            rejection_reasons=[rejection_reason],
        )


@pytest.mark.parametrize(
    "verdict_fields",
    [
        pytest.param(
            {"state": QualityState.accepted, "accepted_via": AcceptedVia.unremarkable},
            id="accepted",
        ),
        pytest.param(
            {
                "state": QualityState.clinically_exceptional_accepted,
                "accepted_via": AcceptedVia.clinician_verified,
            },
            id="clinically_exceptional_accepted",
        ),
        pytest.param(
            {
                "state": QualityState.needs_repeat_or_verification,
                "suspicions": [SuspicionReason.delta_exceeded],
            },
            id="needs_repeat_or_verification",
        ),
    ],
)
def test_a_verdict_that_is_not_a_refusal_must_record_a_unit_resolution(verdict_fields):
    # Arrange / Act / Assert — only a refusal can precede resolution; any other
    # state means the three layers ran (§6.1)
    with pytest.raises(ValidationError):
        QualityVerdict(unit_resolution=None, **verdict_fields)


def test_an_ambiguous_rejected_observation_carries_no_canonical_value():
    # Arrange
    capture = make_capture()
    quality = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=UnitResolution.ambiguous,
        rejection_reasons=[RejectionReason.unit_ambiguous],
    )

    # Act
    observation = CanonicalObservation(**capture.model_dump(), canonical=None, quality=quality)

    # Assert
    assert observation.quality.rejection_reasons == (RejectionReason.unit_ambiguous,)
    assert observation.canonical is None


def test_an_observation_refused_before_unit_resolution_carries_no_canonical_value():
    # Arrange — the source withdrew the record (§13.1 gate 1), so nothing was resolved
    capture = make_capture(source_status=SourceStatus.entered_in_error)
    quality = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=None,
        rejection_reasons=[RejectionReason.source_status_unusable],
    )

    # Act
    observation = CanonicalObservation(**capture.model_dump(), canonical=None, quality=quality)

    # Assert
    assert observation.quality.unit_resolution is None
    assert observation.canonical is None


@pytest.mark.parametrize(
    ("unit_resolution", "rejection_reason"),
    [
        pytest.param(
            UnitResolution.ambiguous, RejectionReason.unit_ambiguous, id="ambiguous_resolution"
        ),
        pytest.param(None, RejectionReason.mapping_unusable, id="resolution_never_ran"),
    ],
)
def test_a_canonical_value_requires_a_resolved_unit(unit_resolution, rejection_reason):
    # Arrange — converting against a unit that was never settled is the silent best
    # guess §5 forbids, whether resolution failed or never ran (§6.3)
    capture = make_capture()
    quality = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=unit_resolution,
        rejection_reasons=[rejection_reason],
    )
    canonical = CanonicalQuantity(value=Decimal("5.5"), ucum="mmol/L")

    # Act / Assert
    with pytest.raises(ValidationError):
        CanonicalObservation(**capture.model_dump(), canonical=canonical, quality=quality)


def test_a_comparable_delta_names_its_baseline_and_its_change():
    # Arrange / Act
    delta = DeltaVerdict(comparable=True, compared_to="OBS-0", change=Decimal("0.6"))

    # Assert — the delta is a recorded fact, not a flag (§5)
    assert delta.suspicious is False
    assert delta.not_comparable_reason is None


def test_a_comparable_delta_without_a_baseline_is_refused():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        DeltaVerdict(comparable=True, change=Decimal("0.6"))


def test_an_incomparable_delta_records_why_nothing_was_compared():
    # Arrange / Act — §11.9's delta-check rate needs "not compared" to be a fact
    delta = DeltaVerdict(
        comparable=False,
        not_comparable_reason=NotComparableReason.no_prior_observation,
    )

    # Assert
    assert delta.compared_to is None
    assert delta.change is None


def test_an_incomparable_delta_that_names_a_baseline_is_refused():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        DeltaVerdict(
            comparable=False,
            compared_to="OBS-0",
            not_comparable_reason=NotComparableReason.no_comparable_prior,
        )


def test_an_incomparable_suspicious_delta_is_refused():
    # Arrange / Act / Assert — incomparable means reason only
    with pytest.raises(ValidationError):
        DeltaVerdict(
            comparable=False,
            suspicious=True,
            not_comparable_reason=NotComparableReason.no_prior_observation,
        )
