"""The store: what it keeps, and the write it refuses (§5.9)."""
from dataclasses import replace
from datetime import date, datetime, time

import pytest
import sqlite3

from noor.domain.plans import Axis, Band, BetweenVisitPlan, GoalOfCare, MeasurementSchedule
from noor.domain.records import Reason, Resolution
from noor.domain.states import Datum, Section, VisitKind, VisitState
from noor.domain.visit import Visit
from noor import store

MONDAY = date(2026, 8, 31)
TUESDAY = date(2026, 9, 1)
NINE = datetime(2026, 8, 31, 9, 0)


@pytest.fixture
def conn(tmp_path):
    connection = store.connect(tmp_path / "noor.sqlite3")
    store.add_patient(connection, "p-1", "Fatima Ali", ["diabetes"])
    yield connection
    connection.close()


def scheduled(visit_id="v-1", patient_id="p-1"):
    return Visit(visit_id, patient_id)


def test_connecting_to_a_fresh_file_creates_the_schema(tmp_path):
    # Arrange / Act
    connection = store.connect(tmp_path / "fresh.sqlite3")

    # Assert — an empty roster, not a missing-table error
    assert store.roster(connection, MONDAY) == []


def test_a_scheduled_visit_loads_back_as_the_visit_that_was_scheduled(conn):
    # Arrange
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")

    # Act
    result = store.load(conn, "v-1")

    # Assert
    assert result == subject


def test_saving_a_visit_replaces_what_was_stored(conn):
    # Arrange
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    subject.start(NINE, VisitKind.ROUTINE)

    # Act
    store.save(conn, subject)

    # Assert
    assert store.load(conn, "v-1").state is VisitState.IN_PROGRESS


def test_the_state_column_agrees_with_the_visit_so_the_roster_reads_no_json(conn):
    # Arrange
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    subject.start(NINE, VisitKind.ROUTINE)
    store.save(conn, subject)

    # Act
    row = conn.execute("select state from visits where id = 'v-1'").fetchone()

    # Assert
    assert row["state"] == "in_progress"


def test_loading_a_visit_that_does_not_exist_is_refused(conn):
    # Act / Assert
    with pytest.raises(store.UnknownVisit):
        store.load(conn, "v-nope")


def test_saving_a_visit_that_was_never_scheduled_is_refused(conn):
    # Act / Assert — a stale form posting to an id the roster never created
    with pytest.raises(store.UnknownVisit):
        store.save(conn, scheduled("v-nope"))


@pytest.mark.parametrize("terminal", [
    VisitState.COMPLETED, VisitState.CANCELLED, VisitState.ENDED_EARLY])
def test_a_visit_in_a_terminal_state_cannot_be_written_again(conn, terminal):
    # Arrange — the close is stored, then a second request arrives for the same Visit
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    subject.state = terminal
    store.save(conn, subject)
    subject.resolutions[Section.NOTES] = Resolution(Section.NOTES, content={"late": True})

    # Act / Assert — §5.9: the row says no, whether or not a transition was involved
    with pytest.raises(store.TerminalVisit):
        store.save(conn, subject)


def test_the_roster_lists_the_days_visits_with_the_patient_and_the_reason(conn):
    # Arrange
    store.schedule(conn, scheduled(), MONDAY, "three months since the last review")

    # Act
    result = store.roster(conn, MONDAY)

    # Assert — §4.9: the roster entry carries the reason the Visit was scheduled
    assert result == [store.RosterEntry(
        "v-1", "p-1", "Fatima Ali",
        "three months since the last review", VisitState.SCHEDULED)]


def test_the_roster_does_not_list_another_days_visits(conn):
    # Arrange
    store.schedule(conn, scheduled(), TUESDAY, "three months since the last review")

    # Act / Assert
    assert store.roster(conn, MONDAY) == []


def test_the_roster_shows_a_finished_visit_rather_than_hiding_it(conn):
    # Arrange
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    subject.state = VisitState.COMPLETED
    store.save(conn, subject)

    # Act
    result = store.roster(conn, MONDAY)

    # Assert — the Silence Audit samples Completed Visits, so they stay on the day
    assert result[0].state is VisitState.COMPLETED


def test_a_visit_for_a_patient_who_is_not_enrolled_is_refused(conn):
    # Act / Assert — foreign keys are off by default in sqlite3; connect turns them on
    with pytest.raises(sqlite3.IntegrityError):
        store.schedule(conn, scheduled("v-2", "p-nobody"), MONDAY, "walk-in")


def test_a_patients_conditions_come_back_as_a_list(conn):
    # Act / Assert
    assert store.conditions(conn, "p-1") == ["diabetes"]


def test_asking_for_an_unknown_patients_conditions_is_refused(conn):
    # Act / Assert
    with pytest.raises(store.StoreError):
        store.conditions(conn, "p-nobody")


def test_a_stale_scheduled_object_cannot_un_start_a_started_visit(conn):
    # Arrange — the stale-page shape: an object loaded before the Start
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    stale = store.load(conn, "v-1")
    subject.start(NINE, VisitKind.ROUTINE)
    store.save(conn, subject)

    # Act / Assert — §5.5: the Start is the attendance record; the row says no
    with pytest.raises(store.StoreError):
        store.save(conn, stale)


def ended_early(conn, visit_id, day):
    """The shortest path to a finished Visit: scheduled, started, ended early.

    Named for the state it produces, not `closed` — Task 21 appends a helper to this same
    module that closes a Visit as *Completed*, and two `closed`s would silently shadow
    each other with the later definition winning.
    """
    visit = scheduled(visit_id)
    store.schedule(conn, visit, day, "three months since the last review")
    visit.start(datetime.combine(day, time(9, 0)), VisitKind.ROUTINE)
    visit.end_early(Reason("time-exhausted"), "nurse-1", datetime.combine(day, time(10, 0)))
    store.save(conn, visit)
    return visit


def test_the_history_of_a_patient_is_their_finished_visits_oldest_first(conn):
    # Arrange — stored newest first, so the order cannot be the insertion order
    ended_early(conn, "v-2", TUESDAY)
    ended_early(conn, "v-1", MONDAY)

    # Act
    past = store.history(conn, "p-1")

    # Assert
    assert [visit.id for visit in past] == ["v-1", "v-2"]


def test_a_visit_that_is_still_open_is_not_history(conn):
    # Arrange
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    subject.start(NINE, VisitKind.ROUTINE)
    store.save(conn, subject)

    # Act
    past = store.history(conn, "p-1")

    # Assert — §5.3 reads the series out of finished Visits, not out of this one
    assert past == []


def proposed(patient_id="p-1"):
    """A Baseline Visit's proposal: home numbers, floor to ceiling (§4.4)."""
    return GoalOfCare(
        patient_id=patient_id,
        bands=(Band(Axis.SYSTOLIC, 120, 135, "ADA older-adult band"),
               Band(Axis.HBA1C, 7.0, 8.0)),
        lineage="ADA Standards of Care 2025, Table 13.1",
        office_anchor="140/90",
        proposed_by="Dr Hana Saleh",
        proposed_at=NINE,
    )


def test_a_proposed_goal_of_care_comes_back_for_the_patient_it_was_proposed_for(conn):
    # Arrange
    subject = proposed()

    # Act
    store.propose_goal(conn, subject)

    # Assert
    assert store.goal(conn, "p-1") == subject


def test_a_patient_with_no_goal_of_care_has_none_rather_than_an_empty_one(conn):
    # Act / Assert — a Patient before their Baseline. Task 17 withholds on exactly this.
    assert store.goal(conn, "p-1") is None


def test_a_second_proposal_replaces_a_target_nobody_ratified(conn):
    # Arrange — the Baseline Ended Early, so a later Baseline proposes again
    store.propose_goal(conn, proposed())
    revised = replace(proposed(), office_anchor="150/90")

    # Act
    store.propose_goal(conn, revised)

    # Assert
    assert store.goal(conn, "p-1").office_anchor == "150/90"


def test_a_ratified_goal_of_care_is_never_overwritten_by_a_new_proposal(conn):
    # Arrange — every reading since ratification was compared against these bands
    store.propose_goal(conn, proposed())
    store.ratify_goal(conn, "p-1", "Dr Omar Farouk", datetime(2026, 9, 2, 11, 0))

    # Act / Assert
    with pytest.raises(store.GoalError):
        store.propose_goal(conn, replace(proposed(), office_anchor="150/90"))


def test_a_refused_proposal_leaves_the_ratified_target_exactly_as_it_was(conn):
    # Arrange
    store.propose_goal(conn, proposed())
    store.ratify_goal(conn, "p-1", "Dr Omar Farouk", datetime(2026, 9, 2, 11, 0))

    # Act — the refusal above, swallowed here so the row can be inspected after it
    with pytest.raises(store.GoalError):
        store.propose_goal(conn, replace(proposed(), office_anchor="150/90"))

    # Assert — the whole target, not just the field the proposal tried to change
    assert store.goal(conn, "p-1") == replace(
        proposed(), ratified_by="Dr Omar Farouk",
        ratified_at=datetime(2026, 9, 2, 11, 0))


def test_ratification_records_who_ratified_and_when(conn):
    # Arrange
    store.propose_goal(conn, proposed())

    # Act
    result = store.ratify_goal(conn, "p-1", "Dr Omar Farouk", datetime(2026, 9, 2, 11, 0))

    # Assert — §5.13: a decision carries an individual name
    assert (result.is_ratified, result.ratified_by, result.ratified_at) == (
        True, "Dr Omar Farouk", datetime(2026, 9, 2, 11, 0))


def test_the_ratified_target_is_what_comes_back_on_the_next_read(conn):
    # Arrange
    store.propose_goal(conn, proposed())

    # Act
    store.ratify_goal(conn, "p-1", "Dr Omar Farouk", datetime(2026, 9, 2, 11, 0))

    # Assert — ratification is stored, not only returned
    assert store.goal(conn, "p-1").is_ratified is True


def test_ratifying_a_target_nobody_proposed_is_refused(conn):
    # Act / Assert
    with pytest.raises(store.GoalError):
        store.ratify_goal(conn, "p-1", "Dr Omar Farouk", datetime(2026, 9, 2, 11, 0))


def test_a_goal_of_care_cannot_be_ratified_twice(conn):
    # Arrange
    store.propose_goal(conn, proposed())
    store.ratify_goal(conn, "p-1", "Dr Omar Farouk", datetime(2026, 9, 2, 11, 0))

    # Act / Assert — two Supervisors each believing they were the reviewer (§5.13)
    with pytest.raises(store.GoalError):
        store.ratify_goal(conn, "p-1", "Dr Layla Nasser", datetime(2026, 9, 3, 9, 0))


def test_a_goal_of_care_for_a_patient_the_store_does_not_have_is_refused(conn):
    # Act / Assert — the foreign key, same guard the roster gets
    with pytest.raises(sqlite3.IntegrityError):
        store.propose_goal(conn, proposed("p-nobody"))


def test_a_band_with_no_numeric_target_survives_the_store(conn):
    # Arrange — ADA's very-complex band is literally *avoid reliance on A1C* (§4.4)
    subject = replace(proposed(), bands=(
        Band(Axis.HBA1C, None, None, "avoid reliance on A1C — very complex health"),))

    # Act
    store.propose_goal(conn, subject)

    # Assert — a value, not an empty field
    assert store.goal(conn, "p-1").bands[0].is_numeric is False


def test_marking_a_visit_written_back_changes_nothing_a_clinician_wrote(conn):
    # Arrange
    subject = scheduled()
    store.schedule(conn, subject, MONDAY, "three months since the last review")
    before = conn.execute("select body from visits where id = 'v-1'").fetchone()["body"]

    # Act
    store.mark_written_back(conn, "v-1", datetime(2026, 8, 31, 19, 0))

    # Assert — §5.9 holds: the delivery receipt is not part of the record
    assert conn.execute(
        "select body from visits where id = 'v-1'").fetchone()["body"] == before


def test_marking_a_visit_written_back_twice_is_refused(conn):
    # Arrange
    store.schedule(conn, scheduled(), MONDAY, "three months since the last review")
    store.mark_written_back(conn, "v-1", datetime(2026, 8, 31, 19, 0))

    # Act / Assert — a second acceptance is a delivery nobody made
    with pytest.raises(store.StoreError):
        store.mark_written_back(conn, "v-1", datetime(2026, 8, 31, 21, 0))


def test_marking_a_visit_the_store_does_not_have_is_refused(conn):
    # Act / Assert — a no-op here would leave a real Visit queued forever
    with pytest.raises(store.StoreError):
        store.mark_written_back(conn, "v-nope", datetime(2026, 8, 31, 19, 0))


def test_recording_a_refusal_against_a_visit_the_store_does_not_have_is_refused(conn):
    # Act / Assert — the same reason as above, from the other direction: a refusal
    # written against nothing is a refusal nobody can find (§4.10)
    with pytest.raises(store.StoreError):
        store.mark_refused(conn, "v-nope", datetime(2026, 8, 31, 19, 0), "no such Patient")


def test_a_refusal_changes_nothing_a_clinician_wrote_and_leaves_the_visit_queued(conn):
    # Arrange
    store.schedule(conn, scheduled(), MONDAY, "three months since the last review")
    before = conn.execute("select body from visits where id = 'v-1'").fetchone()["body"]

    # Act
    store.mark_refused(conn, "v-1", datetime(2026, 8, 31, 19, 0), "unknown Patient")

    # Assert — §5.9 and §5.1 together: the record is untouched and the Visit is still
    # queued, so the next drive back tries again
    row = conn.execute("select body, written_back_at from visits").fetchone()
    assert (row["body"], row["written_back_at"]) == (before, None)


def closed(conn, visit_id: str, day: date) -> None:
    """A Visit in the store with Completed already recorded. Reaching that state through
    §5.8's gate is Task 4's subject and needs eight resolutions; what this query reads is
    the state column, so the Arrange stays one line."""
    store.schedule(conn, scheduled(visit_id), day, "three months since the last review")
    store.save(conn, Visit(visit_id, "p-1", VisitKind.ROUTINE,
                           state=VisitState.COMPLETED))


def test_the_completed_visits_of_a_week_come_back_oldest_first(conn):
    # Arrange — Wednesday stored first, to prove insertion order is not the order
    closed(conn, "v-9", date(2026, 8, 26))
    closed(conn, "v-1", date(2026, 8, 24))

    # Act
    result = store.completed_between(conn, date(2026, 8, 23), date(2026, 8, 30))

    # Assert
    assert [visit.id for visit in result] == ["v-1", "v-9"]


def test_a_visit_scheduled_outside_the_week_is_not_in_the_week(conn):
    # Arrange — the day before the window, both of its edges, and the day after
    closed(conn, "v-1", date(2026, 8, 22))
    closed(conn, "v-2", date(2026, 8, 23))
    closed(conn, "v-3", date(2026, 8, 29))
    closed(conn, "v-4", date(2026, 8, 30))

    # Act
    result = store.completed_between(conn, date(2026, 8, 23), date(2026, 8, 30))

    # Assert — half-open: the Sunday is in it, and the next Sunday starts the next week
    assert [visit.id for visit in result] == ["v-2", "v-3"]


def test_a_visit_that_ended_early_is_not_counted_among_the_weeks_silence(conn):
    # Arrange — §5.6: it produced nothing because it was interrupted, which is a reason
    # already known, and the sample exists to surface the ones that are not
    store.schedule(conn, scheduled("v-1"), date(2026, 8, 24), "post-discharge follow-up")
    store.save(conn, Visit("v-1", "p-1", VisitKind.ROUTINE,
                           state=VisitState.ENDED_EARLY))

    # Act / Assert
    assert store.completed_between(conn, date(2026, 8, 23), date(2026, 8, 30)) == []


def test_a_week_with_nothing_closed_in_it_is_empty_rather_than_an_error(conn):
    # Act / Assert — every week before the first Visit, and the week after a holiday
    assert store.completed_between(conn, date(2026, 8, 23), date(2026, 8, 30)) == []


PLAN = BetweenVisitPlan(schedule=(MeasurementSchedule(Axis.SYSTOLIC, 3),))


def with_a_plan(conn, visit_id: str, day: date, plan: BetweenVisitPlan) -> None:
    """A Completed Visit that emitted a plan. Same shortcut as `closed`: what
    `standing_plan` reads is the stored body, so §5.8's gate is not on this path."""
    store.schedule(conn, scheduled(visit_id), day, "three months since the last review")
    store.save(conn, Visit(visit_id, "p-1", VisitKind.ROUTINE,
                           state=VisitState.COMPLETED, plan=plan,
                           closed_at=datetime.combine(day, time(10, 0))))


def test_the_plan_in_force_is_the_last_one_any_finished_visit_emitted(conn):
    # Arrange — a Visit that emitted a plan, then one that ended before it could
    with_a_plan(conn, "v-1", MONDAY, PLAN)
    ended_early(conn, "v-2", TUESDAY)

    # Act
    standing = store.standing_plan(conn, "p-1")

    # Assert — §5.6: the plan outlives the Visit that emitted nothing
    assert standing == Datum.present(PLAN, as_of=datetime.combine(MONDAY, time(10, 0)))


def test_a_patient_who_has_never_had_a_plan_has_none_in_force_rather_than_an_empty_one(
        conn):
    # Arrange — one finished Visit, and no plan on it
    ended_early(conn, "v-1", MONDAY)

    # Act
    result = store.standing_plan(conn, "p-1")

    # Assert — Absent is the truth only before the first plan (N6)
    assert result == Datum.absent()


def test_patient_name_raises_when_patient_missing(conn):
    # Arrange — p-1 exists, so p-unknown is absent

    # Act / Assert — mirrors conditions() guard, web layer renders 400 not 500 (§4.1)
    with pytest.raises(store.StoreError, match="no Patient"):
        store.patient_name(conn, "p-unknown")


def test_patient_name_returns_name_when_patient_exists(conn):
    # Act / Assert
    assert store.patient_name(conn, "p-1") == "Fatima Ali"


def test_scheduled_reason_raises_when_visit_missing(conn):
    # Act / Assert — mirrors patient_name guard so web layer renders 400 (§4.1) not 500
    with pytest.raises(store.StoreError, match=r"no Visit"):
        store.scheduled_reason(conn, "v-unknown")


def test_scheduled_reason_returns_reason_when_visit_exists(conn):
    # Arrange
    store.schedule(conn, scheduled("v-1"), MONDAY, "quarterly diabetic review")

    # Act / Assert
    assert store.scheduled_reason(conn, "v-1") == "quarterly diabetic review"


def test_enrolled_returns_all_patient_ids(conn):
    # Arrange — p-1 was added in fixture
    store.add_patient(conn, "p-2", "Sara Al-Harbi", ["hypertension"])

    # Act / Assert
    assert store.enrolled(conn) == {"p-1", "p-2"}

