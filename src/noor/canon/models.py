"""The observation model (SSOT §5) and canon's quality verdicts (§6.2).

Every model is frozen and closed: an observation is written once and never
overwritten, and an undeclared field cannot enter the record.
"""

import math
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Self, cast

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


class NoorModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class _FrozenSequence(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        return isinstance(other, (list, tuple)) and tuple(self) == tuple(other)


def _freeze_payload(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("raw_payload floats must be finite")
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        frozen_items: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("raw_payload mapping keys must be strings")
            frozen_items[key] = _freeze_payload(item)
        return MappingProxyType(frozen_items)
    if isinstance(value, (list, tuple)):
        return _FrozenSequence(_freeze_payload(item) for item in value)
    raise ValueError("raw_payload contains an unsupported JSON value")


def _thaw_payload(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_payload(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_payload(item) for item in value]
    return value


class UnitResolution(StrEnum):
    explicit = "explicit"
    inferred_from_code = "inferred_from_code"
    ambiguous = "ambiguous"


class QualityState(StrEnum):
    accepted = "accepted"
    needs_repeat_or_verification = "needs_repeat_or_verification"
    rejected = "rejected"
    clinically_exceptional_accepted = "clinically_exceptional_accepted"


ACCEPTED_FAMILY: frozenset[QualityState] = frozenset(
    {QualityState.accepted, QualityState.clinically_exceptional_accepted}
)


class AcceptedVia(StrEnum):
    unremarkable = "unremarkable"
    repeat_confirmed = "repeat_confirmed"
    clinician_verified = "clinician_verified"


class RejectionReason(StrEnum):
    mapping_unusable = "mapping_unusable"
    source_status_unusable = "source_status_unusable"
    parse_failure = "parse_failure"
    unit_ambiguous = "unit_ambiguous"
    missing_required_context = "missing_required_context"
    outside_physiologic_envelope = "outside_physiologic_envelope"


class SuspicionReason(StrEnum):
    outside_operational_envelope = "outside_operational_envelope"
    decimal_transposition_suspected = "decimal_transposition_suspected"
    unit_changed_from_prior = "unit_changed_from_prior"
    delta_exceeded = "delta_exceeded"


class NotComparableReason(StrEnum):
    """Why delta review compared nothing. "Not compared" is a fact of record, not
    a silent pass (§5), and §11.9's delta-check rate is computed from it."""

    no_prior_observation = "no_prior_observation"  # none of this observable at all
    no_comparable_prior = "no_comparable_prior"  # priors exist, none like-with-like


class SourceStatus(StrEnum):
    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"


# The source withdrew the record. There is no value to validate and nothing to
# resurrect, so canon refuses it before the three layers run (§13.1 gate 1 names
# status alongside units and time). Every other status passes through: whether a
# preliminary result is usable for a decision is a per-rule freshness question
# answered at evaluation time (§5.1), not an intrinsic property of the value.
WITHDRAWN_SOURCE_STATUSES: frozenset[SourceStatus] = frozenset(
    {SourceStatus.cancelled, SourceStatus.entered_in_error}
)


class EntryMode(StrEnum):
    interfaced = "interfaced"
    staff_transcribed = "staff_transcribed"
    patient_reported = "patient_reported"
    device_memory = "device_memory"
    noor_derived = "noor_derived"


class InformantRole(StrEnum):
    patient = "patient"
    medicine_manager = "medicine_manager"


class MappingStatus(StrEnum):
    mapped = "mapped"
    ambiguous = "ambiguous"
    unmapped = "unmapped"


class Setting(StrEnum):
    office = "office"
    home = "home"
    ambulatory = "ambulatory"


class Posture(StrEnum):
    sitting = "sitting"
    supine = "supine"
    standing = "standing"


class Arm(StrEnum):
    left = "left"
    right = "right"


class CuffSize(StrEnum):
    small = "small"
    standard = "standard"
    large = "large"
    thigh = "thigh"


class SourceCode(NoorModel):
    system: str = Field(min_length=1)
    code: str = Field(min_length=1)
    display: str | None = None


class Informant(NoorModel):
    role: InformantRole
    person_id: str = Field(min_length=1)


class MethodContext(NoorModel):
    device_class: str | None = None
    specimen: str | None = None
    assay: str | None = None


class CaptureContext(NoorModel):
    """Per-observable context (SSOT §6.6). BP needs all of it; the registry says so."""

    posture: Posture | None = None
    arm: Arm | None = None
    cuff_size: CuffSize | None = None
    rest_duration_seconds: int | None = Field(default=None, ge=0)
    reading_ordinal: int | None = Field(default=None, ge=1)
    is_average: bool | None = None


class MappingInfo(NoorModel):
    """How the source code became a Noor observable (SSOT §5)."""

    status: MappingStatus = MappingStatus.mapped
    source_display: str | None = None
    terminology_version: str | None = None


class ReportedValue(NoorModel):
    """Exactly as captured. The value stays a string until parse validates it."""

    value: str | None = None
    unit: str | None = None


def _utc(value: datetime | None) -> datetime | None:
    return None if value is None else value.astimezone(UTC)


class ObservationCapture(NoorModel):
    """Canon's input: one observation exactly as captured (SSOT §5).

    `recorded_at` is deliberately absent — the store stamps it (§5).
    `encounter_id` is carried and never read: a rule cannot ask which encounter a
    fact came from (§8.1), but the model is closed, so canon's output has to be
    able to hold the one inert §5 field the workflow adds.
    """

    observable: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    source_identifier: str = Field(min_length=1)
    source_version: int = Field(default=1, ge=1)
    source_code: SourceCode | None = None
    source_status: SourceStatus
    encounter_id: str | None = None
    effective_time: AwareDatetime
    issued_at: AwareDatetime | None = None
    received_at: AwareDatetime | None = None
    entry_mode: EntryMode
    informant: Informant | None = None
    method: MethodContext = MethodContext()
    setting: Setting | None = None
    context: CaptureContext = CaptureContext()
    as_reported: ReportedValue
    absent_reason: str | None = None
    mapping: MappingInfo = MappingInfo()
    context_flags: tuple[str, ...] = Field(default_factory=tuple, validate_default=True)
    raw_payload: Mapping[str, object] = Field(default_factory=dict, validate_default=True)

    @field_validator("effective_time", "issued_at", "received_at")
    @classmethod
    def _normalise_to_utc(cls, value: datetime | None) -> datetime | None:
        return _utc(value)

    @model_validator(mode="after")
    def _patient_reported_requires_an_informant(self) -> Self:
        if self.entry_mode is EntryMode.patient_reported and self.informant is None:
            raise ValueError("patient_reported observations name their informant (SSOT §5.4)")
        return self

    @model_validator(mode="after")
    def _absent_reason_replaces_the_value(self) -> Self:
        if self.absent_reason is not None and self.as_reported.value is not None:
            raise ValueError("absent_reason is set INSTEAD of a value, never alongside it (§5)")
        return self

    @field_validator("raw_payload", mode="before")
    @classmethod
    def _validate_raw_payload(cls, payload: object) -> object:
        return _freeze_payload(payload)

    @field_validator("raw_payload", mode="after")
    @classmethod
    def _freeze_raw_payload(cls, payload: Mapping[str, object]) -> Mapping[str, object]:
        return cast(Mapping[str, object], _freeze_payload(payload))

    @field_validator("context_flags", mode="after")
    @classmethod
    def _freeze_context_flags(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _FrozenSequence(values)

    @field_serializer("context_flags")
    def _serialise_context_flags(self, values: tuple[str, ...]) -> list[str]:
        return list(values)

    @field_serializer("raw_payload")
    def _serialise_raw_payload(self, payload: Mapping[str, object]) -> dict[str, object]:
        return cast(dict[str, object], _thaw_payload(payload))


class ConversionApplied(NoorModel):
    """The conversion that produced a canonical value (SSOT §6.3: "every
    conversion … carries its own provenance").

    Copied onto the value, not referenced: content is versioned and mutable by PR,
    so a stored observation must still say which factor it was computed with. If
    `0.055507` is ever corrected, `version` is how the affected rows are found.
    """

    from_unit: str = Field(min_length=1)
    add: Decimal
    multiply: Decimal
    precision: int = Field(ge=0)
    rounding: str = Field(min_length=1)
    version: str = Field(min_length=1)


class CanonicalQuantity(NoorModel):
    """Derived, and it shows its work (§5, §6.3).

    `conversion_applied` is None exactly when the reported unit was already the
    canonical unit — an identity conversion has no work to show.
    """

    value: Decimal
    ucum: str = Field(min_length=1)
    conversion_applied: ConversionApplied | None = None


class DeltaVerdict(NoorModel):
    """What delta review compared, or why it compared nothing (§5, §6.1).

    Always recorded when the three layers ran: `comparable=False` with a reason is
    the record that nothing was compared, which is what §11.9's delta-check rate
    counts. `QualityVerdict.delta is None` means something else — delta review
    never ran, because the value was rejected before layer 3.
    """

    comparable: bool
    compared_to: str | None = None  # source_identifier of the prior
    change: Decimal | None = None
    suspicious: bool = False
    not_comparable_reason: NotComparableReason | None = None

    @model_validator(mode="after")
    def _the_verdict_says_what_it_compared(self) -> Self:
        if self.comparable:
            if (
                self.compared_to is None
                or self.change is None
                or self.not_comparable_reason is not None
            ):
                raise ValueError("a comparable delta names its baseline and its change (§5)")
        elif (
            self.compared_to is not None
            or self.change is not None
            or self.suspicious
            or self.not_comparable_reason is None
        ):
            raise ValueError("an incomparable delta names its reason and nothing else")
        return self


class QualityVerdict(NoorModel):
    """Canon's intrinsic verdict on one observation (SSOT §6.2)."""

    state: QualityState
    unit_resolution: UnitResolution
    accepted_via: AcceptedVia | None = None
    rejection_reasons: tuple[RejectionReason, ...] = Field(
        default_factory=tuple, validate_default=True
    )
    suspicions: tuple[SuspicionReason, ...] = Field(default_factory=tuple, validate_default=True)
    delta: DeltaVerdict | None = None

    @field_validator("rejection_reasons", "suspicions", mode="after")
    @classmethod
    def _freeze_verdict_collections(cls, values: tuple[Any, ...]) -> tuple[Any, ...]:
        return _FrozenSequence(values)

    @field_serializer("rejection_reasons", "suspicions")
    def _serialise_verdict_collections(self, values: tuple[Any, ...]) -> list[Any]:
        return list(values)

    @model_validator(mode="after")
    def _the_verdict_explains_itself(self) -> Self:
        if self.state in ACCEPTED_FAMILY and self.accepted_via is None:
            raise ValueError("an accepted observation carries how it got there (§6.2)")
        if self.state is QualityState.rejected and not self.rejection_reasons:
            raise ValueError("a rejected observation names why")
        if self.state is QualityState.needs_repeat_or_verification and not self.suspicions:
            raise ValueError("a flagged observation names what is suspected")
        if self.unit_resolution is UnitResolution.ambiguous and (
            self.state is not QualityState.rejected
            or RejectionReason.unit_ambiguous not in self.rejection_reasons
        ):
            raise ValueError("ambiguous unit resolution is rejected as unit_ambiguous (§6.3)")
        return self


class CanonicalObservation(ObservationCapture):
    """Canon's output: the verbatim capture, its canonical value, its quality verdict.

    `canonical` is None exactly when the value could not be made safe to evaluate —
    most sharply when `unit_resolution` is `ambiguous` (§6.3). The converse is an
    invariant, not a hope: an accepted-family observation always carries a
    canonical value, which is what lets `delta` and the engine read it without a
    None check they could get wrong.
    """

    canonical: CanonicalQuantity | None
    quality: QualityVerdict

    @model_validator(mode="after")
    def _an_accepted_observation_carries_a_canonical_value(self) -> Self:
        if self.quality.state in ACCEPTED_FAMILY and self.canonical is None:
            raise ValueError("an accepted observation carries a canonical value (§6.3)")
        if self.quality.unit_resolution is UnitResolution.ambiguous and self.canonical is not None:
            raise ValueError("an ambiguous unit resolution carries no canonical value (§6.3)")
        return self
