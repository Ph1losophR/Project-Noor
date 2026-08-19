"""Quality resolution (SSOT §6.2, §6.5): append-only, named, and never silent."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from noor.canon.models import (
    AcceptedVia,
    Arm,
    CaptureContext,
    CuffSize,
    MethodContext,
    Posture,
    QualityState,
    RejectionReason,
    Setting,
    SourceStatus,
)
from noor.canon.resolution import (
    ResolutionError,
    ResolutionKind,
    confirm_repeat,
    verify_by_clinician,
)
from tests.conftest import make_canonical

RESOLVED_AT = datetime(2026, 6, 12, 9, 0, tzinfo=UTC)


def test_a_concordant_repeat_confirms_a_flagged_value(registry):
    # Arrange — glucose repeat_tolerance is 0.6 mmol/L
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        value="30.0",
        source_identifier="FLAGGED-1",
    )
    repeat = make_canonical(value="29.5", source_identifier="REPEAT-1")

    # Act
    resolution = confirm_repeat(
        flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT
    )

    # Assert — §6.2: accepted via repeat_confirmed, with the pointer
    assert resolution.observation == "FLAGGED-1"
    assert resolution.kind is ResolutionKind.repeat_confirmed
    assert resolution.confirming_observation == "REPEAT-1"
    assert resolution.clinician_id == "RN-7"
    assert resolution.resulting_state is QualityState.accepted
    assert resolution.accepted_via is AcceptedVia.repeat_confirmed


def test_a_discordant_repeat_confirms_nothing(registry):
    # Arrange — |28.0 - 30.0| = 2.0 > 0.6 tolerance
    entry = registry.entry("glucose")
    flagged = make_canonical(state=QualityState.needs_repeat_or_verification, value="30.0")
    repeat = make_canonical(value="28.0")

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_exactly_at_the_tolerance_boundary_confirms(registry):
    # Arrange — |29.4 - 30.0| = 0.6, the glucose tolerance itself: the guard is
    # strict `>` (resolution.py), so the boundary is inside, not out
    entry = registry.entry("glucose")
    flagged = make_canonical(state=QualityState.needs_repeat_or_verification, value="30.0")
    repeat = make_canonical(value="29.4")

    # Act
    resolution = confirm_repeat(
        flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT
    )

    # Assert
    assert resolution.resulting_state is QualityState.accepted
    assert resolution.accepted_via is AcceptedVia.repeat_confirmed


def test_a_repeat_that_is_not_accepted_quality_cannot_confirm(registry):
    # Arrange — a flagged repeat is another question, not an answer
    entry = registry.entry("glucose")
    flagged = make_canonical(state=QualityState.needs_repeat_or_verification, value="30.0")
    repeat = make_canonical(state=QualityState.needs_repeat_or_verification, value="29.5")

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_valueless_flagged_observation_has_nothing_to_confirm(registry):
    # Arrange — the pipeline never emits a flagged record without a canonical
    # value, but the schema permits one (models.py forbids canonical None only
    # for the accepted family); the guard refuses it on its own, not as a side
    # effect of the same-observable check
    entry = registry.entry("glucose")
    flagged = make_canonical(state=QualityState.needs_repeat_or_verification, value="30.0")
    valueless = flagged.model_copy(update={"canonical": None})
    repeat = make_canonical(value="29.5")

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(valueless, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_of_a_different_observable_cannot_confirm(registry):
    # Arrange
    entry = registry.entry("glucose")
    flagged = make_canonical(state=QualityState.needs_repeat_or_verification, value="30.0")
    repeat = make_canonical(observable="pulse", value="29.5", unit="/min")

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_in_a_different_posture_cannot_confirm(registry):
    # Arrange — the reading ordinal may differ; the posture may not
    entry = registry.entry("systolic_bp")
    sitting = CaptureContext(
        posture=Posture.sitting,
        arm=Arm.left,
        cuff_size=CuffSize.standard,
        rest_duration_seconds=300,
        reading_ordinal=1,
        is_average=False,
    )
    standing = CaptureContext(
        posture=Posture.standing,
        arm=Arm.left,
        cuff_size=CuffSize.standard,
        rest_duration_seconds=60,
        reading_ordinal=2,
        is_average=False,
    )
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        observable="systolic_bp",
        value="250",
        unit="mm[Hg]",
        setting=Setting.home,
        context=sitting,
        method=MethodContext(device_class="home-bp-monitor"),
    )
    repeat = make_canonical(
        observable="systolic_bp",
        value="248",
        unit="mm[Hg]",
        setting=Setting.home,
        context=standing,
        method=MethodContext(device_class="home-bp-monitor"),
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_from_a_different_device_class_cannot_confirm(registry):
    # Arrange
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        value="30.0",
        method=MethodContext(device_class="accu-chek"),
    )
    repeat = make_canonical(value="29.5", method=MethodContext(device_class="cgm-different-class"))

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_in_a_different_setting_cannot_confirm(registry):
    # Arrange
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        value="30.0",
        setting=Setting.home,
    )
    repeat = make_canonical(value="29.5", setting=Setting.office)

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_an_unflagged_observation_has_nothing_to_confirm(registry):
    # Arrange
    entry = registry.entry("glucose")
    unremarkable = make_canonical(value="5.5")
    repeat = make_canonical(value="5.5")

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(unremarkable, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_clinician_verified_envelope_rejection_becomes_clinically_exceptional(registry):
    # Arrange — §6.2: the gate must not suppress a genuine emergency
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.outside_physiologic_envelope],
        value="80",
    )

    # Act
    resolution = verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)

    # Assert
    assert resolution.resulting_state is QualityState.clinically_exceptional_accepted
    assert resolution.accepted_via is AcceptedVia.clinician_verified
    assert resolution.kind is ResolutionKind.clinician_verified
    assert resolution.clinician_id == "MD-3"


def test_a_clinician_verified_ordinary_flagged_value_becomes_accepted(registry):
    # Arrange — delta-flagged but the value sits inside the operational envelope
    entry = registry.entry("glucose")
    flagged = make_canonical(state=QualityState.needs_repeat_or_verification, value="6.0")

    # Act
    resolution = verify_by_clinician(flagged, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)

    # Assert
    assert resolution.resulting_state is QualityState.accepted
    assert resolution.accepted_via is AcceptedVia.clinician_verified
    assert resolution.confirming_observation is None  # the §6.2 pointer is the repeat path's


def test_a_clinician_verified_flagged_extreme_value_becomes_clinically_exceptional(registry):
    # Arrange — pulse 220: outside operational, confirmed real by a named clinician
    entry = registry.entry("pulse")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        observable="pulse",
        value="220",
        unit="/min",
    )

    # Act
    resolution = verify_by_clinician(flagged, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)

    # Assert
    assert resolution.resulting_state is QualityState.clinically_exceptional_accepted


def test_a_parse_failure_can_never_be_verified(registry):
    # Arrange — there is no value to stand behind; re-capture is the fix
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.parse_failure],
        value="abc",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_a_unit_ambiguous_rejection_can_never_be_verified(registry):
    # Arrange — §6.3: resolve the unit in the home, not afterwards
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.unit_ambiguous],
        value="5.5",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_a_mapping_unusable_rejection_can_never_be_verified(registry):
    # Arrange — no attestation makes a valueless record valuable: the mapping
    # refusal leaves canonical None, and there is nothing to stand behind
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.mapping_unusable],
        value="5.5",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_a_context_rejection_can_never_be_verified(registry):
    # Arrange — context is recorded at capture, not attested afterwards
    entry = registry.entry("systolic_bp")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.missing_required_context],
        observable="systolic_bp",
        value="120",
        unit="mm[Hg]",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_an_accepted_observation_has_nothing_to_verify(registry):
    # Arrange
    entry = registry.entry("glucose")
    unremarkable = make_canonical(value="5.5")

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(unremarkable, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_a_withdrawn_source_status_rejection_can_never_be_verified(registry):
    # Arrange — §5: the source retracted the record. A clinician can attest that a
    # value is real; nobody can attest that a withdrawn record was not withdrawn.
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.source_status_unusable],
        source_status=SourceStatus.entered_in_error,
        value="5.5",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_the_resolution_timestamp_is_normalised_to_utc(registry):
    # Arrange
    entry = registry.entry("glucose")
    flagged = make_canonical(state=QualityState.needs_repeat_or_verification, value="6.0")
    riyadh_noon = datetime(2026, 6, 12, 12, 0, tzinfo=timezone(timedelta(hours=3)))

    # Act
    resolution = verify_by_clinician(flagged, entry, clinician_id="MD-3", resolved_at=riyadh_noon)

    # Assert — §2.6: stored UTC
    assert resolution.resolved_at.tzinfo is UTC
    assert resolution.resolved_at.hour == 9
