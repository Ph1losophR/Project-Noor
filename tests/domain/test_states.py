from datetime import datetime
from itertools import product

import pytest

from noor.domain import states
from noor.domain.states import (
    RECOMMENDATION_CAP,
    DataState,
    Datum,
    EscalationTier,
    Section,
    VisitState,
)
from noor.domain.states import VisitState as V

AS_OF = datetime(2026, 8, 28, 9, 30)


def test_a_visit_has_exactly_the_six_states_the_ssot_names():
    # Arrange / Act
    states = set(VisitState.__members__)

    # Assert
    assert states == {"SCHEDULED", "IN_PROGRESS", "EMERGENCY", "COMPLETED",
                      "CANCELLED", "ENDED_EARLY"}


def test_the_record_has_exactly_eight_sections_whose_integer_is_their_position():
    # Arrange / Act
    sections = list(Section.__members__)

    # Assert — the fixed order (§4.2)
    assert sections == [
        "VISIT_REASON", "CONCERNS_AND_INTERVAL_HISTORY", "MEDICATION_RECONCILIATION",
        "VITALS", "PHYSICAL_EXAMINATION", "SELF_CARE_CHECK", "CARE_PLAN", "NOTES",
    ]
    assert list(Section) == [1, 2, 3, 4, 5, 6, 7, 8]


def test_the_escalation_tiers_are_exactly_four_ordered_zero_to_three():
    # Arrange / Act
    tiers = set(EscalationTier.__members__)

    # Assert — ordered by time-to-action, never by severity (ADR 0001)
    assert tiers == {"TIER_0", "TIER_1", "TIER_2", "TIER_3"}
    assert list(EscalationTier) == [0, 1, 2, 3]


def test_the_recommendation_cap_is_three():
    # Arrange
    cap = RECOMMENDATION_CAP

    # Act / Assert — N3, §4.7. Welded on purpose (ADR 0007)
    assert cap == 3


def test_a_present_datum_carries_its_value_and_the_time_it_was_true():
    # Arrange / Act
    datum = Datum.present(7.4, as_of=AS_OF)

    # Assert
    assert (datum.state, datum.value, datum.as_of) == (DataState.PRESENT, 7.4, AS_OF)


def test_absent_and_unreachable_are_not_equal_to_each_other():
    # Arrange / Act
    established_none = Datum.absent()
    could_not_find_out = Datum.unreachable()

    # Assert
    assert established_none != could_not_find_out


def test_a_datum_refuses_to_be_used_as_a_truth_value():
    # Arrange
    datum = Datum.absent()

    # Act / Assert
    with pytest.raises(TypeError, match="three states"):
        bool(datum)


def test_a_present_datum_without_an_as_of_time_is_refused():
    # Act / Assert
    with pytest.raises(ValueError, match="as_of"):
        Datum.present(7.4, as_of=None)


def test_an_absent_datum_carrying_a_value_is_refused():
    # Act / Assert
    with pytest.raises(ValueError, match="carries no value"):
        Datum(state=DataState.ABSENT, value=7.4)


def test_only_a_present_datum_reports_is_present():
    # Arrange / Act
    states = [Datum.present(1, as_of=AS_OF).is_present,
              Datum.absent().is_present,
              Datum.unreachable().is_present]

    # Assert
    assert states == [True, False, False]


# The six-state machine (§5.1) — and the twenty-nine transitions it refuses.
# §5.1's table, written out by hand on purpose — deriving it from
# states.LEGAL_TRANSITIONS would make the test agree with any mistake the source made.
SEVEN = [
    (V.SCHEDULED, V.IN_PROGRESS),
    (V.SCHEDULED, V.CANCELLED),
    (V.IN_PROGRESS, V.COMPLETED),
    (V.IN_PROGRESS, V.ENDED_EARLY),
    (V.IN_PROGRESS, V.EMERGENCY),
    (V.EMERGENCY, V.IN_PROGRESS),
    (V.EMERGENCY, V.ENDED_EARLY),
]
TWENTY_NINE = [p for p in product(V, repeat=2) if p not in SEVEN]
TERMINALS = [V.COMPLETED, V.CANCELLED, V.ENDED_EARLY]


def test_the_state_machine_has_exactly_the_seven_transitions_the_ssot_lists():
    # Assert
    assert states.LEGAL_TRANSITIONS == frozenset(SEVEN)


def test_the_grid_is_thirty_six_pairs_of_which_twenty_nine_are_refusals():
    # Assert — pinned arithmetic, so a seventh state forces the grid to be redrawn
    assert len(SEVEN) + len(TWENTY_NINE) == 36
    assert len(TWENTY_NINE) == 29


@pytest.mark.parametrize(("source", "target"), SEVEN)
def test_a_legal_transition_is_permitted(source, target):
    # Act / Assert — check_transition returns None; it is a guard, not a predicate
    assert states.check_transition(source, target) is None


@pytest.mark.parametrize(("source", "target"), TWENTY_NINE)
def test_an_illegal_transition_is_refused(source, target):
    # Act / Assert
    with pytest.raises(states.IllegalTransition):
        states.check_transition(source, target)


@pytest.mark.parametrize("terminal", TERMINALS)
def test_a_terminal_visit_has_no_transition_out_of_it_at_all(terminal):
    # Assert — an Addendum is the only way a closed Visit changes (§5.9)
    assert {pair for pair in states.LEGAL_TRANSITIONS if pair[0] is terminal} == set()


def test_the_three_terminal_states_are_completed_cancelled_and_ended_early():
    # Assert
    assert states.TERMINAL == frozenset(TERMINALS)


def test_an_emergency_can_be_entered_a_second_time_in_the_same_visit():
    # Arrange — §5.7's re-entrant cycle, written as the sequence it is
    cycle = [(V.IN_PROGRESS, V.EMERGENCY), (V.EMERGENCY, V.IN_PROGRESS),
             (V.IN_PROGRESS, V.EMERGENCY), (V.EMERGENCY, V.IN_PROGRESS)]

    # Act
    refused = [pair for pair in cycle if pair not in states.LEGAL_TRANSITIONS]

    # Assert — naming the refused step is what makes this failure readable
    assert refused == []


def test_a_second_emergency_is_not_reached_by_staying_in_the_first():
    # Act / Assert — re-entry goes back through In Progress, so this pair is refused
    with pytest.raises(states.IllegalTransition):
        states.check_transition(V.EMERGENCY, V.EMERGENCY)


def test_a_refusal_names_the_state_it_was_in_and_the_one_it_refused():
    # Act
    with pytest.raises(states.IllegalTransition) as caught:
        states.check_transition(V.COMPLETED, V.IN_PROGRESS)

    # Assert — a refusal nobody can read is a refusal somebody works around
    assert "completed" in str(caught.value)
    assert "in_progress" in str(caught.value)
    assert caught.value.source is V.COMPLETED
    assert caught.value.target is V.IN_PROGRESS
