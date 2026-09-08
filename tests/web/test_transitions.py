"""The two acts a Scheduled Visit has (web_plan §4.2), and what each one writes down."""
from datetime import date, datetime

from noor import store
from noor.domain.plans import Axis, BetweenVisitPlan, MeasurementSchedule
from noor.domain.states import VisitKind, VisitState
from noor.domain.visit import Visit

NOON = datetime(2026, 8, 28, 12, 0)
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"
LAST_MONTH = date(2026, 7, 30)


def scheduled(conn, day, visit_id="v-1"):
    """One Patient with one Scheduled Visit, as the Visit page's fixture arranges it."""
    if "p-1" not in store.enrolled(conn):
        store.add_patient(conn, "p-1", "Fatima Al-Harbi", ["hypertension"],
                          junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    record = Visit(visit_id, "p-1")
    store.schedule(conn, record, day, "Three-month review")
    return record


def test_starting_a_visit_settles_its_kind_and_stamps_who_attended(client, conn, day):
    # Arrange
    scheduled(conn, day)

    # Act
    answer = client.post("/visits/v-1/start")

    # Assert — §5.5 settles the kind, §5.13 stamps the pair, and the page now says both
    assert answer.status_code == 200
    assert "In Progress" in answer.text
    assert "Baseline Visit" in answer.text
    assert "Attended by Dr Layla Al-Amri, with Nurse Huda Al-Zahrani." in answer.text


def test_the_start_records_which_between_visit_plan_was_standing(client, conn, day):
    """N6: for a Routine Visit this must be Present or Unreachable, never left at the
    default — a Visit whose Home Readings have nothing to be scored against, silently."""
    # Arrange
    store.add_patient(conn, "p-1", "Fatima Al-Harbi", ["hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    plan = BetweenVisitPlan(schedule=(MeasurementSchedule(Axis.SYSTOLIC, 3),))
    earlier = Visit("v-0", "p-1", kind=VisitKind.BASELINE, state=VisitState.SCHEDULED)
    store.schedule(conn, earlier, LAST_MONTH, "Enrolment")
    earlier.state = VisitState.COMPLETED
    earlier.plan = plan
    earlier.closed_by = JUNIOR_PHYSICIAN
    earlier.closed_at = datetime(2026, 7, 30, 11, 0)
    store.save(conn, earlier)
    store.schedule(conn, Visit("v-1", "p-1"), day, "Three-month review")

    # Act
    client.post("/visits/v-1/start")

    # Assert
    stored = store.load(conn, "v-1")
    assert stored.kind is VisitKind.ROUTINE
    assert stored.previous_plan.is_present
    assert stored.previous_plan.value == plan


def test_starting_a_visit_that_has_already_started_is_refused_in_words(
        client, conn, day):
    # Arrange — a page left open while somebody else pressed Start
    record = scheduled(conn, day)
    record.start(NOON, VisitKind.BASELINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.save(conn, record)

    # Act
    answer = client.post("/visits/v-1/start")

    # Assert — §4.1: a screen never looks broken
    assert answer.status_code == 409
    assert "This Visit has moved on" in answer.text


def test_cancelling_a_scheduled_visit_records_the_reason_and_who_set_it(
        client, conn, day):
    # Arrange
    scheduled(conn, day)

    # Act
    answer = client.post("/visits/v-1/cancel",
                         data={"reason": "patient-in-hospital", "words": "",
                               "by": NURSE})

    # Assert — §5.4
    assert answer.status_code == 200
    assert "Cancelled by Nurse Huda Al-Zahrani at 09:30, 28 August." in answer.text
    assert "Reason: Patient in hospital." in answer.text
    assert "writes nothing back to the EMR" in answer.text


def test_the_other_row_keeps_the_words_that_were_typed_with_it(client, conn, day):
    # Arrange
    scheduled(conn, day)

    # Act
    answer = client.post("/visits/v-1/cancel",
                         data={"reason": "other", "words": "  the road was flooded  ",
                               "by": JUNIOR_PHYSICIAN})

    # Assert — trimmed, and kept
    assert answer.status_code == 200
    assert "Reason, in their own words: the road was flooded" in answer.text


def test_words_typed_beside_a_named_row_are_kept_too(client, conn, day):
    # Arrange
    scheduled(conn, day)

    # Act
    answer = client.post("/visits/v-1/cancel",
                         data={"reason": "scheduling-error",
                               "words": "double-booked with the clinic",
                               "by": JUNIOR_PHYSICIAN})

    # Assert — §5.10 never asks for them to be thrown away
    assert "In their own words: double-booked with the clinic" in answer.text


def test_a_reason_that_is_not_on_the_list_is_refused_in_words(client, conn, day):
    # Arrange
    scheduled(conn, day)

    # Act — what a submit with nothing chosen posts: no reason at all
    answer = client.post("/visits/v-1/cancel", data={"words": "", "by": NURSE})

    # Assert
    assert answer.status_code == 400
    assert "That is not a reason on this list." in answer.text
    assert store.load(conn, "v-1").state is VisitState.SCHEDULED


def test_the_other_row_without_its_words_is_refused_in_words(client, conn, day):
    # Arrange
    scheduled(conn, day)

    # Act
    answer = client.post("/visits/v-1/cancel",
                         data={"reason": "other", "words": "   ", "by": NURSE})

    # Assert — §5.10's one required field, refused before the state moves
    assert answer.status_code == 400
    assert "Other is the row that needs its own words." in answer.text
    assert store.load(conn, "v-1").state is VisitState.SCHEDULED


def test_cancelling_without_a_name_is_refused_in_words(client, conn, day):
    # Arrange
    scheduled(conn, day)

    # Act
    answer = client.post("/visits/v-1/cancel",
                         data={"reason": "patient-in-hospital",
                               "words": "family asked at the door"})

    # Assert
    assert answer.status_code == 400
    assert "No name on this Cancel" in answer.text
    assert store.load(conn, "v-1").state is VisitState.SCHEDULED


def test_the_scheduled_page_offers_both_acts_and_puts_cancelled_behind_a_guard(
        client, conn, day):
    # Arrange
    scheduled(conn, day)

    # Act
    answer = client.get("/visits/v-1")

    # Assert — design system §7.4: manual, so a stray glove cannot dismiss it
    assert 'action="/visits/v-1/start"' in answer.text
    assert 'action="/visits/v-1/cancel"' in answer.text
    assert 'popover="manual"' in answer.text
    assert "Patient in hospital" in answer.text
    assert "Other — write what happened" in answer.text
    assert "Record this Visit as Cancelled" in answer.text
    assert "Keep this Visit on the day" in answer.text
    assert '<textarea id="words" name="words" rows="3" dir="auto"></textarea>' in answer.text


def test_an_emergency_suspends_the_acts_and_not_only_the_pages(client, conn, day):
    """§4.2: *every* address under /visits/{id}. A POST is an address."""
    # Arrange
    record = scheduled(conn, day)
    record.start(NOON, VisitKind.BASELINE, junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    record.enter_emergency(NOON)
    store.save(conn, record)

    # Act
    answer = client.post("/visits/v-1/start", follow_redirects=False)

    # Assert
    assert answer.status_code == 303
    assert answer.headers["location"] == "/visits/v-1/emergency"
