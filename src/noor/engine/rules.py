"""The closed expression tree (§4.3.1) and the §7.1 rule manifest.

One recursive `Expression` model, discriminated by `op`, serves `when` and
`scope`: an unknown operator or an operator-inappropriate field is refused at
load time, which is what keeps §4.3's standing objection answerable by the
build. The single-rule §10.4 gates land here as validators — a block belongs to
a hard stop alone (gate 6), unusable input is never silenced under one
(gate 10), encounter and trigger state never enter a requirement (gate 11), a
drug reference names its scope level (gate 14) — and so does §7.1's amendment:
every observable a numeric leaf compares is declared in `requires`.
"""

from collections.abc import Iterator, Mapping
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from noor.canon.models import EntryMode, NoorModel, QualityState, SourceStatus
from noor.engine.snapshot import AllergySeverity, ReactionType, VerificationStatus


class Severity(StrEnum):
    """How hard a fired finding interrupts the clinician (SSOT §7.1).

    Lives here because it is a property of the rule; records reuse it for the
    evaluation record's severity fields.
    """

    stop_and_review = "stop_and_review"
    interruptive_review = "interruptive_review"
    passive_task = "passive_task"


class ReleaseStatus(StrEnum):
    """Where a rule sits in the content lifecycle (SSOT §7.1, §10.1)."""

    draft = "draft"
    technical_validation = "technical_validation"
    clinical_review = "clinical_review"
    approved = "approved"
    scheduled = "scheduled"
    active = "active"
    retired = "retired"


class DrugScopeLevel(StrEnum):
    """What a drug reference in this rule matches against (SSOT §7.1(e)).

    Declared, never inferred: the four levels match different patients. V1's
    vocabulary supports `ingredient` only.
    """

    ingredient = "ingredient"
    ingredient_route = "ingredient_route"
    product = "product"
    atc_class = "atc_class"
    curated_set = "curated_set"


class OnUnusable(StrEnum):
    """What happens when a declared requirement cannot be met (SSOT §8.3).

    `silent` proceeds without the fact; `indeterminate` degrades the rule to
    "cannot assess safely". A hard stop may never choose silence.
    """

    silent = "silent"
    indeterminate = "indeterminate"


class Operator(StrEnum):
    """The evaluator's closed operator vocabulary (SSOT §4.3).

    Growing it means editing this enum — a reviewed change to the device, not a
    rule author's private extension. Pydantic refuses anything else at load
    (§10.4 gate 12).
    """

    all = "all"
    any = "any"
    # `not` is a Python keyword and cannot be written as a member name; the
    # value carries the vocabulary verbatim, as entered_in_error does in canon.
    NOT = "not"
    lt = "lt"
    le = "le"
    gt = "gt"
    ge = "ge"
    eq = "eq"
    ne = "ne"
    drug_active = "drug_active"
    drug_requested = "drug_requested"
    allergy = "allergy"
    condition = "condition"
    age = "age"


BOOLEAN_OPERATORS: frozenset[Operator] = frozenset({Operator.all, Operator.any, Operator.NOT})
NUMERIC_OPERATORS: frozenset[Operator] = frozenset(
    {Operator.lt, Operator.le, Operator.gt, Operator.ge, Operator.eq, Operator.ne}
)
DRUG_OPERATORS: frozenset[Operator] = frozenset({Operator.drug_active, Operator.drug_requested})
INGREDIENT_OPERATORS: frozenset[Operator] = DRUG_OPERATORS | {Operator.allergy}

# Scope reads patient state only: who the patient is, not what was measured or
# prescribed (§7.1). A numeric, drug, or allergy predicate inside scope is a
# load refusal.
PATIENT_STATE_OPERATORS: frozenset[Operator] = BOOLEAN_OPERATORS | {
    Operator.condition,
    Operator.age,
}

# §8.1/§8.4 invariant 10: a rule cannot ask which visit produced a fact or which
# trigger invoked it. Enforced on Requirement.observable at load (gate 11).
FORBIDDEN_REQUIREMENT_OBSERVABLES: frozenset[str] = frozenset(
    {"visit_state", "encounter_state", "narrative"}
)

_FIELDS_BY_OPERATOR: Mapping[Operator, frozenset[str]] = (
    {op: frozenset({"children"}) for op in BOOLEAN_OPERATORS}
    | {op: frozenset({"fact", "literal", "threshold_ref"}) for op in NUMERIC_OPERATORS}
    | {
        Operator.drug_active: frozenset({"ingredient_id"}),
        Operator.drug_requested: frozenset({"ingredient_id"}),
        Operator.allergy: frozenset(
            {"ingredient_id", "verification_status", "severity", "reaction_type"}
        ),
        Operator.condition: frozenset({"concept"}),
        Operator.age: frozenset({"minimum", "maximum"}),
    }
)


class Expression(NoorModel):
    """One closed recursive expression node (SSOT §4.3.1).

    Discriminated by `op`: every field except `op` is None exactly when its
    operator does not use it, so the model stays one closed type — no per-op
    subclasses and no open dictionary — while still refusing an operator-
    inappropriate payload at load.
    """

    op: Operator
    children: tuple["Expression", ...] = ()
    fact: str | None = Field(default=None, min_length=1)
    literal: Decimal | None = None
    threshold_ref: str | None = Field(default=None, min_length=1)
    ingredient_id: str | None = Field(default=None, min_length=1)
    verification_status: VerificationStatus | None = None
    severity: AllergySeverity | None = None
    reaction_type: ReactionType | None = None
    concept: str | None = Field(default=None, min_length=1)
    minimum: int | None = None
    maximum: int | None = None

    @model_validator(mode="after")
    def _only_the_permitted_fields_are_present(self) -> Self:
        offenders = self._present_payload_fields() - _FIELDS_BY_OPERATOR[self.op]
        if offenders:
            raise ValueError(
                f"operator `{self.op}` permits only "
                f"{sorted(_FIELDS_BY_OPERATOR[self.op])}, found {sorted(offenders)} (§4.3.1)"
            )
        return self

    @model_validator(mode="after")
    def _the_operator_has_its_operands(self) -> Self:
        self._require_composition_children()
        self._require_one_comparison_source()
        self._require_an_ingredient()
        self._require_a_condition_concept()
        self._require_an_age_bound()
        return self

    def _present_payload_fields(self) -> set[str]:
        present: set[str] = set()
        if self.children:
            present.add("children")
        if self.fact is not None:
            present.add("fact")
        if self.literal is not None:
            present.add("literal")
        if self.threshold_ref is not None:
            present.add("threshold_ref")
        if self.ingredient_id is not None:
            present.add("ingredient_id")
        if self.verification_status is not None:
            present.add("verification_status")
        if self.severity is not None:
            present.add("severity")
        if self.reaction_type is not None:
            present.add("reaction_type")
        if self.concept is not None:
            present.add("concept")
        if self.minimum is not None:
            present.add("minimum")
        if self.maximum is not None:
            present.add("maximum")
        return present

    def _require_composition_children(self) -> None:
        if self.op not in BOOLEAN_OPERATORS:
            return
        if not self.children:
            raise ValueError(f"`{self.op}` composes at least one child expression")
        if self.op is Operator.NOT and len(self.children) != 1:
            raise ValueError("`not` negates exactly one child expression")

    def _require_one_comparison_source(self) -> None:
        if self.op not in NUMERIC_OPERATORS:
            return
        if self.fact is None:
            raise ValueError(f"a `{self.op}` comparison names the observable it reads (§7.1)")
        sources = (self.literal is not None) + (self.threshold_ref is not None)
        if sources != 1:
            raise ValueError(
                "a numeric comparison carries a literal or a threshold_ref, "
                "never both and never neither (§4.3.1)"
            )

    def _require_an_ingredient(self) -> None:
        if self.op in INGREDIENT_OPERATORS and self.ingredient_id is None:
            raise ValueError(f"a `{self.op}` predicate names an ingredient (§7.1)")

    def _require_a_condition_concept(self) -> None:
        if self.op is Operator.condition and self.concept is None:
            raise ValueError("a condition predicate names a snapshot condition concept (§4.2)")

    def _require_an_age_bound(self) -> None:
        if self.op is Operator.age and self.minimum is None and self.maximum is None:
            raise ValueError("an age predicate bounds at least one side of the range")


def walk_expression(node: Expression) -> Iterator[Expression]:
    """Yield the node and every descendant, depth-first (§4.3.1).

    Public because more than one module walks a rule's tree: content validates
    threshold pairings with it, and the loader gates use it to see through
    boolean composition.
    """
    yield node
    for child in node.children:
        yield from walk_expression(child)


class Scope(NoorModel):
    """Who a rule applies to, evaluated as all(include) and not any(exclude) (§7.1).

    Both sides default empty, so an empty scope is in-scope. Scope predicates
    read patient state only — condition concepts, age bounds, boolean
    composition — never a numeric, drug, or allergy leaf.
    """

    include: tuple[Expression, ...] = ()
    exclude: tuple[Expression, ...] = ()

    @model_validator(mode="after")
    def _scope_reads_patient_state_only(self) -> Self:
        for predicate in (*self.include, *self.exclude):
            for node in walk_expression(predicate):
                if node.op not in PATIENT_STATE_OPERATORS:
                    raise ValueError(
                        f"scope predicates read patient state only; `{node.op}` compares "
                        f"data or drugs and belongs in `when` (§7.1)"
                    )
        return self


class Requirement(NoorModel):
    """One entry of the data-requirement manifest (§7.1(a), §5.1).

    Each rule declares its own windows — there is no global TTL. `observable`
    holds a snapshot fact key; `on_unusable` chooses between proceeding without
    the fact and degrading to indeterminate (§8.3).
    """

    observable: str = Field(min_length=1)
    accepted_status: tuple[SourceStatus, ...] = ()
    min_quality: QualityState | None = None
    max_age_days: int | None = None
    prefer_source: tuple[EntryMode, ...] = ()
    required_context: tuple[str, ...] = ()
    on_unusable: OnUnusable
    renal_metric: Literal["egfr", "crcl"] | None = None

    @model_validator(mode="after")
    def _renal_metric_matches_observable(self) -> Self:
        # Gate 15: if renal_metric is specified, observable must match it
        if self.renal_metric is not None and self.observable != self.renal_metric:
            raise ValueError(
                f"renal_metric={self.renal_metric} but observable={self.observable} — "
                f"they must match (§10.4 gate 15)"
            )
        return self


class Monitor(NoorModel):
    """What falls due later when this rule's action lands (§7.1(f), §11.2).

    Separate from `max_age_days` on purpose: freshness asks whether the result
    may be used now; monitoring asks whether the patient is due another one.
    """

    observable: str = Field(min_length=1)
    due_in_days: int
    reason: str = Field(min_length=1)


class OrderBlock(NoorModel):
    """A hard stop's target: the order action it blocks, by name (§7.1(c))."""

    order_of: str = Field(min_length=1)


class Then(NoorModel):
    """The authored half of the disclosure bundle plus the optional block (§7.2).

    `meaning`, `action`, and `uncertainty` are the three authored fields; the
    card renders everything else around them. `blocks` is carried only by a
    stop_and_review rule — enforced at the `Rule`, not here.
    """

    blocks: OrderBlock | None = None
    meaning: str = Field(min_length=1)
    action: str = Field(min_length=1)
    uncertainty: str = Field(min_length=1)


class NamedClinician(NoorModel):
    """A named clinician as §7.1's governance example shapes one."""

    name: str = Field(min_length=1)
    credential: str = Field(min_length=1)


class ClinicalApprover(NamedClinician):
    """The approver, with the date the approval happened (§7.1(d))."""

    approved_at: date


class Governance(NoorModel):
    """Structural governance (§7.1(d)): schema fields checked by CI, not comments.

    Every field is required — a rule with no approver, no review date, or no
    stated rationale does not load.
    """

    clinical_owner: NamedClinician
    clinical_approver: ClinicalApprover
    role_doubling: bool
    effective_from: date
    next_review: date
    change_rationale: str = Field(min_length=1)


class Rule(NoorModel):
    """One clinical rule, field for field per SSOT §7.1.

    The validators below are the single-rule §10.4 gates landing at load time;
    cross-file gates belong to release compilation.
    """

    id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    release_status: ReleaseStatus
    category: str = Field(min_length=1)
    severity: Severity
    scope: Scope = Scope()
    drug_scope_level: DrugScopeLevel | None = None
    requires: tuple[Requirement, ...] = ()
    monitors: tuple[Monitor, ...] = ()
    when: Expression
    then: Then
    governance: Governance

    @model_validator(mode="after")
    def _only_a_hard_stop_blocks_an_order_action(self) -> Self:
        if self.then.blocks is not None and self.severity is not Severity.stop_and_review:
            raise ValueError(
                "only a stop_and_review rule may carry then.blocks — a block stops an order "
                "action, and softer severities have nothing to stop (§7.1(c), §10.4 gate 6)"
            )
        return self

    @model_validator(mode="after")
    def _a_hard_stop_never_sits_on_silenced_data(self) -> Self:
        if self.severity is Severity.stop_and_review and any(
            requirement.on_unusable is OnUnusable.silent for requirement in self.requires
        ):
            raise ValueError(
                "a stop_and_review rule cannot declare on_unusable: silent — unusable input "
                "degrades to indeterminate (§8.3, §10.4 gate 10)"
            )
        return self

    @model_validator(mode="after")
    def _drug_references_declare_their_scope_level(self) -> Self:
        for node in walk_expression(self.when):
            if node.op in DRUG_OPERATORS and self.drug_scope_level is not DrugScopeLevel.ingredient:
                raise ValueError(
                    f"`{node.op}: {node.ingredient_id}` needs drug_scope_level: ingredient — "
                    f"v1 matches at ingredient level only (§7.1(e), §10.4 gate 14)"
                )
        return self

    @model_validator(mode="after")
    def _every_compared_observable_is_declared_in_requires(self) -> Self:
        declared = {requirement.observable for requirement in self.requires}
        for node in walk_expression(self.when):
            if node.op in NUMERIC_OPERATORS and node.fact not in declared:
                raise ValueError(
                    f"`{node.fact}` is compared numerically but absent from requires — a "
                    f"threshold never runs against data of undeclared age and grade "
                    f"(§7.1, §10.4 gate 12)"
                )
        return self

    @model_validator(mode="after")
    def _requirements_never_name_encounter_or_trigger_state(self) -> Self:
        for requirement in self.requires:
            if (
                requirement.observable in FORBIDDEN_REQUIREMENT_OBSERVABLES
                or "trigger" in requirement.observable
            ):
                raise ValueError(
                    f"requirement `{requirement.observable}` is encounter, narrative, or "
                    f"trigger state, which no rule may read (§8.1, §10.4 gate 11)"
                )
        return self
