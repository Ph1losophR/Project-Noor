"""Which Visits reach the Supervisor, and by when (§5.12).

Four routes and no fifth. Three of them are properties of one Visit and are here from the
start; the fourth — the Silence Audit — is a sample across many Visits, and Task 21 appends
it to this module because its arithmetic is clinical policy and takes no connection either.
What that route needs and this module must not have is the query for a week of closed
Visits, which is the store's (Task 21).

Everything here is derived on read. §5.1: 'This Visit has items awaiting review' is
'derived on read, never stored. A stored flag is a second copy of the truth that goes
stale the moment an item is signed.'
"""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import IntEnum
from typing import NamedTuple

from noor.domain.opinions import Flag
from noor.domain.plans import GoalOfCare, ratification_due
from noor.domain.states import EscalationTier, VisitKind
from noor.domain.visit import Visit
from noor.domain.writeback import Windows, response_due

GOAL_OF_CARE = "goal-of-care"
"""The subject of a ratification review. Not a Recommendation id, and never collides
with one: §4.4 makes the target the Patient's, not the Visit's."""


class Route(IntEnum):
    """§5.12's four routes. The integer is that table's row order, so sorting a mixed
    inbox by route needs no lookup table anywhere else."""

    TIER = 1
    RATIFICATION = 2
    MANUAL_FLAG = 3
    SILENCE_AUDIT = 4


class Review(NamedTuple):
    """One row of the Supervisor's inbox.

    `due_at` is `None` where nobody owes an answer by a time — Tier 3 (ADR 0001) and the
    Silence Audit, which is a sampling rate rather than a deadline (§5.12).
    """

    route: Route
    visit_id: str
    patient_id: str
    subject: str
    due_at: datetime | None


class VerdictError(ValueError):
    """A Review Verdict missing the note a disagreement must carry (§5.12)."""


@dataclass(frozen=True)
class Verdict:
    """The Supervisor's answer to one routed item (§5.12, ADR 0009): agreed or not, who,
    when, and the note a disagreement must carry. It removes the inbox row and does nothing
    else — never reopens a Visit, never gates a close (§5.9)."""

    agreed: bool
    by: str
    at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        if not (self.by or "").strip():
            raise VerdictError("a verdict carries a name (§5.13)")
        if not self.agreed and not (self.note or "").strip():
            raise VerdictError(
                "a disagreement carries a note (§5.12) — an answer nobody can read is a "
                "mark, not an answer")


class VerdictKey(NamedTuple):
    """What identifies the item a Verdict answers: the Visit, the route, and the subject
    within it. The same triple the `verdicts` table is keyed on."""

    visit_id: str
    route: Route
    subject: str


def key(review: Review) -> VerdictKey:
    """The identity of the item this row raises, so a stored Verdict matches back to it."""
    return VerdictKey(review.visit_id, review.route, review.subject)


def unanswered(
    rows: Sequence[Review], answered: set[VerdictKey]
) -> tuple[Review, ...]:
    """The inbox: the derived rows no Verdict has closed (ADR 0009). A row leaves only when
    its Verdict is recorded — nothing here clears by being read (§5.1)."""
    return tuple(row for row in rows if not _closed(row, answered))


def _closed(row: Review, answered: set[VerdictKey]) -> bool:
    """A Ratification row is never closed by a Verdict: agreeing *is* ratifying, and a
    ratified Goal stops raising the route through `reviews()` itself, so a Verdict on it
    would be a second copy (ADR 0009). Every other route closes on its Verdict."""
    return row.route is not Route.RATIFICATION and key(row) in answered


def reviews(
    visit: Visit,
    *,
    goal: GoalOfCare | None,
    windows: Windows,
    at: datetime,
) -> tuple[Review, ...]:
    """Every route this one Visit raises, in §5.12's order.

    Ordered here so no screen sorts, and returned whole so an empty tuple is a real
    answer: this Visit reaches the Supervisor by none of the three, which is what makes
    the Silence Audit necessary rather than decorative.
    """
    tiered = tuple(
        _review(Route.TIER, visit, item.id, response_due(item.tier, at, windows))
        for item in visit.shown
        if item.tier is not EscalationTier.TIER_0)
    flagged = tuple(
        _review(Route.MANUAL_FLAG, visit, item.subject,
                response_due(_flag_tier(visit, item), item.at, windows,
                             manually_flagged=True))
        for item in visit.flags)
    return tiered + _ratification(visit, goal, windows) + flagged


def _ratification(
    visit: Visit, goal: GoalOfCare | None, windows: Windows
) -> tuple[Review, ...]:
    """§4.4: the target is proposed at the Baseline and ratified once. A Routine Visit
    compares against it and never resets it, so only a Baseline raises this route — and
    a settled decision returning to the inbox is the inbox losing its meaning."""
    if visit.kind is not VisitKind.BASELINE or goal is None or goal.is_ratified:
        return ()
    return (_review(Route.RATIFICATION, visit, GOAL_OF_CARE,
                    ratification_due(goal, windows.ratification_days)),)


def _flag_tier(visit: Visit, item: Flag) -> EscalationTier:
    """The flagged item's tier, or Tier 0 where the subject has none — §5.11 lets the
    Junior Physician send a reading, a Finding or a whole section. Tier 0 is not a claim
    about severity here; it is the row in `response_due` carrying the flag's own window.
    """
    tiers = {shown.id: shown.tier for shown in visit.shown}
    return tiers.get(item.subject, EscalationTier.TIER_0)


def _review(
    route: Route, visit: Visit, subject: str, due_at: datetime | None
) -> Review:
    """The Visit and the Patient travel with every row: an inbox line reading 'ratify
    135/85' has stripped the lineage that makes it reviewable, and N5's automation-bias
    mitigation *is* the display of that reasoning."""
    return Review(route, visit.id, visit.patient_id, subject, due_at)


def band(review: Review) -> tuple[int, datetime | None]:
    """§5.2's three bands as a sort key, lowest first: Tier 3 (due now, no due time), then
    whatever carries a due time soonest-first, then the Silence Audit (a rate, never late).
    Within a band the second slot is homogeneous — all None in bands 1 and 3, all datetimes
    in band 2 — so a None due time is never compared against a real one."""
    if review.route is Route.SILENCE_AUDIT:
        return (3, None)
    if review.due_at is None:
        return (1, None)
    return (2, review.due_at)


SILENT_VISIT = "silent-visit"
"""The subject of an audit row. The Visit *is* the thing being reviewed — there is no
Recommendation to name, which is the entire point of the route."""


@dataclass(frozen=True)
class Sampling:
    """`response-windows.md`'s `[audit]` table, as data (ADR 0007)."""

    silent_visit_rate: float
    minimum_per_week: int


def sampling(table: Mapping[str, object]) -> Sampling:
    """A missing key raises `KeyError` naming the field — ADR 0007's loud failure."""
    return Sampling(float(table["silent_visit_rate"]),
                    int(table["minimum_per_week"]))


def week_start(day: date) -> date:
    """The Sunday of `day`'s week. The Saudi working week runs Sunday to Thursday and
    `date.weekday()` counts from Monday, hence the shift. The floor is *one per week*, so
    the week has to be a thing with edges before it can have a floor."""
    return day - timedelta(days=(day.weekday() + 1) % 7)


def silence_audit(visits: Sequence[Visit], policy: Sampling) -> tuple[Review, ...]:
    """§5.12's fourth route: sampled Completed Visits that produced no Recommendation.

    Every row's `due_at` is `None`. §5.12 gives this route *a sampling rate rather than a
    deadline* — nobody owes an answer by a time, they owe a look.

    In Phase 1 *produced nothing* is `shown` being empty, because there is no producer and
    so no cap (§8). When **Filed** arrives with the cap in Phase 3, a Visit whose only
    Recommendations were Filed is not silent — it is capped, and that is a different
    finding needing a different route.
    """
    silent = sorted((visit for visit in visits if not visit.shown),
                    key=lambda visit: visit.id)
    size = _sample_size(len(silent), policy)
    # `index * len // size` spreads the sample across the week instead of taking its
    # first few, and never divides by zero: at size 0 the loop body never runs.
    chosen = [silent[index * len(silent) // size] for index in range(size)]
    return tuple(_review(Route.SILENCE_AUDIT, visit, SILENT_VISIT, None)
                 for visit in chosen)


def _sample_size(population: int, policy: Sampling) -> int:
    """How many silent Visits the Supervisor reviews this week.

    The `max` is the floor and the floor is the rule: at four silent Visits the rate
    truncates to nothing, and a week of unreviewed silence is what §4.1 says the whole
    deliverable is judged on. The `min` is the other direction — a week with one silent
    Visit reviews that one and cannot invent a second.

    `int()` truncates, and 0.1 is a hair *above* one tenth in binary, so the product never
    lands just under a whole number: the truncation only ever drops a real fraction.
    """
    return min(population, max(policy.minimum_per_week,
                               int(population * policy.silent_visit_rate)))
