"""The seed: one day of work in the database, and the history that makes it a day.

Arrange is an empty database, Act is one call, and every assertion is about what a screen
reads afterwards — which is the only thing this module exists to produce.
"""
from datetime import date, datetime

import pytest

from noor import prefetch, seed, store
from noor.domain.states import DataState, Section, VisitKind, VisitState
from noor.domain.visit import kind_for

DAY = date(2026, 8, 28)
AT = datetime(2026, 8, 28, 7, 0)        # the clinic, before the van left


@pytest.fixture
def conn(tmp_path):
    """One database file per test — the production shape (ADR 0006), created empty and
    thrown away, so leakage between tests is impossible rather than remembered."""
    connection = store.connect(tmp_path / "noor.db")
    yield connection
    connection.close()


def test_the_days_roster_arrives_with_every_visit_scheduled(conn):
    seed.build(conn, day=DAY, at=AT)

    rows = store.roster(conn, DAY)

    assert sorted(row.visit_id for row in rows) == [
        "v-001", "v-002", "v-003", "v-004", "v-005"]
    assert {row.state for row in rows} == {VisitState.SCHEDULED}


def test_the_count_it_returns_is_how_many_visits_it_put_on_the_day(conn):
    put = seed.build(conn, day=DAY, at=AT)

    assert put == 5


def test_each_patient_carries_their_own_standing_field_team(conn):
    seed.build(conn, day=DAY, at=AT)

    fatima = store.field_team(conn, "p-001")
    noura = store.field_team(conn, "p-003")

    assert fatima == store.FieldTeam("Dr Layla Al-Amri", "Nurse Huda Al-Zahrani")
    assert noura != fatima


def test_a_patient_is_enrolled_for_the_conditions_content_rows_are_written_against(conn):
    seed.build(conn, day=DAY, at=AT)

    assert store.conditions(conn, "p-003") == ["hypertension"]


def test_a_problem_noor_does_not_manage_is_not_enrolled_as_a_condition(conn):
    """Abdullah's stage 3a kidney disease is on his EMR record and is not one of Noor's
    two. Enrolling him for it would put rows on his forms nothing in Phase 1 can act on."""
    seed.build(conn, day=DAY, at=AT)

    assert store.conditions(conn, "p-002") == ["diabetes", "hypertension"]


def test_the_surveillance_items_stored_are_the_ones_that_apply_to_the_patient(conn):
    seed.build(conn, day=DAY, at=AT)

    stored = prefetch.surveillance(conn, "p-003")

    assert sorted(stored) == [
        "creatinine-egfr", "lipid-profile", "potassium", "urine-acr"]


def test_the_pre_departure_read_is_stored_so_the_visit_list_can_state_its_age(conn):
    seed.build(conn, day=DAY, at=AT)

    assert prefetch.readiness(conn, "p-001").prepared_at == AT


def test_the_one_patient_whose_emr_times_out_is_the_one_with_an_unreadable_read(conn):
    seed.build(conn, day=DAY, at=AT)

    assert prefetch.readiness(conn, "p-004").unreadable == ("prescribed",)
    assert prefetch.readiness(conn, "p-001").unreadable == ()


def test_a_patient_with_a_completed_baseline_behind_them_is_due_a_routine_visit(conn):
    seed.build(conn, day=DAY, at=AT)

    assert kind_for(store.history(conn, "p-001")) is VisitKind.ROUTINE


def test_a_patient_with_nothing_behind_them_is_due_a_baseline(conn):
    seed.build(conn, day=DAY, at=AT)

    assert store.history(conn, "p-003") == []
    assert kind_for(store.history(conn, "p-003")) is VisitKind.BASELINE


def test_the_closed_visits_give_the_brief_three_blood_pressures_oldest_first(conn):
    seed.build(conn, day=DAY, at=AT)

    points = [
        (visit.started_at.date(), visit.resolutions[Section.VITALS].content["bp-seated"])
        for visit in store.history(conn, "p-001")]

    assert points == [(date(2025, 11, 12), "168/96"),
                      (date(2026, 2, 18), "158/92"),
                      (date(2026, 5, 21), "152/90")]


def test_the_first_of_those_visits_is_the_baseline_and_the_rest_are_routine(conn):
    seed.build(conn, day=DAY, at=AT)

    kinds = [visit.kind for visit in store.history(conn, "p-001")]

    assert kinds == [VisitKind.BASELINE, VisitKind.ROUTINE, VisitKind.ROUTINE]


def test_a_plan_is_standing_so_the_brief_declares_one_rather_than_none(conn):
    seed.build(conn, day=DAY, at=AT)

    assert store.standing_plan(conn, "p-001").is_present
    assert store.standing_plan(conn, "p-003").state is DataState.ABSENT


def test_the_baseline_left_a_proposed_goal_of_care_awaiting_ratification(conn):
    seed.build(conn, day=DAY, at=AT)

    assert store.goal(conn, "p-001").is_ratified is False
    assert store.goal(conn, "p-003") is None


def test_nothing_historical_is_still_queued_for_the_emr(conn):
    """A Visit that closed five months ago sitting in today's Write-Back queue would make
    the demo's queue about the wrong Visits (§4.10)."""
    seed.build(conn, day=DAY, at=AT)

    assert store.queued(conn) == []


def test_running_it_twice_on_the_same_morning_adds_nothing(conn):
    seed.build(conn, day=DAY, at=AT)

    again = seed.build(conn, day=DAY, at=AT)

    assert again == 0
    assert len(store.roster(conn, DAY)) == 5


def test_a_day_nobody_is_rostered_for_creates_nothing(conn):
    put = seed.build(conn, day=date(2026, 8, 29), at=AT)

    assert put == 0
    assert store.enrolled(conn) == set()
