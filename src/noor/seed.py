"""The demo database: the day's roster, the Patients on it, and the history behind them.

Not a migration and not a test fixture. `schema.sql` makes the tables; this puts one day of
work into them. The roster arrives through the EMR seam the way the office would take it
(§4.9); enrolment comes from the table below, because enrolment has no screen in Phase 1
(web_plan §8). Repeat-safe by Patient, so a second run on the same morning adds nothing.

The history matters as much as the day. With nothing behind them every Patient is due a
Baseline (§5.5), every Brief has one point to draw a trend from, and every §5.3 declaration
reads *no previous plan* — all three true, and all three the empty case.
"""
from collections.abc import Sequence
from datetime import date, datetime, time
from sqlite3 import Connection

from noor import content, emr, prefetch, store
from noor.domain.examination import items
from noor.domain.plans import (
    Axis, Band, BetweenVisitPlan, Comparison, GoalOfCare, MeasurementSchedule, Threshold,
)
from noor.domain.records import Resolution
from noor.domain.states import Section, VisitKind
from noor.domain.visit import Visit, kind_for

CONDITIONS = {
    "Type 2 diabetes mellitus": "diabetes",
    "Essential hypertension": "hypertension",
}
"""The EMR's problem names, mapped to the slugs every ADR 0007 content row is written
against. A problem with no slug here — Abdullah's stage 3a kidney disease — is not a
condition Noor manages, and enrolling him for it would put rows on his Vitals form and his
surveillance list that nothing in Phase 1 can act on."""

TEAMS = {
    "p-001": store.FieldTeam("Dr Layla Al-Amri", "Nurse Huda Al-Zahrani"),
    "p-002": store.FieldTeam("Dr Layla Al-Amri", "Nurse Huda Al-Zahrani"),
    "p-003": store.FieldTeam("Dr Yousef Al-Subaie", "Nurse Maha Al-Rashed"),
    "p-004": store.FieldTeam("Dr Yousef Al-Subaie", "Nurse Maha Al-Rashed"),
    "p-005": store.FieldTeam("Dr Layla Al-Amri", "Nurse Huda Al-Zahrani"),
}
"""§5.13's standing assignment, one pair per Patient. Two pairs across five Patients rather
than one, because with a single pair the Start (Task 7) could stamp a constant onto the
Visit and still pass every test: the attendance record has to come from the Patient it
belongs to."""

PAST = {
    "p-001": ((date(2025, 11, 12), "168/96"),
              (date(2026, 2, 18), "158/92"),
              (date(2026, 5, 21), "152/90")),
    "p-002": ((date(2026, 6, 2), "138/84"),),
    "p-004": ((date(2026, 5, 20), "146/88"),),
}
"""The closed Visits behind today's, each with the seated blood pressure it measured.

Three for Fatima, so the Brief draws a line rather than a dot, and so the line is the one
§5.3 exists for: a pressure coming down and still above the band. One each for Abdullah and
Mohammed, which is all it takes to make today's Visit Routine. Noura and Sara are absent
from this table on purpose — today *is* their Baseline, and an empty tuple against their
names would read as history somebody looked for and did not find.
"""

TRANSCRIBED = "Recorded on paper before Noor; only the Vitals were transcribed."
"""What the seven non-Vitals sections of a historical Visit hold. Vitals holds the real
shape because the Brief reads it; the other seven hold this sentence, because a seeded
Visit carrying eight sections of invented clinical work would be the one lie in this
database. Web Pass 2 decides how to draw a section recorded before Noor existed."""

REASONS = {
    VisitKind.BASELINE: "Enrolment — before Noor",
    VisitKind.ROUTINE: "Three-month review — before Noor",
}

KNOCK = time(9, 20)
CLOSE = time(10, 5)

PLAN = BetweenVisitPlan(
    schedule=(MeasurementSchedule(Axis.SYSTOLIC, 3),
              MeasurementSchedule(Axis.GLUCOSE_PRE_PRANDIAL, 3)),
    stop_rules=(Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 180, "call the Supervisor"),
                Threshold(Axis.GLUCOSE_PRE_PRANDIAL, Comparison.BELOW, 4.0,
                          "treat the hypoglycaemia and call")))
"""No titration line, on any of these Visits: there is nothing ratified to titrate toward,
and `check_titration_allowed` refuses one (§4.8, §4.11)."""


def build(conn: Connection, *, day: date, at: datetime) -> int:
    """Seed one day, and return how many Visits it put on it.

    `at` is when the office did the pre-departure read, so the age the Visit List states is
    the age of a read that actually happened (§5.2). A Patient already enrolled is skipped
    whole — the roster read runs twice in a morning, and the second run adds nothing.
    """
    records = emr.FixtureEMR(at)
    lines = records.roster(day)
    if not lines.is_present:
        return 0
    known = store.enrolled(conn)
    due = [line for line in lines.value if line.patient_id not in known]
    catalogue = items(content.load("surveillance-intervals").data["intervals"]["rows"])
    for line in due:
        _enrol(conn, line)
        for on, reading in PAST.get(line.patient_id, ()):
            _closed(conn, line.patient_id, on, reading)
        store.schedule(conn, Visit(line.visit_id, line.patient_id),
                       line.scheduled_for, line.reason)
        prefetch.prepare(conn, records, line.patient_id, items=catalogue, at=at)
    return len(due)


def _enrol(conn: Connection, line: emr.RosterLine) -> None:
    """The name off the roster line, the conditions and the pair off the fixtures."""
    team = TEAMS[line.patient_id]
    store.add_patient(conn, line.patient_id, line.patient_name,
                      _slugs(emr.FIXTURES[line.patient_id].problems),
                      junior_physician=team.junior_physician, nurse=team.nurse)


def _slugs(problems: Sequence[str]) -> list[str]:
    return [CONDITIONS[name] for name in problems if name in CONDITIONS]


def _closed(conn: Connection, patient_id: str, on: date, reading: str) -> None:
    """One Visit that already happened, walked through the states a live one walks.

    The kind is derived and never chosen: `kind_for` reads what is already in the store, so
    the first of Fatima's three is her Baseline and the other two are Routine — for the same
    reason, and by the same function, as today's (§5.5).
    """
    team = TEAMS[patient_id]
    kind = kind_for(store.history(conn, patient_id))
    goal = _goal(patient_id, on, team.junior_physician)
    closed_at = datetime.combine(on, CLOSE)
    visit = Visit(f"{patient_id}-{on:%Y%m%d}", patient_id)
    store.schedule(conn, visit, on, REASONS[kind])
    visit.start(datetime.combine(on, KNOCK), kind,
                junior_physician=team.junior_physician, nurse=team.nurse)
    visit.previous_plan = store.standing_plan(conn, patient_id)
    for section in Section:
        visit.resolutions[section] = Resolution(section, content=TRANSCRIBED)
    visit.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, content={"bp-seated": reading})
    visit.plan = PLAN
    visit.complete(team.junior_physician, closed_at, goal)
    store.save(conn, visit)
    # Every close is handed a goal, because §5.8 refuses a Baseline without one. Only the
    # Baseline's is stored: §4.4 has a Routine Visit compare against the target and never
    # reset it, so a second proposal would be a Routine Visit moving the goalposts.
    if kind is VisitKind.BASELINE:
        store.propose_goal(conn, goal)
    # Its Write-Back went out the day it closed. Left queued, five months of history would
    # join today's drain and the demo's queue would be about the wrong Visits (§4.10).
    store.mark_written_back(conn, visit.id, closed_at)


def _goal(patient_id: str, on: date, by: str) -> GoalOfCare:
    """The target the Baseline proposed, left unratified on purpose.

    Ratification happens outside the house (§4.4, ADR 0003). An unratified target is what
    puts a real Ratification row in the Supervisor's inbox — already long past its window,
    which is the state §5.11 wants visible rather than smoothed away.
    """
    return GoalOfCare(
        patient_id,
        bands=(Band(Axis.SYSTOLIC, 110, 135, "home band, frailty considered"),
               Band(Axis.DIASTOLIC, 65, 85, "home band"),
               Band(Axis.HBA1C, 7.0, 8.0, "relaxed for age and hypoglycaemia risk")),
        lineage="Proposed at the Baseline Visit from the household's own readings (§4.4)",
        office_anchor=f"the referring clinic's reading of record, {on.isoformat()}",
        proposed_by=by,
        proposed_at=datetime.combine(on, CLOSE))
