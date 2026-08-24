"""The engine's cross-run invariants as executable claims (SSOT §8.4).

Invariant 5: the rules' order in a release never reaches the output. Invariant
6 (claim 45): identical snapshot, requested actions, and release serialise
byte-identically — and varying only the requested actions moves exactly the
`drug_requested` rule's record, which is why actions are part of the input.
Invariant 7: no rule reads another's output, so alone and in batch a rule
yields the same record. Comparisons run on the JSON serialisation of the
immutable records, per §14 step 4.
"""

import json
from decimal import Decimal

from noor.canon.models import MappingStatus
from noor.engine.evaluate import evaluate
from noor.engine.records import Outcome
from noor.engine.rules import Expression, Operator, Severity
from noor.engine.snapshot import ActionKind, RequestedAction, SnapshotMedication
from tests.conftest import (
    make_canonical,
    make_context,
    make_release,
    make_requirement,
    make_rule,
    make_snapshot,
    make_then,
)

EGFR_REF = "metformin.egfr_absolute_contraindication"
START_METFORMIN = (RequestedAction(kind=ActionKind.medication_start, subject="metformin"),)


def hard_stop():
    """The metformin hard stop: triggered by this snapshot's eGFR and list."""
    return make_rule()


def potassium_note():
    """A passive literal comparison over potassium."""
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


def start_guard():
    """An interruptive drug_requested rule reading only the planned actions."""
    return make_rule(
        id="metformin-start-guard",
        severity=Severity.interruptive_review,
        requires=(),
        monitors=(),
        when=Expression(op=Operator.drug_requested, ingredient_id="metformin"),
        then=make_then(blocks=None),
    )


def firing_snapshot():
    """eGFR 25, potassium 6.5, metformin active — all three rules fire."""
    return make_snapshot(
        observations=(
            make_canonical(
                observable="egfr", value="25", context_flags=("ckd_chronicity_confirmed",)
            ),
            make_canonical(observable="potassium", value="6.5"),
        ),
        medications=(
            SnapshotMedication(ingredient_id="metformin", mapping_status=MappingStatus.mapped),
        ),
    )


def serialised(records):
    """The byte-level view of a run: key-sorted JSON of every record (§8.4)."""
    return json.dumps([record.model_dump(mode="json") for record in records], sort_keys=True)


def test_evaluation_order_never_changes_the_records_or_their_bytes():
    # Arrange — invariant 5: one set of rules, two orders in two releases
    rules = (hard_stop(), potassium_note(), start_guard())
    reordered = (rules[2], rules[0], rules[1])
    snapshot = firing_snapshot()

    # Act
    first = evaluate(make_context(release=make_release(rules=rules)), snapshot, START_METFORMIN)
    second = evaluate(
        make_context(release=make_release(rules=reordered)), snapshot, START_METFORMIN
    )

    # Assert — same records in the same order, down to the bytes
    assert first == second
    assert serialised(first) == serialised(second)


def test_the_whole_input_replayed_serialises_byte_identically():
    # Arrange / Act — invariant 6, claim 45: same context, snapshot, and
    # requested actions evaluated twice
    context = make_context(
        release=make_release(rules=(hard_stop(), potassium_note(), start_guard()))
    )
    snapshot = firing_snapshot()
    first = evaluate(context, snapshot, START_METFORMIN)
    second = evaluate(context, snapshot, START_METFORMIN)

    # Assert
    assert first == second
    assert serialised(first) == serialised(second)


def test_varying_only_requested_actions_moves_exactly_the_drug_requested_record():
    # Arrange — invariant 6's negative half: actions are part of the input, and
    # the only rule that reads them is the drug_requested one (§8.4 amendment 2)
    context = make_context(
        release=make_release(rules=(hard_stop(), potassium_note(), start_guard()))
    )
    snapshot = firing_snapshot()

    # Act — identical inputs except requested_actions
    without_actions = evaluate(context, snapshot, ())
    with_actions = evaluate(context, snapshot, START_METFORMIN)

    # Assert — exactly one differing record, and it is that rule's
    assert [
        before.rule_id
        for before, after in zip(without_actions, with_actions, strict=True)
        if before != after
    ] == ["metformin-start-guard"]
    by_id_without = {record.rule_id: record for record in without_actions}
    assert by_id_without["metformin-start-guard"].outcome is Outcome.not_triggered
    by_id_with = {record.rule_id: record for record in with_actions}
    assert by_id_with["metformin-start-guard"].outcome is Outcome.triggered


def test_a_rule_alone_yields_the_record_it_yields_in_the_batch():
    # Arrange — invariant 7: no rule reads another rule's output
    rules = (hard_stop(), potassium_note(), start_guard())
    snapshot = firing_snapshot()
    batch = {
        record.rule_id: record
        for record in evaluate(
            make_context(release=make_release(rules=rules)), snapshot, START_METFORMIN
        )
    }

    # Act / Assert — each rule soloed in its own single-rule release
    for rule in rules:
        (alone,) = evaluate(
            make_context(release=make_release(rules=(rule,))), snapshot, START_METFORMIN
        )
        assert alone == batch[rule.id]
