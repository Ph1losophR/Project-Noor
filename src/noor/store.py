"""One SQLite file, no ORM (ADR 0006). Functions over a connection, not a class."""
import json
import sqlite3
from collections.abc import Sequence
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import NamedTuple

from noor.domain.plans import GoalOfCare
from noor.domain.states import Datum, TERMINAL, VisitState
from noor.domain.visit import Visit
from noor.serial import dump_datum, dump_goal, dump_visit, load_datum, load_goal, load_visit

SCHEMA = Path(__file__).with_name("schema.sql")


class StoreError(Exception):
    """The store was asked for something that is not there."""


class UnknownVisit(StoreError):
    """No row with that Visit id."""


class TerminalVisit(StoreError):
    """A write arrived for a Visit that has already closed (§5.9)."""


class RosterEntry(NamedTuple):
    """One line of the day's roster (§4.9)."""

    visit_id: str
    patient_id: str
    patient_name: str
    reason: str
    state: VisitState


class Pending(NamedTuple):
    """One Visit the EMR has not accepted, with what it last said if it said anything."""

    visit_id: str
    patient_name: str
    refused_at: datetime | None
    said: str | None


def connect(path: Path | str) -> sqlite3.Connection:
    """Open the one database and make sure the tables are there. The web layer opens
    and closes its connection within one request, so use is sequential, never
    concurrent — Starlette runs the dependency and the handler on different threadpool
    threads (§6's single-clinician app, no concurrent writers)."""
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Off by default in sqlite3, and a Visit without its Patient is not a Visit.
    conn.execute("pragma foreign_keys = on")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    return conn


def add_patient(
    conn: sqlite3.Connection, patient_id: str, name: str, conditions: Sequence[str]
) -> None:
    conn.execute("insert into patients (id, name, conditions) values (?, ?, ?)",
                 (patient_id, name, json.dumps(list(conditions))))
    conn.commit()


def conditions(conn: sqlite3.Connection, patient_id: str) -> list[str]:
    """Which chronic conditions this Patient is enrolled for. Drives Vitals (Task 15)."""
    row = conn.execute(
        "select conditions from patients where id = ?", (patient_id,)).fetchone()
    if row is None:
        raise StoreError(f"no Patient {patient_id!r}")
    return json.loads(row["conditions"])


def schedule(
    conn: sqlite3.Connection, visit: Visit, scheduled_for: date, reason: str
) -> None:
    """Put a Visit on a day's roster, carrying why it was scheduled (§4.9)."""
    conn.execute(
        "insert into visits (id, patient_id, scheduled_for, reason, state, body) "
        "values (?, ?, ?, ?, ?, ?)",
        (visit.id, visit.patient_id, scheduled_for.isoformat(),
         reason, visit.state.value, dump_visit(visit)))
    conn.commit()


def save(conn: sqlite3.Connection, visit: Visit) -> None:
    """Update a Visit. Refuses a closed row — §5.9 is a property of the row, not
    only of the transition, because a stale page posts without transitioning."""
    stored = _stored_state(conn, visit.id)
    if stored in TERMINAL:
        raise TerminalVisit(
            f"Visit {visit.id} is {stored.value} and cannot be changed (§5.9)")
    if visit.state is VisitState.SCHEDULED and stored is not VisitState.SCHEDULED:
        raise StoreError(
            f"Visit {visit.id} is {stored.value}; a write cannot un-start it (§5.5)")
    conn.execute("update visits set state = ?, body = ? where id = ?",
                 (visit.state.value, dump_visit(visit), visit.id))
    conn.commit()


def load(conn: sqlite3.Connection, visit_id: str) -> Visit:
    row = conn.execute("select body from visits where id = ?", (visit_id,)).fetchone()
    if row is None:
        raise UnknownVisit(f"no Visit {visit_id!r}")
    return load_visit(row["body"])


def roster(conn: sqlite3.Connection, day: date) -> list[RosterEntry]:
    """The day's Visits, finished ones included — the Silence Audit needs them."""
    rows = conn.execute(
        "select v.id, v.patient_id, p.name, v.reason, v.state "
        "from visits v join patients p on p.id = v.patient_id "
        "where v.scheduled_for = ? order by p.name, v.id",
        (day.isoformat(),)).fetchall()
    return [
        RosterEntry(row["id"], row["patient_id"], row["name"],
                    row["reason"], VisitState(row["state"]))
        for row in rows
    ]


def history(conn: sqlite3.Connection, patient_id: str) -> list[Visit]:
    """That Patient's finished Visits, oldest first. The Brief reads its series out of
    these (§5.3), so a Visit still open is not among them."""
    # The f-string interpolates placeholders only — one '?' per terminal state, never a value.
    marks = ",".join("?" * len(TERMINAL))
    rows = conn.execute(
        f"select body from visits where patient_id = ? and state in ({marks}) "
        "order by scheduled_for, id",
        (patient_id, *sorted(state.value for state in TERMINAL))).fetchall()
    return [load_visit(row["body"]) for row in rows]


def completed_between(
    conn: sqlite3.Connection, start: date, end: date
) -> list[Visit]:
    """Every Visit that reached Completed with a scheduled date in `[start, end)`.

    Half-open, so consecutive weeks neither overlap nor leave a Thursday out. Completed
    only: an Ended Early Visit produced nothing because it was interrupted (§5.6), and
    that is a reason already known. Iso dates sort lexicographically the way they sort
    chronologically, which is why `scheduled_for` is stored as text (Task 11).
    """
    rows = conn.execute(
        "select body from visits "
        "where state = ? and scheduled_for >= ? and scheduled_for < ? "
        "order by scheduled_for, id",
        (VisitState.COMPLETED.value, start.isoformat(), end.isoformat())).fetchall()
    return [load_visit(row["body"]) for row in rows]


def _stored_state(conn: sqlite3.Connection, visit_id: str) -> VisitState:
    row = conn.execute("select state from visits where id = ?", (visit_id,)).fetchone()
    if row is None:
        raise UnknownVisit(f"no Visit {visit_id!r}")
    return VisitState(row["state"])


class GoalError(StoreError):
    """A Goal of Care was asked to change in a way §4.4 does not allow."""


def propose_goal(conn: sqlite3.Connection, goal: GoalOfCare) -> None:
    """Record a Baseline Visit's proposed target (§4.4).

    Replaces an unratified proposal — a Baseline that Ended Early ratified nothing, so
    the next Baseline proposes afresh. Refuses to replace a ratified one, because every
    reading since ratification was compared against those bands.
    """
    if _ratified(conn, goal.patient_id):
        raise GoalError(
            f"{goal.patient_id} has a ratified Goal of Care; it changes by review, "
            f"not by a second proposal (§4.4)")
    conn.execute(
        "insert or replace into goals (patient_id, ratified, body) values (?, 0, ?)",
        (goal.patient_id, dump_goal(goal)))
    conn.commit()


def goal(conn: sqlite3.Connection, patient_id: str) -> GoalOfCare | None:
    """The Patient's target, or None where no Baseline has proposed one yet.

    None is what Task 17's Write-Back and §4.4's withholding rule both consume, so it
    is a real answer here and not an error: a Patient before their Baseline Visit has
    no target, and that is the ordinary case on day one.
    """
    row = conn.execute(
        "select body from goals where patient_id = ?", (patient_id,)).fetchone()
    if row is None:
        return None
    return load_goal(row["body"])


def ratify_goal(
    conn: sqlite3.Connection, patient_id: str, by: str, at: datetime
) -> GoalOfCare:
    """The Supervisor's ratification (§5.12's second route). Refused twice over."""
    current = goal(conn, patient_id)
    if current is None:
        raise GoalError(f"no Goal of Care proposed for {patient_id!r} to ratify")
    if current.is_ratified:
        raise GoalError(
            f"{patient_id}'s Goal of Care was already ratified by "
            f"{current.ratified_by} — a decision carries one name (§5.13)")
    ratified = replace(current, ratified_by=by, ratified_at=at)
    conn.execute("update goals set ratified = 1, body = ? where patient_id = ?",
                 (dump_goal(ratified), patient_id))
    conn.commit()
    return ratified


def _ratified(conn: sqlite3.Connection, patient_id: str) -> bool:
    """One column, one query — the refusal never parses a body."""
    row = conn.execute(
        "select ratified from goals where patient_id = ?", (patient_id,)).fetchone()
    return row is not None and bool(row["ratified"])


def pending(conn: sqlite3.Connection) -> list[Pending]:
    """Visits whose Write-Back the EMR has not accepted, longest wait first.

    Derived on every read from `state` and one timestamp, so it cannot disagree with
    itself (§5.1's reasoning about stored flags). Cancelled is deliberately not here:
    a Visit that never started writes nothing at all (§5.4).
    """
    rows = conn.execute(
        "select v.id, p.name, v.last_refused_at, v.last_refusal "
        "from visits v join patients p on p.id = v.patient_id "
        "where v.state in (:completed, :ended_early) and v.written_back_at is null "
        "order by v.scheduled_for, v.id",
        {"completed": VisitState.COMPLETED.value,
         "ended_early": VisitState.ENDED_EARLY.value}).fetchall()
    return [
        Pending(row["id"], row["name"],
                datetime.fromisoformat(row["last_refused_at"])
                if row["last_refused_at"] else None,
                row["last_refusal"])
        for row in rows
    ]


def queued(conn: sqlite3.Connection) -> list[str]:
    """The ids alone. `dispatch.drain` iterates them and needs nothing else."""
    return [row.visit_id for row in pending(conn)]


def mark_written_back(
    conn: sqlite3.Connection, visit_id: str, at: datetime
) -> None:
    """Record that the EMR accepted this Visit's Write-Back.

    Writes `written_back_at` and nothing else, so §5.9's immutability is untouched: the
    delivery receipt is Noor's record of its own plumbing, not part of the clinical
    record. `save()` still refuses a terminal row and must.

    The `written_back_at is null` in the where clause is what makes a second acceptance
    fail rather than silently overwrite the first. A no-op here would be the quiet
    failure §4.10 forbids, in the other direction — a Visit marked delivered twice, or
    an unknown id marked and nobody told.
    """
    cursor = conn.execute(
        "update visits set written_back_at = ? "
        "where id = ? and written_back_at is null", (at.isoformat(), visit_id))
    if cursor.rowcount == 0:
        raise StoreError(
            f"no Visit {visit_id!r} awaiting a Write-Back — either it does not exist "
            f"or the EMR already accepted it")
    conn.commit()


def mark_refused(
    conn: sqlite3.Connection, visit_id: str, at: datetime, said: str
) -> None:
    """Record that the EMR refused this Visit's Write-Back, and what it said.

    §5.1's third status. Writes these two columns and nothing else — not `state`, so a
    rejected Write-Back cannot reopen a Completed Visit, and not `written_back_at`, so the
    Visit stays queued for the next attempt. The previous refusal is overwritten and a
    later acceptance does not clear either column: how many drives home a delivery took is
    a fact about Noor's own plumbing that nothing else records.
    """
    cursor = conn.execute(
        "update visits set last_refused_at = ?, last_refusal = ? where id = ?",
        (at.isoformat(), said, visit_id))
    if cursor.rowcount == 0:
        raise StoreError(f"no Visit {visit_id!r} to record a refusal against")
    conn.commit()


class Cached(NamedTuple):
    """One office read, and when Noor asked (§5.2)."""

    answer: Datum
    read_at: datetime


def cache_read(
    conn: sqlite3.Connection, patient_id: str, subject: str, answer: Datum, at: datetime
) -> None:
    """Store what the EMR said before the van left.

    `insert or replace`, because a second departure re-reads: what travels is the last
    answer read, and a read that failed this morning is stored *as* Unreachable rather
    than left as yesterday's list. A stale list presented as current is the quiet failure
    §4.10 forbids.
    """
    conn.execute(
        "insert or replace into cached_reads (patient_id, subject, read_at, body) "
        "values (?, ?, ?, ?)",
        (patient_id, subject, at.isoformat(), dump_datum(answer)))
    conn.commit()


def cached(conn: sqlite3.Connection, patient_id: str) -> dict[str, Cached]:
    """Every office read for this Patient, by subject.

    One query and no per-subject getter: a Brief asks about seven surveillance items, and
    seven round trips to answer one page is seven times the work for the same file read.
    """
    rows = conn.execute(
        "select subject, read_at, body from cached_reads where patient_id = ?",
        (patient_id,)).fetchall()
    return {row["subject"]: Cached(load_datum(row["body"]),
                                   datetime.fromisoformat(row["read_at"]))
            for row in rows}


def standing_plan(conn: sqlite3.Connection, patient_id: str) -> Datum:
    """The Between-Visit Plan in force, as §5.3's declaration wants it.

    The last plan any finished Visit emitted — §5.6 keeps it standing across Visits that
    emitted none, and Absent is the truth only before the first one. The Datum comes back
    rather than the Visit because three callers need this, and `None` standing in for both
    "no plan yet" and "could not be read" is exactly the collapse N6 forbids.
    """
    standing = next((finished for finished in reversed(history(conn, patient_id))
                     if finished.plan is not None), None)
    if standing is None:
        return Datum.absent()
    return Datum.present(standing.plan, as_of=standing.closed_at)


def enrolled(conn: sqlite3.Connection) -> set[str]:
    """Who the store already knows. The roster read is run twice in one morning, and the
    second run must not trip the primary key on a Patient it enrolled on the first."""
    return {row["id"] for row in conn.execute("select id from patients")}


def patient_name(conn: sqlite3.Connection, patient_id: str) -> str:
    """The name at the top of the Visit page. Mirrors conditions(): raises StoreError
    when the Patient is missing so the web layer renders a 400 refusal (§4.1) rather
    than a 500 from a TypeError on a broken foreign key."""
    row = conn.execute("select name from patients where id = ?", (patient_id,)).fetchone()
    if row is None:
        raise StoreError(f"no Patient {patient_id!r}")
    return row["name"]


def scheduled_reason(conn: sqlite3.Connection, visit_id: str) -> str:
    """Why the office put this Visit on the day (§4.9), for the Visit Reason section.

    Mirrors patient_name(): raises StoreError when Visit missing so web layer renders
    400 (§4.1) not 500.
    """
    row = conn.execute("select reason from visits where id = ?", (visit_id,)).fetchone()
    if row is None:
        raise StoreError(f"no Visit {visit_id!r}")
    return row["reason"]
