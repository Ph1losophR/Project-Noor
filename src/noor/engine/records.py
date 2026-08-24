"""The outcome vocabulary and the evaluation record (SSOT §8.2, §8.3, §8.5).

Every rule considered writes a record — not just the ones that fired — and the
record is what §11 anchors to: the pinned review, the obligation ledger,
zero-firing surveillance. The shape here is closed on purpose. Run-header
fields (`correlation_id`, `latency_ms`, `trigger`) are absent by construction:
they belong to `app/`'s header, and either one inside a per-rule record would
break invariants 6 and 8 at once (§8.4). Degradation carries exactly §8.3's
three causes, each pinned to its one outcome by §8.3's table, and one shared
cap function fixes every record's effective severity — capped for a degraded
or failed record, authored for a clean one — so evaluate() can never
double-demote and a clean record cannot drift.
"""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from noor.canon.models import NoorModel
from noor.engine.content import Pins
from noor.engine.rules import Severity


class Outcome(StrEnum):
    """How a rule's consideration ended (SSOT §8.2).

    Three come from the evaluator; `out_of_scope` and
    `suppressed_by_governed_policy` keep non-firing distinguishable from not
    considered; `evaluation_failed` is a defect report, never a statement about
    the patient (§8.5).
    """

    triggered = "triggered"
    not_triggered = "not_triggered"
    indeterminate = "indeterminate"
    out_of_scope = "out_of_scope"
    suppressed_by_governed_policy = "suppressed_by_governed_policy"
    evaluation_failed = "evaluation_failed"


class DegradedBecause(StrEnum):
    """Why a record degraded — exactly §8.3's three causes.

    A broken data feed, records that are merely unverified, and a rule that has
    been crashing are different answers to "why has this blocking rule not
    blocked", so surveillance gets one value each rather than one blur (§11.9).
    """

    requirements_unmet = "requirements_unmet"
    evidence_grade = "evidence_grade"
    rule_raised = "rule_raised"


class RequirementVerdictValue(StrEnum):
    """Whether a declared requirement could be used (SSOT §8.2)."""

    usable = "usable"
    unusable = "unusable"


class RequirementReason(StrEnum):
    """The closed machine vocabulary for a verdict's reason (SSOT §8.2).

    The data-quality queue and zero-firing surveillance distinguish different
    failures through it, so it is an enum, never free text.
    """

    met = "met"
    no_result = "no_result"
    quality_below_minimum = "quality_below_minimum"
    stale = "stale"
    wrong_source = "wrong_source"
    missing_context = "missing_context"
    withdrawn_source = "withdrawn_source"
    ambiguous_mapping = "ambiguous_mapping"


class RequirementVerdict(NoorModel):
    """One requirement's verdict, per SSOT §8.2's shape.

    `reason` is required on every verdict and is not constrained against the
    value: the vocabulary exists for surveillance, and linking it to `verdict`
    would invent semantics §8.2 does not state.
    """

    observable: str = Field(min_length=1)
    verdict: RequirementVerdictValue
    reason: RequirementReason
    latest_age_days: int | None = None


def cap_below_stop_and_review(authored: Severity) -> Severity:
    """The single §8.3 severity cap, shared by every degradation cause.

    `effective = interruptive_review if authored == stop_and_review else
    authored`. It never raises a softer severity, and being idempotent it is
    safe to apply once here and once more downstream without a double demotion
    — which is why evaluate() must reuse this function rather than re-derive
    the cap.
    """
    return Severity.interruptive_review if authored is Severity.stop_and_review else authored


# §8.3's cause→outcome table, pinned exactly: each outcome admits only the
# cause the table names it — or no cause at all — so surveillance reads one
# meaning per value and no cause can migrate between outcomes (§11.9).
_PINNED_CAUSES: dict[Outcome, frozenset[DegradedBecause | None]] = {
    Outcome.triggered: frozenset((None, DegradedBecause.evidence_grade)),
    Outcome.not_triggered: frozenset((None,)),
    Outcome.indeterminate: frozenset((DegradedBecause.requirements_unmet,)),
    Outcome.out_of_scope: frozenset((None,)),
    Outcome.suppressed_by_governed_policy: frozenset((None,)),
    Outcome.evaluation_failed: frozenset((DegradedBecause.rule_raised,)),
}

# Outcomes that never reached their requirements manifest, and so have nothing
# truthful to say about verdicts (§8.2, §8.5): suppression stops before
# requirements, scope excludes before them, and a rule that raised before
# reading them cannot report them. A clean negative ran them and they were met,
# so it may still report the verdicts it gathered.
_VERDICTLESS_OUTCOMES: frozenset[Outcome] = frozenset(
    {
        Outcome.out_of_scope,
        Outcome.suppressed_by_governed_policy,
        Outcome.evaluation_failed,
    }
)


class EvaluationRecord(NoorModel):
    """One rule's consideration of one snapshot, field for field per §8.2.

    No run-header fields: `correlation_id`, `latency_ms`, and the trigger are
    stamped by `app/` around the whole call, and inside a record either would
    break invariant 6 (two runs could never compare equal) or invariant 8
    (minting them needs a clock) (§8.4). The validators pin the cross-field
    contract: failure names its exception exactly for `evaluation_failed`,
    degradation carries exactly §8.3's paired cause for its outcome and nothing
    else, effective severity is fixed — the shared cap for any record carrying
    a cause, authored severity for a clean one — and outcomes that never read
    requirements carry no verdicts.
    """

    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    outcome: Outcome
    authored_severity: Severity
    effective_severity: Severity
    degraded_because: DegradedBecause | None = None
    failure_reason: str | None = None
    requirement_verdicts: tuple[RequirementVerdict, ...] = ()
    pins: Pins

    @model_validator(mode="after")
    def _failure_reason_exists_exactly_for_evaluation_failed(self) -> Self:
        # §8.5: the exception TYPE NAME only — never message, never traceback —
        # and nothing for any outcome where no exception occurred.
        if self.outcome is Outcome.evaluation_failed:
            if self.failure_reason is None:
                raise ValueError(
                    "an evaluation_failed record names the exception type that raised (§8.5)"
                )
        elif self.failure_reason is not None:
            raise ValueError("failure_reason exists exactly for evaluation_failed (§8.5)")
        return self

    @model_validator(mode="after")
    def _degradation_appears_exactly_where_it_happened(self) -> Self:
        # §8.3's table is closed, in both directions: unmet requirements degrade
        # to indeterminate only, evidence grade caps a triggered finding only,
        # a raised rule fails only — and the three non-degrading outcomes carry
        # no cause at all. A missing cause on a degrading outcome and a foreign
        # cause anywhere are both refused.
        if self.degraded_because not in _PINNED_CAUSES[self.outcome]:
            raise ValueError(
                f"`{self.outcome}` cannot carry `degraded_because="
                f"{self.degraded_because}` (§8.3 pairs each cause with exactly one outcome)"
            )
        return self

    @model_validator(mode="after")
    def _effective_severity_is_fixed_by_the_degradation_state(self) -> Self:
        # §8.3 / design §7.1: one shared cap fixes effective severity in both
        # directions. Any record carrying a cause — which for evaluation_failed
        # is always rule_raised — presents cap_below_stop_and_review of its
        # authored severity; a clean record presents its authored severity
        # unchanged. Authors cannot opt out either way.
        degraded = self.degraded_because is not None or self.outcome is Outcome.evaluation_failed
        expected = (
            cap_below_stop_and_review(self.authored_severity)
            if degraded
            else self.authored_severity
        )
        if self.effective_severity != expected:
            raise ValueError(
                "effective severity is fixed by §8.3: the shared cap for a "
                "degraded or failed record, the authored severity for a clean one"
            )
        return self

    @model_validator(mode="after")
    def _verdicts_only_where_requirements_were_read(self) -> Self:
        # Scope excludes before requirements, suppression stops before them, and
        # a rule that raised has nothing truthful to say about its verdicts (§8.5).
        if self.outcome in _VERDICTLESS_OUTCOMES and self.requirement_verdicts:
            raise ValueError(
                f"`{self.outcome}` never read its requirements and cannot carry "
                f"requirement_verdicts (§8.2, §8.5)"
            )
        return self
