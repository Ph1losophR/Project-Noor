"""One address, and what it shows is what the Visit is (web_plan §4.2)."""
from datetime import datetime

import pytest

from noor import store
from noor.domain.records import Reason, Resolution
from noor.domain.states import Section, VisitKind, VisitState
from noor.domain.visit import Visit

KNOCK = datetime(2026, 8, 28, 9, 20)
CLOSE = datetime(2026, 8, 28, 10, 5)
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"


@pytest.fixture
def visit(conn, day):
    """One Patient with one Scheduled Visit. Each test moves it to the state it is about
    and saves once — the stored row stays Scheduled until then, which is what lets
    `store.save` accept a closed Visit (§5.9 refuses a closed *row*)."""
    store.add_patient(conn, "p-1", "Fatima Al-Harbi", ["hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    record = Visit("v-1", "p-1")
    store.schedule(conn, record, day, "Three-month review")
    return record


def test_a_scheduled_visit_shows_readiness_the_indicator_and_the_way_to_the_brief(
        client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1")

    # Assert
    assert answer.status_code == 200
    assert "Fatima Al-Harbi" in answer.text
    assert "Scheduled" in answer.text
    assert "Baseline Visit" in answer.text
    assert "The office prepared nothing for this Visit." in answer.text
    assert 'href="/visits/v-1/brief"' in answer.text


def test_the_visit_page_leads_back_to_the_day_it_was_scheduled_on(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1")

    # Assert — §7's one link up, and it goes to the right day rather than to today
    assert 'href="/visits?day=2026-08-28"' in answer.text


def test_an_open_visit_shows_the_eight_sections_and_which_of_them_are_resolved(
        client, conn, visit):
    # Arrange
    visit.start(KNOCK, VisitKind.BASELINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.resolutions[Section.VITALS] = Resolution(Section.VITALS,
                                                   content={"systolic": 138})
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1")

    # Assert
    assert "In Progress" in answer.text
    assert "Physical Examination" in answer.text
    assert "mark-clear" in answer.text
    assert "mark-open" in answer.text
    assert "Nothing recorded" in answer.text
    assert "Attended by Dr Layla Al-Amri, with Nurse Huda Al-Zahrani." in answer.text
    assert ("No Home Readings have been collected on this Visit. That is not a series Noor "
            "could not read — nothing has been entered yet.") in answer.text
    assert 'href="/visits/v-1/home-readings"' in answer.text
    assert "Emergencies during this Visit: 0." in answer.text


def test_a_visit_that_ended_early_shows_the_reason_and_what_the_write_back_is_doing(
        client, conn, visit):
    # Arrange
    visit.start(KNOCK, VisitKind.ROUTINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.end_early(Reason("time-exhausted"), JUNIOR_PHYSICIAN, CLOSE)
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1")

    # Assert
    assert "Ended Early by Dr Layla Al-Amri at 10:05, 28 August." in answer.text
    assert "Reason: Time exhausted." in answer.text
    assert "Write-Backs pending: 1." in answer.text
    assert "Noor has not attempted it yet" in answer.text


def test_a_completed_visit_reaches_the_same_read_only_page(client, conn, visit):
    """§5.8's four gates are `tests/domain/test_visit.py`'s subject, so this arranges the
    closed record directly rather than asserting the same gate through a second door."""
    # Arrange
    for section in Section:
        visit.resolutions[section] = Resolution(section, content={"noted": True})
    closed = Visit("v-1", "p-1", kind=VisitKind.ROUTINE, state=VisitState.COMPLETED,
                   junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE, started_at=KNOCK,
                   resolutions=visit.resolutions,
                   closed_by=JUNIOR_PHYSICIAN, closed_at=CLOSE)
    store.save(conn, closed)

    # Act
    answer = client.get("/visits/v-1")

    # Assert
    assert "Completed by Dr Layla Al-Amri at 10:05, 28 August." in answer.text
    assert "Routine Visit" in answer.text
    assert "This Visit finished the Visit Protocol" in answer.text


def test_a_cancelled_visit_shows_the_reason_who_set_it_and_that_nothing_was_sent(
        client, conn, visit):
    # Arrange
    visit.cancel(Reason("patient-not-at-home"), JUNIOR_PHYSICIAN, CLOSE)
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1")

    # Assert
    assert "Cancelled by Dr Layla Al-Amri at 10:05, 28 August." in answer.text
    assert "Reason: Patient not at home." in answer.text
    assert "writes nothing back to the EMR" in answer.text


def test_an_emergency_sends_every_visit_address_to_the_emergency_protocol(
        client, conn, visit):
    """§5.7: the Visit Protocol stops. §4.2: this is the whole of what that means for
    navigation. The Emergency screen itself is Web Pass 2, so only the redirect is
    asserted."""
    # Arrange
    visit.start(KNOCK, VisitKind.BASELINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    visit.enter_emergency(KNOCK)
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1", follow_redirects=False)

    # Assert
    assert answer.status_code == 303
    assert answer.headers["location"] == "/visits/v-1/emergency"


def test_an_address_naming_no_visit_is_refused_in_words(client):
    # Arrange / Act
    answer = client.get("/visits/v-nope")

    # Assert — §4.1: a screen never looks broken, and a stack trace is the loudest way to
    assert answer.status_code == 404
    assert "No Visit at that address" in answer.text


def test_each_of_the_eight_tiles_on_an_open_visit_leads_to_its_own_section_page(
        client, conn, visit):
    # Arrange
    visit.start(KNOCK, VisitKind.BASELINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1")

    # Assert
    assert 'href="/visits/v-1/sections/visit-reason"' in answer.text
    assert 'href="/visits/v-1/sections/care-plan"' in answer.text
    assert 'class="strip"' not in answer.text
