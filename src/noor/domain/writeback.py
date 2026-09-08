"""The seven structured writes (§4.9), each with an owner and a due time where one is owed.

Pure. Nothing here calls the EMR — `assemble` is a function of its arguments, so the whole
shape is testable with no boundary in sight, and Task 18 does the sending.
"""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from enum import IntEnum

from noor.domain.opinions import Disposition, Recommendation
from noor.domain.plans import BetweenVisitPlan, GoalOfCare, ratification_due
from noor.domain.records import Reason
from noor.domain.states import Datum, EscalationTier, Section, VisitKind, VisitState
from noor.domain.visit import Addendum, Visit
from noor.domain.vitals import HomeReading


class Kind(IntEnum):
    """§4.9's seven writes, in that table's order — the integer *is* the row number. The
    eighth is not one of the seven: it is the Addendum's own Write-Back (§6.2, §5.9), sent
    after the Visit's and carrying no owner and no due time because it asks for nothing."""

    VISIT_OUTCOME = 1
    OBSERVATIONS = 2
    SELF_CARE_FINDINGS = 3
    RECONCILIATION = 4
    RECOMMENDATIONS = 5
    BETWEEN_VISIT_PLAN = 6
    PROPOSED_GOAL_OF_CARE = 7
    ADDENDUM = 8


@dataclass(frozen=True)
class Windows:
    """`response-windows.md`'s `[windows]` table, as data (ADR 0007)."""

    tier_1_hours: int
    tier_2_hours: int
    ratification_days: int


def windows(table: Mapping[str, object]) -> Windows:
    """A missing key raises `KeyError` naming the field, which is ADR 0007's loud failure:
    a half-loaded escalation policy is worse than none, because nobody is told."""
    return Windows(**{field.name: int(table[field.name]) for field in fields(Windows)})


@dataclass(frozen=True)
class Response:
    """A named owner and a due time. Both required, both positional — so §4.9's
    'no owner and no due time is narrative text wearing structure's clothes' is a thing
    that cannot be constructed rather than a thing that gets validated."""

    owner: str
    due_at: datetime

    def as_json(self) -> dict[str, str]:
        return {"owner": self.owner, "due_at": self.due_at.isoformat()}


@dataclass(frozen=True)
class WriteBack:
    """One structured item, ready for `emr.submit(patient_id, payload)`."""

    kind: Kind
    payload: dict[str, object]


def response_due(
    tier: EscalationTier,
    at: datetime,
    windows: Windows,
    *,
    manually_flagged: bool = False,
) -> datetime | None:
    """When the Supervisor owes an answer, or `None` where nobody does.

    Tier 0 is a note for the record. Tier 3 is now, with the Supervisor off the critical
    path — ADR 0001: 'Tier 3 exists specifically so a genuine emergency does not queue
    behind a human,' so a deadline on it would put the bottleneck back. Neither is a
    number `response-windows.md` records. The one exception is §5.12's manual flag on a
    Tier 0 item, which borrows Tier 1's window — read from `tier_1_hours` rather than held
    as a fourth number, so the two cannot drift apart in a content edit.
    """
    if tier is EscalationTier.TIER_1:
        return at + timedelta(hours=windows.tier_1_hours)
    if tier is EscalationTier.TIER_2:
        # Zero by definition, so the item arrives already overdue (§5.11). Intended.
        return at + timedelta(hours=windows.tier_2_hours)
    if tier is EscalationTier.TIER_0 and manually_flagged:
        return at + timedelta(hours=windows.tier_1_hours)
    return None


def _declare(datum: Datum) -> dict[str, object]:
    """A `Datum` as JSON with its state named. The EMR must never be able to read a
    failed request as a clinical finding (N6), so 'unreachable' is a word it receives."""
    if datum.is_present:
        return {"state": datum.state.value, "as_of": datum.as_of.isoformat()}
    return {"state": datum.state.value}


def _reason(reason: Reason | None) -> dict[str, object] | None:
    if reason is None:
        return None
    return {"row_id": reason.row_id, "free_text": reason.free_text}


def _content(visit: Visit, section: Section) -> Mapping[str, object] | None:
    """A section's content, or `None` where it was resolved by a reason or never run.
    §5.8 makes both of those a passing Visit, and neither has anything to report."""
    resolution = visit.resolutions.get(section)
    if resolution is None:
        return None
    return resolution.content


def _plan_json(plan: BetweenVisitPlan) -> dict[str, object]:
    """Machine-testable lines (§4.8). `serial` has the same shapes for the store; this is
    the EMR's copy, and the two are allowed to diverge without one breaking the other."""
    return {
        "titration": [_threshold(rule) for rule in plan.titration],
        "schedule": [{"axis": item.axis.value, "times_per_week": item.times_per_week}
                     for item in plan.schedule],
        "stop_rules": [_threshold(rule) for rule in plan.stop_rules],
    }


def _threshold(rule) -> dict[str, object]:
    return {"axis": rule.axis.value, "comparison": rule.comparison.value,
            "value": rule.value, "action": rule.action}


def _home(reading: HomeReading) -> dict[str, object]:
    """The source travels with the reading, always (§4.8)."""
    return {"measurement": reading.measurement, "value": reading.value,
            "taken_at": reading.taken_at.isoformat(), "source": reading.source.value}


def _something(parts: dict[str, object]) -> dict[str, object] | None:
    """Nothing observed is nothing written. An empty payload would tell the EMR the Field
    Team looked and found normal, which is a clinical claim nobody made."""
    if any(value for value in parts.values()):
        return parts
    return None


def _outcome(visit: Visit) -> dict[str, object]:
    """§4.9 item 1. Every Visit that closed after starting writes exactly this."""
    payload: dict[str, object] = {
        "state": visit.state.value,
        # Never None here: `assemble` has already refused a Visit that did not start.
        "started_at": visit.started_at.isoformat(),
        "closed_by": visit.closed_by,
        "closed_at": visit.closed_at.isoformat(),
        "reason": _reason(visit.closing_reason),
        # ADR 0004 makes the duration clinical data, so it folds in here rather than
        # becoming an eighth row (§4.9's third collapse).
        "emergencies": [{"started_at": record.started_at.isoformat(),
                         "ended_at": record.ended_at.isoformat()}
                        for record in visit.emergencies],
        "sections_not_run": [section.name for section in Section
                             if section not in visit.resolutions],
    }
    if visit.state is VisitState.ENDED_EARLY:
        # §5.6: the previous plan stands, and the EMR is told which one — three states,
        # three different sentences, because 'none' and 'unreadable' are not the same fact.
        payload["previous_plan_in_force"] = _declare(visit.previous_plan)
    return payload


def _observations(visit: Visit) -> dict[str, object] | None:
    """§4.9 item 2. Vitals and Home Readings stay in separate keys — same quantities, a
    different observer, and `CONTEXT.md` says never merged into one series."""
    return _something({
        "vitals": _content(visit, Section.VITALS),
        "examination": _content(visit, Section.PHYSICAL_EXAMINATION),
        "home_readings": [_home(reading) for reading in visit.home_readings],
    })


def _status(answer: Disposition | None) -> str:
    """Two statuses, because Phase 1 has two dispositions. §4.9 item 5's other two —
    **suppressed** (ADR 0002) and **Filed** with its deferral count (§4.7) — arrive with
    the engine. An Ended Early can leave one unanswered, and that is recorded as such
    rather than defaulted to accepted."""
    if answer is None:
        return "not answered"
    return answer.outcome.value


def _override(answer: Disposition | None) -> dict[str, object] | None:
    if answer is None or answer.reason is None:
        return None
    return {"level": answer.level.value, **_reason(answer.reason)}


def _recommendation(
    rec: Recommendation,
    answer: Disposition | None,
    at: datetime,
    windows: Windows,
    supervisor: str,
) -> dict[str, object]:
    """Its lineage travels with it (N5): the automation-bias mitigation *is* the display
    of the reasoning, and an unsourced instruction in a chart cannot be argued with."""
    due = response_due(rec.tier, at, windows)
    return {
        "id": rec.id, "text": rec.text, "tier": rec.tier.value,
        "executor": rec.executor, "provenance": rec.provenance, "strength": rec.strength,
        "status": _status(answer),
        "reason": _override(answer),
        "response": None if due is None else Response(supervisor, due).as_json(),
    }


def _recommendations(
    visit: Visit, at: datetime, windows: Windows, supervisor: str
) -> dict[str, object] | None:
    """§4.9 item 5, and its second collapse: shown, suppressed and Filed are one item and
    not three, because the N3 cap is a display constraint and not a data constraint."""
    answers = {answer.recommendation_id: answer for answer in visit.dispositions}
    return _something({"recommendations": [
        _recommendation(rec, answers.get(rec.id), at, windows, supervisor)
        for rec in visit.shown]})


def _between_visit_plan(visit: Visit) -> dict[str, object] | None:
    if visit.plan is None:
        return None
    return _plan_json(visit.plan)


def _goal(
    visit: Visit, goal: GoalOfCare | None, windows: Windows, supervisor: str
) -> dict[str, object] | None:
    """§4.9 item 7 — 'the one write that is itself a request for a response.' Baseline
    Visits only: a Routine Visit reasons against the ratified target (§4.4) and does not
    re-propose it, which would put the Supervisor's own settled decision back in their
    inbox."""
    if visit.kind is not VisitKind.BASELINE or goal is None:
        return None
    return {
        "patient_id": goal.patient_id,
        "bands": [{"axis": band.axis.value, "floor": band.floor,
                   "ceiling": band.ceiling, "rationale": band.rationale}
                  for band in goal.bands],
        "lineage": goal.lineage,
        "office_anchor": goal.office_anchor,
        "proposed_by": goal.proposed_by,
        "proposed_at": goal.proposed_at.isoformat(),
        "response": Response(
            supervisor, ratification_due(goal, windows.ratification_days)).as_json(),
    }


# Written back at the close (§4.9). A Cancelled Visit writes nothing at all (§5.4), and
# neither does one still open — there is nothing to report about an attendance in progress.
WRITTEN_BACK = frozenset({VisitState.COMPLETED, VisitState.ENDED_EARLY})


def assemble(
    visit: Visit,
    *,
    goal: GoalOfCare | None,
    at: datetime,
    windows: Windows,
    supervisor: str,
) -> tuple[WriteBack, ...]:
    """§4.9's seven, in the SSOT's order, minus the ones this Visit has nothing for.

    `at` is the time the Visit closed and every due time is derived from it — no clock is
    read here, which is §5.5 and the reason a test can pin the whole result.
    """
    if visit.state not in WRITTEN_BACK:
        return ()
    items = [WriteBack(Kind.VISIT_OUTCOME, _outcome(visit))]
    _add(items, Kind.OBSERVATIONS, _observations(visit))
    _add(items, Kind.SELF_CARE_FINDINGS, _content(visit, Section.SELF_CARE_CHECK))
    _add(items, Kind.RECONCILIATION, _content(visit, Section.MEDICATION_RECONCILIATION))
    _add(items, Kind.RECOMMENDATIONS, _recommendations(visit, at, windows, supervisor))
    _add(items, Kind.BETWEEN_VISIT_PLAN, _between_visit_plan(visit))
    _add(items, Kind.PROPOSED_GOAL_OF_CARE, _goal(visit, goal, windows, supervisor))
    return tuple(items)


def _add(items: list[WriteBack], kind: Kind, payload) -> None:
    """One place decides that nothing to say means nothing written, so six items cannot
    each get that decision slightly wrong."""
    if payload is not None:
        items.append(WriteBack(kind, dict(payload)))


def addendum_item(addendum: Addendum) -> WriteBack:
    """The Addendum's own Write-Back item (§6.2). No owner and no due time — it records an
    addition and asks for nothing (§4.9, CONTEXT.md). `assemble` is untouched: this is a
    separate send, after the Visit's, not one of the close's seven."""
    return WriteBack(Kind.ADDENDUM, {
        "visit_id": addendum.visit_id,
        "text": addendum.text,
        "author": addendum.author,
        "written_at": addendum.written_at.isoformat(),
    })
