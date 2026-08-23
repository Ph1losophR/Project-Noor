"""Property tests over generated expression trees (SSOT §8.4 invariants 6 and 9).

Arbitrary valid trees over the closed vocabulary — boolean composition of
numeric (literal), drug, allergy, condition, and age leaves — become rules whose
`requires` are derived from the tree itself, so the loader's own gates pass.
Whatever snapshot and requested actions hypothesis brings, every run stays
inside the closed record contract, and replaying one input serialises
byte-identically. Derandomized to match conftest's CI profile: no flaky draws.
"""

import json
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from noor.canon.models import MappingStatus
from noor.engine.evaluate import evaluate
from noor.engine.records import DegradedBecause, Outcome
from noor.engine.rules import (
    DrugScopeLevel,
    Expression,
    OnUnusable,
    Operator,
    Requirement,
    Severity,
    walk_expression,
)
from noor.engine.snapshot import (
    ActionKind,
    AllergySeverity,
    AllergyStatus,
    CulpritSubstance,
    RequestedAction,
    SnapshotMedication,
    VerificationStatus,
)
from tests.conftest import (
    make_allergy,
    make_canonical,
    make_context,
    make_entry,
    make_registry,
    make_release,
    make_rule,
    make_snapshot,
    make_then,
)

TEST_SETTINGS = settings(max_examples=30, deadline=None, derandomize=True)

FACTS = ("egfr", "potassium", "glucose")
CONCEPTS = ("type_2_diabetes", "hepatic_impairment")
INGREDIENTS = ("metformin", "insulin")

NUMERIC_OPS = (Operator.lt, Operator.le, Operator.gt, Operator.ge, Operator.eq, Operator.ne)
VALUES = st.decimals(
    min_value=Decimal("1"),
    max_value=Decimal("99"),
    places=1,
    allow_nan=False,
    allow_infinity=False,
)

numeric_leaves = st.tuples(st.sampled_from(NUMERIC_OPS), st.sampled_from(FACTS), VALUES).map(
    lambda choice: Expression(op=choice[0], fact=choice[1], literal=choice[2])
)
drug_leaves = st.builds(
    Expression,
    op=st.sampled_from((Operator.drug_active, Operator.drug_requested)),
    ingredient_id=st.sampled_from(INGREDIENTS),
)
allergy_leaves = st.builds(
    Expression,
    op=st.just(Operator.allergy),
    ingredient_id=st.sampled_from(INGREDIENTS),
    verification_status=st.none() | st.sampled_from(list(VerificationStatus)),
    severity=st.none() | st.sampled_from(list(AllergySeverity)),
)
condition_leaves = st.builds(
    Expression, op=st.just(Operator.condition), concept=st.sampled_from(CONCEPTS)
)
age_leaves = st.one_of(
    st.builds(
        Expression,
        op=st.just(Operator.age),
        minimum=st.integers(30, 80),
        maximum=st.none() | st.integers(81, 95),
    ),
    st.builds(
        Expression,
        op=st.just(Operator.age),
        minimum=st.none(),
        maximum=st.integers(31, 95),
    ),
)
leaves = st.one_of(numeric_leaves, drug_leaves, allergy_leaves, condition_leaves, age_leaves)


def _branch(children):
    ops = (
        (Operator.all, Operator.any, Operator.NOT)
        if len(children) == 1
        else (Operator.all, Operator.any)
    )
    return st.sampled_from(ops).map(lambda op: Expression(op=op, children=tuple(children)))


trees = st.recursive(
    leaves,
    lambda child: st.lists(child, min_size=1, max_size=3).flatmap(_branch),
    max_leaves=10,
)

rule_specs = st.lists(st.tuples(st.sampled_from(list(Severity)), trees), min_size=2, max_size=4)

MEDICATION_POOL = (
    SnapshotMedication(ingredient_id="metformin", mapping_status=MappingStatus.mapped),
    SnapshotMedication(ingredient_id="insulin", mapping_status=MappingStatus.mapped),
    SnapshotMedication(ingredient_id="insulin", mapping_status=MappingStatus.ambiguous),
)

snapshot_values = st.builds(
    make_snapshot,
    age_years=st.integers(30, 95),
    observations=st.lists(st.tuples(st.sampled_from(FACTS), VALUES), max_size=4).map(
        lambda specs: tuple(
            make_canonical(observable=fact, value=str(value)) for fact, value in specs
        )
    ),
    medications=st.lists(st.sampled_from(MEDICATION_POOL), max_size=3).map(tuple),
    allergies=st.lists(
        st.builds(
            make_allergy,
            culprit=st.builds(CulpritSubstance, ingredient_id=st.sampled_from(INGREDIENTS)),
            verification_status=st.sampled_from(list(VerificationStatus)),
            severity=st.sampled_from(list(AllergySeverity)),
        ),
        max_size=3,
    ).map(tuple),
    allergy_status=st.sampled_from(list(AllergyStatus)),
    conditions=st.sets(st.sampled_from(CONCEPTS)).map(frozenset),
)

requested_actions = st.lists(
    st.builds(
        RequestedAction,
        kind=st.sampled_from(list(ActionKind)),
        subject=st.sampled_from(INGREDIENTS),
    ),
    max_size=3,
).map(tuple)


def requirements_for(tree):
    """One gate-free requirement per compared fact, derived from the tree (§7.1)."""
    facts = {node.fact for node in walk_expression(tree) if node.op in NUMERIC_OPS}
    return tuple(
        Requirement(observable=fact, on_unusable=OnUnusable.indeterminate) for fact in sorted(facts)
    )


def rules_from(specs):
    """The generated release: one rule per spec, ids from position."""
    return tuple(
        make_rule(
            id=f"generated-{index}",
            version="1.0.0",
            severity=severity,
            requires=requirements_for(tree),
            monitors=(),
            when=tree,
            then=make_then(blocks=None),
            drug_scope_level=DrugScopeLevel.ingredient,
        )
        for index, (severity, tree) in enumerate(specs)
    )


def context_for(specs):
    registry = make_registry(
        *(make_entry(observable=fact, canonical_ucum="mmol/L") for fact in FACTS)
    )
    return make_context(release=make_release(rules=rules_from(specs)), registry=registry)


def serialised(records):
    return json.dumps([record.model_dump(mode="json") for record in records], sort_keys=True)


@TEST_SETTINGS
@given(specs=rule_specs, snapshot=snapshot_values, actions=requested_actions)
def test_generated_evaluations_never_escape_the_closed_record_contract(specs, snapshot, actions):
    # Arrange — arbitrary valid trees; requires derived so the loader passes
    context = context_for(specs)

    # Act
    records = evaluate(context, snapshot, actions)

    # Assert — the closed contract: one record per rule id, sorted by rule_id,
    # every vocabulary member inside its closed set, degradation exactly where
    # records.py's own validator says it may appear
    assert [record.rule_id for record in records] == sorted(rule.id for rule in rules_from(specs))
    assert len(records) == len(specs)
    for record in records:
        assert record.outcome in Outcome
        assert record.authored_severity in Severity
        assert record.effective_severity in Severity
        assert record.degraded_because is None or record.degraded_because in DegradedBecause


@TEST_SETTINGS
@given(specs=rule_specs, snapshot=snapshot_values, actions=requested_actions)
def test_replaying_the_same_generated_input_serialises_byte_identically(specs, snapshot, actions):
    # Arrange
    context = context_for(specs)

    # Act — invariant 6 / claim 45 over arbitrary input
    first = evaluate(context, snapshot, actions)
    second = evaluate(context, snapshot, actions)

    # Assert
    assert first == second
    assert serialised(first) == serialised(second)
