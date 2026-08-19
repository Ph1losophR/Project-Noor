"""The canon pipeline (SSOT §6): the three layers, the four quality states,
and the guarantee that a value without a safe canonical form never becomes
a fact."""

from datetime import timedelta
from decimal import Decimal

import pytest

from noor.canon.models import (
    WITHDRAWN_SOURCE_STATUSES,
    Arm,
    CaptureContext,
    CuffSize,
    MappingInfo,
    MappingStatus,
    MethodContext,
    NotComparableReason,
    Posture,
    QualityState,
    RejectionReason,
    ReportedValue,
    Setting,
    SourceCode,
    SourceStatus,
    SuspicionReason,
    UnitResolution,
)
from noor.canon.pipeline import AbsentObservationError, canonicalise
from noor.canon.registry import ObservableRegistry, UnknownObservableError
from tests.conftest import T0, make_canonical, make_capture, make_conversion, make_entry


def bp_capture(value: str, **kw):
    """A fully-contextualised systolic BP capture (SSOT §6.6)."""
    fields = {
        "observable": "systolic_bp",
        "value": value,
        "unit": "mm[Hg]",
        "setting": Setting.home,
        "context": CaptureContext(
            posture=Posture.sitting,
            arm=Arm.left,
            cuff_size=CuffSize.standard,
            rest_duration_seconds=300,
            reading_ordinal=1,
            is_average=False,
        ),
        "method": MethodContext(device_class="home-bp-monitor"),
    }
    fields.update(kw)
    overrides = {k: fields.pop(k) for k in ("value", "unit")}
    return make_capture(as_reported=ReportedValue(**overrides), **fields)


def test_an_ordinary_capture_is_accepted_unremarkable(registry):
    # Arrange
    capture = make_capture()

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.quality.accepted_via == "unremarkable"
    assert result.quality.unit_resolution is UnitResolution.explicit
    assert result.canonical is not None
    assert result.canonical.value == Decimal("5.5")
    assert result.canonical.ucum == "mmol/L"
    assert result.canonical.conversion_applied is None  # already canonical
    assert result.quality.delta is not None  # "not compared" is recorded, not absent
    assert result.quality.delta.comparable is False
    assert result.quality.delta.not_comparable_reason is NotComparableReason.no_prior_observation
    assert result.as_reported.value == "5.5"  # the verbatim value survives (§5)


def test_a_converted_value_preserves_the_original_unit_and_shows_its_work(registry):
    # Arrange — §6.3: preserve the original unit; convert with provenance
    capture = make_capture(value="90", unit="mg/dL")

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.canonical is not None
    assert result.canonical.value == Decimal("5.00")
    assert result.canonical.ucum == "mmol/L"
    assert result.as_reported.value == "90"
    assert result.as_reported.unit == "mg/dL"
    # The stored value can be traced to the factor that produced it (§5, §6.3)
    declared = next(c for c in registry.entry("glucose").conversions if c.from_unit == "mg/dL")
    applied = result.canonical.conversion_applied
    assert applied is not None
    assert applied.from_unit == "mg/dL"
    assert applied.multiply == declared.multiply
    assert applied.version == declared.version


def test_a_code_implied_unit_is_recorded_as_inferred(registry):
    # Arrange
    capture = make_capture(
        observable="hba1c_ngsp",
        as_reported=ReportedValue(value="7.4", unit=None),
        source_code=SourceCode(system="http://loinc.org", code="4548-4"),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.quality.unit_resolution is UnitResolution.inferred_from_code
    assert result.canonical is not None
    assert result.canonical.value == Decimal("7.4")
    assert result.canonical.ucum == "%"


def test_an_ambiguous_unit_is_a_hard_failure_with_no_canonical_value(registry):
    # Arrange — §6.3: the one capture-time hard stop
    capture = make_capture(as_reported=ReportedValue(value="5.5", unit=None))

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == (RejectionReason.unit_ambiguous,)
    assert result.quality.unit_resolution is UnitResolution.ambiguous
    assert result.canonical is None  # never receives a canonical value


def test_an_unparseable_value_is_rejected(registry):
    # Arrange
    capture = make_capture(as_reported=ReportedValue(value="7,4", unit="mmol/L"))

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == (RejectionReason.parse_failure,)
    assert result.canonical is None


def test_an_ambiguous_mapping_reaches_canon_as_unusable(registry):
    # Arrange — §5: never a silent best guess
    capture = make_capture(mapping=MappingInfo(status=MappingStatus.ambiguous))

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == (RejectionReason.mapping_unusable,)
    assert result.quality.unit_resolution is None  # resolution never ran (§6.3)
    assert result.canonical is None


@pytest.mark.parametrize("status", sorted(WITHDRAWN_SOURCE_STATUSES))
def test_a_withdrawn_source_record_is_refused(registry, status):
    # Arrange — §5: the source retracted this. Canonicalising it would turn a
    # retraction into a fact. Driven off the frozenset so a new withdrawn status
    # cannot be added to the enum without a row here.
    capture = make_capture(source_status=status)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == (RejectionReason.source_status_unusable,)
    assert result.quality.unit_resolution is None  # resolution never ran (§6.3)
    assert result.canonical is None


@pytest.mark.parametrize("status", sorted(set(SourceStatus) - WITHDRAWN_SOURCE_STATUSES))
def test_a_source_record_the_source_still_stands_behind_is_canonicalised_normally(registry, status):
    # Arrange — canon gates on withdrawal, not on finality: whether a preliminary
    # result is fresh enough for a decision is a per-rule §5.1 question, and a
    # correction is the value that stands rather than a withdrawal (assumption 11).
    capture = make_capture(source_status=status)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.canonical is not None
    assert result.canonical.value == Decimal("5.5")


def test_an_unusable_mapping_and_an_unusable_status_are_both_named(registry):
    # Arrange — two independent §5 refusals on one capture; neither hides the other
    capture = make_capture(
        mapping=MappingInfo(status=MappingStatus.ambiguous),
        source_status=SourceStatus.cancelled,
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert set(result.quality.rejection_reasons) == {
        RejectionReason.mapping_unusable,
        RejectionReason.source_status_unusable,
    }
    assert result.quality.unit_resolution is None  # both refusals precede it (§6.3)
    assert result.canonical is None


def test_a_bp_capture_missing_required_context_is_rejected(registry):
    # Arrange — §6.6: BP without posture is meaningless
    capture = make_capture(
        observable="systolic_bp",
        as_reported=ReportedValue(value="120", unit="mm[Hg]"),
        setting=Setting.home,
        context=CaptureContext(posture=None, arm=Arm.left, cuff_size=CuffSize.standard),
        method=MethodContext(device_class="home-bp-monitor"),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert RejectionReason.missing_required_context in result.quality.rejection_reasons
    assert result.canonical is not None  # the value exists; the context does not


def test_a_bp_capture_missing_required_method_fields_is_rejected(registry):
    # Arrange — §6.6: the device class is required method context for BP
    capture = make_capture(
        observable="systolic_bp",
        as_reported=ReportedValue(value="120", unit="mm[Hg]"),
        setting=Setting.home,
        context=CaptureContext(
            posture=Posture.sitting,
            arm=Arm.left,
            cuff_size=CuffSize.standard,
            rest_duration_seconds=300,
            reading_ordinal=1,
            is_average=False,
        ),
        method=MethodContext(device_class=None),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert RejectionReason.missing_required_context in result.quality.rejection_reasons


def test_a_physiologically_impossible_value_is_rejected_but_kept(registry):
    # Arrange — 80 mmol/L glucose cannot be generated (physiologic ceiling 70)
    capture = make_capture(value="80", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry)

    # Assert — the value is kept so a clinician can resurrect it (§6.2)
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == (RejectionReason.outside_physiologic_envelope,)
    assert result.canonical is not None
    assert result.canonical.value == Decimal("80")


def test_an_extreme_but_possible_value_is_flagged_not_rejected(registry):
    # Arrange — pulse 220: outside operational [35, 200], inside physiologic
    capture = make_capture(observable="pulse", value="220", unit="/min")

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert result.quality.suspicions == (SuspicionReason.outside_operational_envelope,)
    assert result.canonical is not None
    assert result.canonical.value == Decimal("220")


def test_a_rejected_observation_keeps_the_suspicion_it_earned(registry):
    # Arrange — systolic 300: outside operational [70, 260] but inside physiologic
    # [40, 320], and the capture misses required context. The suspicion must
    # survive the rejection, or review loses the emergency signal (§6.2).
    capture = make_capture(
        observable="systolic_bp",
        value="300",
        unit="mm[Hg]",
        setting=Setting.home,
        context=CaptureContext(posture=None, arm=Arm.left, cuff_size=CuffSize.standard),
        method=MethodContext(device_class="home-bp-monitor"),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert RejectionReason.missing_required_context in result.quality.rejection_reasons
    assert result.quality.suspicions == (SuspicionReason.outside_operational_envelope,)


def test_a_real_but_extreme_value_and_a_mistyped_value_land_in_different_states(registry):
    # Arrange — §14 step 2's verification, §6.2's reason for four states:
    # systolic 300 is a genuine-emergency value; "abc" is a mistype
    extreme = bp_capture("300")
    mistyped = bp_capture("abc")

    # Act
    extreme_result = canonicalise(extreme, registry)
    mistyped_result = canonicalise(mistyped, registry)

    # Assert — never the same system outcome
    assert extreme_result.quality.state is QualityState.needs_repeat_or_verification
    assert mistyped_result.quality.state is QualityState.rejected
    assert extreme_result.quality.state != mistyped_result.quality.state


@pytest.mark.parametrize(
    ("observable", "value", "unit", "shape"),
    [
        # pulse 20 with a 200 partner: the operational envelope spans 5.7x, so a
        # ten-times slip is real news. No swap of "20" lands inside it.
        pytest.param(
            "pulse",
            "20",
            "/min",
            SuspicionReason.decimal_shift_suspected,
            id="a_pulse_of_20_that_could_be_200",
        ),
        # glucose 0.3 with a 3.0 partner: true, but glucose spans 23.3x, where a
        # partner exists for every flagged value, so the decimal shape stays silent
        # and only the swap that produced 0.3 from 3.0 is recorded.
        pytest.param(
            "glucose",
            "0.3",
            "mmol/L",
            SuspicionReason.digit_transposition_suspected,
            id="a_glucose_of_0_3_that_could_be_3_0",
        ),
    ],
)
def test_a_flagged_value_records_only_the_mistype_shape_that_discriminates(
    registry, observable, value, unit, shape
):
    # Arrange — §6.1's two shapes are recorded where they say something about this
    # reading, and nowhere else: a hint true of every flagged value trains the
    # reader to skim the flag that matters.
    capture = make_capture(observable=observable, value=value, unit=unit)

    # Act
    result = canonicalise(capture, registry)

    # Assert — the exact tuple: the other shape is absent, not merely unasserted
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert result.quality.suspicions == (SuspicionReason.outside_operational_envelope, shape)


def canonicalised_prior(registry, value: str, unit: str, **kw):
    """A prior as canon actually stored it.

    Canonicalised rather than assembled, so its canonical value carries the real
    conversion provenance (§6.3) — which is how a stored record still names the
    unit the source reported.
    """
    return canonicalise(make_capture(value=value, unit=unit, **kw), registry)


def test_a_unit_changed_from_the_patients_prior_record_is_flagged(registry):
    # Arrange — §6.1 layer 1: the prior was mg/dL, today's says mmol/L
    prior = canonicalised_prior(
        registry,
        "100",
        "mg/dL",
        effective_time=T0 - timedelta(hours=1),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="5.5", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry, priors=[prior])

    # Assert
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert result.quality.suspicions == (SuspicionReason.unit_changed_from_prior,)


def test_a_unit_matching_the_patients_prior_record_is_unremarkable(registry):
    # Arrange — same unit as the prior: no suspicion
    prior = canonicalised_prior(
        registry,
        "100",
        "mg/dL",
        effective_time=T0 - timedelta(hours=1),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="101", unit="mg/dL")

    # Act
    result = canonicalise(capture, registry, priors=[prior])

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.quality.suspicions == ()


def test_a_later_observation_is_not_a_unit_change_baseline(registry):
    # Arrange — results land out of order; only earlier priors count
    later = canonicalised_prior(
        registry,
        "100",
        "mg/dL",
        effective_time=T0 + timedelta(hours=1),
        source_identifier="LATER-1",
    )
    capture = make_capture(value="5.5", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry, priors=[later])

    # Assert — no earlier prior, so no unit-change suspicion
    assert result.quality.state is QualityState.accepted


def test_a_superseded_prior_is_not_the_unit_change_baseline(registry):
    # Arrange — §5: the source sent 100 mg/dL, then corrected the same record to
    # 5.55 mmol/L. Today's mmol/L capture matches the version that stands, so
    # there is no unit change to flag. Newest first: arrival order is not sorted.
    versions = [
        canonicalised_prior(
            registry,
            value,
            unit,
            effective_time=T0 - timedelta(hours=1),
            source_identifier="PRIOR-1",
            source_version=version,
        )
        for value, unit, version in (("5.55", "mmol/L", 2), ("100", "mg/dL", 1))
    ]
    capture = make_capture(value="5.5", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry, priors=versions)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.quality.suspicions == ()


def test_the_unit_change_flag_does_not_depend_on_prior_arrival_order(registry):
    # Arrange — two priors at the same effective_time, one mg/dL and one mmol/L.
    # The tie is broken by source_identifier, so PRIOR-B (already mmol/L) is the
    # baseline whichever order the priors arrive in (§5: a never-rewritten verdict
    # cannot depend on query order).
    prior_a = canonicalised_prior(
        registry,
        "100",
        "mg/dL",
        effective_time=T0 - timedelta(hours=1),
        source_identifier="PRIOR-A",
    )
    prior_b = canonicalised_prior(
        registry,
        "5.5",
        "mmol/L",
        effective_time=T0 - timedelta(hours=1),
        source_identifier="PRIOR-B",
    )
    capture = make_capture(value="5.5", unit="mmol/L")

    # Act — newest first, then oldest first
    forward = canonicalise(capture, registry, priors=[prior_a, prior_b])
    reversed_order = canonicalise(capture, registry, priors=[prior_b, prior_a])

    # Assert — the tie-break picks the same baseline; no unit change either way
    assert forward == reversed_order
    assert forward.quality.suspicions == ()


@pytest.fixture
def dual_unit_registry() -> ObservableRegistry:
    """One observable that accepts both units and maps an observation code to each.

    Synthetic because no shipped observable does both: an entry needs a non-empty
    code_unit_map *and* a second accepted unit before a source can switch between
    an explicit unit and a code-implied one, and content/observables/registry.yaml
    has no such entry. Envelopes come from make_entry: [2, 10] and [4, 8] mmol/L.
    """
    return ObservableRegistry(
        entries={
            "glucose": make_entry(
                observable="glucose",
                accepted_units=["mmol/L", "mg/dL"],
                conversions=[make_conversion(multiply=Decimal("0.0555"))],
                code_unit_map={
                    "http://loinc.org|2345-7": "mg/dL",  # glucose [mass/volume]
                    "http://loinc.org|14749-6": "mmol/L",  # glucose [moles/volume]
                },
            )
        }
    )


@pytest.mark.parametrize(
    ("code", "value", "state", "suspicions"),
    [
        pytest.param(
            "2345-7",
            "100",
            QualityState.needs_repeat_or_verification,
            (SuspicionReason.unit_changed_from_prior,),
            id="a_code_implied_mg_dL_after_an_explicit_mmol_L_prior",
        ),
        pytest.param(
            "14749-6",
            "5.6",
            QualityState.accepted,
            (),
            id="a_code_implied_mmol_L_after_an_explicit_mmol_L_prior",
        ),
    ],
)
def test_a_unit_change_is_read_from_the_resolved_unit_not_the_reported_text(
    dual_unit_registry, code, value, state, suspicions
):
    # Arrange — §6.3: an interfaced source stops sending a unit and starts relying
    # on its observation code. Whether that is a unit change is a question about the
    # resolved units, not about the reported text, which is absent on one side here.
    prior = canonicalised_prior(
        dual_unit_registry,
        "5.5",
        "mmol/L",
        effective_time=T0 - timedelta(hours=1),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(
        value=value,
        unit=None,
        source_code=SourceCode(system="http://loinc.org", code=code),
    )

    # Act
    result = canonicalise(capture, dual_unit_registry, priors=[prior])

    # Assert — the incoming unit really did arrive implied, and the flag followed
    # the unit rather than the absence
    assert result.quality.unit_resolution is UnitResolution.inferred_from_code
    assert result.quality.state is state
    assert result.quality.suspicions == suspicions


def test_priors_may_be_a_generator(registry):
    # Arrange — canonicalise reads the priors twice (unit change, then delta);
    # a one-shot iterable must not read empty on the second pass
    prior = make_canonical(
        value="5.5",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="14.0", method=MethodContext(device_class="accu-chek"))

    # Act
    result = canonicalise(capture, registry, priors=(p for p in [prior]))

    # Assert — the delta was found on the second pass
    assert result.quality.suspicions == (SuspicionReason.delta_exceeded,)


def test_a_suspicious_delta_is_flagged_and_recorded(registry):
    # Arrange
    prior = make_canonical(
        value="5.5",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="14.0", method=MethodContext(device_class="accu-chek"))

    # Act
    result = canonicalise(capture, registry, priors=[prior])

    # Assert
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert result.quality.suspicions == (SuspicionReason.delta_exceeded,)
    assert result.quality.delta is not None
    assert result.quality.delta.compared_to == "PRIOR-1"
    assert result.quality.delta.change == Decimal("8.5")


def test_a_clean_delta_is_recorded_without_flagging(registry):
    # Arrange
    prior = make_canonical(
        value="5.5",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="6.0", method=MethodContext(device_class="accu-chek"))

    # Act
    result = canonicalise(capture, registry, priors=[prior])

    # Assert — a delta that ran and passed is a fact of record, not silence
    assert result.quality.state is QualityState.accepted
    assert result.quality.delta is not None
    assert result.quality.delta.suspicious is False


def test_every_rejection_reason_is_named_when_several_apply(registry):
    # Arrange — unparseable value AND an unrecognised unit
    capture = make_capture(as_reported=ReportedValue(value="abc", unit="mg%"))

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert set(result.quality.rejection_reasons) == {
        RejectionReason.parse_failure,
        RejectionReason.unit_ambiguous,
    }


def test_an_unknown_observable_is_refused_loudly(registry):
    # Arrange — an ungoverned observable is a system error, not a clinical one
    capture = make_capture(observable="tsh")

    # Act / Assert
    with pytest.raises(UnknownObservableError):
        canonicalise(capture, registry)


def test_an_absent_reason_capture_has_nothing_to_canonicalise(registry):
    # Arrange — §5: absence-with-reason is stored verbatim by the caller
    capture = make_capture(
        as_reported=ReportedValue(value=None, unit=None),
        absent_reason="not_done",
    )

    # Act / Assert
    with pytest.raises(AbsentObservationError):
        canonicalise(capture, registry)


def test_context_flags_pass_through_and_the_value_is_never_corrected(registry):
    # Arrange — §5.3: the flag prompts review; it does not adjust a number
    capture = make_capture(
        observable="hba1c_ngsp",
        value="7.4",
        unit="%",
        context_flags=["a1c_interpretation_caution"],
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.canonical is not None
    assert result.canonical.value == Decimal("7.4")
    assert result.context_flags == ("a1c_interpretation_caution",)


def test_a_code_display_name_is_carried_but_never_required(registry):
    # Arrange — §3.3: LOINC display names carry a licence condition, so the
    # registry keys code_unit_map on bare "system|code" and stores no display
    # text (assumption 9). A display arriving on a capture is the source's data:
    # canon carries it verbatim and never needs it to resolve anything.
    capture = make_capture(
        observable="hba1c_ngsp",
        as_reported=ReportedValue(value="7.4", unit=None),
        source_code=SourceCode(
            system="http://loinc.org", code="4548-4", display="Hemoglobin A1c/Hemoglobin.total"
        ),
        mapping=MappingInfo(source_display="HbA1c", terminology_version="LOINC 2.77"),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert — resolved from the code alone; both displays survive untouched
    assert result.quality.unit_resolution is UnitResolution.inferred_from_code
    assert result.source_code is not None
    assert result.source_code.display == "Hemoglobin A1c/Hemoglobin.total"
    assert result.mapping.source_display == "HbA1c"
    assert result.mapping.terminology_version == "LOINC 2.77"


def test_the_capture_is_never_mutated(registry):
    # Arrange
    capture = make_capture(value="40", unit="mmol/L")

    # Act
    canonicalise(capture, registry)

    # Assert — §6.1: never silently converts, replaces, or suppresses
    assert capture.as_reported.value == "40"
    assert capture.as_reported.unit == "mmol/L"
