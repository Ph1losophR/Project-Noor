"""The words a Visit List row is made of, tested where they are chosen.

No client and no database: these are functions over what the store already answered, which
is the whole reason they exist as functions rather than as `{% if %}` in the template.
"""
from datetime import date, datetime

from noor.domain.brief import Due, LastVisit, Point, Trend
from noor.domain.examination import Composed, Composition, Element
from noor.domain.plans import (Axis, BetweenVisitPlan, Comparison,
                              MeasurementSchedule, Threshold)
from noor.domain.records import Reason, Resolution
from noor.domain.reconciliation import (Discrepancy, DiscrepancyKind, Medication,
                                        Product, Reconciliation)
from noor.domain.selfcare import SelfCareItem
from noor.domain.states import DataState, Datum, Section, VisitKind, VisitState
from noor.domain.visit import Visit
from noor.domain.vitals import HomeReading, Measurement, Source
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


def test_every_one_of_the_eight_has_an_address_that_is_its_own_name():
    # Arrange / Act
    slugs = [views.SLUG_OF[section] for section in Section]

    # Assert — web_plan §4.3's eight, in the record's order
    assert slugs == ["visit-reason", "concerns-and-interval-history",
                     "medication-reconciliation", "vitals", "physical-examination",
                     "self-care-check", "care-plan", "notes"]


def test_the_strip_carries_the_eight_in_the_records_order_with_this_page_marked():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.VITALS] = Resolution(Section.VITALS, content={"pulse": "72"})

    # Act
    steps = views.strip(record, Section.NOTES)

    # Assert
    assert len(steps) == 8
    assert steps[3] == views.Step("Vitals", "Resolved", "mark-clear",
                                  "/visits/v-1/sections/vitals", "strip-link", "false")
    assert steps[7] == views.Step("Notes", "Nothing recorded", "mark-open",
                                  "/visits/v-1/sections/notes",
                                  "strip-link strip-here", "page")


def test_a_section_nobody_has_touched_says_so_rather_than_showing_an_empty_region():
    # Arrange
    record = Visit("v-1", "p-1")

    # Act
    sentence = views.recorded_sentence(record, Section.VITALS)

    # Assert
    assert sentence == "Nothing recorded in this section yet."


def test_a_section_resolved_by_content_says_it_was_recorded_in_this_visit():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.NOTES] = Resolution(Section.NOTES, content="Family present.")

    # Act
    sentence = views.recorded_sentence(record, Section.NOTES)

    # Assert
    assert sentence == "Recorded in this Visit."


def test_a_section_resolved_by_a_reason_says_which_reason_rather_than_only_resolved():
    """§5.8 makes both a passing Visit, so the Visit page's tile says only *Resolved*.
    The distinction lives here, on the section's own page (web_plan §4.3)."""
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, reason=Reason("no-working-device"))

    # Act
    sentence = views.recorded_sentence(record, Section.VITALS)

    # Assert
    assert sentence == ("Resolved without content: "
                        "No working device in the household.")


def test_a_section_resolved_by_the_other_row_says_the_words_that_were_typed():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.NOTES] = Resolution(
        Section.NOTES, reason=Reason("other", "The Caregiver asked us to come back."))

    # Act
    sentence = views.recorded_sentence(record, Section.NOTES)

    # Assert
    assert sentence == ("Resolved without content: "
                        "The Caregiver asked us to come back.")


def test_every_section_can_be_resolved_without_content_including_the_two_with_no_rows_of_their_own():
    """`visit_reason` and `care_plan` are deliberately empty in `reason-lists.md`, so the
    five shared rows and the Other row are what they offer (§5.10, N6)."""
    # Arrange / Act
    counts = {section: len(views.SECTION_REASONS[section]) for section in Section}

    # Assert
    assert counts[Section.VISIT_REASON] == 6
    assert counts[Section.CARE_PLAN] == 6
    assert counts[Section.PHYSICAL_EXAMINATION] == 10
    assert min(counts.values()) == 6


def test_a_section_resolved_by_a_named_reason_keeps_words_typed_beside_it():
    """`reason_for` keeps words typed beside a named row, so the section's own page keeps
    them too — the same shape as the closing sentence, without its wrapper."""
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, reason=Reason("no-working-device", "the clinic lent one later"))

    # Act
    sentence = views.recorded_sentence(record, Section.VITALS)

    # Assert
    assert sentence == ("Resolved without content: No working device in the household. "
                        "In their own words: the clinic lent one later")


def test_a_free_text_section_with_something_in_it_hands_that_text_back_to_the_form():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.NOTES] = Resolution(Section.NOTES,
                                                   content="Daughter interpreted.")

    # Act
    held = views.held_text(record, Section.NOTES)

    # Assert
    assert held == "Daughter interpreted."


def test_a_free_text_section_resolved_without_content_hands_the_form_an_empty_box():
    """The box is empty because there is nothing to put in it, and the reason is already
    on the page in `recorded_sentence` — so nothing is lost and nothing is invented."""
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.VISIT_REASON] = Resolution(
        Section.VISIT_REASON, reason=Reason("patient-declined"))

    # Act
    held = views.held_text(record, Section.VISIT_REASON)

    # Assert
    assert held == ""


def test_a_free_text_section_nobody_has_touched_hands_the_form_an_empty_box():
    # Arrange
    record = Visit("v-1", "p-1")

    # Act
    held = views.held_text(record, Section.NOTES)

    # Assert
    assert held == ""


def test_the_interval_history_offers_every_event_a_rule_will_read_and_none_of_these():
    # Arrange / Act
    labels = [row["label"] for row in views.EVENT_ROWS]

    # Assert
    assert labels[0] == "Admitted to hospital"
    assert labels[-1] == "None of these"
    assert "A hypoglycaemic episode" in labels


def test_the_events_already_ticked_come_back_ticked_rather_than_blank():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.CONCERNS_AND_INTERVAL_HISTORY] = Resolution(
        Section.CONCERNS_AND_INTERVAL_HISTORY,
        content={"events": ["a-fall"], "concerns": []})

    # Act
    ticks = views.event_ticks(record)

    # Assert
    assert views.Tick("a-fall", "A fall", "checked") in ticks
    assert views.Tick("none-of-these", "None of these", "") in ticks


def test_an_interval_history_nobody_has_answered_offers_eight_unticked_rows():
    # Arrange
    record = Visit("v-1", "p-1")

    # Act
    ticks = views.event_ticks(record)

    # Assert
    assert len(ticks) == 8
    assert {tick.checked for tick in ticks} == {""}


def test_each_concern_comes_back_in_the_box_of_whoever_raised_it():
    """Attribution is the point of the two boxes: *his feet burn at night* said by the
    Caregiver and said by the Patient are different clinical facts (§4.2)."""
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.CONCERNS_AND_INTERVAL_HISTORY] = Resolution(
        Section.CONCERNS_AND_INTERVAL_HISTORY,
        content={"events": ["none-of-these"],
                 "concerns": [{"raised_by": "Patient", "words": "His feet burn at night."},
                              {"raised_by": "Caregiver", "words": "He sleeps in a chair."},
                              {"raised_by": "Patient", "words": "Dizzy standing up."}]})

    # Act
    held = views.concerns_held(record)

    # Assert
    assert held == {"Patient": "His feet burn at night.\nDizzy standing up.",
                    "Caregiver": "He sleeps in a chair."}


def test_a_section_resolved_without_content_leaves_both_concern_boxes_empty():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.CONCERNS_AND_INTERVAL_HISTORY] = Resolution(
        Section.CONCERNS_AND_INTERVAL_HISTORY, reason=Reason("cannot-communicate"))

    # Act
    held = views.concerns_held(record)

    # Assert
    assert held == {"Patient": "", "Caregiver": ""}


def test_each_measurement_asked_for_gets_a_field_carrying_its_unit():
    # Arrange
    record = Visit("v-1", "p-1")
    asked = (Measurement("bp-seated", "Blood pressure, seated", "mmHg", ("hypertension",)),
             Measurement("pulse", "Pulse", "beats per minute", ()))

    # Act
    fields = views.vitals_fields(record, asked)

    # Assert
    assert fields == (views.Field("bp-seated", "Blood pressure, seated", "mmHg", ""),
                      views.Field("pulse", "Pulse", "beats per minute", ""))


def test_a_reading_already_recorded_comes_back_in_its_own_field():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.VITALS] = Resolution(Section.VITALS,
                                                    content={"pulse": "72"})
    asked = (Measurement("pulse", "Pulse", "beats per minute", ()),)

    # Act
    fields = views.vitals_fields(record, asked)

    # Assert
    assert fields == (views.Field("pulse", "Pulse", "beats per minute", "72"),)


def test_a_composed_list_says_it_was_composed_and_carries_no_hairline_block():
    # Arrange
    composed = Composed(required=(), basis=Composition.COMPOSED)

    # Act
    sentence, css = views.composition_block(composed)

    # Assert
    assert sentence == ("This list was composed from the Patient's conditions and the "
                        "surveillance that is overdue.")
    assert css == "note"


def test_a_baseline_says_the_examination_is_complete_rather_than_composed():
    """§4.3's first difference: a Baseline has no surveillance history to compose from,
    so the whole examination is required and that is a fact, not a degradation."""
    # Arrange
    composed = Composed(required=(), basis=Composition.BASELINE)

    # Act
    sentence, css = views.composition_block(composed)

    # Assert
    assert sentence == ("This is a Baseline Visit, so the whole examination is required — "
                        "there is no surveillance history to compose from.")
    assert css == "note"


def test_surveillance_dates_that_could_not_be_read_name_the_input_and_the_consequence():
    """§7.2's Unreachable: not an empty region and not a badge, but a bounded block
    saying what could not be read and what follows from that."""
    # Arrange
    composed = Composed(required=(), basis=Composition.UNREACHABLE)

    # Act
    sentence, css = views.composition_block(composed)

    # Assert
    assert sentence == ("The surveillance dates could not be read. The whole examination "
                        "is required, and no element is marked overdue.")
    assert css == "unreachable"


def test_an_element_that_is_overdue_says_which_surveillance_made_it_required():
    # Arrange
    record = Visit("v-1", "p-1")
    required = (Element("monofilament", "Monofilament testing", ("diabetes",),
                        "foot-examination"),
                Element("general-appearance", "General appearance", ()))

    # Act
    rows = views.element_rows(record, required)

    # Assert
    assert rows == (
        views.Row("monofilament", "Monofilament testing",
                  "Required because foot-examination surveillance is overdue.", ""),
        views.Row("general-appearance", "General appearance",
                  "Required for every Patient.", ""))


def test_a_finding_already_recorded_comes_back_beside_its_element():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.PHYSICAL_EXAMINATION] = Resolution(
        Section.PHYSICAL_EXAMINATION,
        content={"elements": {"pedal-pulses": "Present, both feet."}, "added": ""})
    required = (Element("pedal-pulses", "Pedal pulses", ("diabetes",)),)

    # Act
    rows = views.element_rows(record, required)

    # Assert
    assert rows[0].held == "Present, both feet."


def test_each_self_care_item_offers_the_three_outcomes_of_watching_it():
    # Arrange
    record = Visit("v-1", "p-1")
    items = (SelfCareItem("meter-technique", "Using the glucose meter", "demonstrated",
                          ("diabetes",), "glucose-meter"),)

    # Act
    rows = views.self_care_rows(record, items)

    # Assert
    assert rows == (views.Watched(
        "meter-technique", "Using the glucose meter", "demonstrated",
        (views.Choice("correct", "Done correctly", ""),
         views.Choice("incorrect", "Done, and not correctly", ""),
         views.Choice("nothing-to-use", "Nothing in the house to do it with", ""))),)


def test_an_outcome_already_recorded_comes_back_chosen():
    # Arrange
    record = Visit("v-1", "p-1")
    record.resolutions[Section.SELF_CARE_CHECK] = Resolution(
        Section.SELF_CARE_CHECK, content={"foot-routine": "incorrect"})
    items = (SelfCareItem("foot-routine", "The daily foot routine", "observed",
                          ("diabetes",)),)

    # Act
    rows = views.self_care_rows(record, items)

    # Assert
    assert rows[0].choices[1] == views.Choice("incorrect", "Done, and not correctly",
                                              "checked")
    assert rows[0].choices[0].checked == ""


METFORMIN = Product("metformin-500", "Metformin", "500 mg", "tablet", "biguanide")
AMLODIPINE = Product("amlodipine-5", "Amlodipine", "5 mg", "tablet",
                     "calcium channel blocker")


def test_a_search_result_shows_the_strength_and_the_form_it_will_be_recorded_with():
    """§4.2: name, strength and form come from the list. Showing them at the moment of
    choosing is what stops the Nurse typing a strength that is not on the box."""
    # Arrange / Act
    found = views.search_results([METFORMIN, AMLODIPINE])

    # Assert
    assert found == (views.Found("metformin-500", "Metformin 500 mg tablet"),
                     views.Found("amlodipine-5", "Amlodipine 5 mg tablet"))


def test_a_matched_box_in_the_house_shows_what_was_typed_against_it():
    # Arrange
    house = [Medication("Metformin", METFORMIN, 42, date(2027, 3, 1))]

    # Act
    boxes = views.house_boxes(house)

    # Assert
    assert boxes == (views.Box(0, "Metformin 500 mg tablet", "biguanide",
                               "42 remaining", "expires 2027-03-01"),)


def test_a_box_the_drug_list_has_no_row_for_says_noor_cannot_reconcile_it():
    """§4.2's outcome, not workaround: the free text stands and Noor states the limit."""
    # Arrange
    house = [Medication("Cordarone 200 mg (brought from Cairo)")]

    # Act
    boxes = views.house_boxes(house)

    # Assert
    assert boxes == (views.Box(0, "Cordarone 200 mg (brought from Cairo)",
                               "Not on the drug list — Noor cannot reconcile this item",
                               "no count recorded", "no expiry recorded"),)


def test_a_discrepancy_is_one_sentence_naming_the_kind_and_its_subject():
    # Arrange
    found = [Discrepancy(DiscrepancyKind.OMISSION, "Gliclazide"),
             Discrepancy(DiscrepancyKind.EXPIRED, "Amlodipine")]

    # Act
    lines = views.discrepancy_lines(found)

    # Assert
    assert lines == ("Gliclazide — prescribed, not in the house",
                     "Amlodipine — in the house, past its expiry")


def test_a_comparison_that_ran_says_so_in_the_flow():
    # Arrange
    result = Reconciliation((), (), DataState.PRESENT)

    # Act
    sentence, css = views.comparison_block(result)

    # Assert
    assert sentence == ("The house was compared against the prescribed list Noor read "
                        "before the van left.")
    assert css == "note"


def test_a_prescribed_list_noor_could_not_read_names_what_that_costs():
    """§7.2 again, and §4.10's rule that a degraded comparison declares itself: the
    cupboard checks still ran, and the ones needing the list did not."""
    # Arrange
    result = Reconciliation((), (), DataState.UNREACHABLE)

    # Act
    sentence, css = views.comparison_block(result)

    # Assert
    assert sentence == ("The prescribed list could not be read. What is in the house is "
                        "recorded in full, and nothing is compared against the list — no "
                        "omission and no unprescribed item can be found here.")
    assert css == "unreachable"


def test_the_plan_offers_the_four_axes_a_household_can_measure_and_not_the_lab_one():
    """HbA1c is drawn in a laboratory. A home measurement schedule with HbA1c on it is a
    line nobody in the house can carry out, and §4.8 says every line is testable."""
    # Assert
    assert views.HOME_AXES == (Axis.SYSTOLIC, Axis.DIASTOLIC,
                               Axis.GLUCOSE_PRE_PRANDIAL, Axis.GLUCOSE_POST_PRANDIAL)
    assert Axis.HBA1C not in views.HOME_AXES


def test_each_axis_gets_a_row_for_its_schedule_and_its_two_stop_thresholds():
    # Arrange
    record = Visit("v-1", "p-1")

    # Act
    rows = views.plan_rows(record)

    # Assert
    assert rows[0] == views.PlanRow(Axis.SYSTOLIC, "Systolic blood pressure",
                                     "", "", "")
    assert len(rows) == 4


def test_a_plan_already_emitted_comes_back_line_by_line():
    # Arrange
    record = Visit("v-1", "p-1")
    record.plan = BetweenVisitPlan(
        schedule=(MeasurementSchedule(Axis.SYSTOLIC, 3),),
        stop_rules=(Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 180.0,
                              "call the Supervisor"),))

    # Act
    rows = views.plan_rows(record)

    # Assert
    assert rows[0] == views.PlanRow(Axis.SYSTOLIC, "Systolic blood pressure",
                                     "3", "", "180.0")


def test_the_withheld_titration_says_what_is_missing_and_what_follows_from_it():
    """§4.11: a withheld thing declares itself, names the input, and never looks like a
    thing that was considered and rejected."""
    # Assert
    assert views.TITRATION_WITHHELD == (
        "No titration step can be set on this Visit. Titration needs a ratified Goal of "
        "Care, and this Patient has none — the home measurement schedule and the stop "
        "rules do not, and both are set below.")


def test_the_care_plan_names_every_section_it_is_still_waiting_on():
    # Arrange / Act
    sentence = views.too_early_sentence([Section.VITALS, Section.NOTES])

    # Assert
    assert sentence == ("The Care Plan is assembled after the other seven. Still "
                        "unresolved: Vitals, Notes.")


GLUCOSE = Measurement("capillary-glucose", "Capillary blood glucose", "mmol/L",
                      ("diabetes",))
SEATED = Measurement("bp-seated", "Blood pressure, seated", "mmHg", ())


def test_the_two_sources_are_offered_in_the_words_section_4_8_uses():
    """§4.8 names both, and web_plan §4.4 requires every reading to record which. The
    words are the enum's own, so the page and the record cannot disagree."""
    # Assert
    assert views.SOURCE_ROWS == (("device memory", "Read off the device's own memory"),
                                 ("Caregiver paper log", "Copied from a Caregiver's "
                                                         "paper log"))


def test_a_reading_reads_back_with_its_unit_its_time_and_where_it_came_from():
    # Arrange
    readings = [HomeReading("capillary-glucose", "7.2",
                            datetime(2026, 8, 26, 7, 30), Source.DEVICE_MEMORY)]

    # Act
    lines = views.reading_lines(readings, [GLUCOSE, SEATED])

    # Assert
    assert lines == (views.Reading("Capillary blood glucose", "7.2 mmol/L",
                                   "07:30, 26 August", "device memory"),)


def test_a_series_reads_back_grouped_by_measurement_and_in_time_order():
    """A series is only readable as a series. Sorted here rather than in the template,
    because a template that sorts is a template that decides."""
    # Arrange
    readings = [HomeReading("bp-seated", "138/84",
                            datetime(2026, 8, 27, 8, 0), Source.PAPER_LOG),
                HomeReading("capillary-glucose", "9.1",
                            datetime(2026, 8, 27, 7, 15), Source.DEVICE_MEMORY),
                HomeReading("capillary-glucose", "7.2",
                            datetime(2026, 8, 26, 7, 30), Source.DEVICE_MEMORY)]

    # Act
    lines = views.reading_lines(readings, [GLUCOSE, SEATED])

    # Assert
    assert [line.value for line in lines] == ["138/84 mmHg", "7.2 mmol/L", "9.1 mmol/L"]


def test_a_reading_against_a_measurement_this_patient_is_not_asked_for_still_reads_back():
    """A condition removed from the Patient must not blank a reading already collected. The
    id stands in for the label, so the row says what it is rather than vanishing."""
    # Arrange
    readings = [HomeReading("weight", "81", datetime(2026, 8, 26, 7, 0),
                            Source.PAPER_LOG)]

    # Act
    lines = views.reading_lines(readings, [GLUCOSE])

    # Assert
    assert lines == (views.Reading("weight", "81", "07:00, 26 August",
                                   "Caregiver paper log"),)


def test_the_measurements_offered_are_the_ones_this_patient_is_asked_for():
    # Arrange / Act
    options = views.reading_options([GLUCOSE, SEATED])

    # Assert
    assert options == (views.Found("capillary-glucose",
                                   "Capillary blood glucose (mmol/L)"),
                       views.Found("bp-seated", "Blood pressure, seated (mmHg)"))


def test_no_readings_yet_is_a_finding_and_says_which_of_the_two_absences_it_is():
    # Arrange / Act
    sentence = views.home_readings_sentence([])

    # Assert
    assert sentence == ("No Home Readings have been collected on this Visit. That is not "
                        "a series Noor could not read — nothing has been entered yet.")


def test_a_collected_series_is_reported_as_a_count():
    # Arrange
    readings = [HomeReading("bp-seated", "138/84",
                            datetime(2026, 8, 27, 8, 0), Source.PAPER_LOG)]

    # Act / Assert
    assert views.home_readings_sentence(readings) == (
        "Home Readings collected on this Visit: 1.")
