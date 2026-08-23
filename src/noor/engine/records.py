"""The outcome vocabulary and the evaluation record (SSOT §8.2, §8.3, §8.5).

Every rule considered writes a record — not just the ones that fired — and the
record is what §11 anchors to: the pinned review, the obligation ledger,
zero-firing surveillance. The shape here is closed on purpose. Run-header
fields (`correlation_id`, `latency_ms`, `trigger`) are absent by construction:
they belong to `app/`'s header, and either one inside a per-rule record would
break invariants 6 and 8 at once (§8.4). Degradation carries exactly §8.3's
three causes, and one shared cap function keeps every degraded or failed
record below a hard stop, so evaluate() can never double-demote.
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

    no_result = "no_result"
    quality_below_minimum = "quality_below_minimum"
    stale = "stale"
    wrong_source = "wrong_source"
    missing_context = "missing_context"
    withdrawn_source = "withdrawn_source"
    ambiguous_mapping = "ambiguous_mapping"
    wrong_observable = "wrong_observable"


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


# Outcomes that structurally cannot have degraded: scope excluded before any
# requirement was read, suppression stopped before that, and a clean negative
# ran to completion on usable data (§8.2).
_OUTCOMES_WITHOUT_DEGRADATION: frozenset[Outcome] = frozenset(
    {Outcome.not_triggered, Outcome.out_of_scope, Outcome.suppressed_by_governed_policy}
)

# Outcomes whose very meaning is degradation (§8.3): indeterminate is reserved
# for questions a human can close, and evaluation_failed is a defect report.
_DEGRADED_OUTCOMES: frozenset[Outcome] = frozenset(
    {Outcome.indeterminate, Outcome.evaluation_failed}
)

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
    degradation appears exactly where §8.3 says it happened, every degraded or
    failed hard stop presents at the capped severity, and outcomes that never
    read requirements carry no verdicts.
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
        # §8.3 pairs each cause with its outcome: unmet requirements degrade to
        # indeterminate, evidence grade caps a triggered finding, a raised rule
        # fails. Nothing else may carry a cause, and the degraded outcomes may
        # never lack one.
        if self.outcome in _OUTCOMES_WITHOUT_DEGRADATION:
            if self.degraded_because is not None:
                raise ValueError(
                    f"`{self.outcome}` did not degrade and cannot carry degraded_because (§8.3)"
                )
        elif self.outcome in _DEGRADED_OUTCOMES:
            if self.degraded_because is None:
                raise ValueError(f"`{self.outcome}` always degrades and must name why (§8.3)")
        # Only `triggered` remains: evidence grade is the one cause that can sit
        # on a reached finding, absent otherwise.
        elif (
            self.degraded_because is not None
            and self.degraded_because is not DegradedBecause.evidence_grade
        ):
            raise ValueError(
                f"`{self.degraded_because}` belongs to another outcome — evidence "
                f"grade is the only cause that can sit on a triggered finding (§8.3)"
            )
        return self

    @model_validator(mode="after")
    def _degraded_and_failed_records_present_the_capped_severity(self) -> Self:
        # §8.3 / design §7.1: all three causes route through the one shared cap,
        # so a degraded or failed record can never present a blocking action.
        capped = self.outcome is Outcome.evaluation_failed or self.degraded_because in (
            DegradedBecause.requirements_unmet,
            DegradedBecause.evidence_grade,
        )
        if capped and self.effective_severity != cap_below_stop_and_review(self.authored_severity):
            raise ValueError(
                "a degraded or failed record presents the capped severity — authors "
                "cannot opt out, and nothing blocks on degraded input (§8.3)"
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
