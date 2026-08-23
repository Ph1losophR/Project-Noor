"""The outcome vocabulary and the evaluation-record contract (SSOT §8.2).

The record is the unit the rest of the system builds on — the pinned review,
the obligation ledger, zero-firing surveillance — so its shape is closed here:
exactly six outcomes, exactly three degradation causes (§8.3), an eight-reason
verdict vocabulary, no run-header fields (§8.4 invariant 6), a failure reason
that exists exactly for `evaluation_failed` (§8.5), and one shared severity cap
so degradation can never leave a hard stop blocking.
"""

import pytest
from pydantic import ValidationError

from noor.engine.content import Pins
from noor.engine.records import (
    DegradedBecause,
    EvaluationRecord,
    Outcome,
    RequirementReason,
    RequirementVerdict,
    RequirementVerdictValue,
    cap_below_stop_and_review,
)
from noor.engine.rules import Severity
from tests.conftest import make_pins

# The per-outcome extras that make each of §8.2's six outcomes well-formed:
# indeterminate degrades as requirements_unmet, evaluation_failed as rule_raised
# carrying the exception type name only (§8.5), and both are capped below the
# authored stop_and_review.
WELL_FORMED_BY_OUTCOME: dict[Outcome, dict[str, object]] = {
    Outcome.triggered: {},
    Outcome.not_triggered: {},
    Outcome.indeterminate: {
        "degraded_because": DegradedBecause.requirements_unmet,
        "effective_severity": Severity.interruptive_review,
    },
    Outcome.out_of_scope: {},
    Outcome.suppressed_by_governed_policy: {},
    Outcome.evaluation_failed: {
        "degraded_because": DegradedBecause.rule_raised,
        "failure_reason": "AmbiguousGoalOfCareError",
        "effective_severity": Severity.interruptive_review,
        "requirement_verdicts": (),
    },
}

# The outcomes whose shape forbids requirement verdicts: suppression stops
# before requirements are read, scope excludes before them, and a rule that
# raised has nothing truthful to say about its verdicts (§8.5).
VERDICTLESS_OUTCOMES = (
    Outcome.out_of_scope,
    Outcome.suppressed_by_governed_policy,
    Outcome.evaluation_failed,
)


def make_verdict(**overrides):
    """The §8.2 example verdict: egfr unusable because stale; override anything."""
    fields = {
        "observable": "egfr",
        "verdict": RequirementVerdictValue.unusable,
        "reason": RequirementReason.stale,
        "latest_age_days": None,
    }
    fields.update(overrides)
    return RequirementVerdict(**fields)


def make_record(**overrides):
    """A triggered metformin hard-stop record; override anything."""
    fields = {
        "rule_id": "metformin-egfr-contraindicated",
        "rule_version": "1.0.0",
        "outcome": Outcome.triggered,
        "authored_severity": Severity.stop_and_review,
        "effective_severity": Severity.stop_and_review,
        "degraded_because": None,
        "failure_reason": None,
        "requirement_verdicts": (),
        "pins": make_pins(),
    }
    fields.update(overrides)
    return EvaluationRecord(**fields)


def test_the_outcome_vocabulary_holds_exactly_the_six_ssot_members():
    # Arrange / Act / Assert — §8.2's outcome column, closed like every
    # vocabulary inside the device boundary
    assert tuple(outcome.value for outcome in Outcome) == (
        "triggered",
        "not_triggered",
        "indeterminate",
        "out_of_scope",
        "suppressed_by_governed_policy",
        "evaluation_failed",
    )


def test_the_degradation_vocabulary_holds_exactly_the_three_ssot_causes():
    # Arrange / Act / Assert — §8.3's three causes, no fourth
    assert tuple(cause.value for cause in DegradedBecause) == (
        "requirements_unmet",
        "evidence_grade",
        "rule_raised",
    )


def test_the_requirement_reason_vocabulary_holds_exactly_the_eight_ssot_members():
    # Arrange / Act / Assert — §8.2's closed machine vocabulary for verdicts
    assert tuple(reason.value for reason in RequirementReason) == (
        "no_result",
        "quality_below_minimum",
        "stale",
        "wrong_source",
        "missing_context",
        "withdrawn_source",
        "ambiguous_mapping",
        "wrong_observable",
    )


def test_the_verdict_value_vocabulary_holds_usable_and_unusable_only():
    # Arrange / Act / Assert — §5.3's closed usable/unusable pair
    assert tuple(value.value for value in RequirementVerdictValue) == (
        "usable",
        "unusable",
    )


@pytest.mark.parametrize("outcome", list(Outcome))
def test_a_record_is_constructible_for_every_outcome(outcome):
    # Arrange / Act
    record = make_record(outcome=outcome, **WELL_FORMED_BY_OUTCOME[outcome])

    # Assert — every rule considered writes a record; none is excluded (§8.2)
    assert record.outcome is outcome
    assert record.rule_id == "metformin-egfr-contraindicated"
    assert record.rule_version == "1.0.0"


def test_a_record_carries_its_pins_through():
    # Arrange
    pins = make_pins(snapshot_id="SNAP-1")

    # Act
    record = make_record(pins=pins)

    # Assert — the pins are copied onto every record (§8.2), snapshot stamped
    assert isinstance(record.pins, Pins)
    assert record.pins == pins
    assert record.pins.snapshot_id == "SNAP-1"


@pytest.mark.parametrize(
    ("cause", "outcome"),
    [
        (DegradedBecause.requirements_unmet, Outcome.indeterminate),
        (DegradedBecause.evidence_grade, Outcome.triggered),
        (DegradedBecause.rule_raised, Outcome.evaluation_failed),
    ],
)
def test_each_degradation_cause_is_constructible_on_its_own_outcome(cause, outcome):
    # Arrange — §8.3 pairs each cause with exactly one outcome; a triggered
    # finding with a graded evidence base presents the capped severity
    overrides = dict(WELL_FORMED_BY_OUTCOME[outcome])
    if cause is not None:
        overrides["degraded_because"] = cause
    if cause is DegradedBecause.evidence_grade:
        overrides["effective_severity"] = Severity.interruptive_review

    # Act
    record = make_record(outcome=outcome, **overrides)

    # Assert
    assert record.degraded_because is cause


@pytest.mark.parametrize(
    ("authored", "expected"),
    [
        (Severity.stop_and_review, Severity.interruptive_review),
        (Severity.interruptive_review, Severity.interruptive_review),
        (Severity.passive_task, Severity.passive_task),
    ],
)
def test_cap_below_stop_and_review_demotes_only_a_hard_stop(authored, expected):
    # Arrange / Act / Assert — design §7.1: one shared cap function, applied once;
    # it never raises passive_task to interruptive_review and it is idempotent
    assert cap_below_stop_and_review(authored) is expected
    assert cap_below_stop_and_review(cap_below_stop_and_review(authored)) is expected


@pytest.mark.parametrize(
    "degraded_context",
    [
        {"outcome": Outcome.indeterminate, "degraded_because": DegradedBecause.requirements_unmet},
        {"outcome": Outcome.triggered, "degraded_because": DegradedBecause.evidence_grade},
        {
            "outcome": Outcome.evaluation_failed,
            "degraded_because": DegradedBecause.rule_raised,
            "failure_reason": "AmbiguousGoalOfCareError",
        },
    ],
)
@pytest.mark.parametrize("authored", list(Severity))
def test_a_degraded_or_failed_record_presents_the_capped_severity(
    degraded_context,
    authored,
):
    # Arrange — all three §8.3 causes route through the same single cap
    context = {**degraded_context, "authored_severity": authored}

    # Act
    record = make_record(**context, effective_severity=cap_below_stop_and_review(authored))

    # Assert — never a blocking action from a degraded or failed record
    assert record.effective_severity is cap_below_stop_and_review(authored)


@pytest.mark.parametrize(
    "degraded_context",
    [
        {"outcome": Outcome.indeterminate, "degraded_because": DegradedBecause.requirements_unmet},
        {"outcome": Outcome.triggered, "degraded_because": DegradedBecause.evidence_grade},
        {
            "outcome": Outcome.evaluation_failed,
            "degraded_because": DegradedBecause.rule_raised,
            "failure_reason": "AmbiguousGoalOfCareError",
        },
    ],
)
def test_a_degraded_or_failed_hard_stop_presented_uncapped_is_refused(degraded_context):
    # Arrange / Act / Assert — §8.3: authors cannot opt out of the cap
    with pytest.raises(ValidationError):
        make_record(**degraded_context, effective_severity=Severity.stop_and_review)


def test_an_evaluation_failed_record_requires_a_failure_reason():
    # Arrange / Act / Assert — §8.5: the exception type name is what the record carries
    with pytest.raises(ValidationError):
        make_record(
            outcome=Outcome.evaluation_failed,
            degraded_because=DegradedBecause.rule_raised,
            effective_severity=Severity.interruptive_review,
            failure_reason=None,
        )


@pytest.mark.parametrize("outcome", [o for o in Outcome if o is not Outcome.evaluation_failed])
def test_a_failure_reason_on_any_other_outcome_is_refused(outcome):
    # Arrange / Act / Assert — §8.5: failure_reason is None for every other outcome
    with pytest.raises(ValidationError):
        make_record(
            outcome=outcome,
            **WELL_FORMED_BY_OUTCOME[outcome],
            failure_reason="AmbiguousGoalOfCareError",
        )


@pytest.mark.parametrize(
    "outcome",
    [Outcome.indeterminate, Outcome.evaluation_failed],
)
def test_an_indeterminate_or_failed_record_always_names_why_it_degraded(outcome):
    # Arrange / Act / Assert — §8.3: the record says which of the three causes happened
    with pytest.raises(ValidationError):
        make_record(
            outcome=outcome,
            **{**WELL_FORMED_BY_OUTCOME[outcome], "degraded_because": None},
        )


@pytest.mark.parametrize(
    "outcome",
    [Outcome.not_triggered, Outcome.out_of_scope, Outcome.suppressed_by_governed_policy],
)
def test_an_outcome_that_did_not_degrade_carries_no_degradation_cause(outcome):
    # Arrange / Act / Assert — degradation is exactly §8.3's three causes; nothing
    # else may wear it
    with pytest.raises(ValidationError):
        make_record(outcome=outcome, degraded_because=DegradedBecause.evidence_grade)


@pytest.mark.parametrize(
    "cause",
    [DegradedBecause.requirements_unmet, DegradedBecause.rule_raised],
)
def test_a_triggered_record_refuses_a_cause_that_belongs_to_another_outcome(cause):
    # Arrange / Act / Assert — evidence grade is the only cause that can sit on a
    # triggered finding (§8.3); unmet requirements degrade to indeterminate and a
    # raised rule fails
    with pytest.raises(ValidationError):
        make_record(outcome=Outcome.triggered, degraded_because=cause)


@pytest.mark.parametrize("outcome", VERDICTLESS_OUTCOMES)
def test_an_outcome_that_never_read_requirements_carries_no_verdicts(outcome):
    # Arrange — suppression stops before requirements, scope excludes before them,
    # and a rule that raised has nothing truthful to say about its verdicts (§8.5)
    verdict = make_verdict()

    # Act / Assert
    with pytest.raises(ValidationError):
        make_record(
            outcome=outcome,
            **{**WELL_FORMED_BY_OUTCOME[outcome], "requirement_verdicts": (verdict,)},
        )


@pytest.mark.parametrize(
    "outcome",
    [Outcome.triggered, Outcome.not_triggered, Outcome.indeterminate],
)
def test_an_outcome_that_reached_requirements_may_carry_verdicts(outcome):
    # Arrange
    verdicts = (
        make_verdict(latest_age_days=214),
        make_verdict(
            observable="systolic_bp",
            verdict=RequirementVerdictValue.usable,
            reason=RequirementReason.no_result,
        ),
    )

    # Act
    record = make_record(
        outcome=outcome,
        **{**WELL_FORMED_BY_OUTCOME[outcome], "requirement_verdicts": verdicts},
    )

    # Assert
    assert record.requirement_verdicts == verdicts


def test_a_verdict_requires_a_reason():
    # Arrange / Act / Assert — the machine reason is stable and is what
    # comparisons and surveillance use (§8.2); it is never absent
    with pytest.raises(ValidationError):
        make_verdict(reason=None)


def test_a_verdict_refuses_a_reason_outside_the_closed_vocabulary():
    # Arrange / Act / Assert — closed machine vocabulary, not free text (§8.2)
    with pytest.raises(ValidationError):
        make_verdict(reason="lab_feed_down")


def test_a_usable_verdict_still_carries_a_reason_without_a_linking_constraint():
    # Arrange / Act — reason is required on every verdict and is not constrained
    # against the verdict value
    verdict = make_verdict(verdict=RequirementVerdictValue.usable, reason=RequirementReason.stale)

    # Assert
    assert verdict.verdict is RequirementVerdictValue.usable
    assert verdict.reason is RequirementReason.stale


def test_latest_age_days_defaults_to_absent_and_can_be_set():
    # Arrange / Act
    bare = make_verdict()
    stale = make_verdict(latest_age_days=214)

    # Assert — §8.2's example carries the age of the finding it found stale
    assert bare.latest_age_days is None
    assert stale.latest_age_days == 214


def test_records_are_frozen():
    # Arrange
    record = make_record()
    verdict = make_verdict()

    # Act / Assert — written once, never overwritten (§8.2); nested too
    with pytest.raises(ValidationError):
        record.outcome = Outcome.not_triggered
    with pytest.raises(ValidationError):
        verdict.reason = RequirementReason.wrong_source


def test_two_identical_records_compare_equal():
    # Arrange / Act
    first = make_record(requirement_verdicts=(make_verdict(latest_age_days=214),))
    second = make_record(requirement_verdicts=(make_verdict(latest_age_days=214),))

    # Assert — identical input ⇒ identical records (§8.4 invariant 6)
    assert first == second


def test_the_record_holds_no_run_header_fields():
    # Arrange / Act / Assert — correlation_id, latency_ms, and trigger belong to
    # app/'s run header, excluded from the per-rule record by construction (§8.2);
    # asserted by field-set equality so widening fails here rather than passing
    assert set(EvaluationRecord.model_fields) == {
        "rule_id",
        "rule_version",
        "outcome",
        "authored_severity",
        "effective_severity",
        "degraded_because",
        "failure_reason",
        "requirement_verdicts",
        "pins",
    }
    assert "correlation_id" not in EvaluationRecord.model_fields
    assert "latency_ms" not in EvaluationRecord.model_fields
    assert "trigger" not in EvaluationRecord.model_fields
