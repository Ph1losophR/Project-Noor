"""Shared builders and fixtures (docs/testing-standards.md: factories live here)."""

import os
from datetime import UTC, datetime
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
