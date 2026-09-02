"""The eight sections (§4.2) and what Resolved actually means (§5.8)."""
import pytest

from noor.domain import records
from noor.domain.records import Reason, Resolution
from noor.domain.states import Section

FILLED = {s: Resolution(s, content={"noted": True}) for s in Section}


def test_the_visit_protocol_has_eight_sections_numbered_one_to_eight():
    # Assert — the integer is the position, so nothing can be absent (§4.2)
    assert [s.value for s in Section] == [1, 2, 3, 4, 5, 6, 7, 8]


def test_the_care_plan_is_seventh_in_the_record_and_notes_is_eighth():
    # Assert
    assert Section.CARE_PLAN.value == 7
    assert Section.NOTES.value == 8


def test_a_section_is_resolved_by_its_content():
    # Act
    resolution = Resolution(Section.VITALS, content={"bp-seated": "138/84"})

    # Assert — a Resolution that exists is resolved; the two ways differ in shape
    assert resolution.content == {"bp-seated": "138/84"}
    assert resolution.reason is None


def test_a_section_is_equally_resolved_by_a_structured_reason_for_having_none():
    # Act — §5.8: Resolved is not filled
    resolution = Resolution(Section.VITALS, reason=Reason("no-working-device"))

    # Assert
    assert resolution.content is None
    assert resolution.reason == Reason("no-working-device")


def test_a_section_with_neither_content_nor_a_reason_is_refused():
    # Act / Assert
    with pytest.raises(records.ResolutionError):
        Resolution(Section.NOTES)


def test_a_section_carrying_both_content_and_a_reason_is_refused():
    # Act / Assert — a reason for having no content, alongside content, is a bug
    with pytest.raises(records.ResolutionError):
        Resolution(Section.NOTES, content={"text": "hi"}, reason=Reason("nothing-further"))


def test_the_other_row_without_its_free_text_is_refused():
    # Act / Assert — Other is only meaningful with the text (§5.10)
    with pytest.raises(records.ResolutionError):
        Resolution(Section.NOTES, reason=Reason(records.OTHER))


def test_the_other_row_with_its_free_text_is_accepted():
    # Act
    resolution = Resolution(Section.NOTES, reason=Reason(records.OTHER, "power cut"))

    # Assert
    assert resolution.reason.free_text == "power cut"


def test_unresolved_names_the_missing_sections_in_the_records_order():
    # Arrange — resolve everything, then remove two, out of order
    partial = {s: FILLED[s] for s in Section
               if s not in (Section.NOTES, Section.VITALS)}

    # Act
    missing = records.unresolved(partial)

    # Assert — Vitals is fourth and Notes eighth, so that is the order they come in
    assert missing == (Section.VITALS, Section.NOTES)


def test_the_care_plan_cannot_be_assembled_while_notes_is_still_unresolved():
    # Arrange — the one place the working order and the record's order differ (§4.2)
    seven = {s: FILLED[s] for s in Section
             if s not in (Section.CARE_PLAN, Section.NOTES)}

    # Act / Assert
    with pytest.raises(records.CarePlanTooEarly):
        records.check_care_plan_ready(seven)


def test_the_care_plan_may_be_assembled_once_the_other_seven_are_resolved():
    # Arrange
    seven = {s: FILLED[s] for s in Section if s is not Section.CARE_PLAN}

    # Act / Assert — a guard, so returning None is the pass
    assert records.check_care_plan_ready(seven) is None


@pytest.mark.parametrize("empty", [{}, [], ""])
def test_empty_content_is_refused(empty):
    # Act / Assert — a section cannot be resolved by something that says nothing (§5.8)
    with pytest.raises(records.ResolutionError):
        Resolution(Section.NOTES, content=empty)


CANCELLED = ({"id": "patient-not-at-home", "label": "Patient not at home"},
             {"id": "patient-died", "label": "Patient died"})
SHARED = ({"id": "patient-declined", "label": "Patient declined"},)
VITALS_ROWS = ({"id": "no-working-device", "label": "No working device in the household"},)


def test_every_reason_list_ends_in_the_other_row_no_content_file_holds():
    # Act
    rows = records.reason_rows(CANCELLED)

    # Assert — §5.10 makes Other structural: the code shows it, an owner cannot remove it
    assert [row["id"] for row in rows] == ["patient-not-at-home", "patient-died", "other"]


def test_a_sections_list_is_its_shared_core_and_then_its_own_rows():
    # Act — the two lists §5.10 composes for one section, in the order they are read
    rows = records.reason_rows(SHARED, VITALS_ROWS)

    # Assert
    assert [row["id"] for row in rows] == [
        "patient-declined", "no-working-device", "other"]


def test_a_row_that_is_not_on_the_list_is_not_a_reason():
    # Act / Assert — a page left open while the list changed is the ordinary way here
    with pytest.raises(records.ResolutionError, match="not a reason on this list"):
        records.reason_for(records.reason_rows(CANCELLED), "patient-emigrated", "")


def test_the_other_row_is_not_a_reason_without_the_words_that_make_it_one():
    # Act / Assert — whitespace is not words
    with pytest.raises(records.ResolutionError, match="needs its own words"):
        records.reason_for(records.reason_rows(CANCELLED), "other", "   ")


def test_a_named_row_becomes_a_reason_and_keeps_anything_written_beside_it():
    # Act
    rows = records.reason_rows(CANCELLED)
    plain = records.reason_for(rows, "patient-died", "")
    annotated = records.reason_for(rows, "patient-died", " at dawn, per the daughter ")

    # Assert — the row is the record; the words are kept wherever there are any
    assert plain == Reason("patient-died", None)
    assert annotated == Reason("patient-died", "at dawn, per the daughter")
