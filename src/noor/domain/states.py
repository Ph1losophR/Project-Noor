"""The enumerations the whole system is welded to (SSOT §5.1, §4.2, ADR 0001)."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum


class VisitState(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    EMERGENCY = "emergency"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ENDED_EARLY = "ended_early"


TERMINAL = frozenset(
    {VisitState.COMPLETED, VisitState.CANCELLED, VisitState.ENDED_EARLY}
)


class Section(IntEnum):
    """The record's fixed order. The integer *is* the position (§4.2)."""
    VISIT_REASON = 1
    CONCERNS_AND_INTERVAL_HISTORY = 2
    MEDICATION_RECONCILIATION = 3
    VITALS = 4
    PHYSICAL_EXAMINATION = 5
    SELF_CARE_CHECK = 6
    CARE_PLAN = 7
    NOTES = 8


class EscalationTier(IntEnum):
    """Ordered by time-to-action, never by severity (ADR 0001)."""
    TIER_0 = 0
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


RECOMMENDATION_CAP = 3  # N3, §4.7. Welded on purpose (ADR 0007) — never a setting.


class DataState(Enum):
    """Exactly three. Staleness is as_of on a PRESENT value, not a fourth (§1.1)."""
    PRESENT = "present"
    ABSENT = "absent"
    UNREACHABLE = "unreachable"


@dataclass(frozen=True)
class Datum:
    state: DataState
    value: object | None = None
    as_of: datetime | None = None

    def __post_init__(self) -> None:
        if self.state is DataState.PRESENT:
            if self.value is None or self.as_of is None:
                raise ValueError("a Present Datum needs a value and an as_of time")
        elif self.value is not None or self.as_of is not None:
            raise ValueError(f"{self.state.value} carries no value and no as_of")

    @classmethod
    def present(cls, value: object, as_of: datetime | None) -> "Datum":
        return cls(DataState.PRESENT, value, as_of)

    @classmethod
    def absent(cls) -> "Datum":
        return cls(DataState.ABSENT)

    @classmethod
    def unreachable(cls) -> "Datum":
        return cls(DataState.UNREACHABLE)

    @property
    def is_present(self) -> bool:
        return self.state is DataState.PRESENT

    def __bool__(self) -> bool:
        raise TypeError(
            "a Datum has three states (§1.1) — read .state, never its truthiness"
        )


# §5.1's whole state machine. Seven pairs; the other twenty-nine are refusals.
LEGAL_TRANSITIONS = frozenset({
    (VisitState.SCHEDULED, VisitState.IN_PROGRESS),
    (VisitState.SCHEDULED, VisitState.CANCELLED),
    (VisitState.IN_PROGRESS, VisitState.COMPLETED),
    (VisitState.IN_PROGRESS, VisitState.ENDED_EARLY),
    (VisitState.IN_PROGRESS, VisitState.EMERGENCY),
    (VisitState.EMERGENCY, VisitState.IN_PROGRESS),
    (VisitState.EMERGENCY, VisitState.ENDED_EARLY),
})


class IllegalTransition(Exception):
    """A transition §5.1 does not have. Terminal states have none at all (§5.9)."""

    def __init__(self, source: VisitState, target: VisitState) -> None:
        super().__init__(f"a {source.value} Visit cannot become {target.value}")
        self.source = source
        self.target = target


def check_transition(source: VisitState, target: VisitState) -> None:
    """Guard, not predicate: returns None or raises. A caller cannot ignore it."""
    if (source, target) not in LEGAL_TRANSITIONS:
        raise IllegalTransition(source, target)


class VisitKind(Enum):
    """Which Visit Protocol variant runs (§5.5). Settled by the Start, never scheduled."""
    BASELINE = "baseline"
    ROUTINE = "routine"
