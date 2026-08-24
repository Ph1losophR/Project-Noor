"""§8.5 failure isolation: one raising rule neither silences nor blocks.

§8.4 invariant 11 and §12.6 claim 43, driven through `evaluate` with a real
raise: two conflicting goals of care make threshold resolution refuse (§8.2),
the affected rule records `evaluation_failed` carrying the exception TYPE NAME
only (§8.5), its presented severity is capped below a hard stop, and every
healthy neighbour still produces exactly its own record.
"""

from decimal import Decimal

import pytest

from noor.canon.models import MappingStatus
from noor.engine.evaluate import evaluate
from noor.engine.records import DegradedBecause, Outcome
from noor.engine.rules import Expression, Operator, Severity
from noor.engine.snapshot import ActionKind, RequestedAction, SnapshotMedication
from tests.conftest import (
    make_canonical,
    make_context,
    make_goal,
    make_release,
    make_requirement,
    make_rule,
    make_snapshot,
    make_then,
)

EGFR_REF = "metformin.egfr_absolute_contraindication"
CONFLICTED_ID = "metformin-egfr-contraindicated"


def conflicting_egfr_goals():
    """Two active, unexpired goals on one observable: resolution refuses (§8.2)."""
    return (
        make_goal(observable="egfr", value=Decimal("20"), unit="mL/min/{1.73_m2}"),
        make_goal(
            observable="egfr",
            value=Decimal("22"),
            unit="mL/min/{1.73_m2}",
            clinician_id="DR-9",
            reason="Second opinion, unresolved",
        ),
    )


def conflicted_snapshot(**overrides):
    """eGFR 25 with metformin on the list — and the conflicting goal pair."""
    fields = {
        "observations": (
            make_canonical(
                observable="egfr", value="25", context_flags=("ckd_chronicity_confirmed",)
            ),
        ),
        "medications": (
            SnapshotMedication(ingredient_id="metformin", mapping_status=MappingStatus.mapped),
        ),
        "goals_of_care": conflicting_egfr_goals(),
    }
    fields.update(overrides)
    return make_snapshot(**fields)


def conflicted_hard_stop(**overrides):
    """The default hard stop, which raises at threshold resolution."""
    fields = {"id": CONFLICTED_ID}
    fields.update(overrides)
    return make_rule(**fields)


def potassium_neighbour():
    """A passive literal comparison over potassium, far from the conflict."""
    return make_rule(
        id="hyperkalemia-note",
        severity=Severity.passive_task,
        requires=(
            make_requirement(observable="potassium", required_context=(), renal_metric=None),
        ),
        monitors=(),
        when=Expression(op=Operator.gt, fact="potassium", literal=Decimal("6.0")),
        then=make_then(blocks=None),
    )


def start_guard_neighbour():
    """An interruptive drug_requested rule needing no data at all."""
    return make_rule(
        id="metformin-start-guard",
        severity=Severity.interruptive_review,
        requires=(),
        monitors=(),
        when=Expression(op=Operator.drug_requested, ingredient_id="metformin"),
        then=make_then(blocks=None),
    )


def test_one_raising_rule_records_evaluation_failed_without_silencing_the_rest():
    # Arrange — the conflicted hard stop shares a release with two healthy
    # neighbours; the snapshot satisfies every requirement they read
    snapshot = conflicted_snapshot(
        observations=(
            make_canonical(
                observable="egfr", value="25", context_flags=("ckd_chronicity_confirmed",)
            ),
            make_canonical(observable="potassium", value="6.5"),
        ),
    )
    actions = (RequestedAction(kind=ActionKind.medication_start, subject="metformin"),)
    context = make_context(
        release=make_release(
            rules=(conflicted_hard_stop(), potassium_neighbour(), start_guard_neighbour())
        )
    )

    # Act
    records = evaluate(context, snapshot, actions)
    by_id = {record.rule_id: record for record in records}

    # Assert — claim 43: N rules considered, N records out; only the raiser failed
    assert len(records) == 3
    failed = by_id[CONFLICTED_ID]
    assert failed.outcome is Outcome.evaluation_failed
    assert failed.failure_reason == "AmbiguousGoalOfCareError"
    assert failed.degraded_because is DegradedBecause.rule_raised
    assert failed.requirement_verdicts == ()
    potassium = by_id["hyperkalemia-note"]
    assert potassium.outcome is Outcome.triggered
    assert potassium.authored_severity is Severity.passive_task
    assert potassium.effective_severity is Severity.passive_task
    assert potassium.degraded_because is None
    guard = by_id["metformin-start-guard"]
    assert guard.outcome is Outcome.triggered
    assert guard.effective_severity is Severity.interruptive_review
    assert guard.degraded_because is None


@pytest.mark.parametrize(
    ("authored", "presented"),
    [
        (Severity.stop_and_review, Severity.interruptive_review),
        (Severity.passive_task, Severity.passive_task),
    ],
)
def test_a_failed_rule_degrades_to_the_capped_severity_and_never_blocks(authored, presented):
    # Arrange — the same goal conflict, authored at each severity: a hard stop
    # must come back below blocking, a passive task stays passive (§8.3/§8.5)
    rule = conflicted_hard_stop(
        id="conflicted-rule",
        severity=authored,
        when=Expression(op=Operator.lt, fact="egfr", threshold_ref=EGFR_REF),
        then=make_then(blocks=None),
    )
    context = make_context(release=make_release(rules=(rule,)))

    # Act
    (record,) = evaluate(context, conflicted_snapshot(), ())

    # Assert — the exact presented values, not merely "did not block"
    assert record.outcome is Outcome.evaluation_failed
    assert record.authored_severity is authored
    assert record.effective_severity is presented
    assert record.degraded_because is DegradedBecause.rule_raised
    assert record.failure_reason == "AmbiguousGoalOfCareError"
    assert record.requirement_verdicts == ()


def test_the_failure_reason_carries_the_exception_type_name_only():
    # Arrange — §8.5: the type name only; the message names no patient either,
    # but the record must not carry even the generic wording
    context = make_context(release=make_release(rules=(conflicted_hard_stop(),)))

    # Act
    (record,) = evaluate(context, conflicted_snapshot(), ())

    # Assert — exact type name, then prove no message text rode along
    assert record.outcome is Outcome.evaluation_failed
    assert record.failure_reason == "AmbiguousGoalOfCareError"
    leaked = [
        fragment
        for fragment in ("two or more", "active goals", "resolve", "conflict", "apply")
        if fragment in record.failure_reason.lower()
    ]
    assert leaked == []
