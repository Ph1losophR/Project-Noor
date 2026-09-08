"""Delivery (§4.9), and the one thing §4.10 forbids: a Write-Back that fails quietly."""
from datetime import date, datetime

import pytest

from noor.domain.plans import Axis, Band, BetweenVisitPlan, GoalOfCare, MeasurementSchedule
from noor.domain.records import Reason, Resolution
from noor.domain.opinions import Disposition, Outcome, Recommendation
from noor.domain.states import EscalationTier, Section, VisitKind
from noor.domain.visit import Addendum, Visit
from noor.domain.writeback import Kind, Windows
from noor.emr import FixtureEMR, WriteRejected
from noor import dispatch, store

MONDAY = date(2026, 8, 31)
EIGHT = datetime(2026, 8, 31, 8, 0)
NOON = datetime(2026, 8, 31, 12, 0)
EVENING = datetime(2026, 8, 31, 19, 0)
LATER = datetime(2026, 8, 31, 21, 0)
WINDOWS = Windows(tier_1_hours=72, tier_2_hours=0, ratification_days=7)
SUPERVISOR = "Dr Omar Farouk"
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"
PROPOSAL = GoalOfCare(
    patient_id="p-001",
    bands=(Band(Axis.SYSTOLIC, 120, 135, "ADA older-adult band"),),
    lineage="ADA Standards of Care 2025, Table 13.1",
    office_anchor="140/90", proposed_by="Dr Hana Saleh", proposed_at=NOON)


@pytest.fixture
def conn(tmp_path):
    """Patient ids match the fixture EMR's, so p-005 is the one that rejects writes."""
    connection = store.connect(tmp_path / "noor.sqlite3")
    store.add_patient(connection, "p-001", "Fatima Ali", ["diabetes"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.add_patient(connection, "p-005", "Sara Al-Harbi", ["hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    yield connection
    connection.close()


@pytest.fixture
def emr():
    return FixtureEMR(now=NOON)


def completed(visit_id="v-1", patient_id="p-001", kind=VisitKind.ROUTINE) -> Visit:
    """A silent Visit through §5.8's gate — the least Arrange that still writes back."""
    visit = Visit(visit_id, patient_id)
    for section in Section:
        visit.resolutions[section] = Resolution(section, reason=Reason("patient-declined"))
    visit.plan = BetweenVisitPlan(
        schedule=(MeasurementSchedule(Axis.SYSTOLIC, times_per_week=3),))
    visit.start(EIGHT, kind, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    # A Baseline's close needs a proposal to exist (§5.5). The envelope's copy comes from
    # the store (Task 18), so this one only has to satisfy the gate.
    visit.complete(by="Dr Nada Al-Ghamdi", at=NOON,
                   goal=PROPOSAL if kind is VisitKind.BASELINE else None)
    return visit


def completed_with_response() -> Visit:
    visit = completed()
    visit.shown = [Recommendation(
        "r-1", "Review the home blood-pressure plan", EscalationTier.TIER_1,
        executor="Junior Physician", provenance="Noor test rule", strength="strong")]
    visit.dispositions = [Disposition(
        "r-1", Outcome.ACCEPTED, by="Dr Nada Al-Ghamdi", at=NOON)]
    return visit


def stored(conn, visit: Visit) -> Visit:
    """On the roster first, then closed — the row's state must start out non-terminal
    or Task 11's guard refuses the write, which is the guard doing its job."""
    store.schedule(conn, Visit(visit.id, visit.patient_id),
                   MONDAY, "three months since the last review")
    store.save(conn, visit)
    return visit


def drain(conn, emr, attempted_at=EVENING):
    return dispatch.drain(conn, emr, windows=WINDOWS, supervisor=SUPERVISOR,
                          attempted_at=attempted_at)


class FlakyEMR:
    """Refuses once, then accepts — a house with no signal, then a road with some.

    A local stub rather than a flag on `FixtureEMR`, because the fixtures' hostility is
    data about a *Patient* (§4.9) and a Patient does not stop refusing halfway through
    the day. This is the EMR boundary, which `docs/testing-standards.md` names as the
    one place a mock belongs.
    """

    def __init__(self) -> None:
        self.accepted: list[tuple[str, dict]] = []
        self.refusals = 1

    def submit(self, patient_id: str, payload: dict) -> None:
        if self.refusals:
            self.refusals -= 1
            raise WriteRejected("no route to the EMR")
        self.accepted.append((patient_id, payload))


def test_a_closed_visit_reaches_the_emr_as_one_envelope_for_the_whole_visit(conn, emr):
    # Arrange
    stored(conn, completed())

    # Act
    drain(conn, emr)

    # Assert — one submit, carrying the Visit id and every item assemble() produced
    assert emr.accepted == [("p-001", {
        "visit_id": "v-1",
        "items": [{"kind": Kind.VISIT_OUTCOME.name, "payload": {
            "state": "completed",
            "started_at": EIGHT.isoformat(),
            "closed_by": "Dr Nada Al-Ghamdi",
            "closed_at": NOON.isoformat(),
            "reason": None,
            "emergencies": [],
            "sections_not_run": [],
        }},
        {"kind": Kind.BETWEEN_VISIT_PLAN.name, "payload": {
            "titration": [],
            "schedule": [{"axis": "systolic", "times_per_week": 3}],
            "stop_rules": [],
        }}],
    })]


def test_a_delivered_visit_leaves_the_queue(conn, emr):
    # Arrange
    stored(conn, completed())

    # Act
    drain(conn, emr)

    # Assert
    assert store.queued(conn) == []


def test_a_rejected_write_leaves_the_visit_queued_for_the_next_drive_within_range(conn, emr):
    # Arrange — p-005 is the fixture Patient whose EMR refuses the write (§4.9)
    stored(conn, completed(patient_id="p-005"))

    # Act
    drain(conn, emr)

    # Assert — still queued, so nothing was lost and the next drain will try again
    assert store.queued(conn) == ["v-1"]


def test_a_rejected_write_is_reported_with_what_the_emr_said(conn, emr):
    # Arrange
    stored(conn, completed(patient_id="p-005"))

    # Act
    result = drain(conn, emr)

    # Assert — §4.10: never quiet. The caller is handed the refusal, not a silence.
    assert result == dispatch.Delivery(
        sent=(), failed=(("v-1", "the EMR refused the write for 'p-005'"),))


def test_a_rejected_write_is_recorded_against_the_visit_with_what_the_emr_said(conn, emr):
    # Arrange
    stored(conn, completed(patient_id="p-005"))

    # Act
    drain(conn, emr)

    # Assert — §5.1's third status, and the state untouched: a refusal does not reopen
    row = conn.execute(
        "select state, last_refused_at, last_refusal from visits").fetchone()
    assert tuple(row) == ("completed", EVENING.isoformat(),
                          "the EMR refused the write for 'p-005'")


def test_one_patients_rejecting_emr_does_not_stop_the_next_visits_delivery(conn, emr):
    # Arrange — the refusing Patient sorts first, so a bail-out would be visible
    stored(conn, completed(visit_id="v-1", patient_id="p-005"))
    stored(conn, completed(visit_id="v-2", patient_id="p-001"))

    # Act
    result = drain(conn, emr)

    # Assert
    assert result == dispatch.Delivery(
        sent=("v-2",), failed=(("v-1", "the EMR refused the write for 'p-005'"),))


def test_a_retry_keeps_the_close_based_deadline_and_records_each_attempt_time(conn):
    # Arrange
    stored(conn, completed_with_response())
    store.mark_refused(conn, "v-1", EVENING, "no route to the EMR")
    flaky = FlakyEMR()
    flaky.refusals = 0

    # Act
    delivery = drain(conn, flaky, attempted_at=LATER)

    # Assert
    row = conn.execute("select written_back_at, last_refused_at from visits").fetchone()
    response = flaky.accepted[0][1]["items"][1]["payload"]["recommendations"][0]["response"]
    assert (delivery, len(flaky.accepted), store.queued(conn), response, tuple(row)) == (
        dispatch.Delivery(sent=("v-1",), failed=()),
        1,
        [],
        {"owner": SUPERVISOR,
         "due_at": datetime(2026, 9, 3, 12, 0).isoformat()},
        (LATER.isoformat(), EVENING.isoformat()),
    )


def test_draining_an_empty_queue_is_not_an_error(conn, emr):
    # Act — the ordinary case: a morning with nothing outstanding
    result = drain(conn, emr)

    # Assert
    assert result == dispatch.Delivery(sent=(), failed=())


def test_a_cancelled_visit_is_never_queued_for_a_write_back(conn, emr):
    # Arrange — §5.4: a Visit that never started writes nothing at all, and never held a kind
    visit = Visit("v-1", "p-001")
    visit.cancel(Reason("patient-in-hospital"), by="Nurse Amal Yousef", at=EIGHT)
    stored(conn, visit)

    # Act
    result = drain(conn, emr)

    # Assert — not queued, not sent, and not reported as a failure either
    assert (store.queued(conn), result) == ([], dispatch.Delivery(sent=(), failed=()))


def test_a_visit_still_in_progress_is_not_queued(conn):
    # Arrange — the Field Team is in the house
    visit = Visit("v-1", "p-001")
    visit.start(EIGHT, VisitKind.ROUTINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    stored(conn, visit)

    # Act / Assert — there is nothing to report about an attendance in progress
    assert store.queued(conn) == []


def test_sending_a_visit_that_has_not_closed_is_refused(conn, emr):
    # Arrange
    visit = Visit("v-1", "p-001")
    visit.start(EIGHT, VisitKind.ROUTINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    stored(conn, visit)

    # Act / Assert — an empty envelope would mark an open Visit as delivered
    with pytest.raises(dispatch.NotClosed):
        dispatch.send(conn, emr, "v-1", windows=WINDOWS,
                      supervisor=SUPERVISOR, attempted_at=EVENING)


def test_the_queue_is_oldest_first_so_the_longest_wait_is_delivered_first(conn):
    # Arrange — Tuesday's Visit stored first, to prove insertion order is not the order
    store.schedule(conn, Visit("v-9", "p-001"),
                   date(2026, 9, 1), "post-discharge follow-up")
    store.save(conn, completed(visit_id="v-9"))
    stored(conn, completed(visit_id="v-1"))

    # Act / Assert
    assert store.queued(conn) == ["v-1", "v-9"]


def test_a_visit_that_ended_early_is_written_back_like_one_that_completed(conn, emr):
    # Arrange — §5.6: what was captured is not discarded, so it is still reported
    visit = Visit("v-1", "p-001")
    visit.start(EIGHT, VisitKind.ROUTINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("transferred-to-hospital"),
                    by="Nurse Amal Yousef", at=NOON)
    stored(conn, visit)

    # Act
    result = drain(conn, emr)

    # Assert
    assert (result.sent, emr.accepted[0][1]["items"][0]["payload"]["state"]) == (
        ("v-1",), "ended_early")


def test_a_baseline_visits_envelope_carries_the_target_awaiting_ratification(conn, emr):
    # Arrange — Task 18's persisted proposal, and the Baseline Visit that made it
    store.propose_goal(conn, PROPOSAL)
    stored(conn, completed(kind=VisitKind.BASELINE))

    # Act
    drain(conn, emr)

    # Assert — §5.12's second route, the Supervisor named and seven days to answer
    assert emr.accepted[0][1]["items"][-1] == {
        "kind": Kind.PROPOSED_GOAL_OF_CARE.name,
        "payload": {
            "patient_id": "p-001",
            "bands": [{"axis": "systolic", "floor": 120, "ceiling": 135,
                       "rationale": "ADA older-adult band"}],
            "lineage": "ADA Standards of Care 2025, Table 13.1",
            "office_anchor": "140/90",
            "proposed_by": "Dr Hana Saleh",
            "proposed_at": NOON.isoformat(),
            "response": {"owner": SUPERVISOR,
                         "due_at": datetime(2026, 9, 7, 12, 0).isoformat()},
        },
    }


def test_drain_returns_empty_delivery_when_lock_is_held(conn, emr):
    # Arrange — hold the drain lock
    with dispatch._DRAIN_LOCK:
        # Act
        result = drain(conn, emr)

    # Assert — overlapping drains coalesce without processing
    assert result == dispatch.Delivery((), ())


def test_a_queued_addendum_is_delivered_and_marked(conn, emr):
    # Arrange — a closed Visit with an Addendum queued behind it
    stored(conn, completed("v-1"))
    store.add_addendum(conn, Addendum(
        "a-1", "v-1", "BP rechecked, 128/82",
        author="Dr Nada Al-Ghamdi", written_at=NOON))

    # Act
    result = drain(conn, emr)

    # Assert — sent, and no longer queued
    assert "a-1" in result.sent
    assert store.queued_addenda(conn) == []


def test_a_refused_addendum_is_reported_and_stays_queued(conn):
    # Arrange — the EMR with no route home (p-005 rejects writes in the fixture)
    stored(conn, completed("v-2", patient_id="p-005"))
    store.add_addendum(conn, Addendum(
        "a-2", "v-2", "note added late",
        author="Dr Nada Al-Ghamdi", written_at=NOON))

    # Act
    result = drain(conn, FixtureEMR(now=NOON))

    # Assert — reported with what the EMR said, and still queued for the next drive
    assert any(addendum_id == "a-2" for addendum_id, _ in result.failed)
    assert store.queued_addenda(conn) == ["a-2"]

