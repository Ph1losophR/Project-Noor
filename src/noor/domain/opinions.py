"""Findings and Recommendations — the shape, with nothing in Phase 1 producing one."""
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from noor.domain.records import OTHER, Reason
from noor.domain.states import EscalationTier


class Outcome(Enum):
    """What a Field Team did with a shown Recommendation. Two, and both proceed."""

    ACCEPTED = "accepted"
    OVERRIDDEN = "overridden"


class OverrideLevel(Enum):
    """§5.10's two levels: fix the rule, or fix the supply chain."""

    RULE_WRONG_HERE = "rule_wrong_here"
    COULD_NOT_ACT = "could_not_act"


class OpinionError(ValueError):
    """A Finding, Recommendation or Disposition that is missing what it needs."""


class Undispositioned(Exception):
    """A shown Recommendation nobody answered. Completed requires all of them (§5.8)."""


@dataclass(frozen=True)
class Finding:
    """An observation about the Patient. Never an instruction (CONTEXT.md)."""

    id: str
    text: str


@dataclass(frozen=True)
class Recommendation:
    """One executable action, one tier, a named Executor, and its lineage (N2, N5)."""

    id: str
    text: str
    tier: EscalationTier
    executor: str
    provenance: str
    strength: str

    def __post_init__(self) -> None:
        if not self.executor:
            raise OpinionError(f"{self.id}: a Recommendation needs a named Executor (N2)")
        if not self.provenance:
            raise OpinionError(f"{self.id}: a Recommendation needs its provenance (N5)")
        if not self.strength:
            raise OpinionError(f"{self.id}: a Recommendation needs its strength (N5)")


@dataclass(frozen=True)
class Disposition:
    """What was decided, by whom, and when. An override never blocks (N4)."""

    recommendation_id: str
    outcome: Outcome
    by: str
    at: datetime
    level: OverrideLevel | None = None
    reason: Reason | None = None

    def __post_init__(self) -> None:
        if not self.by:
            raise OpinionError("a disposition is a decision and carries a name (§5.13)")
        overridden = self.outcome is Outcome.OVERRIDDEN
        if overridden and (self.level is None or self.reason is None):
            raise OpinionError("an override carries a level and a row (§5.10)")
        if not overridden and (self.level is not None or self.reason is not None):
            raise OpinionError("only an override carries a level and a row")
        if self.reason is not None and self.reason.row_id == OTHER and not self.reason.free_text:
            raise OpinionError("the Other row needs its free text (§5.10)")


@dataclass(frozen=True)
class Flag:
    """The Junior Physician sending something to the Supervisor (§5.11).

    `subject` is a Recommendation id, or the name of anything else in the Visit — §5.11
    says *anything*, at any time, and routing is a floor the software may add to. It
    lives here rather than in `supervisor.py` because a Visit carries these, and a Visit
    importing the module that reads Visits is a cycle.
    """

    subject: str
    by: str
    at: datetime
    note: str

    def __post_init__(self) -> None:
        if not self.by or not self.note:
            raise OpinionError(
                "a flag carries who sent it and why (§5.13) — a Supervisor guessing "
                "at why something is in their inbox is the flag not working")


def check_all_dispositioned(
    shown: Sequence[Recommendation], dispositions: Sequence[Disposition]
) -> None:
    """Guard: every *shown* Recommendation has an answer, accepted or overridden."""
    answered = {d.recommendation_id for d in dispositions}
    shown_ids = {r.id for r in shown}
    stray = answered - shown_ids
    if stray:
        raise OpinionError(f"dispositions for Recommendations never shown: {sorted(stray)}")
    outstanding = sorted(shown_ids - answered)
    if outstanding:
        raise Undispositioned(f"no disposition recorded for: {', '.join(outstanding)}")
