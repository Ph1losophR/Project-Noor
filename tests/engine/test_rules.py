"""The closed expression tree (§4.3.1) and the §7.1 rule contract.

Every refusal here is a §10.4 gate landing at load time: the operator vocabulary
is closed (§4.3), a block belongs to a hard stop alone (gate 6), unusable input
is never silenced under a hard stop (gate 10), encounter and trigger state never
enter a requirement (gate 11), a drug reference names its scope level (gate 14),
and every observable a numeric leaf compares is declared in `requires` (§7.1).
"""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.engine.rules import (
    DrugScopeLevel,
    Expression,
    OnUnusable,
    Operator,
    OrderBlock,
    ReleaseStatus,
    Scope,
    Severity,
)
from noor.engine.snapshot import AllergySeverity, ReactionType, VerificationStatus
from tests.conftest import make_governance, make_requirement, make_rule, make_then


@pytest.mark.parametrize(
    ("vocabulary", "members"),
    [
        (
            Operator,
            (
                "all",
                "any",
                "not",
                "lt",
                "le",
                "gt",
                "ge",
                "eq",
                "ne",
                "drug_active",
                "drug_requested",
                "allergy",
                "condition",
                "age",
            ),
        ),
        (
            ReleaseStatus,
            (
                "draft",
                "technical_validation",
                "clinical_review",
                "approved",
                "scheduled",
                "active",
                "retired",
            ),
        ),
        (Severity, ("stop_and_review", "interruptive_review", "passive_task")),
        (
            DrugScopeLevel,
            ("ingredient", "ingredient_route", "product", "atc_class", "curated_set"),
        ),
        (OnUnusable, ("silent", "indeterminate")),
    ],
)
def test_the_closed_vocabularies_hold_exactly_the_ssot_members(vocabulary, members):
    # Arrange / Act / Assert — growing a vocabulary edits the enum, a reviewed
    # change to the device, never an author's private extension (§4.3)
    assert tuple(member.value for member in vocabulary) == members


def test_all_and_any_compose_child_expressions():
    # Arrange
    low_egfr = Expression(op=Operator.lt, fact="egfr", literal=Decimal("30"))
    on_dialysis = Expression(op=Operator.condition, concept="on_dialysis")

    # Act
    conjunction = Expression(op=Operator.all, children=(low_egfr, on_dialysis))
    disjunction = Expression(op=Operator.any, children=(low_egfr, on_dialysis))

    # Assert
    assert conjunction.children == (low_egfr, on_dialysis)
    assert disjunction.children == (low_egfr, on_dialysis)


def test_negation_carries_exactly_one_child():
    # Arrange
    pregnant = Expression(op=Operator.condition, concept="pregnant")

    # Act
    negation = Expression(op=Operator.NOT, children=(pregnant,))

    # Assert
    assert negation.children == (pregnant,)


@pytest.mark.parametrize(
    ("operator", "source"),
    [
        (Operator.lt, {"literal": Decimal("7.0")}),
        (Operator.le, {"literal": Decimal("7.0")}),
        (Operator.gt, {"threshold_ref": "bp.systolic_target"}),
        (Operator.ge, {"threshold_ref": "bp.systolic_target"}),
        (Operator.eq, {"literal": Decimal("1")}),
        (Operator.ne, {"threshold_ref": "hba1c.ngsp_target"}),
    ],
)
def test_each_numeric_comparison_names_a_fact_and_one_source(operator, source):
    # Arrange
    payload = {"fact": "hba1c_ngsp", **source}

    # Act
    leaf = Expression(op=operator, **payload)

    # Assert
    assert leaf.fact == "hba1c_ngsp"


def test_a_numeric_leaf_cannot_carry_both_comparison_sources():
    # Arrange / Act / Assert — a literal or a threshold_ref, never both (§4.3.1)
    with pytest.raises(ValidationError):
        Expression(
            op=Operator.lt,
            fact="egfr",
            literal=Decimal("30"),
            threshold_ref="metformin.egfr_absolute_contraindication",
        )


def test_a_numeric_leaf_must_carry_a_comparison_source():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        Expression(op=Operator.lt, fact="egfr")


def test_a_numeric_leaf_must_name_the_observable_it_compares():
    # Arrange / Act / Assert — a threshold with no fact compares nothing
    with pytest.raises(ValidationError):
        Expression(op=Operator.lt, literal=Decimal("30"))


def test_an_unknown_operator_is_refused_at_load():
    # Arrange / Act / Assert — §4.3: the vocabulary is a closed enum, so Pydantic
    # refuses an unrecognised operator before §10.4 gate 12 ever sees a merge
    with pytest.raises(ValidationError):
        Expression(op="similar_to", fact="egfr", literal=Decimal("30"))


def test_an_unknown_expression_field_is_refused_at_load():
    # Arrange / Act / Assert — §4.3.1: no open dictionary escape hatch
    with pytest.raises(ValidationError):
        Expression(op=Operator.condition, concept="on_dialysis", free_text="chat")


@pytest.mark.parametrize(
    ("operator", "foreign_field"),
    [
        (Operator.condition, "fact"),
        (Operator.drug_active, "concept"),
        (Operator.allergy, "literal"),
        (Operator.age, "ingredient_id"),
        (Operator.lt, "children"),
    ],
)
def test_no_operator_carries_another_operators_payload(operator, foreign_field):
    # Arrange — each leaf supplies its own operands plus one alien field
    operands = {
        Operator.condition: {"concept": "on_dialysis"},
        Operator.drug_active: {"ingredient_id": "metformin"},
        Operator.allergy: {"ingredient_id": "amoxicillin"},
        Operator.age: {"minimum": 18},
        Operator.lt: {"fact": "egfr", "literal": Decimal("30")},
    }[operator]
    alien = (
        (Expression(op=Operator.condition, concept="on_dialysis"),)
        if foreign_field == "children"
        else {"fact": "egfr", "concept": "x", "literal": Decimal("1"), "ingredient_id": "m"}[
            foreign_field
        ]
    )

    # Act / Assert — §4.3.1: only the fields permitted by that operator
    with pytest.raises(ValidationError):
        Expression(op=operator, **operands, **{foreign_field: alien})


@pytest.mark.parametrize(
    ("operator", "child_count"),
    [
        (Operator.all, 0),
        (Operator.any, 0),
        (Operator.NOT, 0),
        (Operator.NOT, 2),
    ],
)
def test_boolean_nodes_need_operands_and_negation_needs_exactly_one(operator, child_count):
    # Arrange
    children = tuple(
        Expression(op=Operator.condition, concept="on_dialysis") for _ in range(child_count)
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        Expression(op=operator, children=children)


@pytest.mark.parametrize(
    "operator",
    [Operator.drug_active, Operator.drug_requested, Operator.allergy],
)
def test_ingredient_predicates_name_their_ingredient(operator):
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        Expression(op=operator)


def test_a_condition_leaf_names_its_condition():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        Expression(op=Operator.condition)


def test_drug_leaves_name_an_ingredient_and_sit_inside_the_declared_scope():
    # Arrange
    active = Expression(op=Operator.drug_active, ingredient_id="metformin")
    requested = Expression(op=Operator.drug_requested, ingredient_id="metformin")

    # Act
    rule = make_rule(when=Expression(op=Operator.any, children=(active, requested)))

    # Assert
    assert rule.when.children == (active, requested)


def test_an_allergy_leaf_accepts_verification_and_severity_filters():
    # Arrange — §5.5's match shape: the leaf carries its filters, and they are
    # optional (a filterless allergy leaf is a weaker, still-closed predicate)
    filtered = Expression(
        op=Operator.allergy,
        ingredient_id="amoxicillin",
        verification_status=VerificationStatus.confirmed,
        severity=AllergySeverity.severe,
    )
    unfiltered = Expression(op=Operator.allergy, ingredient_id="penicillin")

    # Act
    rule = make_rule(when=Expression(op=Operator.any, children=(filtered, unfiltered)))

    # Assert
    assert rule.when.children[0].verification_status is VerificationStatus.confirmed
    assert rule.when.children[0].severity is AllergySeverity.severe
    assert rule.when.children[1].verification_status is None
    assert rule.when.children[1].severity is None


def test_a_boolean_patient_state_is_a_condition_leaf_in_scope():
    # Arrange — §7.1's scope: the snapshot has no free boolean attribute space
    # (§4.2), so on_dialysis is a condition concept
    scope = Scope(
        include=(Expression(op=Operator.condition, concept="type_2_diabetes"),),
        exclude=(
            Expression(op=Operator.age, maximum=17),
            Expression(op=Operator.condition, concept="on_dialysis"),
        ),
    )

    # Act
    rule = make_rule(scope=scope)

    # Assert
    assert rule.scope.include[0].concept == "type_2_diabetes"
    assert rule.scope.exclude[1].concept == "on_dialysis"


@pytest.mark.parametrize(
    "bounds",
    [{"minimum": 18}, {"maximum": 80}, {"minimum": 18, "maximum": 80}],
)
def test_an_age_leaf_accepts_either_bound_or_both(bounds):
    # Arrange / Act
    leaf = Expression(op=Operator.age, **bounds)

    # Assert
    assert leaf.minimum == bounds.get("minimum")
    assert leaf.maximum == bounds.get("maximum")


def test_an_age_leaf_with_neither_bound_is_refused():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        Expression(op=Operator.age)


def test_an_empty_scope_is_in_scope():
    # Arrange / Act — both sides default empty, so an empty scope admits everyone (§7.1)
    scope = Scope()

    # Assert
    assert scope.include == ()
    assert scope.exclude == ()


def test_the_ssot_metformin_rule_loads_whole():
    # Arrange / Act — §7.1's own example, field for field
    rule = make_rule()

    # Assert
    assert rule.id == "metformin-egfr-contraindicated"
    assert rule.version == "1.0.0"
    assert rule.release_status is ReleaseStatus.active
    assert rule.severity is Severity.stop_and_review
    assert rule.drug_scope_level is DrugScopeLevel.ingredient
    numeric_leaf, drug_leaf = rule.when.children
    assert numeric_leaf.threshold_ref == "metformin.egfr_absolute_contraindication"
    assert drug_leaf.ingredient_id == "metformin"
    assert rule.then.blocks is not None
    assert rule.then.blocks.order_of == "metformin"
    assert rule.requires[0].observable == "egfr"
    assert rule.requires[0].renal_metric == "egfr"
    assert rule.monitors[0].due_in_days == 90
    assert rule.governance.clinical_approver.approved_at == date(2026, 8, 1)


def test_blocks_on_a_rule_that_is_not_a_hard_stop_are_refused():
    # Arrange / Act / Assert — invariant 1 lands at load: only stop_and_review
    # may block, so a soft rule cannot perform one downstream (§7.1(c), gate 6)
    with pytest.raises(ValidationError):
        make_rule(severity=Severity.interruptive_review)


def test_a_block_must_name_the_order_action_it_blocks():
    # Arrange / Act / Assert — §7.1(c), gate 6
    with pytest.raises(ValidationError):
        make_rule(then=make_then(blocks=OrderBlock(order_of="")))


def test_a_hard_stop_cannot_treat_unusable_input_as_silent():
    # Arrange / Act / Assert — degradation is not opt-out (§8.3, gate 10)
    with pytest.raises(ValidationError):
        make_rule(requires=(make_requirement(on_unusable=OnUnusable.silent),))


def test_silence_remains_available_below_a_hard_stop():
    # Arrange — gate 10 binds stop_and_review alone
    requirement = make_requirement(on_unusable=OnUnusable.silent)

    # Act
    rule = make_rule(
        severity=Severity.passive_task,
        requires=(requirement,),
        then=make_then(),
    )

    # Assert
    assert rule.requires[0].on_unusable is OnUnusable.silent


def test_a_drug_reference_without_a_declared_scope_level_is_refused():
    # Arrange / Act / Assert — the level is declared, never inferred (§7.1(e), gate 14)
    with pytest.raises(ValidationError):
        make_rule(drug_scope_level=None)


@pytest.mark.parametrize(
    "level",
    [
        DrugScopeLevel.ingredient_route,
        DrugScopeLevel.product,
        DrugScopeLevel.atc_class,
        DrugScopeLevel.curated_set,
    ],
)
def test_v1_admits_only_ingredient_as_the_drug_scope_level(level):
    # Arrange / Act / Assert — the v1 vocabulary supports ingredient only
    with pytest.raises(ValidationError):
        make_rule(drug_scope_level=level)


def test_a_comparison_against_an_undeclared_observable_is_refused():
    # Arrange / Act / Assert — §7.1: no threshold is compared against data of
    # undeclared age and grade (gate 12 territory)
    with pytest.raises(ValidationError):
        make_rule(
            requires=(make_requirement(observable="egfr"),),
            when=Expression(op=Operator.lt, fact="systolic_bp", literal=Decimal("180")),
        )


def test_the_when_tree_is_walked_recursively_for_undeclared_comparisons():
    # Arrange — buried under not(any(...)) the comparison is still a comparison
    buried = Expression(
        op=Operator.NOT,
        children=(
            Expression(
                op=Operator.any,
                children=(
                    Expression(op=Operator.gt, fact="potassium", literal=Decimal("6.5")),
                    Expression(op=Operator.drug_active, ingredient_id="spironolactone"),
                ),
            ),
        ),
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        make_rule(when=buried)


@pytest.mark.parametrize(
    "observable",
    ["visit_state", "encounter_state", "narrative", "admission_trigger"],
)
def test_requirements_cannot_reference_encounter_narrative_or_trigger_state(observable):
    # Arrange / Act / Assert — gate 11: a rule cannot ask which visit produced a
    # fact or which trigger invoked it (§8.1). The `when` drops its numeric
    # comparison so gate 12 does not refuse first.
    with pytest.raises(ValidationError):
        make_rule(
            requires=(make_requirement(observable=observable),),
            when=Expression(op=Operator.drug_active, ingredient_id="metformin"),
        )


@pytest.mark.parametrize(
    "missing",
    [
        "clinical_owner",
        "clinical_approver",
        "role_doubling",
        "effective_from",
        "next_review",
        "change_rationale",
    ],
)
def test_incomplete_governance_is_refused(missing):
    # Arrange / Act / Assert — governance is structural, checked at load (§7.1(d))
    with pytest.raises(ValidationError):
        make_governance(**{missing: None})


def test_authored_prose_is_required_and_non_empty():
    # Arrange / Act / Assert — §7.2: meaning, action, and uncertainty are authored
    with pytest.raises(ValidationError):
        make_then(uncertainty="")


@pytest.mark.parametrize(
    "predicate",
    [
        Expression(op=Operator.lt, fact="egfr", literal=Decimal("30")),
        Expression(op=Operator.drug_active, ingredient_id="metformin"),
        Expression(op=Operator.allergy, ingredient_id="amoxicillin"),
    ],
)
def test_scope_refuses_data_and_drug_predicates(predicate):
    # Arrange / Act / Assert — scope reads patient state only: condition, age,
    # and boolean composition (§7.1)
    with pytest.raises(ValidationError):
        Scope(include=(predicate,))


def test_scope_composition_hides_nothing_from_the_operator_check():
    # Arrange — a drug leaf wrapped in boolean composition is still a drug leaf,
    # and the exclude side is checked exactly as the include side
    smuggled = Expression(
        op=Operator.all,
        children=(
            Expression(op=Operator.condition, concept="type_2_diabetes"),
            Expression(op=Operator.drug_active, ingredient_id="metformin"),
        ),
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        Scope(exclude=(smuggled,))


def test_an_allergy_leaf_accepts_reaction_type_filter():
    # Arrange — the leaf may ask for a specific reaction type (§5.5 rule 3)
    leaf = Expression(
        op=Operator.allergy,
        ingredient_id="penicillin",
        verification_status=VerificationStatus.confirmed,
        severity=AllergySeverity.severe,
        reaction_type=ReactionType.immediate_hypersensitivity,
    )

    # Act / Assert — loads without error, field is present
    assert leaf.reaction_type is ReactionType.immediate_hypersensitivity


def test_requirement_renal_metric_must_match_observable():
    # Arrange — gate 15: renal_metric must match observable
    from noor.engine.rules import OnUnusable, Requirement

    # Valid: renal_metric matches observable
    valid = Requirement(
        observable="egfr",
        on_unusable=OnUnusable.indeterminate,
        renal_metric="egfr",
    )
    assert valid.renal_metric == "egfr"

    # Valid: renal_metric is None
    valid_none = Requirement(
        observable="potassium",
        on_unusable=OnUnusable.indeterminate,
        renal_metric=None,
    )
    assert valid_none.renal_metric is None

    # Invalid: renal_metric doesn't match observable
    with pytest.raises(ValidationError, match="they must match"):
        Requirement(
            observable="egfr",
            on_unusable=OnUnusable.indeterminate,
            renal_metric="crcl",
        )

    with pytest.raises(ValidationError, match="they must match"):
        Requirement(observable="crcl", on_unusable=OnUnusable.indeterminate, renal_metric="egfr")
