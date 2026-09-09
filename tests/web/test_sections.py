"""One page per Visit Protocol section, and the strip that moves between them
(web_plan §4.3)."""
from datetime import datetime

import pytest

from noor import store
from noor.domain.plans import (Axis, BetweenVisitPlan, Comparison, MeasurementSchedule,
                              Threshold)
from noor.domain.records import Reason, Resolution
from noor.domain.states import Section, VisitKind
from noor.domain.visit import Visit
from noor.web import views

KNOCK = datetime(2026, 8, 28, 9, 20)
CLOSE = datetime(2026, 8, 28, 10, 5)
JUNIOR_PHYSICIAN = "Dr Layla Al-Amri"
NURSE = "Nurse Huda Al-Zahrani"


@pytest.fixture
def scheduled(conn, day):
    """One Patient with both conditions, and one Scheduled Visit. Both conditions so a
    section's form shows every row its content file can offer."""
    store.add_patient(conn, "p-1", "Fatima Al-Harbi", ["diabetes", "hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    record = Visit("v-1", "p-1")
    store.schedule(conn, record, day, "Three-month review")
    return record


@pytest.fixture
def visit(conn, scheduled):
    """The same Visit, In Progress — the only state the Visit Protocol is worked
    through in, so it is the state every section page needs."""
    scheduled.start(KNOCK, VisitKind.ROUTINE,
                    junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.save(conn, scheduled)
    return scheduled


@pytest.fixture
def seven(conn, visit):
    """A Visit with the seven sections before the Care Plan resolved, so the Care Plan
    will open. Resolved by a reason rather than by content, because §5.8 counts both and a
    reason is one line where seven forms' worth of content is not."""
    for section in Section:
        if section is not Section.CARE_PLAN:
            visit.resolutions[section] = Resolution(
                section, reason=Reason(views.SECTION_REASONS[Section.VITALS][0]["id"]))
    store.save(conn, visit)
    return visit


def test_every_one_of_the_eight_sections_has_a_page_of_its_own(client, visit):
    # Arrange
    slugs = ["visit-reason", "concerns-and-interval-history",
             "medication-reconciliation", "vitals", "physical-examination",
             "self-care-check", "care-plan", "notes"]

    # Act
    codes = {slug: client.get(f"/visits/v-1/sections/{slug}").status_code
             for slug in slugs}

    # Assert — the Care Plan assembles after the other seven, so its page is the
    # 409 naming them until they resolve (§4.2); the other seven open at once
    assert codes == dict.fromkeys(slugs, 200) | {"care-plan": 409}


def test_a_section_page_carries_the_strip_of_eight_and_marks_the_one_you_are_on(
        client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/vitals")

    # Assert
    assert 'class="strip"' in answer.text
    assert 'href="/visits/v-1/sections/notes"' in answer.text
    assert 'class="strip-link strip-here" aria-current="page"' in answer.text
    assert "Medication Reconciliation" in answer.text


def test_a_section_page_leads_one_link_up_to_the_visit_and_not_to_the_day(
        client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/notes")

    # Assert — web_plan §7's one link up
    assert 'href="/visits/v-1"' in answer.text


def test_a_section_page_says_whether_it_was_resolved_by_content_or_by_a_reason(
        client, conn, visit):
    # Arrange
    visit.resolutions[Section.VITALS] = Resolution(
        Section.VITALS, reason=Reason("no-appropriate-cuff"))
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1/sections/vitals")

    # Assert
    assert ("Resolved without content: No cuff of an appropriate size."
            in answer.text)


def test_an_address_that_is_not_one_of_the_eight_sections_is_answered_in_words(
        client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/blood-pressure")

    # Assert — §4.1: a screen never looks broken, and a stack trace is the loudest way to
    assert answer.status_code == 404
    assert "No such page" in answer.text


def test_a_section_page_refuses_while_the_visit_is_still_scheduled(client, scheduled):
    """CONTEXT.md makes In Progress the only state the Visit Protocol is worked through
    in, so the form has nothing to attach to yet."""
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/vitals")

    # Assert
    assert answer.status_code == 400
    assert "This Visit is not open" in answer.text
    assert "It is Scheduled." in answer.text


def test_a_section_page_refuses_once_the_visit_has_closed(client, conn, visit):
    """§5.9: a closed Visit is immutable, and the Addendum is Web Pass 3's screen."""
    # Arrange
    visit.end_early(Reason("time-exhausted"), JUNIOR_PHYSICIAN, CLOSE)
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1/sections/notes")

    # Assert
    assert answer.status_code == 400
    assert "It is Ended Early." in answer.text


def test_an_emergency_sends_a_section_address_to_the_emergency_protocol(
        client, conn, visit):
    """§5.7: while a Visit is in Emergency the Visit Protocol stops, and §4.2 makes that
    true of every address under /visits/{id} — this one included."""
    # Arrange
    visit.enter_emergency(KNOCK)
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1/sections/vitals", follow_redirects=False)

    # Assert
    assert answer.status_code == 303
    assert answer.headers["location"] == "/visits/v-1/emergency"


def test_a_section_offers_the_reasons_for_having_no_content_in_it(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/physical-examination")

    # Assert — the five shared rows, this section's four, and §5.10's Other row
    assert "Nothing to record here" in answer.text
    assert "No time remaining in the Visit" in answer.text
    assert "Declined to remove footwear" in answer.text
    assert "Other — write what happened" in answer.text


def test_a_section_resolved_with_a_reason_is_resolved_and_returns_to_the_visit(
        client, conn, visit):
    """§5.8's bar is resolved, not filled: a section carrying only a structured reason is
    a passing Visit."""
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/vitals",
                         data={"reason": "no-working-device", "words": ""},
                         follow_redirects=False)

    # Assert
    assert answer.status_code == 303
    assert answer.headers["location"] == "/visits/v-1"
    stored = store.load(conn, "v-1").resolutions[Section.VITALS]
    assert stored == Resolution(Section.VITALS, reason=Reason("no-working-device"))


def test_the_other_row_records_the_words_that_were_typed_beside_it(client, conn, visit):
    # Arrange / Act
    client.post("/visits/v-1/sections/notes",
                data={"reason": "other", "words": "Referred to the clinic instead."},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.NOTES]
    assert stored == Resolution(
        Section.NOTES, reason=Reason("other", "Referred to the clinic instead."))


def test_the_other_row_without_its_words_is_refused_rather_than_stored(
        client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/notes",
                         data={"reason": "other", "words": ""})

    # Assert
    assert answer.status_code == 400
    assert "That reason cannot be recorded" in answer.text
    assert Section.NOTES not in store.load(conn, "v-1").resolutions


def test_a_reason_from_another_sections_list_is_refused_rather_than_stored(
        client, conn, visit):
    """`reason_for` checks the posted row against the list that was rendered, so a page
    left open against a different section cannot write a row this one never offered."""
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/vitals",
                         data={"reason": "declined-footwear", "words": ""})

    # Assert
    assert answer.status_code == 400
    assert Section.VITALS not in store.load(conn, "v-1").resolutions


def test_a_reason_posted_to_a_closed_visit_is_refused_and_changes_nothing(
        client, conn, visit):
    """§5.9 is a property of the row as well as of the transition, because a stale page
    posts without transitioning. web_plan §6.2 puts this on the Addendum in Web Pass 3."""
    # Arrange
    visit.end_early(Reason("time-exhausted"), JUNIOR_PHYSICIAN, CLOSE)
    store.save(conn, visit)

    # Act
    answer = client.post("/visits/v-1/sections/notes",
                         data={"reason": "nothing-further", "words": ""})

    # Assert
    assert answer.status_code == 400
    assert "This Visit is not open" in answer.text
    assert Section.NOTES not in store.load(conn, "v-1").resolutions


def test_a_post_carrying_neither_content_nor_a_reason_is_refused_in_words(
        client, conn, visit):
    """`Resolution` refuses both-or-neither in domain language. A person holding a tablet
    in a doorway needs to be told which of the two things to do instead."""
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/notes", data={"words": ""})

    # Assert
    assert answer.status_code == 400
    assert "Nothing was recorded" in answer.text
    assert "Nothing to record here" in answer.text
    assert Section.NOTES not in store.load(conn, "v-1").resolutions


def test_the_visit_reason_records_what_the_household_said(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/visit-reason",
                         data={"words": "Dizzy when standing since Ramadan."},
                         follow_redirects=False)

    # Assert
    assert answer.status_code == 303
    stored = store.load(conn, "v-1").resolutions[Section.VISIT_REASON]
    assert stored == Resolution(Section.VISIT_REASON,
                                content="Dizzy when standing since Ramadan.")


def test_notes_records_what_the_other_seven_sections_have_no_place_for(
        client, conn, visit):
    # Arrange / Act
    client.post("/visits/v-1/sections/notes",
                data={"words": "Daughter interpreted throughout."},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.NOTES]
    assert stored == Resolution(Section.NOTES,
                                content="Daughter interpreted throughout.")


def test_what_is_already_recorded_comes_back_in_the_box_rather_than_being_lost(
        client, conn, visit):
    # Arrange
    visit.resolutions[Section.NOTES] = Resolution(Section.NOTES,
                                                  content="Daughter interpreted.")
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1/sections/notes")

    # Assert
    assert "Daughter interpreted." in answer.text
    assert "Recorded in this Visit." in answer.text


def test_the_interval_history_records_the_events_a_rule_will_read(client, conn, visit):
    # Arrange / Act
    client.post("/visits/v-1/sections/concerns-and-interval-history",
                data={"events": ["a-fall", "hypoglycaemic-episode"],
                      "Patient": "", "Caregiver": ""},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.CONCERNS_AND_INTERVAL_HISTORY]
    assert stored.content == {"events": ["a-fall", "hypoglycaemic-episode"],
                              "concerns": []}


def test_nothing_having_happened_is_recorded_as_an_answer_and_not_as_a_blank(
        client, conn, visit):
    """*None of these* is a positive answer: the difference between nothing happened and
    nobody asked (`interval-events.md`)."""
    # Arrange / Act
    client.post("/visits/v-1/sections/concerns-and-interval-history",
                data={"events": ["none-of-these"], "Patient": "", "Caregiver": ""},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.CONCERNS_AND_INTERVAL_HISTORY]
    assert stored.content == {"events": ["none-of-these"], "concerns": []}


def test_each_concern_is_recorded_against_whoever_raised_it(client, conn, visit):
    # Arrange / Act
    client.post("/visits/v-1/sections/concerns-and-interval-history",
                data={"events": ["none-of-these"],
                      "Patient": "His feet burn at night.\nDizzy standing up.",
                      "Caregiver": "He sleeps in a chair."},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.CONCERNS_AND_INTERVAL_HISTORY]
    assert stored.content["concerns"] == [
        {"raised_by": "Patient", "words": "His feet burn at night."},
        {"raised_by": "Patient", "words": "Dizzy standing up."},
        {"raised_by": "Caregiver", "words": "He sleeps in a chair."}]


def test_none_of_these_ticked_beside_an_event_that_happened_is_refused(
        client, conn, visit):
    """Both cannot be true, and storing both would put a contradiction where a rule reads."""
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/concerns-and-interval-history",
                         data={"events": ["none-of-these", "a-fall"],
                               "Patient": "", "Caregiver": ""})

    # Assert
    assert answer.status_code == 400
    assert "None of these" in answer.text
    assert Section.CONCERNS_AND_INTERVAL_HISTORY not in store.load(conn, "v-1").resolutions


def test_an_interval_history_with_no_row_ticked_at_all_is_refused(client, conn, visit):
    """A concern without the tick-list is half a section: the list is what the engine
    reads, and *None of these* is there so it can always be answered."""
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/concerns-and-interval-history",
                         data={"Patient": "His feet burn at night.", "Caregiver": ""})

    # Assert
    assert answer.status_code == 400
    assert "Nothing was recorded" in answer.text
    assert Section.CONCERNS_AND_INTERVAL_HISTORY not in store.load(conn, "v-1").resolutions


def test_what_was_ticked_comes_back_ticked_when_the_section_is_opened_again(
        client, conn, visit):
    # Arrange
    visit.resolutions[Section.CONCERNS_AND_INTERVAL_HISTORY] = Resolution(
        Section.CONCERNS_AND_INTERVAL_HISTORY,
        content={"events": ["ran-out-of-medication"],
                 "concerns": [{"raised_by": "Caregiver", "words": "The box was empty."}]})
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1/sections/concerns-and-interval-history")

    # Assert
    assert 'value="ran-out-of-medication" checked' in answer.text
    assert "The box was empty." in answer.text


def test_vitals_asks_for_what_both_conditions_need_and_not_for_the_baseline_only_rows(
        client, visit):
    """A Routine Visit; `bp-other-arm` and `height` are baseline_only, so they are not
    asked for here (`vitals-by-condition.md`)."""
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/vitals")

    # Assert
    assert "Blood pressure, seated" in answer.text
    assert "Capillary blood glucose" in answer.text
    assert "mmHg" in answer.text
    assert 'name="height"' not in answer.text


def test_vitals_records_the_readings_that_were_taken(client, conn, visit):
    # Arrange / Act
    client.post("/visits/v-1/sections/vitals",
                data={"bp-seated": "138/84", "pulse": "72", "weight": "",
                      "bp-standing": "", "capillary-glucose": "9.1"},
                follow_redirects=False)

    # Assert — only what was typed, because a box left blank is not a reading of nought
    stored = store.load(conn, "v-1").resolutions[Section.VITALS]
    assert stored.content == {"bp-seated": "138/84", "pulse": "72",
                              "capillary-glucose": "9.1"}


def test_vitals_with_every_box_left_blank_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/vitals",
                         data={"bp-seated": "", "pulse": ""})

    # Assert
    assert answer.status_code == 400
    assert "Nothing was recorded" in answer.text
    assert Section.VITALS not in store.load(conn, "v-1").resolutions


def test_a_reading_already_taken_comes_back_in_its_field(client, conn, visit):
    # Arrange
    visit.resolutions[Section.VITALS] = Resolution(Section.VITALS,
                                                   content={"pulse": "72"})
    store.save(conn, visit)

    # Act
    answer = client.get("/visits/v-1/sections/vitals")

    # Assert
    assert 'value="72"' in answer.text


def test_the_examination_list_is_composed_and_says_it_was(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/physical-examination")

    # Assert
    assert "composed from the Patient" in answer.text
    assert "General appearance" in answer.text
    assert "Foot inspection" in answer.text


def test_a_baseline_visit_requires_the_whole_examination(client, conn, scheduled):
    # Arrange
    scheduled.start(KNOCK, VisitKind.BASELINE,
                    junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.save(conn, scheduled)

    # Act
    answer = client.get("/visits/v-1/sections/physical-examination")

    # Assert
    assert "no surveillance history to compose from" in answer.text
    assert "unreachable" not in answer.text


def test_the_examination_records_a_finding_against_each_element_examined(
        client, conn, visit):
    # Arrange / Act
    client.post("/visits/v-1/sections/physical-examination",
                data={"general-appearance": "Comfortable at rest.",
                      "foot-inspection": "Callus under the left first metatarsal.",
                      "added": "Ankle reflexes, both absent."},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.PHYSICAL_EXAMINATION]
    assert stored.content == {
        "elements": {"general-appearance": "Comfortable at rest.",
                     "foot-inspection": "Callus under the left first metatarsal."},
        "added": "Ankle reflexes, both absent."}


def test_the_field_team_may_add_an_element_without_any_of_the_required_ones(
        client, conn, visit):
    """§4.2: the Field Team may add elements. An addition is content, so the section is
    resolved by it — which of the required ones went unexamined is the review screen's
    question, in Web Pass 3."""
    # Arrange / Act
    client.post("/visits/v-1/sections/physical-examination",
                data={"added": "Ankle reflexes, both absent."},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.PHYSICAL_EXAMINATION]
    assert stored.content == {"elements": {}, "added": "Ankle reflexes, both absent."}


def test_an_examination_with_nothing_written_anywhere_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/physical-examination",
                         data={"general-appearance": "", "added": ""})

    # Assert
    assert answer.status_code == 400
    assert "Nothing was recorded" in answer.text
    assert Section.PHYSICAL_EXAMINATION not in store.load(conn, "v-1").resolutions


def test_the_self_care_check_asks_only_about_what_this_patients_conditions_call_for(
        client, conn, day):
    # Arrange — hypertension alone, so no insulin or meter item applies
    store.add_patient(conn, "p-2", "Omar Al-Qahtani", ["hypertension"],
                      junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    record = Visit("v-2", "p-2")
    store.schedule(conn, record, day, "Three-month review")
    record.start(KNOCK, VisitKind.ROUTINE,
                 junior_physician=JUNIOR_PHYSICIAN, nurse=NURSE)
    store.save(conn, record)

    # Act
    answer = client.get("/visits/v-2/sections/self-care-check")

    # Assert
    assert "cuff-technique" in answer.text
    assert "insulin-storage" not in answer.text


def test_the_self_care_check_records_what_was_watched(client, conn, visit):
    # Arrange / Act
    client.post("/visits/v-1/sections/self-care-check",
                data={"cuff-technique": "correct", "foot-routine": "incorrect"},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.SELF_CARE_CHECK]
    assert stored.content == {"cuff-technique": "correct",
                              "foot-routine": "incorrect"}


def test_an_item_with_nothing_in_the_house_to_do_it_with_is_recorded_as_a_finding(
        client, conn, visit):
    """`self-care-items.md`: what an item requires being absent is a Finding, not a skip."""
    # Arrange / Act
    client.post("/visits/v-1/sections/self-care-check",
                data={"meter-technique": "nothing-to-use"},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.SELF_CARE_CHECK]
    assert stored.content == {"meter-technique": "nothing-to-use"}


def test_a_self_care_check_with_nothing_watched_at_all_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/self-care-check", data={})

    # Assert
    assert answer.status_code == 400
    assert "Nothing was recorded" in answer.text
    assert Section.SELF_CARE_CHECK not in store.load(conn, "v-1").resolutions


def test_an_outcome_that_is_not_one_of_the_three_is_refused_rather_than_stored(
        client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/self-care-check",
                         data={"cuff-technique": "probably-fine"})

    # Assert
    assert answer.status_code == 400
    assert "not one of the three" in answer.text
    assert Section.SELF_CARE_CHECK not in store.load(conn, "v-1").resolutions


def test_searching_the_drug_list_offers_what_it_holds_and_never_a_typed_strength(
        client, visit):
    # Arrange / Act
    answer = client.get(
        "/visits/v-1/sections/medication-reconciliation?q=metf")

    # Assert
    assert "Metformin 500 mg tablet" in answer.text
    assert 'name="strength"' not in answer.text


def test_a_search_that_matches_nothing_says_so_and_offers_the_unmatched_box(
        client, visit):
    """§4.2: a product the list does not contain is an outcome. The page has to offer
    that outcome at the moment the search fails, or the Nurse drops the item."""
    # Arrange / Act
    answer = client.get(
        "/visits/v-1/sections/medication-reconciliation?q=cordarone")

    # Assert
    assert "No product on the drug list matches" in answer.text
    assert 'name="label"' in answer.text


def test_adding_a_box_records_the_product_and_the_two_typed_fields(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/medication-reconciliation",
                         data={"act": "add", "product": "metformin-500",
                               "quantity": "42", "expiry": "2027-03-01"},
                         follow_redirects=False)

    # Assert
    assert answer.headers["location"] == (
        "/visits/v-1/sections/medication-reconciliation")
    stored = store.load(conn, "v-1").resolutions[Section.MEDICATION_RECONCILIATION]
    assert stored.content["in_house"] == [
        {"label": "Metformin", "product_id": "metformin-500",
         "quantity_remaining": 42, "expiry": "2027-03-01"}]


def test_a_box_added_without_a_count_or_an_expiry_is_still_recorded(client, conn, visit):
    """Both typed fields are optional: a blister with the strip torn off has no count, and
    refusing the box would lose the drug to keep the count (N6)."""
    # Arrange / Act
    client.post("/visits/v-1/sections/medication-reconciliation",
                data={"act": "add", "product": "amlodipine-5",
                      "quantity": "", "expiry": ""},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.MEDICATION_RECONCILIATION]
    assert stored.content["in_house"] == [
        {"label": "Amlodipine", "product_id": "amlodipine-5",
         "quantity_remaining": None, "expiry": None}]


def test_a_product_the_list_does_not_hold_is_kept_as_written_and_marked_unmatched(
        client, conn, visit):
    # Arrange / Act
    client.post("/visits/v-1/sections/medication-reconciliation",
                data={"act": "add", "product": "",
                      "label": "Cordarone 200 mg (brought from Cairo)",
                      "quantity": "", "expiry": ""},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.MEDICATION_RECONCILIATION]
    assert stored.content["in_house"] == [
        {"label": "Cordarone 200 mg (brought from Cairo)", "product_id": None,
         "quantity_remaining": None, "expiry": None}]
    assert {"kind": "not on the drug list — Noor cannot reconcile this item",
            "subject": "Cordarone 200 mg (brought from Cairo)"} in \
        stored.content["discrepancies"]


def test_a_box_named_both_ways_is_refused_rather_than_losing_its_words(
        client, conn, visit):
    """The form offers the list or the box. Filling both must not silently drop the
    typed words."""
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/medication-reconciliation",
                         data={"act": "add", "product": "metformin-500",
                               "label": "Metformin (spare strip)",
                               "quantity": "", "expiry": ""})

    # Assert
    assert answer.status_code == 400
    assert "Two names for one box" in answer.text
    assert Section.MEDICATION_RECONCILIATION not in store.load(conn, "v-1").resolutions


def test_the_house_and_what_was_found_read_back_on_the_section(client, conn, visit):
    """One test closes two gate gaps: _house's content path and discrepancy_heading's
    non-empty arm — neither is reachable with a fresh house."""
    # Arrange
    client.post("/visits/v-1/sections/medication-reconciliation",
                data={"act": "add", "product": "",
                      "label": "Cordarone 200 mg (brought from Cairo)",
                      "quantity": "", "expiry": ""}, follow_redirects=False)

    # Act
    answer = client.get("/visits/v-1/sections/medication-reconciliation")

    # Assert
    assert "Cordarone 200 mg (brought from Cairo)" in answer.text
    assert "What the comparison found" in answer.text
    assert "cannot reconcile this item" in answer.text


def test_an_add_with_neither_a_product_nor_a_name_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/medication-reconciliation",
                         data={"act": "add", "product": "", "label": ""})

    # Assert
    assert answer.status_code == 400
    assert "no name on it" in answer.text
    assert Section.MEDICATION_RECONCILIATION not in store.load(conn, "v-1").resolutions


def test_a_count_of_tablets_that_is_not_a_number_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/medication-reconciliation",
                         data={"act": "add", "product": "metformin-500",
                               "quantity": "about half", "expiry": ""})

    # Assert
    assert answer.status_code == 400
    assert "a count of tablets" in answer.text


def test_a_negative_count_is_refused_by_the_domain_and_answered_in_words(
        client, conn, visit):
    """`Medication.__post_init__` raises `ReconError`; the handler does not re-check it."""
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/medication-reconciliation",
                         data={"act": "add", "product": "metformin-500",
                               "quantity": "-3", "expiry": ""})

    # Assert
    assert answer.status_code == 400
    assert "cannot be negative" in answer.text


def test_a_box_added_by_mistake_can_be_taken_back_out_of_the_house(client, conn, visit):
    # Arrange
    client.post("/visits/v-1/sections/medication-reconciliation",
                data={"act": "add", "product": "metformin-500",
                      "quantity": "42", "expiry": ""}, follow_redirects=False)
    client.post("/visits/v-1/sections/medication-reconciliation",
                data={"act": "add", "product": "amlodipine-5",
                      "quantity": "28", "expiry": ""}, follow_redirects=False)

    # Act
    client.post("/visits/v-1/sections/medication-reconciliation",
                data={"act": "remove", "row": "0"}, follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.MEDICATION_RECONCILIATION]
    assert [row["product_id"] for row in stored.content["in_house"]] == ["amlodipine-5"]


def test_a_row_number_that_is_not_in_the_house_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/medication-reconciliation",
                         data={"act": "remove", "row": "4"})

    # Assert
    assert answer.status_code == 400
    assert "no longer in the house" in answer.text


def test_an_empty_cupboard_is_recorded_as_a_finding_when_it_is_ticked_as_one(
        client, conn, visit):
    """An empty cupboard is content, not an absence: every prescribed drug becomes an
    omission. But it has to be claimed, because nobody having looked yet is the other
    thing an empty house could mean."""
    # Arrange / Act
    client.post("/visits/v-1/sections/medication-reconciliation",
                data={"act": "done", "empty": "on"}, follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.MEDICATION_RECONCILIATION]
    assert stored.content["in_house"] == []


def test_saving_an_empty_house_nobody_claimed_is_empty_is_refused(client, conn, visit):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/medication-reconciliation",
                         data={"act": "done"})

    # Assert
    assert answer.status_code == 400
    assert "Nothing was recorded" in answer.text
    assert Section.MEDICATION_RECONCILIATION not in store.load(conn, "v-1").resolutions


def test_save_and_return_goes_back_to_the_visit_and_adding_stays_on_the_section(
        client, conn, visit):
    # Arrange
    client.post("/visits/v-1/sections/medication-reconciliation",
                data={"act": "add", "product": "metformin-500",
                      "quantity": "42", "expiry": ""}, follow_redirects=False)

    # Act
    answer = client.post("/visits/v-1/sections/medication-reconciliation",
                         data={"act": "done"}, follow_redirects=False)

    # Assert
    assert answer.headers["location"] == "/visits/v-1"


def test_a_prescribed_list_nobody_prepared_degrades_and_says_what_it_costs(
        client, conn, visit):
    """The `visit` fixture's Patient has no cached read, so `prefetch.prescribed` answers
    Unreachable — which is §4.10's rule that in the house the two are one fact."""
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/medication-reconciliation")

    # Assert
    assert "The prescribed list could not be read" in answer.text
    assert "no omission and no unprescribed item can be found here" in answer.text


def test_the_care_plan_refuses_to_open_until_the_other_seven_are_resolved(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/care-plan")

    # Assert
    assert answer.status_code == 409
    assert "assembled after the other seven" in answer.text
    assert "Visit Reason" in answer.text


def test_the_care_plan_opens_once_the_other_seven_are_resolved(client, conn, seven):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/care-plan")

    # Assert
    assert answer.status_code == 200
    assert "Systolic blood pressure" in answer.text
    assert "Glucose two hours after a meal" in answer.text


def test_the_care_plan_states_that_no_titration_can_be_set_and_why(client, seven):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/care-plan")

    # Assert
    assert "needs a ratified Goal of Care" in answer.text
    assert 'name="titration"' not in answer.text


def test_the_care_plan_emits_a_between_visit_plan_the_visit_carries(client, conn, seven):
    """§4.8: the Care Plan *emits* the plan. `Visit.complete` refuses without one, so this
    is the write that makes Web Pass 3's Complete Visit possible."""
    # Arrange / Act
    client.post("/visits/v-1/sections/care-plan",
                data={"times-systolic": "3", "times-glucose_pre_prandial": "3",
                      "above-systolic": "180", "below-glucose_pre_prandial": "4.0",
                      "action": "call the Supervisor"},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1")
    assert stored.plan.schedule == (
        MeasurementSchedule(Axis.SYSTOLIC, 3),
        MeasurementSchedule(Axis.GLUCOSE_PRE_PRANDIAL, 3))
    assert stored.plan.stop_rules == (
        Threshold(Axis.SYSTOLIC, Comparison.ABOVE, 180.0, "call the Supervisor"),
        Threshold(Axis.GLUCOSE_PRE_PRANDIAL, Comparison.BELOW, 4.0,
                  "call the Supervisor"))
    assert stored.plan.titration == ()


def test_the_emitted_plan_is_also_the_sections_content(client, conn, seven):
    # Arrange / Act
    client.post("/visits/v-1/sections/care-plan",
                data={"times-systolic": "3", "action": "call the Supervisor"},
                follow_redirects=False)

    # Assert
    stored = store.load(conn, "v-1").resolutions[Section.CARE_PLAN]
    assert stored.content == {"schedule": [{"axis": "systolic", "times_per_week": 3}],
                              "stop_rules": [],
                              "titration": []}


def test_a_stop_rule_with_no_action_against_it_is_refused_as_prose_with_a_number_in_it(
        client, conn, seven):
    """§4.8's own words. `Threshold.__post_init__` raises `PlanError`; the handler does
    not re-check it."""
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/care-plan",
                         data={"above-systolic": "180", "action": ""})

    # Assert
    assert answer.status_code == 400
    assert "prose with a number in it" in answer.text
    assert Section.CARE_PLAN not in store.load(conn, "v-1").resolutions


def test_a_plan_with_no_line_in_it_at_all_is_refused(client, conn, seven):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/care-plan",
                         data={"action": "call the Supervisor"})

    # Assert
    assert answer.status_code == 400
    assert "no line in it is not a plan" in answer.text


def test_a_measurement_schedule_of_nought_times_a_week_is_refused(client, conn, seven):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/care-plan",
                         data={"times-systolic": "0"})

    # Assert
    assert answer.status_code == 400
    assert "is not a schedule" in answer.text


def test_a_number_of_measurements_that_is_not_a_number_is_refused(client, conn, seven):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/care-plan",
                         data={"times-systolic": "twice-ish"})

    # Assert
    assert answer.status_code == 400
    assert "cannot read" in answer.text


def test_a_stop_threshold_that_is_not_a_number_is_refused(client, conn, seven):
    # Arrange / Act
    answer = client.post("/visits/v-1/sections/care-plan",
                         data={"above-systolic": "high", "action": "call the Supervisor"})

    # Assert
    assert answer.status_code == 400
    assert "not a threshold" in answer.text
    assert Section.CARE_PLAN not in store.load(conn, "v-1").resolutions


def test_a_plan_already_emitted_comes_back_in_its_boxes(client, conn, seven):
    # Arrange
    client.post("/visits/v-1/sections/care-plan",
                data={"times-systolic": "3", "action": "call the Supervisor"},
                follow_redirects=False)

    # Act
    answer = client.get("/visits/v-1/sections/care-plan")

    # Assert
    assert 'value="3"' in answer.text


def test_emitted_stop_rules_come_back_in_their_boxes_with_their_action(
        client, conn, seven):
    # Arrange
    client.post("/visits/v-1/sections/care-plan",
                data={"above-systolic": "180", "below-glucose_pre_prandial": "4.0",
                      "action": "call the Supervisor"},
                follow_redirects=False)

    # Act
    answer = client.get("/visits/v-1/sections/care-plan")

    # Assert
    assert 'value="180.0"' in answer.text
    assert 'value="4.0"' in answer.text
    assert "call the Supervisor" in answer.text


def test_the_care_plan_refusal_links_to_each_outstanding_section_and_back_to_the_visit(
        client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/care-plan")

    # Assert
    assert answer.status_code == 409
    assert 'href="/visits/v-1/sections/visit-reason"' in answer.text
    assert 'href="/visits/v-1"' in answer.text


def test_a_section_page_names_its_section_in_the_title(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/vitals")

    # Assert
    assert "<title>Vitals" in answer.text


def test_the_guard_box_does_not_share_its_id_with_the_content_box(client, visit):
    # Arrange / Act
    answer = client.get("/visits/v-1/sections/notes")

    # Assert
    assert answer.text.count('id="words"') == 1
    assert 'id="reason-words"' in answer.text
