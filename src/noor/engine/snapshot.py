"""The closed evaluation snapshot (§4.2) with the §5.5 allergy record, §5.6 goals
of care, and §11.6's requested-action projection.

The snapshot is the evaluator's entire world: `app` builds it, and the data half
of the seam (§4.2) keeps it closed — a field that is not declared cannot enter,
so a computed clinical value cannot cross the boundary by inventing a key. Time
enters as data too: `evaluated_at` is an explicit input, never a clock read.
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import AwareDatetime, field_validator, model_validator

from noor.canon.models import CanonicalObservation, MappingStatus, NoorModel


class ActionKind(StrEnum):
    """What the clinician intends to do (SSOT §11.6)."""

    medication_start = "medication_start"
    medication_stop = "medication_stop"
    medication_dose_change = "medication_dose_change"
    lab_order = "lab_order"
    referral = "referral"
    plan_change = "plan_change"


class RequestedAction(NoorModel):
    """The planned action reduced to what the evaluator reads (SSOT §11.6).

    Detail, state, and blocked_by belong to the encounter; this projection
    carries exactly what `order_of` matches against.
    """

    kind: ActionKind
    subject: str


class AllergyStatus(StrEnum):
    """Whether anyone asked about allergies (SSOT §5.5 rule 2).

    An unasked patient and a cleared patient are opposite facts, and neither is
    ever inferred from an empty list.
    """

    no_known_allergy = "no_known_allergy"
    not_asked = "not_asked"
    recorded = "recorded"


class ReactionType(StrEnum):
    """What kind of reaction was recorded (SSOT §5.5 rule 3: intolerance is not allergy)."""

    immediate_hypersensitivity = "immediate_hypersensitivity"
    delayed = "delayed"
    intolerance = "intolerance"
    unknown = "unknown"


class AllergySeverity(StrEnum):
    """How bad the worst recorded reaction was (SSOT §5.5)."""

    severe = "severe"
    moderate = "moderate"
    mild = "mild"
    unknown = "unknown"


class VerificationStatus(StrEnum):
    """Whether the allergy itself is believed (SSOT §5.5 rule 1).

    Only `confirmed` with `severity: severe` satisfies "verified severe allergy";
    `refuted` and `entered_in_error` never surface at any severity.
    """

    confirmed = "confirmed"
    unconfirmed = "unconfirmed"
    refuted = "refuted"
    entered_in_error = "entered_in_error"


class EvidenceSource(StrEnum):
    """Who the finding came from (SSOT §5.5)."""

    clinical_record = "clinical_record"
    patient_reported = "patient_reported"
    family_reported = "family_reported"


class CulpritSubstance(NoorModel):
    """The substance behind the record (SSOT §5.5); rules match on `ingredient_id`."""

    ingredient_id: str
    atc: str | None = None
    source_display: str | None = None


class AllergyOnset(NoorModel):
    """When the reaction happened (SSOT §5.5's example shape).

    Partial dates stay strings: "2019-03" is not a date.
    """

    timing: str | None = None
    date: str | None = None
    precision: str | None = None


class Recorder(NoorModel):
    """Who made the entry (SSOT §5.5)."""

    person_id: str
    role: str


class AllergyRecord(NoorModel):
    """One allergy entry, complete enough to carry its finding into the card
    (SSOT §5.5, §8.3).

    The evaluator decides on `culprit.ingredient_id`, `verification_status`, and
    `severity`; everything else rides along for display.
    """

    culprit: CulpritSubstance
    reaction: tuple[str, ...]
    reaction_type: ReactionType
    severity: AllergySeverity
    onset: AllergyOnset
    verification_status: VerificationStatus
    evidence_source: EvidenceSource
    recorder: Recorder
    recorded_at: AwareDatetime


class SnapshotMedication(NoorModel):
    """One medication-list entry, with canon's mapping verdict attached (§4.2).

    An ambiguous mapping travels into the snapshot unresolved: matching a
    requested action against it is a finding, not a construction refusal.
    """

    ingredient_id: str
    mapping_status: MappingStatus


class GoalOfCare(NoorModel):
    """A clinician-set override of a guideline target (SSOT §5.6).

    There is no lifecycle status field: a goal is active exactly when the
    evaluation timestamp falls in `[effective_date, expires_at)`, and early
    revocation shortens `expires_at`. `op`, `reason`, and `clinician_id` carry
    meaning and accountability into the card; the numeric comparison operator
    belongs to the rule (§7.1).
    """

    observable: str
    value: Decimal
    unit: str
    op: str
    reason: str
    clinician_id: str
    effective_date: AwareDatetime
    expires_at: AwareDatetime

    @model_validator(mode="after")
    def _the_goal_window_is_never_empty(self) -> Self:
        if self.expires_at <= self.effective_date:
            raise ValueError(
                "a goal's window is [effective_date, expires_at); expires_at must be later"
            )
        return self


class Snapshot(NoorModel):
    """Everything the evaluator may read about one patient at one instant
    (SSOT §4.2, §8.1).

    Closed by construction (`extra="forbid"` from `NoorModel`): every field is
    either a `canon` output or a declared input, so nothing computed outside the
    boundary slips past it. Rejected observations travel with their verdicts —
    hiding them would hide a data-quality finding (§8.3).
    """

    snapshot_id: str
    evaluated_at: AwareDatetime
    patient_id: str
    age_years: int
    observations: tuple[CanonicalObservation, ...] = ()
    medications: tuple[SnapshotMedication, ...] = ()
    allergies: tuple[AllergyRecord, ...] = ()
    allergy_status: AllergyStatus
    conditions: frozenset[str] = frozenset()
    goals_of_care: tuple[GoalOfCare, ...] = ()

    @field_validator("evaluated_at")
    @classmethod
    def _normalise_to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)
