"""What Noor produces, and what a Field Team does with it (§4.5, N2, N4, N5)."""
from datetime import datetime

import pytest

from noor.domain import opinions
from noor.domain.opinions import Disposition, Finding, Outcome, OverrideLevel, Recommendation
from noor.domain.records import OTHER, Reason
from noor.domain.states import EscalationTier

AT = datetime(2026, 8, 28, 11, 30)
REC = Recommendation(
    id="check-potassium",
    text="Take a potassium and creatinine sample within two weeks",
    tier=EscalationTier.TIER_1,
    executor="Nurse",
    provenance="ace-inhibitor-monitoring, surveillance-intervals.md v0.1",
    strength="local service policy",
)


def test_a_finding_is_an_observation_and_carries_no_tier():
    # Act
    finding = Finding(id="hba1c-overdue", text="No HbA1c recorded in eighteen months")

    # Assert — a Finding that acquired a tier would be a Recommendation (CONTEXT.md)
    assert not hasattr(finding, "tier")


def test_a_recommendation_carries_exactly_one_escalation_tier():
    # Assert
    assert REC.tier is EscalationTier.TIER_1


def test_a_recommendation_with_no_named_executor_is_refused():
    # Act / Assert — N2 asks whether the Executor can act; no field, no question
    with pytest.raises(opinions.OpinionError):
        Recommendation(id="x", text="do it", tier=EscalationTier.TIER_1,
                       executor="", provenance="rule-x", strength="policy")


def test_a_recommendation_with_no_provenance_is_refused():
    # Act / Assert — N5: automation bias at RR 1.26 is what provenance is for
    with pytest.raises(opinions.OpinionError):
        Recommendation(id="x", text="do it", tier=EscalationTier.TIER_1,
                       executor="Nurse", provenance="", strength="policy")


def test_accepting_a_recommendation_needs_no_reason():
    # Act
    accepted = Disposition(REC.id, Outcome.ACCEPTED, by="Dr Salma", at=AT)

    # Assert
    assert (accepted.level, accepted.reason) == (None, None)


def test_the_two_override_levels_separate_a_wrong_rule_from_an_impossible_one():
    # Assert — §5.10's two levels; the split is fix-the-rule vs fix-the-supply-chain
    assert [level.value for level in OverrideLevel] == ["rule_wrong_here", "could_not_act"]


def test_an_override_carries_its_level_and_its_row():
    # Act
    overridden = Disposition(REC.id, Outcome.OVERRIDDEN, by="Dr Salma", at=AT,
                             level=OverrideLevel.COULD_NOT_ACT,
                             reason=Reason("no-supply"))

    # Assert — override reasons are engine data, not prose (N4)
    assert (overridden.level, overridden.reason) == (
        OverrideLevel.COULD_NOT_ACT, Reason("no-supply"))


def test_an_override_with_no_reason_at_all_is_refused():
    # Act / Assert
    with pytest.raises(opinions.OpinionError):
        Disposition(REC.id, Outcome.OVERRIDDEN, by="Dr Salma", at=AT,
                    level=OverrideLevel.RULE_WRONG_HERE)


def test_an_accepted_recommendation_carrying_an_override_reason_is_refused():
    # Act / Assert
    with pytest.raises(opinions.OpinionError):
        Disposition(REC.id, Outcome.ACCEPTED, by="Dr Salma", at=AT,
                    level=OverrideLevel.RULE_WRONG_HERE, reason=Reason("already-addressed"))


def test_an_override_on_the_other_row_needs_its_free_text():
    # Act / Assert — §5.10's Other rate is a metric, and blank text tells it nothing
    with pytest.raises(opinions.OpinionError):
        Disposition(REC.id, Outcome.OVERRIDDEN, by="Dr Salma", at=AT,
                    level=OverrideLevel.COULD_NOT_ACT, reason=Reason(OTHER))


def test_a_disposition_names_the_individual_who_made_the_decision():
    # Act / Assert — §5.13: observations belong to the Field Team, decisions to a person
    with pytest.raises(opinions.OpinionError):
        Disposition(REC.id, Outcome.ACCEPTED, by="", at=AT)


def test_a_visit_that_showed_no_recommendation_at_all_passes_the_gate():
    # Act / Assert — the Golden Case's other half (§4.1)
    assert opinions.check_all_dispositioned([], []) is None


def test_an_undispositioned_recommendation_blocks_the_gate_and_is_named():
    # Act
    with pytest.raises(opinions.Undispositioned) as caught:
        opinions.check_all_dispositioned([REC], [])

    # Assert
    assert "check-potassium" in str(caught.value)


def test_a_visit_whose_every_recommendation_was_overridden_still_passes_the_gate():
    # Arrange — N4: an override never blocks anything
    overridden = Disposition(REC.id, Outcome.OVERRIDDEN, by="Dr Salma", at=AT,
                             level=OverrideLevel.RULE_WRONG_HERE,
                             reason=Reason("already-addressed"))

    # Act / Assert
    assert opinions.check_all_dispositioned([REC], [overridden]) is None


def test_a_disposition_for_a_recommendation_that_was_never_shown_is_refused():
    # Arrange
    stray = Disposition("some-other-id", Outcome.ACCEPTED, by="Dr Salma", at=AT)

    # Act / Assert
    with pytest.raises(opinions.OpinionError):
        opinions.check_all_dispositioned([REC], [stray])


def test_a_recommendation_with_no_strength_is_refused():
    # Act / Assert — N5: strength rides beside provenance, against automation bias
    with pytest.raises(opinions.OpinionError):
        Recommendation(id="x", text="do it", tier=EscalationTier.TIER_1,
                       executor="Nurse", provenance="rule-x", strength="")


@pytest.mark.parametrize(
    ("level", "reason"),
    [(None, None), (None, Reason("no-supply"))],
)
def test_an_override_needs_its_level_and_its_row_together(level, reason):
    # Act / Assert — an override carries both (§5.10); either alone is refused
    with pytest.raises(opinions.OpinionError):
        Disposition(REC.id, Outcome.OVERRIDDEN, by="Dr Salma", at=AT,
                    level=level, reason=reason)


def test_an_override_on_the_other_row_with_its_free_text_is_accepted():
    # Act
    overridden = Disposition(REC.id, Outcome.OVERRIDDEN, by="Dr Salma", at=AT,
                             level=OverrideLevel.COULD_NOT_ACT,
                             reason=Reason(OTHER, "household refused entry"))

    # Assert
    assert overridden.reason.free_text == "household refused entry"
