"""The words a Visit List row is made of, tested where they are chosen.

No client and no database: these are functions over what the store already answered, which
is the whole reason they exist as functions rather than as `{% if %}` in the template.
"""
from datetime import date, datetime

from noor.domain.brief import Due, LastVisit, Point, Trend
from noor.domain.plans import Axis, BetweenVisitPlan, MeasurementSchedule
from noor.domain.records import Reason, Resolution
from noor.domain.states import Datum, Section, VisitKind, VisitState
from noor.domain.visit import Visit
from noor.prefetch import Readiness
from noor.store import Pending, RosterEntry
from noor.web import views

SEVEN = datetime(2026, 8, 28, 7, 0)
KNOCK = datetime(2026, 8, 28, 9, 20)
CLOSE = datetime(2026, 8, 28, 10, 5)
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"


def entry(state: VisitState) -> RosterEntry:
    """One roster line in whatever state the test is about."""
    return RosterEntry("v-001", "p-001", "Fatima Al-Harbi", "Three-month review", state)


def test_a_scheduled_row_shows_the_planning_indicator_for_a_first_visit():
    # Arrange
    row = entry(VisitState.SCHEDULED)

    # Act
    shown = views.line(row, visit=Visit("v-001", "p-001"),
                       planned=VisitKind.BASELINE, prepared=Readiness(SEVEN, ()))

    # Assert
    assert shown.kind == "Baseline Visit"


def test_a_scheduled_row_shows_routine_once_a_baseline_has_completed():
    # Arrange
    row = entry(VisitState.SCHEDULED)

    # Act
    shown = views.line(row, visit=Visit("v-001", "p-001"),
                       planned=VisitKind.ROUTINE, prepared=Readiness(SEVEN, ()))

    # Assert
    assert shown.kind == "Routine Visit"


def test_a_started_row_shows_the_kind_the_start_settled_and_not_the_indicator():
    """ADR 0008: the Start recomputes and stores the kind, and the record stands even if
    the history has moved on since. The two arguments disagree here on purpose."""
    # Arrange
    row = entry(VisitState.IN_PROGRESS)
    started = Visit("v-001", "p-001", kind=VisitKind.BASELINE,
                    state=VisitState.IN_PROGRESS)

    # Act
    shown = views.line(row, visit=started, planned=VisitKind.ROUTINE,
                       prepared=Readiness(SEVEN, ()))

    # Assert
    assert shown.kind == "Baseline Visit"


def test_a_cancelled_row_states_that_no_visit_type_was_ever_settled():
    # Arrange
    row = entry(VisitState.CANCELLED)
    never = Visit("v-001", "p-001", state=VisitState.CANCELLED)

    # Act
    shown = views.line(row, visit=never, planned=VisitKind.BASELINE,
                       prepared=Readiness(SEVEN, ()))

    # Assert — §7.2: not an empty cell, not an em dash, not "N/A"
    assert shown.kind == "Never started, so no Visit type was settled."


def test_a_row_carries_the_patient_the_reason_and_the_state_as_words():
    # Arrange
    row = entry(VisitState.ENDED_EARLY)
    ended = Visit("v-001", "p-001", kind=VisitKind.ROUTINE,
                  state=VisitState.ENDED_EARLY)

    # Act
    shown = views.line(row, visit=ended, planned=VisitKind.ROUTINE,
                       prepared=Readiness(SEVEN, ()))

    # Assert
    assert shown.visit_id == "v-001"
    assert shown.patient_name == "Fatima Al-Harbi"
    assert shown.reason == "Three-month review"
    assert shown.state == "Ended Early"


def test_every_visit_state_has_a_word():
    # Arrange / Act / Assert — a seventh state would be a blank in a row otherwise
    assert set(views.STATE_WORDS) == set(VisitState)


def test_a_prepared_visit_states_when_the_office_read_and_that_it_all_came_back():
    # Arrange
    prepared = Readiness(SEVEN, ())

    # Act
    sentence = views.readiness_sentence(prepared)

    # Assert
    assert sentence == "Prepared 07:00, 28 August. Every read came back."


def test_a_failed_read_is_named_by_the_read_and_not_by_the_items_behind_it():
    # Arrange — `readiness` collapses seven failed surveillance items into one name
    prepared = Readiness(SEVEN, ("surveillance",))

    # Act
    sentence = views.readiness_sentence(prepared)

    # Assert
    assert sentence == ("Prepared 07:00, 28 August. "
                        "Could not be read: the surveillance dates.")


def test_two_failed_reads_are_named_in_the_one_sentence():
    # Arrange
    prepared = Readiness(SEVEN, ("allergies", "prescribed"))

    # Act
    sentence = views.readiness_sentence(prepared)

    # Assert
    assert sentence == ("Prepared 07:00, 28 August. "
                        "Could not be read: the allergy list, the prescribed list.")


def test_an_unprepared_visit_says_so_and_says_it_does_not_hold_the_visit_up():
    """§5.2 and N4: an unprepared Visit still starts. A readiness line that read like a
    refusal would be software preventing care."""
    # Arrange
    prepared = Readiness(None, ())

    # Act
    sentence = views.readiness_sentence(prepared)

    # Assert
    assert sentence.startswith("The office prepared nothing for this Visit.")
    assert "starts" in sentence
    assert "Unreachable" in sentence


def test_an_empty_roster_is_a_finding_rather_than_a_gap_where_rows_would_be():
    # Arrange / Act
    sentence = views.summary([])

    # Assert
    assert sentence.startswith("The office scheduled no Visits for this day.")
    assert "could not read" in sentence


def test_a_roster_with_visits_on_it_states_how_many():
    # Arrange
    rows = [entry(VisitState.SCHEDULED), entry(VisitState.COMPLETED)]

    # Act
    sentence = views.summary(rows)

    # Assert
    assert sentence == "Visits on this day's roster: 2."


def test_the_day_is_written_out_in_full_so_the_wrong_day_is_obvious():
    # Arrange / Act
    written = views.day_words(date(2026, 8, 28))

    # Assert
    assert written == "Friday 28 August 2026"


def closed(state: VisitState, reason: Reason | None) -> Visit:
    """One Visit that closed, in whichever terminal state the test is about."""
    return Visit("v-001", "p-001", kind=VisitKind.ROUTINE, state=state,
                 junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE, started_at=KNOCK,
                 closed_by=JUNIOR_PHYSICIAN, closed_at=CLOSE, closing_reason=reason)


def test_a_started_visit_reports_the_kind_it_settled_on():
    # Arrange
    started = Visit("v-001", "p-001", kind=VisitKind.BASELINE,
                    state=VisitState.IN_PROGRESS)

    # Act / Assert
    assert views.settled_kind(started) == "Baseline Visit"


def test_a_visit_that_never_started_settled_no_kind_and_says_so():
    # Arrange
    never = Visit("v-001", "p-001", state=VisitState.CANCELLED)

    # Act / Assert
    assert views.settled_kind(never) == "Never started, so no Visit type was settled."


def test_every_section_has_a_word():
    # Arrange / Act / Assert — a ninth section would be a blank tile otherwise
    assert set(views.SECTION_WORDS) == set(Section)


def test_the_eight_sections_come_back_in_the_records_order():
    # Arrange
    subject = Visit("v-001", "p-001")

    # Act
    tiles = views.marks(subject)

    # Assert — §4.2: the integer is the position
    assert [tile.name for tile in tiles] == [
        "Visit Reason", "Concerns & Interval History", "Medication Reconciliation",
        "Vitals", "Physical Examination", "Self-Care Check", "Care Plan", "Notes"]


def test_a_resolved_section_is_marked_with_a_word_beside_its_colour():
    """§4.3: a status colour never appears without its word, so the two travel together."""
    # Arrange
    subject = Visit("v-001", "p-001")
    subject.resolutions[Section.VITALS] = Resolution(Section.VITALS,
                                                     content={"systolic": 138})

    # Act
    tiles = {tile.name: tile for tile in views.marks(subject)}

    # Assert
    assert tiles["Vitals"].word == "Resolved"
    assert tiles["Vitals"].mark == "mark-clear"
    assert tiles["Notes"].word == "Nothing recorded"
    assert tiles["Notes"].mark == "mark-open"


def test_who_attended_travels_with_the_visit():
    # Arrange
    started = Visit("v-001", "p-001", kind=VisitKind.ROUTINE,
                    state=VisitState.IN_PROGRESS,
                    junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)

    # Act / Assert — §5.13
    assert views.attendance(started) == (
        "Attended by Dr Layla Al-Amri, with Nurse Huda Al-Zahrani.")


def test_a_closed_visit_states_its_state_who_closed_it_and_when():
    # Arrange
    subject = closed(VisitState.COMPLETED, None)

    # Act / Assert
    assert views.closed_sentence(subject) == (
        "Completed by Dr Layla Al-Amri at 10:05, 28 August.")


def test_a_visit_that_finished_the_protocol_carries_no_closing_reason():
    # Arrange
    subject = closed(VisitState.COMPLETED, None)

    # Act
    sentence = views.reason_sentence(subject)

    # Assert — §7.2: a written finding, not a blank where a reason would be
    assert sentence == ("This Visit finished the Visit Protocol, so it carries no "
                        "closing reason.")


def test_a_closing_reason_is_shown_as_the_words_the_list_used():
    # Arrange
    subject = closed(VisitState.CANCELLED, Reason("patient-not-at-home"))

    # Act / Assert — the row id is never what a clinician reads
    assert views.reason_sentence(subject) == "Reason: Patient not at home."


def test_words_typed_beside_a_named_reason_are_kept():
    # Arrange
    subject = closed(VisitState.ENDED_EARLY,
                     Reason("time-exhausted", "the next house was across the city"))

    # Act / Assert — §5.10 asks for them on Other and never asks for them thrown away
    assert views.reason_sentence(subject) == (
        "Reason: Time exhausted. In their own words: the next house was across the city")


def test_the_other_row_is_shown_as_the_words_and_not_as_its_instruction():
    # Arrange
    subject = closed(VisitState.CANCELLED, Reason("other", "the road was flooded"))

    # Act / Assert
    assert views.reason_sentence(subject) == (
        "Reason, in their own words: the road was flooded")


def test_the_write_back_queue_is_a_count_and_a_word():
    # Arrange
    queued = {"v-001": Pending("v-001", "Fatima Al-Harbi", None, None),
              "v-002": Pending("v-002", "Noura Al-Otaibi", None, None)}

    # Act / Assert — §7.3, and never a glyph with a number on it
    assert views.queue_count(queued) == "Write-Backs pending: 2."


def test_a_cancelled_visit_says_it_wrote_nothing_back_at_all():
    # Arrange
    subject = closed(VisitState.CANCELLED, Reason("patient-not-at-home"))

    # Act
    sentence = views.writeback_sentence(subject, None)

    # Assert — §5.4
    assert sentence == ("A Visit that never started writes nothing back to the EMR, so "
                        "there is nothing queued for this one.")


def test_a_visit_the_emr_accepted_says_so():
    # Arrange
    subject = closed(VisitState.COMPLETED, None)

    # Act / Assert — off the queue and terminal means accepted
    assert views.writeback_sentence(subject, None) == (
        "The EMR accepted this Visit's Write-Back.")


def test_a_queued_visit_nobody_has_tried_yet_says_that_nothing_retries_by_itself():
    # Arrange
    subject = closed(VisitState.COMPLETED, None)
    row = Pending("v-001", "Fatima Al-Harbi", None, None)

    # Act / Assert — §6.1: no background loop, no timer, no polling
    assert views.writeback_sentence(subject, row) == (
        "This Visit's Write-Back is queued. Noor has not attempted it yet, and nothing "
        "retries by itself.")


def test_a_refused_write_back_repeats_what_the_emr_said():
    # Arrange
    subject = closed(VisitState.COMPLETED, None)
    row = Pending("v-001", "Fatima Al-Harbi", CLOSE, "patient record locked by another user")

    # Act
    sentence = views.writeback_sentence(subject, row)

    # Assert — §4.10 forbids the silent failure; the EMR's own words are the loud one
    assert sentence == ("The EMR refused this Visit's Write-Back at 10:05, 28 August "
                        "and said: patient record locked by another user")


PLAN = BetweenVisitPlan(schedule=(MeasurementSchedule(Axis.SYSTOLIC, 3),))


def test_a_measurement_reads_as_its_label_its_unit_and_its_series():
    # Arrange
    trend = Trend("bp-seated", "Blood pressure, seated", "mmHg",
                  (Point(date(2026, 5, 12), "148/92"), Point(date(2026, 7, 30), "138/84")))

    # Act
    tiles = views.trend_tiles((trend,))

    # Assert — oldest first, which is the direction it is read in
    assert tiles[0].name == "Blood pressure, seated (mmHg)"
    assert tiles[0].detail == "12 May 2026: 148/92 · 30 July 2026: 138/84"


def test_a_patient_with_a_series_is_told_how_many():
    # Arrange
    trend = Trend("pulse", "Pulse", "bpm", (Point(date(2026, 7, 30), "72"),))

    # Act / Assert
    assert views.trend_summary((trend,)) == "Vitals series Noor holds for this Patient: 1."


def test_a_patient_with_no_series_gets_a_written_finding_and_not_a_gap():
    # Arrange / Act
    sentence = views.trend_summary(())

    # Assert — §7.2: never an empty cell, an em dash or 'N/A'
    assert sentence == ("No previous Visit recorded any Vitals for this Patient, so there "
                        "is no series to read yet.")


def test_an_overdue_item_with_a_date_says_when_it_was_last_done():
    # Arrange
    due = Due("potassium", "Serum potassium",
              Datum.present(date(2025, 2, 10), as_of=SEVEN))

    # Act
    tiles = views.due_tiles((due,))

    # Assert
    assert tiles[0].name == "Serum potassium"
    assert tiles[0].detail == "Last done 10 February 2025."


def test_an_overdue_item_nobody_ever_recorded_says_that_in_the_value_s_place():
    # Arrange
    due = Due("retinal-screening", "Retinal screening", Datum.absent())

    # Act / Assert — §7.2's Absent shape: a clinical fact, not an emptiness
    assert views.due_tiles((due,))[0].detail == "The record holds none."


def test_a_patient_with_nothing_overdue_is_told_so_in_words():
    # Arrange / Act / Assert
    assert views.due_summary(()) == (
        "Every surveillance item this Patient's conditions call for is current.")


def test_a_patient_with_no_earlier_visit_is_told_this_is_the_first():
    # Arrange / Act / Assert
    assert views.last_visit_sentence(None) == (
        "This is the first Visit Noor holds for this Patient.")


def test_the_last_visit_reads_as_what_it_concluded_and_when():
    # Arrange
    last = LastVisit(date(2026, 7, 30), VisitState.ENDED_EARLY, Reason("time-exhausted"))

    # Act / Assert — §5.3: what the last Visit concluded
    assert views.last_visit_sentence(last) == (
        "The last Visit was Ended Early on 30 July 2026. Reason: Time exhausted.")


def test_a_standing_plan_is_declared_with_the_date_it_has_stood_since():
    # Arrange
    standing = Datum.present(PLAN, as_of=datetime(2026, 7, 30, 11, 0))

    # Act / Assert
    assert views.plan_sentence(standing) == (
        "A Between-Visit Plan has been standing since 30 July 2026. Its titration steps, "
        "schedule and stop rules are on the Care Plan section.")


def test_a_patient_who_has_never_had_a_plan_is_a_different_fact_from_one_unread():
    # Arrange / Act
    absent = views.plan_sentence(Datum.absent())
    unreachable = views.plan_sentence(Datum.unreachable())

    # Assert — N6: 'none' and 'unreadable' are not the same fact
    assert absent == ("No Visit has emitted a Between-Visit Plan for this Patient yet, so "
                      "there is none standing.")
    assert unreachable == ("The Between-Visit Plan in force could not be read. Noor cannot "
                           "say whether one is standing.")
    assert absent != unreachable


def test_blind_spots_are_counted_when_there_are_any():
    # Arrange / Act / Assert
    assert views.spot_summary(("HbA1c: the date could not be read from the record",)) == (
        "Reads Noor could not make: 1.")


def test_a_brief_that_saw_everything_says_that_rather_than_showing_nothing():
    # Arrange / Act / Assert — N6 cuts both ways: silence is not an answer either
    assert views.spot_summary(()) == (
        "Noor read everything it asked the EMR for, so nothing on this page is missing "
        "because of a failed read.")
