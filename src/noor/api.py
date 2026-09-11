"""The JSON API the static SPA talks to (docs/frontend_ssot.md §12, ADR 0006).

Above the seam: it may touch the store and the versioned content, never the
domain's decision path beyond calling what a route needs. Each handler parses
its request, calls one tested function, and serialises the answer — no clinical
judgement lives here, so the coverage gate can see all of it.
"""
from datetime import date, datetime
from json import JSONDecodeError
import json
import sqlite3
from pathlib import Path
from typing import cast

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from noor import content, dispatch, prefetch, store
from noor import serial
from noor.domain.brief import Brief, brief
from noor.domain.emergency import EmergencyError, EntryKind
from noor.domain.examination import items
from noor.domain.opinions import Disposition, Flag, Recommendation
from noor.domain.plans import BetweenVisitPlan, GoalOfCare, PlanError, Threshold
from noor.domain.records import (
    CarePlanTooEarly,
    Reason,
    Resolution,
    ResolutionError,
    check_care_plan_ready,
    reason_for,
    reason_rows,
)
from noor.domain.states import TERMINAL, Datum, IllegalTransition, Section
from noor.domain.supervisor import (
    Route as SupervisorRoute,
    Verdict,
    VerdictError,
    VerdictKey,
    key,
    sampling,
    week_start,
)
from noor.domain.visit import Addendum, AddendumError, NotReadyToComplete, VisitError, kind_for
from noor.domain.vitals import measurements
from noor.domain.writeback import Windows, assemble, windows as load_windows
from noor.emr import FixtureEMR, WriteRejected

SECTION_SLUGS = {section.name.lower(): section for section in Section}
"""URL slugs for the eight sections — the record's names, lowercased (§4.2)."""

SECTION_REASON_KEYS = {
    Section.VISIT_REASON: "visit_reason",
    Section.CONCERNS_AND_INTERVAL_HISTORY: "concerns_and_interval_history",
    Section.MEDICATION_RECONCILIATION: "medication_reconciliation",
    Section.VITALS: "vitals",
    Section.PHYSICAL_EXAMINATION: "physical_examination",
    Section.SELF_CARE_CHECK: "self_care_check",
    Section.CARE_PLAN: "care_plan",
    Section.NOTES: "notes",
}
"""Which `reason-lists.md` rows each section resolves against (§5.10)."""


class _Refused(Exception):
    """The request was refused before anything was decided — carries its status."""

    def __init__(self, detail: str, status: int) -> None:
        super().__init__(detail)
        self.status = status


async def _posted(request: Request) -> dict[str, object]:
    """The JSON body, or the refusal. Every write route starts here."""
    try:
        posted = await request.json()
    except JSONDecodeError:
        raise _Refused("a JSON body carries the write", 400)
    if not isinstance(posted, dict):
        raise _Refused("a JSON body carries the write", 400)
    return posted


def _required(posted: dict[str, object], *fields: str) -> None:
    """The named fields must all be present and non-empty."""
    missing = [field for field in fields if not posted.get(field)]
    if missing:
        raise _Refused("missing: " + ", ".join(missing), 400)


def _at(posted: dict[str, object]) -> datetime:
    """When the act happened — a parameter, never a clock read (FIRST)."""
    try:
        return datetime.fromisoformat(str(posted.get("at")))
    except ValueError:
        raise _Refused("at is an iso datetime naming when this was set", 400)


def _value(value: object) -> object:
    """A Brief value as JSON. Dates travel as iso text; a plan travels as lines."""
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, BetweenVisitPlan):
        return {
            "titration": [_rule(rule) for rule in value.titration],
            "schedule": [
                {"axis": item.axis.value, "times_per_week": item.times_per_week}
                for item in value.schedule
            ],
            "stop_rules": [_rule(rule) for rule in value.stop_rules],
        }
    return value


def _rule(rule: Threshold) -> dict[str, object]:
    return {
        "axis": rule.axis.value,
        "comparison": rule.comparison.value,
        "value": rule.value,
        "action": rule.action,
    }


def _datum(datum: Datum) -> dict[str, object]:
    return {
        "state": datum.state.value,
        "value": _value(datum.value),
        "as_of": _value(datum.as_of),
    }


def _reason(reason: Reason | None) -> dict[str, object] | None:
    if reason is None:
        return None
    return {"row_id": reason.row_id, "free_text": _value(reason.free_text)}


def _recommendation(item: Recommendation) -> dict[str, object]:
    """A shown Recommendation as JSON — what a TIER row's detail reads (N5)."""
    return {
        "id": item.id,
        "text": item.text,
        "tier": item.tier.name.lower(),
        "executor": item.executor,
        "provenance": item.provenance,
        "strength": item.strength,
    }


def _disposition(item: Disposition) -> dict[str, object]:
    """What the Field Team did with a shown item — an override never blocks (N4)."""
    return {
        "recommendation_id": item.recommendation_id,
        "outcome": item.outcome.value,
        "by": item.by,
        "at": item.at.isoformat(),
        "level": None if item.level is None else item.level.value,
        "reason": _reason(item.reason),
    }


def _flag(item: Flag) -> dict[str, object]:
    """A manual flag (§5.11): who sent what to the Supervisor, and why."""
    return {
        "subject": item.subject,
        "by": item.by,
        "at": item.at.isoformat(),
        "note": item.note,
    }


def _goal(goal: GoalOfCare) -> dict[str, object]:
    """The proposed target with its lineage — the number alone would be a
    rubber stamp (N5), so the bands never travel without it."""
    return {
        "patient_id": goal.patient_id,
        "bands": [
            {
                "axis": band.axis.value,
                "floor": band.floor,
                "ceiling": band.ceiling,
                "rationale": band.rationale,
            }
            for band in goal.bands
        ],
        "lineage": goal.lineage,
        "office_anchor": goal.office_anchor,
        "proposed_by": goal.proposed_by,
        "proposed_at": goal.proposed_at.isoformat(),
        "ratified_by": goal.ratified_by,
        "ratified_at": None
        if goal.ratified_at is None
        else goal.ratified_at.isoformat(),
    }


def _inbox_patient(patient: store.InboxPatient) -> dict[str, object]:
    """One Patient's door: the name, and the rows already in band order (§5.2)."""
    return {
        "patient_id": patient.patient_id,
        "patient_name": patient.patient_name,
        "rows": [
            {
                "route": row.review.route.name.lower(),
                "visit_id": row.review.visit_id,
                "patient_id": row.review.patient_id,
                "subject": row.review.subject,
                "due_at": None
                if row.review.due_at is None
                else row.review.due_at.isoformat(),
                "patient_name": row.patient_name,
                "visit_date": row.visit_date.isoformat(),
            }
            for row in patient.rows
        ],
    }


SUPERVISOR = "Dr Tariq Mansoor"
"""Who the demo server's Write-Backs answer to. Phase 1 has no sign-in, so the
queue and the drain name the cluster's Supervisor — the same fiction the
inbox's verdicts carry in their `by` field."""


def _queue_visit(
    conn: sqlite3.Connection,
    row: store.Pending,
    *,
    windows: Windows,
    supervisor: str,
) -> dict[str, object]:
    """One queued envelope: who, what state, when it closed, what the EMR last
    said, and the assembled items with their owners and due times (§4.9)."""
    visit = store.load(conn, row.visit_id)
    items = assemble(
        visit,
        goal=store.goal(conn, visit.patient_id),
        # Pending holds only closed Visits, so the close is always present — a
        # cast, not a branch, because an absent close here is impossible.
        at=cast(datetime, visit.closed_at),
        windows=windows,
        supervisor=supervisor,
    )
    return {
        "visit_id": visit.id,
        "patient_id": visit.patient_id,
        "patient_name": row.patient_name,
        "state": visit.state.value,
        "scheduled_for": store.visit_day(conn, visit.id).isoformat(),
        "scheduled_reason": store.scheduled_reason(conn, visit.id),
        "closed_at": _value(visit.closed_at),
        "closed_by": visit.closed_by,
        "refused_at": _value(row.refused_at),
        "refusal": row.said,
        "items": [
            {"kind": item.kind.name, "payload": item.payload} for item in items
        ],
    }


def _queue_addendum(
    conn: sqlite3.Connection, row: store.PendingAddendum
) -> dict[str, object]:
    """One queued Addendum — its own send, after the Visit's (§5.9)."""
    return {
        "addendum_id": row.addendum_id,
        "visit_id": row.visit_id,
        "patient_id": row.patient_id,
        "patient_name": store.patient_name(conn, row.patient_id),
        "text": row.text,
        "author": row.author,
        "written_at": row.written_at.isoformat(),
        "refused_at": _value(row.refused_at),
        "refusal": row.said,
    }


def _week(raw: str | None) -> date:
    """The Sunday the Silence Audit samples — stated, or the current week."""
    if raw is None:
        return week_start(date.today())
    try:
        return week_start(date.fromisoformat(raw))
    except ValueError:
        raise _Refused("week=YYYY-MM-DD names the audit's week", 400)


def _plan_from(content: object) -> BetweenVisitPlan | None:
    """The plan a Care Plan resolution carries (§4.8 emits it), if it carries one.

    A resolution without plan lines is still a resolution — the gate, not the
    save, decides whether the Visit may close.
    """
    if not isinstance(content, dict):
        return None
    plan = content.get("plan")
    if not isinstance(plan, dict):
        return None
    try:
        return serial.read_plan(plan)
    except (KeyError, PlanError, ValueError):
        raise _Refused("the Care Plan's plan lines do not hold", 400)


def _brief(body: Brief) -> dict[str, object]:
    last = body.last_visit
    return {
        "patient_id": body.patient_id,
        "trends": [
            {
                "measurement": trend.measurement,
                "label": trend.label,
                "unit": trend.unit,
                "points": [
                    {"on": _value(point.on), "value": _value(point.value)}
                    for point in trend.points
                ],
            }
            for trend in body.trends
        ],
        "last_visit": None
        if last is None
        else {
            "on": _value(last.on),
            "state": last.state.value,
            "reason": _reason(last.reason),
        },
        "previous_plan": _datum(body.previous_plan),
        "due": [
            {"item": item.item, "label": item.label, "last_done": _datum(item.last_done)}
            for item in body.due
        ],
        "blind_spots": list(body.blind_spots),
    }


def build(db: Path | str) -> Starlette:
    """One app over one file (ADR 0006). Content loads here, so a broken content
    file refuses the process at startup rather than mid-Visit (rung 1)."""
    path = Path(db)
    catalogue = items(content.load("surveillance-intervals").data["intervals"]["rows"])
    measures = measurements(content.load("vitals-by-condition").data["measurements"]["rows"])
    cancelled = reason_rows(content.load("reason-lists").data["cancelled"]["rows"])
    ended_early = reason_rows(content.load("reason-lists").data["ended_early"]["rows"])
    response = content.load("response-windows").data
    service_windows = load_windows(response["windows"])
    audit_policy = sampling(response["audit"])
    no_content = content.load("reason-lists").data["no_content"]
    section_reasons = {
        section: reason_rows(
            no_content["shared"], no_content["per_section"][SECTION_REASON_KEYS[section]]
        )
        for section in Section
    }

    async def roster(request: Request) -> JSONResponse:
        try:
            day = date.fromisoformat(request.query_params.get("day", ""))
        except ValueError:
            return JSONResponse(
                {"detail": "day=YYYY-MM-DD names the roster's day"}, status_code=400
            )
        conn = store.connect(path)
        try:
            visits = []
            for entry in store.roster(conn, day):
                past = store.history(conn, entry.patient_id)
                ready = prefetch.readiness(conn, entry.patient_id)
                visits.append(
                    {
                        "visit_id": entry.visit_id,
                        "patient_id": entry.patient_id,
                        "patient_name": entry.patient_name,
                        "reason": entry.reason,
                        "state": entry.state.value,
                        "planning": kind_for(past).value,
                        "readiness": {
                            "prepared_at": _value(ready.prepared_at),
                            "unreadable": list(ready.unreadable),
                        },
                    }
                )
        finally:
            conn.close()
        return JSONResponse({"day": day.isoformat(), "visits": visits})

    async def visit_brief(request: Request) -> JSONResponse:
        visit_id = request.path_params["visit_id"]
        try:
            as_of = date.fromisoformat(request.query_params.get("as_of", ""))
        except ValueError:
            return JSONResponse(
                {"detail": "as_of=YYYY-MM-DD dates the surveillance check"},
                status_code=400,
            )
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            visit.previous_plan = store.standing_plan(conn, visit.patient_id)
            body = brief(
                visit,
                history=store.history(conn, visit.patient_id),
                conditions=store.conditions(conn, visit.patient_id),
                catalogue=catalogue,
                measures=measures,
                surveillance=prefetch.surveillance(conn, visit.patient_id),
                as_of=as_of,
            )
            return JSONResponse(_brief(body))
        finally:
            conn.close()

    async def cancel_visit(request: Request) -> JSONResponse:
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "row_id", "by", "at")
            at_time = _at(posted)
            reason = reason_for(
                cancelled, str(posted["row_id"]), str(posted.get("free_text", ""))
            )
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        except ResolutionError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=400)
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            try:
                visit.cancel(reason, str(posted["by"]), at_time)
            except (IllegalTransition, VisitError) as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            store.save(conn, visit)
            return JSONResponse({"visit_id": visit.id, "state": visit.state.value})
        finally:
            conn.close()

    async def visit_detail(request: Request) -> JSONResponse:
        visit_id = request.path_params["visit_id"]
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            return JSONResponse(
                {
                    "visit_id": visit.id,
                    "patient_id": visit.patient_id,
                    "patient_name": store.patient_name(conn, visit.patient_id),
                    "scheduled_for": store.visit_day(conn, visit_id).isoformat(),
                    "scheduled_reason": store.scheduled_reason(conn, visit_id),
                    "state": visit.state.value,
                    "kind": None if visit.kind is None else visit.kind.value,
                    "junior_physician": visit.junior_physician,
                    "nurse": visit.nurse,
                    "started_at": _value(visit.started_at),
                    "closed_at": _value(visit.closed_at),
                    "closed_by": visit.closed_by,
                    "closing_reason": _reason(visit.closing_reason),
                    "resolutions": {
                        section.name: {
                            "content": resolution.content,
                            "reason": _reason(resolution.reason),
                        }
                        for section, resolution in visit.resolutions.items()
                    },
                    "emergencies": [
                        {
                            "started_at": record.started_at.isoformat(),
                            "ended_at": _value(record.ended_at),
                            "entries": [
                                {
                                    "kind": entry.kind.value,
                                    "text": entry.text,
                                    "at": entry.at.isoformat(),
                                }
                                for entry in record.entries
                            ],
                        }
                        for record in visit.emergencies
                    ],
                    "allergies": _datum(prefetch.allergies(conn, visit.patient_id)),
                    "shown": [_recommendation(item) for item in visit.shown],
                    "dispositions": [_disposition(item) for item in visit.dispositions],
                    "flags": [_flag(item) for item in visit.flags],
                    "plan": _value(visit.plan),
                }
            )
        finally:
            conn.close()

    async def start_visit(request: Request) -> JSONResponse:
        """The deliberate start (§5.5): the kind settled from history, the pair
        copied from the standing assignment — never chosen at the door (§5.13)."""
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "at")
            at_time = _at(posted)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            team = store.field_team(conn, visit.patient_id)
            kind = kind_for(store.history(conn, visit.patient_id))
            try:
                visit.start(
                    at_time,
                    kind,
                    junior_physician=team.junior_physician,
                    nurse=team.nurse,
                )
            except IllegalTransition as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            store.save(conn, visit)
            return JSONResponse(
                {
                    "visit_id": visit.id,
                    "state": visit.state.value,
                    "kind": kind.value,
                }
            )
        finally:
            conn.close()

    async def save_section(request: Request) -> JSONResponse:
        """One section resolved — content, or a structured reason for having
        none (§5.8). The Care Plan waits its turn (§4.2)."""
        slug = request.path_params["slug"]
        visit_id = request.path_params["visit_id"]
        if slug not in SECTION_SLUGS:
            return JSONResponse(
                {"detail": f"no section {slug!r}; the Visit Protocol has eight (§4.2)"},
                status_code=404,
            )
        section = SECTION_SLUGS[slug]
        conn = store.connect(path)
        try:
            try:
                posted = await _posted(request)
            except _Refused as refused:
                return JSONResponse({"detail": str(refused)}, status_code=refused.status)
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            try:
                reason = None
                if posted.get("reason") is not None:
                    given = posted["reason"]
                    row = given.get("row_id") if isinstance(given, dict) else None
                    text = given.get("free_text", "") if isinstance(given, dict) else ""
                    reason = reason_for(section_reasons[section], str(row), str(text))
                resolution = Resolution(section, posted.get("content"), reason)
            except ResolutionError as exc:
                return JSONResponse({"detail": str(exc)}, status_code=400)
            visit.resolutions[section] = resolution
            if section is Section.CARE_PLAN:
                try:
                    check_care_plan_ready(visit.resolutions)
                except CarePlanTooEarly as exc:
                    return JSONResponse({"detail": str(exc)}, status_code=409)
                try:
                    plan = _plan_from(resolution.content)
                except _Refused as refused:
                    return JSONResponse(
                        {"detail": str(refused)}, status_code=refused.status
                    )
                if plan is not None:
                    visit.plan = plan
            try:
                store.save(conn, visit)
            except store.TerminalVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            return JSONResponse(
                {
                    "visit_id": visit.id,
                    "section": section.name,
                    "resolved": "content" if reason is None else "reason",
                }
            )
        finally:
            conn.close()

    async def end_early_visit(request: Request) -> JSONResponse:
        """The honest exit (§5.6): what was captured is not discarded."""
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "row_id", "by", "at")
            at_time = _at(posted)
            reason = reason_for(
                ended_early, str(posted["row_id"]), str(posted.get("free_text", ""))
            )
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        except ResolutionError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=400)
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            try:
                visit.end_early(reason, str(posted["by"]), at_time)
            except (IllegalTransition, VisitError) as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            store.save(conn, visit)
            return JSONResponse({"visit_id": visit.id, "state": visit.state.value})
        finally:
            conn.close()

    async def enter_emergency(request: Request) -> JSONResponse:
        """One action, zero required fields (§5.7) — besides when, which arrives
        in the body rather than from a clock."""
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "at")
            at_time = _at(posted)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            try:
                visit.enter_emergency(at_time)
            except IllegalTransition as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            store.save(conn, visit)
            return JSONResponse({"visit_id": visit.id, "state": visit.state.value})
        finally:
            conn.close()

    async def record_timeline_entry(request: Request) -> JSONResponse:
        """A line on the open Emergency's record (§5.7) — during, or after the
        leave, since documentation is retrospective."""
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "kind", "text", "at")
            at_time = _at(posted)
            try:
                kind = EntryKind(str(posted["kind"]))
            except ValueError:
                raise _Refused("kind is observed or done, never a severity", 400)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            try:
                visit.record_timeline(kind, str(posted["text"]), at_time)
            except VisitError as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            except EmergencyError as exc:
                return JSONResponse({"detail": str(exc)}, status_code=400)
            store.save(conn, visit)
            return JSONResponse(
                {"visit_id": visit.id, "entries": len(visit.emergencies[-1].entries)}
            )
        finally:
            conn.close()

    async def resume_visit(request: Request) -> JSONResponse:
        """Option A of the exit binary (§5.7): the Patient stayed home, so the
        Visit Protocol resumes where the Emergency suspended it."""
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "at")
            at_time = _at(posted)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            try:
                visit.leave_emergency(at_time)
            except IllegalTransition as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            store.save(conn, visit)
            return JSONResponse({"visit_id": visit.id, "state": visit.state.value})
        finally:
            conn.close()

    async def ended_early_reasons(request: Request) -> JSONResponse:
        """§5.10's Ended Early rows as rendered — the Emergency's exit drawer
        reads them, since that exit carries no reason of its own (§5.7)."""
        return JSONResponse(
            {
                "rows": [
                    {"id": row["id"], "label": row["label"]} for row in ended_early
                ]
            }
        )

    async def read_inbox(request: Request) -> JSONResponse:
        """The Supervisor's queue, derived on read (§5.1, ADR 0009)."""
        try:
            week = _week(request.query_params.get("week"))
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            patients = store.inbox(
                conn, windows=service_windows, policy=audit_policy, week=week
            )
            return JSONResponse(
                {
                    "week": week.isoformat(),
                    "patients": [_inbox_patient(patient) for patient in patients],
                }
            )
        finally:
            conn.close()

    async def answer_review(request: Request) -> JSONResponse:
        """One Review Verdict — the only thing that removes an item (ADR 0009).

        Answers the current week's inbox: the page reads that week, so that is
        the week a posted answer belongs to."""
        try:
            posted = await _posted(request)
            _required(posted, "visit_id", "route", "subject", "by", "at")
            at_time = _at(posted)
            if not isinstance(posted.get("agreed"), bool):
                raise _Refused("agreed answers yes or no, nothing between", 400)
            try:
                route = SupervisorRoute[str(posted["route"]).upper()]
            except KeyError:
                raise _Refused("four routes, and no fifth (§5.12)", 400)
            note = posted.get("note")
            if note is not None and not isinstance(note, str):
                raise _Refused("a note travels as words", 400)
            try:
                verdict = Verdict(
                    agreed=bool(posted["agreed"]),
                    by=str(posted["by"]),
                    at=at_time,
                    note=note,
                )
            except VerdictError as exc:
                return JSONResponse({"detail": str(exc)}, status_code=400)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            week = week_start(date.today())
            open_keys = {
                key(row.review)
                for patient in store.inbox(
                    conn, windows=service_windows, policy=audit_policy, week=week
                )
                for row in patient.rows
            }
            verdict_key = VerdictKey(
                str(posted["visit_id"]), route, str(posted["subject"])
            )
            if verdict_key not in open_keys:
                return JSONResponse(
                    {"detail": "no open item answers to that"}, status_code=404
                )
            store.record_verdict(conn, verdict_key, verdict)
            return JSONResponse(
                {
                    "visit_id": verdict_key.visit_id,
                    "route": route.name.lower(),
                    "subject": verdict_key.subject,
                    "closed": route is not SupervisorRoute.RATIFICATION,
                }
            )
        finally:
            conn.close()

    async def read_goal(request: Request) -> JSONResponse:
        """The Patient's proposed target with its lineage — what a ratification
        row's detail reads before the Supervisor answers (N5)."""
        patient_id = request.path_params["patient_id"]
        conn = store.connect(path)
        try:
            goal = store.goal(conn, patient_id)
            if goal is None:
                return JSONResponse(
                    {"detail": f"no Goal of Care proposed for {patient_id!r}"},
                    status_code=404,
                )
            return JSONResponse(_goal(goal))
        finally:
            conn.close()

    async def ratify_goal(request: Request) -> JSONResponse:
        """Agreeing is ratifying: the Goal carries its ratifier and its time, so
        no second record is kept (§5.12, ADR 0009)."""
        patient_id = request.path_params["patient_id"]
        try:
            posted = await _posted(request)
            _required(posted, "by", "at")
            at_time = _at(posted)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            if store.goal(conn, patient_id) is None:
                return JSONResponse(
                    {"detail": f"no Goal of Care proposed for {patient_id!r}"},
                    status_code=404,
                )
            try:
                ratified = store.ratify_goal(
                    conn, patient_id, str(posted["by"]), at_time
                )
            except store.GoalError as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            return JSONResponse(
                {"patient_id": patient_id, "ratified_by": ratified.ratified_by}
            )
        finally:
            conn.close()

    async def read_queue(request: Request) -> JSONResponse:
        """What still waits for the Field Team's explicit resend (§4.10) — closed
        Visits the EMR has not accepted, and Addenda behind them."""
        conn = store.connect(path)
        try:
            visits = [
                _queue_visit(conn, row, windows=service_windows,
                             supervisor=SUPERVISOR)
                for row in store.pending(conn)
            ]
            addenda = [
                _queue_addendum(conn, row) for row in store.pending_addenda(conn)
            ]
        finally:
            conn.close()
        return JSONResponse({"visits": visits, "addenda": addenda})

    async def dispatch_queue(request: Request) -> JSONResponse:
        """One explicit resend for everything queued — the close tried once, and
        nothing retries by itself (§4.10). Every refusal is named, none is quiet."""
        try:
            posted = await _posted(request)
            _required(posted, "at")
            at_time = _at(posted)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            delivery = dispatch.drain(
                conn, FixtureEMR(at_time), windows=service_windows,
                supervisor=SUPERVISOR, attempted_at=at_time)
        finally:
            conn.close()
        return JSONResponse({
            "sent": list(delivery.sent),
            "failed": [
                {"id": visit_id, "refusal": said}
                for visit_id, said in delivery.failed
            ],
        })

    async def dispatch_visit(request: Request) -> JSONResponse:
        """One envelope's explicit resend — what Transmit Now honestly needs. A
        refusal is recorded against the Visit and named, so it stays queued."""
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "at")
            at_time = _at(posted)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            try:
                dispatch.send(
                    conn, FixtureEMR(at_time), visit_id, windows=service_windows,
                    supervisor=SUPERVISOR, attempted_at=at_time)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            except dispatch.NotClosed as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            except WriteRejected as exc:
                return JSONResponse(
                    {"visit_id": visit_id, "sent": False, "refusal": str(exc)})
            return JSONResponse({"visit_id": visit_id, "sent": True})
        finally:
            conn.close()

    async def commit_addendum(request: Request) -> JSONResponse:
        """The only write a closed Visit accepts (§5.9) — timestamped,
        attributed, additive. Refuses a Visit still open before writing; the
        store's terminal refusal is the second lock, not the first. A flagged
        one also reaches the Supervisor as a manual flag (§5.12)."""
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "text", "author", "at")
            at_time = _at(posted)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            if visit.state not in TERMINAL:
                return JSONResponse(
                    {"detail": (
                        f"Visit {visit_id} is {visit.state.value}; an addition "
                        "to a Visit still open is the section write, "
                        "not an Addendum (§5.9)")},
                    status_code=409,
                )
            flagged = bool(posted.get("flagged", False))
            try:
                addendum = Addendum(
                    f"{visit_id}-a{len(store.addenda(conn, visit_id)) + 1}",
                    visit_id,
                    str(posted["text"]),
                    str(posted["author"]),
                    at_time,
                    flagged=flagged,
                )
            except AddendumError as exc:
                return JSONResponse({"detail": str(exc)}, status_code=400)
            store.add_addendum(conn, addendum)
            return JSONResponse(
                {
                    "addendum_id": addendum.id,
                    "visit_id": visit_id,
                    "flagged": addendum.flagged,
                }
            )
        finally:
            conn.close()

    async def read_addenda(request: Request) -> JSONResponse:
        """Prior additions to this Visit, oldest first (§5.9, §5.13)."""
        visit_id = request.path_params["visit_id"]
        conn = store.connect(path)
        try:
            try:
                store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            return JSONResponse(
                {
                    "visit_id": visit_id,
                    "addenda": [
                        {
                            "addendum_id": item.id,
                            "text": item.text,
                            "author": item.author,
                            "written_at": item.written_at.isoformat(),
                            "flagged": item.flagged,
                        }
                        for item in store.addenda(conn, visit_id)
                    ],
                }
            )
        finally:
            conn.close()

    async def complete_visit(request: Request) -> JSONResponse:
        """The §5.8 gate, enforced rather than displayed. A Baseline owes its
        proposed Goal of Care; a Routine reasons against one already held."""
        visit_id = request.path_params["visit_id"]
        try:
            posted = await _posted(request)
            _required(posted, "by", "at")
            at_time = _at(posted)
        except _Refused as refused:
            return JSONResponse({"detail": str(refused)}, status_code=refused.status)
        conn = store.connect(path)
        try:
            try:
                visit = store.load(conn, visit_id)
            except store.UnknownVisit as exc:
                return JSONResponse({"detail": str(exc)}, status_code=404)
            goal: GoalOfCare | None = None
            if posted.get("goal") is not None:
                given = posted["goal"]
                if not isinstance(given, dict):
                    return JSONResponse(
                        {"detail": "the proposed Goal of Care does not hold"},
                        status_code=400,
                    )
                try:
                    goal = serial.load_goal(
                        json.dumps({"patient_id": visit.patient_id, **given})
                    )
                except (KeyError, PlanError, ValueError) as exc:
                    return JSONResponse(
                        {"detail": f"the proposed Goal of Care does not hold: {exc}"},
                        status_code=400,
                    )
            try:
                visit.complete(by=str(posted["by"]), at=at_time, goal=goal)
            except (IllegalTransition, NotReadyToComplete) as exc:
                return JSONResponse({"detail": str(exc)}, status_code=409)
            store.save(conn, visit)
            return JSONResponse({"visit_id": visit.id, "state": visit.state.value})
        finally:
            conn.close()

    return Starlette(
        routes=[
            Route("/api/roster", roster),
            Route("/api/visits/{visit_id}", visit_detail),
            Route("/api/visits/{visit_id}/brief", visit_brief),
            Route("/api/visits/{visit_id}/cancel", cancel_visit, methods=["POST"]),
            Route("/api/visits/{visit_id}/start", start_visit, methods=["POST"]),
            Route("/api/visits/{visit_id}/sections/{slug}", save_section, methods=["POST"]),
            Route("/api/visits/{visit_id}/end-early", end_early_visit, methods=["POST"]),
            Route("/api/visits/{visit_id}/emergency", enter_emergency, methods=["POST"]),
            Route("/api/visits/{visit_id}/emergency/entries", record_timeline_entry, methods=["POST"]),
            Route("/api/visits/{visit_id}/emergency/resume", resume_visit, methods=["POST"]),
            Route("/api/reasons/ended_early", ended_early_reasons),
            Route("/api/inbox", read_inbox),
            Route("/api/inbox/verdict", answer_review, methods=["POST"]),
            Route("/api/queue", read_queue),
            Route("/api/queue/dispatch", dispatch_queue, methods=["POST"]),
            Route("/api/visits/{visit_id}/dispatch", dispatch_visit, methods=["POST"]),
            Route("/api/patients/{patient_id}/goal", read_goal),
            Route("/api/patients/{patient_id}/goal/ratify", ratify_goal, methods=["POST"]),
            Route("/api/visits/{visit_id}/complete", complete_visit, methods=["POST"]),
            Route("/api/visits/{visit_id}/addenda", commit_addendum, methods=["POST"]),
            Route("/api/visits/{visit_id}/addenda", read_addenda),
        ]
    )


app = build(Path("noor.db"))
"""The demo server's app, over the repo-root file `seed.py` fills.

Run from the repo root with ``uvicorn noor.api:app --port 8000`` (with
``src`` on the path). Connections still open and close within one request —
this object holds the path, never a connection.
"""
