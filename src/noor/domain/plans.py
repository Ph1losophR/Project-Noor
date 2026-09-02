"""The Goal of Care (§4.4) and the Between-Visit Plan the last section emits (§4.8)."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class Axis(Enum):
    """What a target, a schedule or a stop rule is about — §4.4's table."""

    SYSTOLIC = "systolic"
    DIASTOLIC = "diastolic"
    HBA1C = "hba1c"
    GLUCOSE_PRE_PRANDIAL = "glucose_pre_prandial"
    GLUCOSE_POST_PRANDIAL = "glucose_post_prandial"


class Comparison(Enum):
    ABOVE = "above"
    BELOW = "below"


class PlanError(ValueError):
    """A target or a plan line a machine cannot test (§4.8)."""


@dataclass(frozen=True)
class Band:
    """A floor and a ceiling, stated as the home numbers themselves (§4.4).

    Both bounds None *with* a rationale is the deliberate "no numeric target"
    value; both None without one is "not yet set", which is what the ratification
    gate withholds against. The two must not look alike.
    """

    axis: Axis
    floor: float | None
    ceiling: float | None
    rationale: str | None = None

    def __post_init__(self) -> None:
        if self.floor is None and self.ceiling is None:
            if not self.rationale:
                raise PlanError(
                    f"{self.axis.value}: no numeric target is a value and needs its "
                    "rationale; without one this is 'not yet set'"
                )
        elif self.floor is None or self.ceiling is None:
            raise PlanError(
                f"{self.axis.value}: every axis is a band, never a bare ceiling"
            )
        elif self.floor >= self.ceiling:
            raise PlanError(
                f"{self.axis.value}: a band runs floor to ceiling, "
                f"not {self.floor} to {self.ceiling}"
            )

    @property
    def is_numeric(self) -> bool:
        return self.floor is not None


@dataclass(frozen=True)
class GoalOfCare:
    """Proposed by the Junior Physician, ratified by the Supervisor, then persistent."""

    patient_id: str
    bands: tuple[Band, ...]
    lineage: str
    office_anchor: str
    proposed_by: str
    proposed_at: datetime
    ratified_by: str | None = None
    ratified_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.bands:
            raise PlanError("a Goal of Care with no band in it is not a target")
        axes = [band.axis for band in self.bands]
        if len(set(axes)) != len(axes):
            raise PlanError("a Goal of Care carries one band per axis, never two")
        if not self.lineage or not self.office_anchor:
            raise PlanError(
                "a target carries the guideline it came from and the office anchor "
                "it was written against (N5, §4.4) — displayed, never recomputed"
            )
        if (self.ratified_by is None) != (self.ratified_at is None):
            raise PlanError("ratification carries a name and a time, or neither")

    @property
    def is_ratified(self) -> bool:
        return self.ratified_at is not None


def ratification_due(goal: GoalOfCare, days: int) -> datetime:
    """The window is content (`response-windows.md`), so it arrives as an argument."""
    return goal.proposed_at + timedelta(days=days)


@dataclass(frozen=True)
class Threshold:
    """A number and what to do when it is crossed. Both, or it is prose (§4.8)."""

    axis: Axis
    comparison: Comparison
    value: float
    action: str

    def __post_init__(self) -> None:
        if not self.action:
            raise PlanError(
                f"{self.axis.value} {self.comparison.value} {self.value} "
                "with no action against it is prose with a number in it"
            )


@dataclass(frozen=True)
class MeasurementSchedule:
    axis: Axis
    times_per_week: int

    def __post_init__(self) -> None:
        if self.times_per_week < 1:
            raise PlanError(
                f"{self.axis.value}: {self.times_per_week} a week is not a schedule"
            )


@dataclass(frozen=True)
class BetweenVisitPlan:
    """Titration steps, the home measurement schedule, and the stop rules (§4.8)."""

    titration: tuple[Threshold, ...] = ()
    schedule: tuple[MeasurementSchedule, ...] = ()
    stop_rules: tuple[Threshold, ...] = ()

    def __post_init__(self) -> None:
        if not (self.titration or self.schedule or self.stop_rules):
            raise PlanError("a Between-Visit Plan with no line in it is not a plan")


def check_titration_allowed(plan: BetweenVisitPlan, goal: GoalOfCare | None) -> None:
    """Guard: titration needs a ratified target to titrate toward (§4.8, §4.11)."""
    if plan.titration and (goal is None or not goal.is_ratified):
        raise PlanError(
            "titration steps need a ratified Goal of Care; the schedule and the "
            "stop rules do not, and a Baseline Visit's plan carries those"
        )
