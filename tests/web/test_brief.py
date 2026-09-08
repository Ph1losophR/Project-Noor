"""§5.3's Brief: findings before the knock, computed on open and never stored."""
from datetime import date, datetime

import pytest

from noor import store
from noor.domain.plans import Axis, BetweenVisitPlan, MeasurementSchedule
from noor.domain.records import Resolution
from noor.domain.states import Datum, Section, VisitKind, VisitState
from noor.domain.visit import Visit

OFFICE = datetime(2026, 8, 28, 7, 0)
KNOCK = datetime(2026, 5, 12, 9, 20)
CLOSE = datetime(2026, 5, 12, 10, 40)
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"


@pytest.fixture
def scheduled(conn, day):
    """One hypertension Patient with one Scheduled Visit. Four surveillance items apply to
    hypertension, and nothing is cached, so all four are overdue until a test says
    otherwise — `surveillance-intervals.md` calls an item nobody recorded one to do now."""
    store.add_patient(conn, "p-1", "Fatima Al-Harbi", ["hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    record = Visit("v-1", "p-1")
    store.schedule(conn, record, day, "Three-month review")
    return record


def earlier(conn, *, plan=None, vitals=None):
    """One Completed Visit behind the Scheduled one, so the Brief has a history to read."""
    past = Visit("v-0", "p-1")
    store.schedule(conn, past, date(2026, 5, 12), "Enrolment")
    past.state = VisitState.COMPLETED
    past.kind = VisitKind.BASELINE
    past.started_at = KNOCK
    past.closed_by = JUNIOR_PHYSICIAN
    past.closed_at = CLOSE
    past.plan = plan
    if vitals is not None:
        past.resolutions[Section.VITALS] = Resolution(Section.VITALS, content=vitals)
    store.save(conn, past)
    return past


def test_a_first_visit_brief_says_so_everywhere_rather_than_showing_gaps(
        client, scheduled):
    # Arrange / Act
    answer = client.get("/visits/v-1/brief")

    # Assert — §7.2 four times over on the emptiest Brief Noor can produce
    assert answer.status_code == 200
    assert "This is the first Visit Noor holds for this Patient." in answer.text
    assert "No Visit has emitted a Between-Visit Plan for this Patient yet" in answer.text
    assert "there is no series to read yet." in answer.text
    assert "Surveillance items overdue: 4." in answer.text
    assert "Noor read everything it asked the EMR for" in answer.text


def test_the_brief_states_both_of_its_own_limits(client, scheduled):
    # Arrange / Act
    answer = client.get("/visits/v-1/brief")

    # Assert — §5.3's title, and §5.3's paragraph on Home Readings
    assert "It makes no recommendation" in answer.text
    assert "read off the devices' own memory when the Nurse arrives" in answer.text


def test_the_vitals_series_reads_across_the_visits_that_recorded_it(
        client, conn, scheduled):
    # Arrange
    earlier(conn, vitals={"bp-seated": "148/92", "pulse": "78"})

    # Act
    answer = client.get("/visits/v-1/brief")

    # Assert
    assert "Vitals series Noor holds for this Patient: 2." in answer.text
    assert "Blood pressure, seated (mmHg)" in answer.text
    assert "12 May 2026: 148/92" in answer.text
    assert "The last Visit was Completed on 12 May 2026." in answer.text


def test_a_standing_plan_is_read_now_while_the_visit_is_still_scheduled(
        client, conn, scheduled):
    """§5.3: computed on open. Nothing has frozen this yet, so the Brief reads the store."""
    # Arrange
    earlier(conn, plan=BetweenVisitPlan(
        schedule=(MeasurementSchedule(Axis.SYSTOLIC, 3),)))

    # Act
    answer = client.get("/visits/v-1/brief")

    # Assert
    assert "A Between-Visit Plan has been standing since 12 May 2026." in answer.text


def test_an_unreadable_item_is_a_blind_spot_and_not_an_overdue_one(
        client, conn, scheduled):
    # Arrange
    store.cache_read(conn, "p-1", "surveillance:potassium",
                     Datum.present("2025-02-10", as_of=OFFICE), OFFICE)
    store.cache_read(conn, "p-1", "surveillance:lipid-profile",
                     Datum.unreachable(), OFFICE)

    # Act
    answer = client.get("/visits/v-1/brief")

    # Assert — listing a failed read as overdue would make a clinical claim out of it
    assert "Surveillance items overdue: 3." in answer.text
    assert "Last done 10 February 2025." in answer.text
    assert "Reads Noor could not make: 1." in answer.text
    assert "Lipid profile: the date could not be read from the record" in answer.text


def test_an_open_visit_shows_the_plan_the_start_froze_and_not_a_newer_answer(
        client, conn, scheduled):
    """§5.5: the Start freezes the engine's inputs for the Visit's duration. Here the store
    would answer Absent and the record says Unreachable — the record wins."""
    # Arrange
    scheduled.start(datetime(2026, 8, 28, 9, 20), VisitKind.ROUTINE,
                    junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    scheduled.previous_plan = Datum.unreachable()
    store.save(conn, scheduled)

    # Act
    answer = client.get("/visits/v-1/brief")

    # Assert — the declaration names the failed read, the blind spot names what it costs
    assert "The Between-Visit Plan in force could not be read." in answer.text
    assert "Reads Noor could not make: 1." in answer.text
    assert "have nothing to be scored against" in answer.text


def test_the_brief_leads_back_to_the_visit_and_starts_nothing(client, conn, scheduled):
    # Arrange / Act
    answer = client.get("/visits/v-1/brief")

    # Assert — §5.3: preparation is not attendance
    assert 'href="/visits/v-1"' in answer.text
    assert store.load(conn, "v-1").state is VisitState.SCHEDULED


def test_an_emergency_suspends_the_brief_like_every_other_visit_address(
        client, conn, scheduled):
    # Arrange
    scheduled.start(datetime(2026, 8, 28, 9, 20), VisitKind.ROUTINE,
                    junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    scheduled.enter_emergency(datetime(2026, 8, 28, 9, 30))
    store.save(conn, scheduled)

    # Act
    answer = client.get("/visits/v-1/brief", follow_redirects=False)

    # Assert
    assert answer.status_code == 303
    assert answer.headers["location"] == "/visits/v-1/emergency"
