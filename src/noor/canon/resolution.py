"""Quality resolution (SSOT §6.2, §6.5).

Observations are write-once (§5), so a resolution is a separate append-only
record, not an edit. A repeat that resolves a flag must be concordant and
like-with-like; a clinician verification names the clinician. A resolved value
outside the operational envelope becomes clinically_exceptional_accepted — the
state that stops the plausibility gate from suppressing a genuine emergency —
and a confirmed ordinary value becomes accepted. Either way, the record keeps
how it got there.
"""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import AwareDatetime, Field, field_validator

from noor.canon.models import (
    ACCEPTED_FAMILY,
    AcceptedVia,
    CanonicalObservation,
    NoorModel,
    QualityState,
    RejectionReason,
)
from noor.canon.plausibility import EnvelopePosition, locate
from noor.canon.registry import ObservableEntry


class ResolutionError(ValueError):
    """A resolution that does not meet its bar is refused, not approximated."""


class ResolutionKind(StrEnum):
    repeat_confirmed = "repeat_confirmed"
    clinician_verified = "clinician_verified"


class QualityResolution(NoorModel):
    observation: str = Field(min_length=1)  # source_identifier of the resolved observation
    kind: ResolutionKind
    clinician_id: str = Field(min_length=1)
    confirming_observation: str | None = None  # the repeat's source_identifier (§6.2)
    resolved_at: AwareDatetime
    resulting_state: QualityState
    accepted_via: AcceptedVia

    @field_validator("resolved_at")
    @classmethod
    def _normalise_to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


def confirm_repeat(
    flagged: CanonicalObservation,
    repeat: CanonicalObservation,
    entry: ObservableEntry,
    *,
    clinician_id: str,
    resolved_at: datetime,
) -> QualityResolution:
    """Resolve a needs_repeat_or_verification observation against a concordant repeat.

    The repeat must itself be accepted-quality, the same observable, in the same
    context (reading ordinal and averaging aside) and device class, and within
    the registry's repeat tolerance. A discordant repeat confirms nothing.
    """
    if flagged.quality.state is not QualityState.needs_repeat_or_verification:
        raise ResolutionError(f"nothing to confirm: state is {flagged.quality.state}")
    if repeat.quality.state not in ACCEPTED_FAMILY or repeat.canonical is None:
        raise ResolutionError("the repeat must itself be accepted-quality")
    if flagged.canonical is None or repeat.observable != flagged.observable:
        raise ResolutionError("the repeat must be the same observable with a canonical value")
    context_fields = {"reading_ordinal", "is_average"}
    if flagged.context.model_dump(exclude=context_fields) != repeat.context.model_dump(
        exclude=context_fields
    ):
        raise ResolutionError("the repeat must be measured in the same context")
    if flagged.setting != repeat.setting:
        raise ResolutionError("the repeat must be measured in the same setting")
    if flagged.method.device_class != repeat.method.device_class:
        raise ResolutionError("the repeat must come from the same device class")
    if abs(repeat.canonical.value - flagged.canonical.value) > entry.repeat_tolerance:
        raise ResolutionError("the repeat does not confirm the flagged value")
    return QualityResolution(
        observation=flagged.source_identifier,
        kind=ResolutionKind.repeat_confirmed,
        clinician_id=clinician_id,
        confirming_observation=repeat.source_identifier,
        resolved_at=resolved_at,
        resulting_state=QualityState.accepted,
        accepted_via=AcceptedVia.repeat_confirmed,
    )


def verify_by_clinician(
    observation: CanonicalObservation,
    entry: ObservableEntry,
    *,
    clinician_id: str,
    resolved_at: datetime,
) -> QualityResolution:
    """A named clinician attests that a questioned or envelope-rejected value is real.

    Parse, unit, mapping, context, and withdrawn-status rejections can never be
    verified — the fix is re-capture, not attestation, and no attestation makes a
    record the source retracted un-retracted. An accepted observation has nothing
    to verify. Both guards below already refuse those: they carry no canonical
    value, and their reasons are not the envelope rejection.
    """
    if observation.canonical is None:
        raise ResolutionError("an observation without a canonical value cannot be verified")
    if observation.quality.state is QualityState.rejected and (
        observation.quality.rejection_reasons != (RejectionReason.outside_physiologic_envelope,)
    ):
        raise ResolutionError("only an envelope rejection can be clinician-verified; re-capture")
    if observation.quality.state not in (
        QualityState.needs_repeat_or_verification,
        QualityState.rejected,
    ):
        raise ResolutionError(f"nothing to verify: state is {observation.quality.state}")
    # A verified value outside the operational envelope is clinically exceptional
    # (§6.2); a verified ordinary value is simply accepted.
    resulting_state = (
        QualityState.accepted
        if locate(observation.canonical.value, entry) is EnvelopePosition.within_operational
        else QualityState.clinically_exceptional_accepted
    )
    return QualityResolution(
        observation=observation.source_identifier,
        kind=ResolutionKind.clinician_verified,
        clinician_id=clinician_id,
        resolved_at=resolved_at,
        resulting_state=resulting_state,
        accepted_via=AcceptedVia.clinician_verified,
    )
