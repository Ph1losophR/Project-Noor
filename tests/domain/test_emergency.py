"""The Emergency (§5.7, ADR 0004) — cheap to enter, impossible to leave open."""
from datetime import datetime

import pytest

from noor.domain import emergency
from noor.domain.emergency import EmergencyRecord, EntryKind

ENTERED = datetime(2026, 8, 28, 10, 0)
LATER = datetime(2026, 8, 28, 10, 6)
LATER_STILL = datetime(2026, 8, 28, 10, 40)


def test_an_emergency_is_entered_with_nothing_but_the_time_it_started():
    # Act — ADR 0004: zero required fields at entry
    record = EmergencyRecord(started_at=ENTERED)

    # Assert
    assert record.entries == []
    assert record.is_resolved is False


def test_the_timeline_tags_each_entry_as_observed_or_as_done():
    # Assert — two kinds, not a severity and not a free-text label
    assert [k.value for k in EntryKind] == ["observed", "done"]


def test_the_timeline_holds_the_entries_in_the_order_they_were_recorded():
    # Arrange
    record = EmergencyRecord(started_at=ENTERED)

    # Act
    record.record(EntryKind.OBSERVED, "unresponsive, breathing", ENTERED)
    record.record(EntryKind.DONE, "ambulance called", LATER)

    # Assert — one assertion of the whole timeline, so a diff says what changed
    assert record.entries == [
        emergency.TimelineEntry(EntryKind.OBSERVED, "unresponsive, breathing", ENTERED),
        emergency.TimelineEntry(EntryKind.DONE, "ambulance called", LATER),
    ]


def test_an_emergency_that_has_ended_carries_both_of_its_times():
    # Arrange
    record = EmergencyRecord(started_at=ENTERED)

    # Act
    record.resolve(LATER_STILL)

    # Assert
    assert (record.started_at, record.ended_at) == (ENTERED, LATER_STILL)
    assert record.has_ended is True


def test_an_emergency_that_ended_with_an_empty_timeline_is_not_documented():
    # Arrange
    record = EmergencyRecord(started_at=ENTERED)

    # Act
    record.resolve(LATER)

    # Assert — passing through an ambulance call and recording nothing is not resolved
    assert record.is_documented is False
    assert record.is_resolved is False


def test_an_emergency_that_ended_and_was_written_down_is_resolved():
    # Arrange
    record = EmergencyRecord(started_at=ENTERED)
    record.record(EntryKind.DONE, "ambulance called", ENTERED)

    # Act
    record.resolve(LATER)

    # Assert
    assert record.is_resolved is True



def test_an_emergency_cannot_be_resolved_a_second_time():
    # Arrange
    record = EmergencyRecord(started_at=ENTERED)
    record.resolve(LATER)

    # Act / Assert
    with pytest.raises(emergency.EmergencyError):
        record.resolve(LATER_STILL)


def test_an_emergency_cannot_end_before_it_began():
    # Arrange
    record = EmergencyRecord(started_at=LATER)

    # Act / Assert — time is a parameter, so nothing else catches this
    with pytest.raises(emergency.EmergencyError):
        record.resolve(ENTERED)


def test_a_timeline_entry_cannot_predate_the_emergency_it_belongs_to():
    # Arrange
    record = EmergencyRecord(started_at=LATER)

    # Act / Assert
    with pytest.raises(emergency.EmergencyError):
        record.record(EntryKind.OBSERVED, "seen on arrival", ENTERED)


def test_two_emergencies_in_one_visit_each_have_their_own_start_and_end():
    # Arrange — §5.7: the Emergency is re-entrant, and each entry is its own record
    first = EmergencyRecord(started_at=ENTERED)
    first.resolve(LATER)
    second = EmergencyRecord(started_at=LATER_STILL)

    # Act
    second.resolve(datetime(2026, 8, 28, 11, 15))

    # Assert
    assert first.ended_at == LATER
    assert second.started_at == LATER_STILL
    assert second.ended_at == datetime(2026, 8, 28, 11, 15)


def test_a_visit_with_no_emergency_at_all_passes_the_gate():
    # Act / Assert — the ordinary Visit, and the reason this is a guard not a flag
    assert emergency.check_all_resolved([]) is None


def test_a_visit_whose_emergencies_are_all_resolved_passes_the_gate():
    # Arrange
    record = EmergencyRecord(started_at=ENTERED)
    record.record(EntryKind.DONE, "ambulance called", ENTERED)
    record.resolve(LATER)

    # Act / Assert
    assert emergency.check_all_resolved([record]) is None


def test_an_emergency_that_ended_but_was_never_written_down_blocks_the_gate():
    # Arrange — the only way this gate fires in practice, and the reason it exists
    record = EmergencyRecord(started_at=ENTERED)
    record.resolve(LATER)

    # Act / Assert
    with pytest.raises(emergency.UnresolvedEmergency):
        emergency.check_all_resolved([record])


def test_an_unresolved_emergency_blocks_the_gate_and_says_when_it_started():
    # Arrange — one resolved, one still open; the open one is what matters
    resolved = EmergencyRecord(started_at=ENTERED)
    resolved.record(EntryKind.OBSERVED, "responsive again", ENTERED)
    resolved.resolve(LATER)
    open_record = EmergencyRecord(started_at=LATER_STILL)
    open_record.record(EntryKind.DONE, "ambulance called", LATER_STILL)


    # Act
    with pytest.raises(emergency.UnresolvedEmergency) as caught:
        emergency.check_all_resolved([resolved, open_record])

    # Assert — the Field Team has to be told which one, and it is 10:40's
    assert "10:40" in str(caught.value)


def test_a_timeline_entry_may_be_written_after_the_emergency_has_ended():
    # Arrange — ADR 0004: documentation is retrospective; the close forces it
    record = EmergencyRecord(started_at=ENTERED)
    record.resolve(LATER)

    # Act
    record.record(EntryKind.DONE, "ambulance called", ENTERED)

    # Assert — the late entry is exactly what resolves the record (§5.7)
    assert record.is_resolved is True
