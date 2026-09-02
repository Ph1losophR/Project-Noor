"""The Emergency: an interrupt with a timeline, and a gate on both exits (§5.7)."""
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EntryKind(Enum):
    """What a timeline line is. Two kinds, and neither is a severity (ADR 0004)."""

    OBSERVED = "observed"
    DONE = "done"


class EmergencyError(ValueError):
    """A timeline that does not hold together in time."""


class UnresolvedEmergency(Exception):
    """A Visit tried to close over an Emergency that never ended, or that ended
    with an empty timeline (§5.7)."""


@dataclass(frozen=True)
class TimelineEntry:
    kind: EntryKind
    text: str
    at: datetime


@dataclass
class EmergencyRecord:
    """One entry into Emergency. A re-entry is a second record, not a second row."""

    started_at: datetime
    entries: list[TimelineEntry] = field(default_factory=list)
    ended_at: datetime | None = None

    @property
    def has_ended(self) -> bool:
        return self.ended_at is not None

    @property
    def is_documented(self) -> bool:
        """One timeline entry is the floor. Zero is a Visit that says nothing."""
        return bool(self.entries)

    @property
    def is_resolved(self) -> bool:
        """Ended *and* documented — §5.7's stricter bar, with no reason path."""
        return self.has_ended and self.is_documented

    def record(self, kind: EntryKind, text: str, at: datetime) -> None:
        if at < self.started_at:
            raise EmergencyError(f"a timeline entry at {at:%H:%M} predates the Emergency")
        self.entries.append(TimelineEntry(kind, text, at))

    def resolve(self, at: datetime) -> None:
        """The exit carries no reason of its own (§5.7) — only the time it ended."""
        if self.has_ended:
            raise EmergencyError(f"the Emergency already ended at {self.ended_at:%H:%M}")
        if at < self.started_at:
            raise EmergencyError(f"an Emergency cannot end at {at:%H:%M}, before it began")
        self.ended_at = at



def check_all_resolved(records: Sequence[EmergencyRecord]) -> None:
    """Guard: no terminal state while any Emergency is open — Ended Early too (§5.8)."""
    unresolved = [r for r in records if not r.is_resolved]
    if unresolved:
        raise UnresolvedEmergency(
            "an Emergency must have ended and been written down before the Visit "
            "closes; still outstanding: "
            + ", ".join(f"entered {r.started_at:%H:%M}" for r in unresolved)
        )
