"""The canon pipeline (SSOT §6): the three layers, the four quality states,
and the guarantee that a value without a safe canonical form never becomes
a fact."""

from datetime import timedelta
from decimal import Decimal

import pytest

from noor.canon.models import (
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
from noor.canon.registry import UnknownObservableError
from tests.conftest import T0, make_canonical, make_capture


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


def test_a_withdrawn_source_record_is_refused(registry):
    # Arrange — §5: the source retracted this. Canonicalising it would turn a
    # retraction into a fact.
    capture = make_capture(source_status=SourceStatus.entered_in_error)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == (RejectionReason.source_status_unusable,)
    assert result.quality.unit_resolution is None  # resolution never ran (§6.3)
    assert result.canonical is None


def test_a_cancelled_source_record_is_refused(registry):
    # Arrange — the other withdrawn status; both rows of the boundary
    capture = make_capture(source_status=SourceStatus.cancelled)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == (RejectionReason.source_status_unusable,)
    assert result.quality.unit_resolution is None  # resolution never ran (§6.3)


def test_a_corrected_source_record_is_canonicalised_normally(registry):
    # Arrange — a correction is the value that stands, not a withdrawal
    # (assumption 11); freshness is a per-rule §5.1 question, not canon's.
    capture = make_capture(source_status=SourceStatus.corrected)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.canonical is not None
    assert result.canonical.value == Decimal("5.5")


def test_a_preliminary_source_record_is_canonicalised_normally(registry):
    # Arrange — canon does not gate on finality (assumption 11)
    capture = make_capture(source_status=SourceStatus.preliminary)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted


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


def test_a_decimal_transposition_pattern_adds_a_suspicion(registry):
    # Arrange — glucose 40 mmol/L: outside operational, and 4.0 would be inside
    capture = make_capture(value="40", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert SuspicionReason.outside_operational_envelope in result.quality.suspicions
    assert SuspicionReason.decimal_transposition_suspected in result.quality.suspicions


def test_a_unit_changed_from_the_patients_prior_record_is_flagged(registry):
    # Arrange — §6.1 layer 1: the prior was mg/dL, today's says mmol/L
    prior = make_canonical(
        value="100",
        unit="mg/dL",
        canonical_value="5.55",
        canonical_ucum="mmol/L",
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
    prior = make_canonical(
        value="100",
        unit="mg/dL",
        canonical_value="5.55",
        canonical_ucum="mmol/L",
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
    later = make_canonical(
        value="100",
        unit="mg/dL",
        canonical_value="5.55",
        canonical_ucum="mmol/L",
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
        make_canonical(
            value=value,
            unit=unit,
            canonical_value="5.55",
            canonical_ucum="mmol/L",
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
    # Arrange — two priors at the same effective_time: the same-source, same-time
    # tie is broken by source_identifier, so PRIOR-B (already mmol/L) is the
    # latest baseline whichever order the priors arrive in (§5: a never-rewritten
    # verdict cannot depend on query order).
    prior_a = make_canonical(
        value="100",
        unit="mg/dL",
        canonical_value="5.55",
        canonical_ucum="mmol/L",
        effective_time=T0 - timedelta(hours=1),
        source_identifier="PRIOR-A",
    )
    prior_b = make_canonical(
        value="5.5",
        unit="mmol/L",
        canonical_value="5.5",
        canonical_ucum="mmol/L",
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
