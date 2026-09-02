"""The seven reads, the one write, and the five fixtures that misbehave (§4.9)."""
from datetime import date, datetime

import pytest

from noor import emr
from noor.domain.reconciliation import Medication
from noor.domain.states import DataState, Datum
from noor.emr import FixtureEMR, WriteRejected

NOW = datetime(2026, 8, 28, 7, 30)
TODAY = date(2026, 8, 28)


@pytest.fixture
def ehr():
    """Named `ehr` so it does not shadow the module under test."""
    return FixtureEMR(now=NOW)


def test_the_fixture_emr_satisfies_the_boundary_protocol(ehr):
    # Assert — names only, which is all a Protocol can check; the parametrised test
    # below is what checks that each of them answers with a Datum
    assert isinstance(ehr, emr.EMR)


def test_the_boundary_gives_noor_no_way_to_schedule_or_cancel_a_visit(ehr):
    # Assert — §4.9: the roster is a read. Noor records what became of a Visit only
    assert (hasattr(ehr, "schedule"), hasattr(ehr, "cancel")) == (False, False)


@pytest.mark.parametrize("read, args", [
    ("demographics", ("p-001",)),
    ("problems", ("p-001",)),
    ("medications", ("p-001",)),
    ("lab", ("p-001", "hba1c")),
    ("surveillance", ("p-002", "foot-examination")),
    ("allergies", ("p-001",)),
    ("roster", (TODAY,)),
])
def test_every_read_answers_with_a_datum(ehr, read, args):
    # Act
    answer = getattr(ehr, read)(*args)

    # Assert — N6: an EMR out of reach is a value, not an exception a caller may forget
    assert isinstance(answer, Datum)


def test_demographics_carries_the_name_the_field_team_will_read(ehr):
    # Act
    answer = ehr.demographics("p-001")

    # Assert
    assert answer.value["name"] == "Fatima Al-Harbi"


def test_a_read_for_a_patient_the_emr_does_not_have_is_absent_and_not_an_error(ehr):
    # Act / Assert
    assert ehr.demographics("p-999").state is DataState.ABSENT


def test_an_hba1c_eighteen_months_old_is_present_and_carries_the_day_it_was_drawn(ehr):
    # Act
    answer = ehr.lab("p-001", "hba1c")

    # Assert — §5.2: staleness is the as_of on a Present value, never a fourth state
    assert (answer.state, answer.value, answer.as_of) == (
        DataState.PRESENT, 9.1, datetime(2025, 2, 10))


def test_a_lab_the_patient_has_never_had_is_absent(ehr):
    # Act / Assert — a different answer from Fatima's, and the caller can tell
    assert ehr.lab("p-003", "hba1c").state is DataState.ABSENT


def test_a_read_that_times_out_is_unreachable(ehr):
    # Act / Assert — §4.10's trigger, arriving as one of the three states
    assert ehr.medications("p-004").state is DataState.UNREACHABLE


def test_one_read_timing_out_does_not_darken_the_others_for_that_patient(ehr):
    # Act / Assert — a request times out, not a Patient
    assert ehr.demographics("p-004").is_present is True


def test_a_free_text_allergy_is_handed_over_exactly_as_it_was_written(ehr):
    # Act
    answer = ehr.allergies("p-001")

    # Assert — Noor does not code it, split it, or tidy it (N6)
    assert answer.value == ("Sulfa — rash, per daughter",)


def test_a_patient_with_no_allergy_recorded_is_absent_not_no_known_allergies(ehr):
    # Act / Assert — silence is not a negative finding (§4.1)
    assert ehr.allergies("p-003").state is DataState.ABSENT


def test_the_prescribed_list_arrives_as_medications_the_domain_already_understands(ehr):
    # Act
    lines = ehr.medications("p-001").value

    # Assert
    assert [line.product.id for line in lines] == [
        "metformin-500", "gliclazide-80", "amlodipine-5"]


def test_a_prescribed_drug_the_list_has_no_row_for_arrives_unmatched(ehr):
    # Act
    lines = ehr.medications("p-002").value

    # Assert — Wright's amiodarone failure, preserved instead of dropped (§4.2)
    assert lines[-1] == Medication("Cordarone 200 mg (brought from Cairo)")


def test_a_surveillance_date_is_the_day_the_item_was_last_done(ehr):
    # Act / Assert — Task 14 turns this into "overdue"; the boundary only reports it
    assert ehr.surveillance("p-002", "foot-examination").value == date(2024, 11, 3)


def test_a_surveillance_item_that_was_never_done_is_absent(ehr):
    # Act / Assert
    assert ehr.surveillance("p-003", "retinal-screening").state is DataState.ABSENT


def test_the_roster_carries_the_reason_each_visit_was_scheduled(ehr):
    # Act
    lines = ehr.roster(TODAY).value

    # Assert — §4.9: this is what the Visit Reason section opens with, cached at Scheduled
    assert lines[0].reason.startswith("Three-month review")


def test_a_day_with_nothing_on_the_roster_is_absent_not_an_empty_day(ehr):
    # Act / Assert
    assert ehr.roster(date(2026, 1, 1)).state is DataState.ABSENT


def test_an_accepted_write_is_recorded_against_the_patient(ehr):
    # Act
    ehr.submit("p-001", {"item": "visit outcome"})

    # Assert
    assert ehr.accepted == [("p-001", {"item": "visit outcome"})]


def test_the_emr_that_rejects_the_write_raises_rather_than_failing_quietly(ehr):
    # Act / Assert — §4.10: a silently failed Write-Back is worse than none
    with pytest.raises(WriteRejected):
        ehr.submit("p-005", {"item": "visit outcome"})


def test_a_rejected_write_leaves_nothing_behind_that_looks_accepted(ehr):
    # Arrange
    with pytest.raises(WriteRejected):
        ehr.submit("p-005", {"item": "visit outcome"})

    # Assert — Task 19's drain reads this, so a false positive here becomes a lost task
    assert ehr.accepted == []


def test_a_write_for_a_patient_the_emr_does_not_have_is_rejected(ehr):
    # Act / Assert
    with pytest.raises(WriteRejected):
        ehr.submit("p-999", {"item": "visit outcome"})


@pytest.mark.parametrize(("member", "args"), [
    ("demographics", (None, "p-001")),
    ("problems", (None, "p-001")),
    ("medications", (None, "p-001")),
    ("lab", (None, "p-001", "hba1c")),
    ("surveillance", (None, "p-001", "hba1c")),
    ("allergies", (None, "p-001")),
    ("roster", (None, TODAY)),
    ("submit", (None, "p-001", {})),
])
def test_the_protocol_member_bodies_are_placeholders(member, args):
    # Act / Assert — invoked on the class itself, each one-line body is its `...`:
    # the Protocol is the shape; the fixture is the behaviour (§4.9)
    assert getattr(emr.EMR, member)(*args) is None
