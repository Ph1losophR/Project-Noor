"""The Vitals section's measurements, and Home Readings (§4.2, §4.8).

Two series of the same quantities with different observers, kept apart by their types:
Vitals is what the Field Team measured in the house, Home Readings are what the household
took between Visits. Nothing here returns both together.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from noor.domain.examination import applies
from noor.domain.states import VisitKind


class VitalsError(ValueError):
    """A reading that is not a reading."""


class Source(Enum):
    """Where a Home Reading came from. Displayed with every Finding built on it (N5)."""

    DEVICE_MEMORY = "device memory"
    PAPER_LOG = "Caregiver paper log"


@dataclass(frozen=True)
class Measurement:
    """One row of `vitals-by-condition.md`. No source field: see the module docstring."""

    id: str
    label: str
    unit: str
    conditions: tuple[str, ...]
    baseline_only: bool = False


@dataclass(frozen=True)
class HomeReading:
    """A value, a time, and which of the two sources it came from — never optional."""

    measurement: str
    value: str
    taken_at: datetime
    source: Source

    def __post_init__(self) -> None:
        if not self.value:
            raise VitalsError(f"{self.measurement}: a reading with no value is not a reading")


def measurements(rows: Sequence[Mapping[str, object]]) -> tuple[Measurement, ...]:
    return tuple(
        Measurement(row["id"], row["label"], row["unit"], tuple(row["conditions"]),
                    row.get("baseline_only", False))
        for row in rows
    )


def asked_for(
    catalogue: Sequence[Measurement],
    *,
    conditions: Sequence[str],
    kind: VisitKind,
) -> tuple[Measurement, ...]:
    """What the Vitals section asks for, in the file's order — which is the form's order."""
    held = set(conditions)
    return tuple(
        m for m in catalogue
        if applies(m.conditions, held)
        and (kind is VisitKind.BASELINE or not m.baseline_only)
    )
