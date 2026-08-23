"""Shared builders and fixtures (docs/testing-standards.md: factories live here)."""

import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from hypothesis import settings

from noor.canon.models import (
    PRE_RESOLUTION_REJECTIONS,
    AcceptedVia,
    CanonicalObservation,
    CanonicalQuantity,
    DeltaVerdict,
    EntryMode,
    ObservationCapture,
    QualityState,
    QualityVerdict,
    RejectionReason,
    ReportedValue,
    SourceStatus,
    SuspicionReason,
    UnitResolution,
)
from noor.canon.registry import (
    Conversion,
    DeltaPolicy,
    Envelope,
    ObservableEntry,
    ObservableRegistry,
)
from noor.catalogue.registry_loader import load_registry
from noor.engine.content import (
    ENGINE_VERSION,
    CatalogueRelease,
    Citation,
    EvaluationContext,
    Pins,
    Profile,
    RuleDisablement,
    Threshold,
    ThresholdStatus,
)
from noor.engine.rules import (
    ClinicalApprover,
    DrugScopeLevel,
    Expression,
    Governance,
    Monitor,
    NamedClinician,
    OnUnusable,
    Operator,
    OrderBlock,
    ReleaseStatus,
    Requirement,
    Rule,
    Scope,
    Severity,
    Then,
)
from noor.engine.snapshot import (
    AllergyOnset,
    AllergyRecord,
    AllergySeverity,
    AllergyStatus,
    CulpritSubstance,
    EvidenceSource,
    GoalOfCare,
    ReactionType,
    Recorder,
    Snapshot,
    VerificationStatus,
)

settings.register_profile("ci", derandomize=True)
if os.environ.get("CI"):
    settings.load_profile("ci")

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "content" / "observables" / "registry.yaml"

T0 = datetime(2026, 6, 12, 8, 20, tzinfo=UTC)

# The rejections that leave no canonical value: the two that precede unit
# resolution, plus the two that refuse the value itself. Written once here because
# both the builder below and the boundary property assert against it.
VALUELESS_REJECTIONS: frozenset[RejectionReason] = PRE_RESOLUTION_REJECTIONS | {
    RejectionReason.parse_failure,
    RejectionReason.unit_ambiguous,
}


def make_capture(**overrides: Any) -> ObservationCapture:
    """A well-formed glucose capture; override anything.

    `value` and `unit` are shorthands for the `as_reported` pair, which is what
    almost every canon test varies. Anything else goes straight through.
    """
    fields: dict[str, Any] = {
        "observable": "glucose",
        "source_system": "test-lis",
        "source_identifier": "OBS-1",
        "source_status": SourceStatus.final,
        "effective_time": T0,
        "entry_mode": EntryMode.staff_transcribed,
        "as_reported": ReportedValue(value="5.5", unit="mmol/L"),
    }
    if "value" in overrides or "unit" in overrides:
        fields["as_reported"] = ReportedValue(
            value=overrides.pop("value", "5.5"), unit=overrides.pop("unit", "mmol/L")
        )
    fields.update(overrides)
    return ObservationCapture(**fields)


@pytest.fixture
def registry() -> ObservableRegistry:
    """The real content/observables/registry.yaml, loaded and validated."""
    return load_registry(REGISTRY_PATH)


def make_entry(**overrides: Any) -> ObservableEntry:
    """A synthetic registry entry with tight envelopes for boundary tests.

    Physiologic [2, 10], operational [4, 8], both in canonical mmol/L.
    """
    fields: dict[str, Any] = {
        "observable": "test_obs",
        "owner": "test-owner",
        "canonical_ucum": "mmol/L",
        "accepted_units": ["mmol/L"],
        "physiologic": Envelope(low=Decimal("2"), high=Decimal("10"), version="t1"),
        "operational": Envelope(low=Decimal("4"), high=Decimal("8"), version="t1"),
        "delta_policy": DeltaPolicy(max_abs_change=Decimal("3"), within_hours=24),
        "repeat_tolerance": Decimal("0.5"),
    }
    fields.update(overrides)
    return ObservableEntry(**fields)


def make_conversion(**overrides: Any) -> Conversion:
    """A synthetic mg/dL conversion into the canonical mmol/L; override anything.

    Precision and the two round-trip tolerances are what every unit test carries
    unchanged; `from_unit`, `multiply`, and `version` are what they vary.
    """
    fields: dict[str, Any] = {
        "from_unit": "mg/dL",
        "precision": 2,
        "tolerance": Decimal("0.5"),
        "canonical_tolerance": Decimal("0.01"),
        "version": "t1",
    }
    fields.update(overrides)
    return Conversion(**fields)


def make_canonical(
    *,
    state: QualityState = QualityState.accepted,
    rejection_reasons: list[RejectionReason] | None = None,
    canonical_value: str | None = None,
    canonical_ucum: str | None = None,
    delta: DeltaVerdict | None = None,
    **capture_overrides: Any,
) -> CanonicalObservation:
    """A canonical observation as the pipeline would emit it; override anything.

    The quality verdict is built consistently with the state (§6.2). Canonical
    value defaults to the capture's as-reported value and unit — say what the
    test needs via canonical_value / canonical_ucum.
    """
    capture = make_capture(**capture_overrides)

    def quantity() -> CanonicalQuantity:
        return CanonicalQuantity(
            value=Decimal(canonical_value or capture.as_reported.value or "0"),
            ucum=canonical_ucum or capture.as_reported.unit or "mmol/L",
        )

    if state is QualityState.rejected:
        reasons = rejection_reasons or [RejectionReason.outside_physiologic_envelope]
        canonical = None if VALUELESS_REJECTIONS & set(reasons) else quantity()
        unit_resolution = (
            None
            if set(reasons) <= PRE_RESOLUTION_REJECTIONS
            else UnitResolution.ambiguous
            if RejectionReason.unit_ambiguous in reasons
            else UnitResolution.explicit
        )
        quality = QualityVerdict(
            state=state,
            unit_resolution=unit_resolution,
            rejection_reasons=reasons,
        )
    elif state is QualityState.needs_repeat_or_verification:
        canonical = quantity()
        quality = QualityVerdict(
            state=state,
            unit_resolution=UnitResolution.explicit,
            suspicions=[SuspicionReason.delta_exceeded],
            delta=delta,
        )
    else:
        canonical = quantity()
        quality = QualityVerdict(
            state=state,
            unit_resolution=UnitResolution.explicit,
            accepted_via=(
                AcceptedVia.clinician_verified
                if state is QualityState.clinically_exceptional_accepted
                else AcceptedVia.unremarkable
            ),
            delta=delta,
        )
    return CanonicalObservation(**capture.model_dump(), canonical=canonical, quality=quality)


def make_allergy(**overrides: Any) -> AllergyRecord:
    """A confirmed severe amoxicillin allergy (§5.5); override anything.

    The onset mirrors the SSOT's example shape: a partial date is a string,
    because "2019-03" is not a date.
    """
    fields: dict[str, Any] = {
        "culprit": CulpritSubstance(
            ingredient_id="amoxicillin", atc="J01CA04", source_display="Amoxicillin"
        ),
        "reaction": ("anaphylaxis",),
        "reaction_type": ReactionType.immediate_hypersensitivity,
        "severity": AllergySeverity.severe,
        "onset": AllergyOnset(timing="within 1h of first dose", date="2019-03", precision="month"),
        "verification_status": VerificationStatus.confirmed,
        "evidence_source": EvidenceSource.clinical_record,
        "recorder": Recorder(person_id="DR-7", role="physician"),
        "recorded_at": T0,
    }
    fields.update(overrides)
    return AllergyRecord(**fields)


def make_goal(**overrides: Any) -> GoalOfCare:
    """A systolic-BP goal of <150 mmHg, active for a year from T0 (§5.6); override anything."""
    fields: dict[str, Any] = {
        "observable": "systolic_bp",
        "value": Decimal("150"),
        "unit": "mmHg",
        "op": "lt",
        "reason": "High orthostatic fall risk",
        "clinician_id": "DR-7",
        "effective_date": T0,
        "expires_at": T0 + timedelta(days=365),
    }
    fields.update(overrides)
    return GoalOfCare(**fields)


def make_snapshot(**overrides: Any) -> Snapshot:
    """A well-formed evaluation snapshot; override anything.

    Collections default to empty — say what the test needs via the keyword
    arguments.
    """
    fields: dict[str, Any] = {
        "snapshot_id": "SNAP-1",
        "evaluated_at": T0,
        "patient_id": "PAT-1",
        "age_years": 67,
        "observations": (),
        "medications": (),
        "allergies": (),
        "allergy_status": AllergyStatus.recorded,
        "conditions": frozenset(),
        "goals_of_care": (),
    }
    fields.update(overrides)
    return Snapshot(**fields)


def make_requirement(**overrides: Any) -> Requirement:
    """The §7.1 eGFR requirement; override anything."""
    fields: dict[str, Any] = {
        "observable": "egfr",
        "accepted_status": (SourceStatus.final, SourceStatus.corrected),
        "min_quality": QualityState.accepted,
        "max_age_days": 90,
        "prefer_source": (EntryMode.interfaced, EntryMode.staff_transcribed),
        "required_context": ("ckd_chronicity_confirmed",),
        "on_unusable": OnUnusable.indeterminate,
        "renal_metric": "egfr",
    }
    fields.update(overrides)
    return Requirement(**fields)


def make_then(**overrides: Any) -> Then:
    """A hard stop's `then` without blocks; pass blocks where one is meant."""
    fields: dict[str, Any] = {
        "blocks": None,
        "meaning": "Metformin is contraindicated below this eGFR.",
        "action": "Discontinue metformin and select an alternative agent.",
        "uncertainty": "Based on a single eGFR. Confirm CKD chronicity before acting.",
    }
    fields.update(overrides)
    return Then(**fields)


def make_governance(**overrides: Any) -> Governance:
    """Complete §7.1(d) governance; override anything (pass None to omit)."""
    fields: dict[str, Any] = {
        "clinical_owner": NamedClinician(name="Dr. Owner", credential="Internal Medicine"),
        "clinical_approver": ClinicalApprover(
            name="Dr. Approver", credential="Endocrinology", approved_at=date(2026, 8, 1)
        ),
        "role_doubling": False,
        "effective_from": date(2026, 9, 1),
        "next_review": date(2027, 9, 1),
        "change_rationale": "Initial approval against the 2022 ADA/KDIGO consensus.",
    }
    fields.update(overrides)
    return Governance(**fields)


def make_rule(**overrides: Any) -> Rule:
    """The §7.1 metformin hard stop, reduced to the smallest complete rule."""
    fields: dict[str, Any] = {
        "id": "metformin-egfr-contraindicated",
        "version": "1.0.0",
        "release_status": ReleaseStatus.active,
        "category": "drug_safety",
        "severity": Severity.stop_and_review,
        "scope": Scope(),
        "drug_scope_level": DrugScopeLevel.ingredient,
        "requires": (make_requirement(),),
        "monitors": (
            Monitor(
                observable="egfr",
                due_in_days=90,
                reason="renal function after a metformin decision",
            ),
        ),
        "when": Expression(
            op=Operator.all,
            children=(
                Expression(
                    op=Operator.lt,
                    fact="egfr",
                    threshold_ref="metformin.egfr_absolute_contraindication",
                ),
                Expression(op=Operator.drug_active, ingredient_id="metformin"),
            ),
        ),
        "then": make_then(blocks=OrderBlock(order_of="metformin")),
        "governance": make_governance(),
    }
    fields.update(overrides)
    return Rule(**fields)


def make_citation(**overrides: Any) -> Citation:
    """The §7.3 citation of the ADA/KDIGO consensus report; override anything."""
    fields: dict[str, Any] = {
        "organisation": "ADA / KDIGO",
        "document": "Consensus Report on Diabetes Management in CKD",
        "version": "2022",
        "locator": "Metformin recommendations",
        "jurisdiction": "international",
        "evidence_grade": "consensus",
        "review_date": date(2027, 1, 1),
    }
    fields.update(overrides)
    return Citation(**fields)


def make_threshold(**overrides: Any) -> Threshold:
    """The §7.3 metformin eGFR contraindication threshold, clinician-approved."""
    fields: dict[str, Any] = {
        "ref": "metformin.egfr_absolute_contraindication",
        "value": Decimal("30"),
        "unit": "mL/min/{1.73_m2}",
        "source_family": "ada-kdigo",
        "citation": make_citation(),
        "status": ThresholdStatus.clinician_approved,
        "fallback_from": None,
        "approved_by": "Dr. Approver",
        "approved_at": date(2026, 8, 1),
    }
    fields.update(overrides)
    return Threshold(**fields)


def make_disablement(**overrides: Any) -> RuleDisablement:
    """A governed disablement with its named accountability (§10.5)."""
    fields: dict[str, Any] = {
        "rule_id": "foot-screening-annual",
        "reason": "Screening already delivered by the provider's own programme",
        "requested_by": "Dr. Requester",
        "approved_by": "Dr. Owner",
    }
    fields.update(overrides)
    return RuleDisablement(**fields)


def make_profile(**overrides: Any) -> Profile:
    """The Riyadh home-healthcare profile, pinned to the ada-kdigo family (§10.5)."""
    fields: dict[str, Any] = {
        "name": "riyadh-hh",
        "version": "3",
        "source_family": "ada-kdigo",
        "disablements": (),
    }
    fields.update(overrides)
    return Profile(**fields)


def make_pins(**overrides: Any) -> Pins:
    """The §8.2 pins at release level; snapshot_id is stamped per record later."""
    fields: dict[str, Any] = {
        "catalogue_release": "rel-2026-09-01",
        "profile": "riyadh-hh@3",
        "source_family": "ada-kdigo",
        "snapshot_id": None,
        "engine_version": ENGINE_VERSION,
        "terminology_version": "term-2026-06-01",
    }
    fields.update(overrides)
    return Pins(**fields)


def make_registry(*entries: ObservableEntry) -> ObservableRegistry:
    """A registry from synthetic entries, keyed by each entry's observable."""
    return ObservableRegistry(entries={entry.observable: entry for entry in entries})


def make_release(**overrides: Any) -> CatalogueRelease:
    """A release holding the metformin hard stop and its §7.3 threshold."""
    fields: dict[str, Any] = {
        "release_id": "rel-2026-09-01",
        "rules": (make_rule(),),
        "thresholds": (make_threshold(),),
        "profile": make_profile(),
    }
    fields.update(overrides)
    return CatalogueRelease(**fields)


def make_context(**overrides: Any) -> EvaluationContext:
    """The evaluation context binding the release to a synthetic egfr registry.

    The registry entry carries egfr's canonical UCUM unit, so the default
    release loads whole and tests vary one piece at a time.
    """
    fields: dict[str, Any] = {
        "release": make_release(),
        "registry": make_registry(
            make_entry(
                observable="egfr",
                canonical_ucum="mL/min/{1.73_m2}",
                accepted_units=["mL/min/{1.73_m2}"],
            )
        ),
        "pins": make_pins(),
    }
    fields.update(overrides)
    return EvaluationContext(**fields)
