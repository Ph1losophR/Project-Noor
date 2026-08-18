"""The §5 observation model: closed, immutable, UTC, with the §5.4/§5 invariants."""

import copy
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.canon.models import (
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
    SuspicionReason,
    UnitResolution,
)
from tests.conftest import make_capture


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
    with pytest.raises(TypeError):
        capture.context_flags.append("clinic")
    with pytest.raises(TypeError):
        capture.raw_payload["details"]["source"] = "manual"
    with pytest.raises(TypeError):
        capture.raw_payload["readings"].append("6.0")

    # Assert — nested payload data remains write-once as well
    assert capture.context_flags == ["home"]
    assert capture.raw_payload["details"]["source"] == "meter"
    assert capture.raw_payload["readings"] == ["5.5"]
    assert copy.deepcopy(capture.context_flags) is capture.context_flags
    assert copy.deepcopy(capture.raw_payload) is capture.raw_payload


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda values: values.__setitem__(0, "clinic"), id="setitem"),
        pytest.param(lambda values: values.__delitem__(0), id="delitem"),
        pytest.param(lambda values: values.__iadd__(["clinic"]), id="iadd"),
        pytest.param(lambda values: values.__imul__(2), id="imul"),
        pytest.param(lambda values: values.append("clinic"), id="append"),
        pytest.param(lambda values: values.clear(), id="clear"),
        pytest.param(lambda values: values.extend(["clinic"]), id="extend"),
        pytest.param(lambda values: values.insert(0, "clinic"), id="insert"),
        pytest.param(lambda values: values.pop(), id="pop"),
        pytest.param(lambda values: values.remove("home"), id="remove"),
        pytest.param(lambda values: values.reverse(), id="reverse"),
        pytest.param(lambda values: values.sort(), id="sort"),
    ],
)
def test_capture_list_mutations_are_refused(mutate):
    # Arrange
    capture = make_capture(context_flags=["home"])

    # Act / Assert
    with pytest.raises(TypeError):
        mutate(capture.context_flags)

    # Assert
    assert capture.context_flags == ["home"]


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


def test_a_consistent_flagged_verdict_is_accepted():
    # Arrange / Act
    verdict = QualityVerdict(
        state=QualityState.needs_repeat_or_verification,
        unit_resolution=UnitResolution.explicit,
        suspicions=[SuspicionReason.delta_exceeded],
    )

    # Assert
    assert verdict.suspicions == [SuspicionReason.delta_exceeded]


def test_accepted_via_unremarkable_round_trips():
    # Arrange / Act
    verdict = QualityVerdict(
        state=QualityState.accepted,
        unit_resolution=UnitResolution.explicit,
        accepted_via=AcceptedVia.unremarkable,
    )

    # Assert
    assert verdict.accepted_via is AcceptedVia.unremarkable


def test_quality_verdict_collections_are_immutable_in_place():
    # Arrange
    verdict = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=UnitResolution.explicit,
        rejection_reasons=[RejectionReason.parse_failure],
        suspicions=[SuspicionReason.delta_exceeded],
    )

    # Act / Assert
    with pytest.raises(TypeError):
        verdict.rejection_reasons.append(RejectionReason.unit_ambiguous)
    with pytest.raises(TypeError):
        verdict.suspicions.append(SuspicionReason.unit_changed_from_prior)

    # Assert
    assert verdict.rejection_reasons == [RejectionReason.parse_failure]
    assert verdict.suspicions == [SuspicionReason.delta_exceeded]


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda values: values.__delitem__("source"), id="delitem"),
        pytest.param(lambda values: values.__ior__({"other": "value"}), id="ior"),
        pytest.param(lambda values: values.clear(), id="clear"),
        pytest.param(lambda values: values.pop("source"), id="pop"),
        pytest.param(lambda values: values.popitem(), id="popitem"),
        pytest.param(lambda values: values.setdefault("other", "value"), id="setdefault"),
        pytest.param(lambda values: values.update(other="value"), id="update"),
    ],
)
def test_capture_mapping_mutations_are_refused(mutate):
    # Arrange
    capture = make_capture(raw_payload={"source": "meter"})

    # Act / Assert
    with pytest.raises(TypeError):
        mutate(capture.raw_payload)

    # Assert
    assert capture.raw_payload == {"source": "meter"}


def test_an_accepted_observation_must_carry_a_canonical_value():
    # Arrange
    capture = make_capture()
    quality = QualityVerdict(
        state=QualityState.accepted,
        unit_resolution=UnitResolution.explicit,
        accepted_via=AcceptedVia.unremarkable,
    )

    # Act / Assert — §6.3 as a type invariant, not a convention: nothing accepted
    # reaches the engine without a canonical value
    with pytest.raises(ValidationError):
        CanonicalObservation(**capture.model_dump(), canonical=None, quality=quality)


def test_an_accepted_observation_with_a_canonical_value_is_accepted():
    # Arrange
    capture = make_capture()
    quality = QualityVerdict(
        state=QualityState.accepted,
        unit_resolution=UnitResolution.explicit,
        accepted_via=AcceptedVia.unremarkable,
    )
    canonical = CanonicalQuantity(value=Decimal("5.5"), ucum="mmol/L")

    # Act
    observation = CanonicalObservation(**capture.model_dump(), canonical=canonical, quality=quality)

    # Assert
    assert observation.canonical == canonical
    assert observation.quality.state is QualityState.accepted


def test_ambiguous_unit_resolution_cannot_produce_an_accepted_verdict():
    # Arrange / Act / Assert — ambiguous units are a hard failure (§6.3)
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.accepted,
            unit_resolution=UnitResolution.ambiguous,
            accepted_via=AcceptedVia.unremarkable,
        )


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
    assert observation.quality.rejection_reasons == [RejectionReason.unit_ambiguous]
    assert observation.canonical is None


def test_an_ambiguous_observation_with_a_canonical_value_is_refused():
    # Arrange
    capture = make_capture()
    quality = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=UnitResolution.ambiguous,
        rejection_reasons=[RejectionReason.unit_ambiguous],
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
