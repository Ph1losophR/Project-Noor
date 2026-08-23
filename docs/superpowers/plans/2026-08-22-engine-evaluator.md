# Engine Evaluator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the pure `engine` evaluator and its four closed data contracts, including deterministic rule evaluation, degradation, per-rule failure isolation, and the SSOT §14 step 4 verification claims.

**Architecture:** `engine` imports only `canon` and evaluates a frozen `Snapshot` against a frozen `EvaluationContext` and an explicit tuple of two-field `RequestedAction` projections. Rules use one closed recursive expression tree. Every rule produces exactly one immutable `EvaluationRecord`; suppression, scope, requirements, and conditions are evaluated in that order, and a failure in one rule cannot stop the remaining rules.

**Tech Stack:** Python 3.12+, Pydantic v2, pytest + hypothesis, ruff, mypy `--strict`, uv. No I/O, clock, database, network, catalogue loader, or clinical content.

## Global Constraints

- Read `docs/cds-architecture.md` and `docs/testing-standards.md` before implementation; the SSOT wins any conflict.
- Dependency direction is `canon <- engine <- catalogue <- app`; `engine` never imports `catalogue` or `app`.
- The engine performs no I/O and reads no clock; time enters as `Snapshot.evaluated_at`.
- Every model is frozen and closed through `NoorModel` (`frozen=True`, `extra="forbid"`).
- `evaluate(context, snapshot, requested_actions)` returns `tuple[EvaluationRecord, ...]`, not an `EvaluationRun`.
- Records are sorted by `rule_id`; no rule reads another rule's output.
- The six outcomes are exactly `triggered`, `not_triggered`, `indeterminate`, `out_of_scope`, `suppressed_by_governed_policy`, and `evaluation_failed`.
- The three severities are exactly `stop_and_review`, `interruptive_review`, and `passive_task`.
- A missing or unusable requirement yields `indeterminate` only when its manifest says `on_unusable: indeterminate`; a `stop_and_review` rule may never use `on_unusable: silent`.
- A `stop_and_review` rule with unmet requirements, lower evidence grade, or a raised exception is capped below `stop_and_review` and never blocks. The cap is one shared function — `interruptive_review if authored == stop_and_review else authored` — applied once; a record carries exactly one `degraded_because` and never a stacked double demotion.
- Every observable a numeric `when` leaf compares is declared in the rule's `requires`; a numeric leaf naming an undeclared observable is a load failure, and at evaluation a numeric leaf reads only the requirement-validated value (freshness and quality gate is not optional).
- A boolean patient state (`on_dialysis`, pregnancy) is a `condition` concept matched against `Snapshot.conditions`; the closed snapshot has no free boolean-attribute field. `Scope` is `{include, exclude}`, evaluated as `all(include) and not any(exclude)`.
- Evidence grade is derived centrally from structured facts, not configured independently by a rule. v1 cases are unconfirmed allergy, medicine-manager report with `cognitive_impairment` in `conditions`, and a Noor-derived observation when the requirement prefers an interfaced source.
- Requirement machine reasons are exactly `no_result`, `quality_below_minimum`, `stale`, `wrong_source`, `missing_context`, `withdrawn_source`, `ambiguous_mapping`, and `wrong_observable`.
- Conflicting active, unexpired goals for one patient and observable raise `AmbiguousGoalOfCareError`; the affected rule records `evaluation_failed`, is capped below `stop_and_review`, and never blocks.
- Numeric expression leaves carry exactly one of a literal or `threshold_ref`.
- `RequestedAction` has exactly the fields `kind` and `subject`; no encounter state, narrative, trigger, detail, or `blocked_by` crosses the boundary.
- `correlation_id`, `latency_ms`, whole-run fail-closed handling, persistence, obligations, rendering, and catalogue loading remain out of scope.
- Every test follows Arrange-Act-Assert, has a sentence name, tests behaviour rather than implementation, and reaches 100% branch coverage with no exclusions.
- Run the existing suite before business-logic work. Do not proceed with a failing baseline.
- Commit every task on a feature branch; never commit this work directly to `main`.

## File Structure

```text
src/noor/engine/__init__.py       # update boundary docstring only if needed
src/noor/engine/snapshot.py        # patient facts and requested-action projection
src/noor/engine/rules.py           # operators, expression tree, rule manifest
src/noor/engine/content.py         # thresholds, goals, profiles, release context
src/noor/engine/records.py         # outcomes, severity, requirement verdicts, records
src/noor/engine/evaluate.py        # evaluate() and per-rule evaluation
tests/test_import_direction.py    # extend invariant-10 seam checks
tests/conftest.py                 # engine factories and shared timestamps
tests/engine/test_snapshot.py
tests/engine/test_rules.py
tests/engine/test_content.py
tests/engine/test_records.py
tests/engine/test_evaluate.py
tests/engine/test_degradation.py
tests/engine/test_failure.py
tests/engine/test_invariants.py
tests/engine/test_properties.py
```

---

### Task 1: Establish the engine branch and baseline

**Files:** None.

**Interfaces:** Confirms the predecessor suite is green before adding business logic.

The design spec and this plan already live on `design/engine-evaluator`. Branch the implementation from there so the design note, this plan, and the code travel to `main` in one pull request — the §7.5 four-eyes review then covers the SSOT amendments (design §9.1) and the code together.

- [ ] **Step 1: Create the working branch**

```bash
git switch -c feat/engine-evaluator   # from design/engine-evaluator
```

- [ ] **Step 2: Run the baseline suite**

Run:

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Expected: all commands pass before engine files are changed.

- [ ] **Step 3: Commit the branch marker**

No code changes yet, so there is nothing to commit here; the first real commit lands at the end of Task 2. Proceed once the baseline above is green.

---

### Task 2: Snapshot and requested-action contracts

**Files:**
- Create: `src/noor/engine/snapshot.py`
- Modify: `tests/conftest.py`
- Create: `tests/engine/test_snapshot.py`

**Interfaces:**
- Consumes: `NoorModel`, `CanonicalObservation`, and `MappingStatus` from `noor.canon.models`.
- Produces: `Snapshot`, `SnapshotMedication`, `AllergyRecord`, `AllergyStatus`, `GoalOfCare`, `RequestedAction`, `ActionKind`, and the allergy enums/sub-models `VerificationStatus`, `AllergySeverity`, `ReactionType`, `EvidenceSource`, `CulpritSubstance`, `AllergyOnset`, `Recorder`.

`Snapshot` fields are `snapshot_id`, `evaluated_at`, `patient_id`, `age_years`, `observations`, `medications`, `allergies`, `allergy_status`, `conditions`, and `goals_of_care`. `evaluated_at` is timezone-aware and normalised to UTC. `conditions` is a frozen set of strings; the v1 evidence-grade check uses the exact condition key `cognitive_impairment`.

Re-implement the UTC normaliser as a one-line `field_validator` in `snapshot.py` (`value.astimezone(UTC)`); `canon.models._utc` is module-private, so mirror the pattern rather than importing it.

`SnapshotMedication` contains only `ingredient_id` and `mapping_status`. `AllergyRecord` is the full §5.5 record: `culprit` (a `CulpritSubstance` of `ingredient_id`, optional `atc`, optional `source_display`), `reaction`, `reaction_type` (`ReactionType`: `immediate_hypersensitivity | delayed | intolerance | unknown`), `severity` (`AllergySeverity`: `severe | moderate | mild | unknown`), `onset` (an `AllergyOnset`), `verification_status` (`VerificationStatus`: `confirmed | unconfirmed | refuted | entered_in_error`), `evidence_source` (`EvidenceSource`: `clinical_record | patient_reported | family_reported`), `recorder` (a `Recorder`), and `recorded_at`. The evaluator reads `culprit.ingredient_id`, `verification_status`, and `severity`; the remaining fields carry the finding into the card (§8.3). `GoalOfCare` contains `observable`, `value`, `unit`, `op`, `reason`, `clinician_id`, `effective_date`, and `expires_at`; there is no `status` field — active means the evaluation timestamp falls in `[effective_date, expires_at)` (§5.6, design §9.1 amendment 4). `RequestedAction` contains exactly `kind` and `subject`.

- [ ] **Step 1: Write failing tests for closed models and UTC handling**

Cover: valid construction; naive datetime rejection; UTC normalisation; rejected observations retained; ambiguous medication mapping accepted into the snapshot; `allergy_status=not_asked` distinct from an empty allergy tuple; undeclared fields refused; each allergy enum rejecting an unknown member; a goal with `expires_at <= effective_date` refused; `RequestedAction.model_fields` exactly equals `{"kind", "subject"}`; an invalid action kind refused. Add `make_snapshot`, `make_allergy`, and `make_goal` factories to `tests/conftest.py`.

- [ ] **Step 2: Run the focused tests**

Run: `uv run pytest tests/engine/test_snapshot.py -v`

Expected: collection failure because `noor.engine.snapshot` does not exist.

- [ ] **Step 3: Implement the minimal frozen models**

Use `NoorModel` for every model. Use `AwareDatetime` and a one-line UTC-normalising `field_validator` (do not import `canon.models._utc`). Use `tuple[...]` and `frozenset[...]` for immutable collections. A goal validator refuses `expires_at <= effective_date`. Do not add encounter, visit, narrative, trigger, detail, block, or goal-`status` fields.

- [ ] **Step 4: Run focused and boundary tests**

Run: `uv run pytest tests/engine/test_snapshot.py tests/test_import_direction.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/noor/engine/snapshot.py tests/engine/test_snapshot.py tests/conftest.py
git commit -m "feat(engine): snapshot and requested-action contracts"
```

---

### Task 3: Closed expression tree and rule contracts

**Files:**
- Create: `src/noor/engine/rules.py`
- Create: `tests/engine/test_rules.py`

**Interfaces:**
- Consumes: `NoorModel` and snapshot fact names.
- Produces: `Operator`, `Severity`, `ReleaseStatus`, `Scope`, `Requirement`, `Monitor`, `Then`, `Governance`, `Expression`, `Rule`.

Implement one recursive `Expression` model. Boolean nodes are `all`, `any`, and `not`. Leaf operators are `lt`, `le`, `gt`, `ge`, `eq`, `ne`, `drug_active`, `drug_requested`, `allergy`, `condition`, and `age`. Numeric leaves carry `fact`, `literal`, and `threshold_ref`, with exactly one comparison source. Drug leaves carry `ingredient_id`; allergy leaves carry `ingredient_id`, `verification_status`, and `severity`; condition leaves carry `concept`; age leaves carry `minimum` and/or `maximum`. A boolean patient state (`on_dialysis`, a pregnancy flag) has no dedicated operator: it is a `condition` leaf matched against `Snapshot.conditions` (design §5.2, §9.1 amendment 6) — the closed snapshot has no free boolean-attribute field.

`Scope` is `{include: tuple[Expression, ...], exclude: tuple[Expression, ...]}`, evaluated as `all(include) and not any(exclude)`; both default empty, so an empty scope is in-scope. Scope expressions use only `condition`, `age`, and boolean composition — never a numeric or drug/allergy leaf.

`Rule` carries the SSOT §7.1 fields. `Requirement` carries `observable`, `accepted_status`, `min_quality`, `max_age_days`, `prefer_source`, `required_context`, `on_unusable`, and optional `renal_metric`. `Then.blocks` is `None` or `order_of`. Validators enforce: only `stop_and_review` may block; blocks name an order action; `stop_and_review` cannot use `on_unusable=silent`; drug expressions require `drug_scope_level=ingredient`; **every observable a numeric leaf compares in `when` is declared in `requires`** (design §5.2, §9.1 amendment 5 — a numeric leaf naming an undeclared observable is a load failure); and no unsupported operator or field can load.

- [ ] **Step 1: Write failing tests for operator and rule validation**

Cover every valid operator shape and invalid shape, both numeric-source exclusivity failures, unknown operators, unknown fields, non-order blocks, non-hard-stop blocks, silent hard-stop requirements, missing drug scope, a numeric `when` leaf whose observable is absent from `requires` (refused), a boolean patient state expressed as a `condition` leaf (accepted), incomplete governance, and forbidden encounter/narrative/trigger references.

- [ ] **Step 2: Run focused tests to verify failure**

Run: `uv run pytest tests/engine/test_rules.py -v`

Expected: collection failure because `noor.engine.rules` does not exist.

- [ ] **Step 3: Implement the closed models and validators**

Use discriminated validation by `op` or an equivalent model-level validator. Keep the public representation one closed model; do not create an open `dict[str, object]` escape hatch. The `when ⊆ requires` check is a `Rule`-level validator that walks the `when` tree collecting numeric-leaf `fact` names and asserts each is a `Requirement.observable`.

- [ ] **Step 4: Verify focused tests and the seam**

Run: `uv run pytest tests/engine/test_rules.py tests/test_import_direction.py -v`

Expected: PASS, including the existing threshold-name guard.

- [ ] **Step 5: Commit**

```bash
git add src/noor/engine/rules.py tests/engine/test_rules.py
git commit -m "feat(engine): closed expression tree and rule contracts"
```

---

### Task 4: Threshold, profile, release, and evaluation context

**Files:**
- Create: `src/noor/engine/content.py`
- Create: `tests/engine/test_content.py`

**Interfaces:**
- Consumes: `Rule`, `Snapshot`, and `GoalOfCare`.
- Produces: `ThresholdStatus`, `Citation`, `Threshold`, `Profile`, `Pins`, `CatalogueRelease`, `AmbiguousGoalOfCareError`, `EvaluationContext`.

`Citation` requires organisation, document, version, locator, jurisdiction, evidence grade, and review date. `Threshold` requires `ref`, value, unit, source family, citation, status, and optional `fallback_from`; an unpopulated threshold cannot be used by a context. `Profile` pins one source family and contains the governed disablement set; a hard-stop rule cannot be disabled. `CatalogueRelease` contains immutable release id, rules, thresholds, and profile. `Pins` contains catalogue release, profile, source family, snapshot id, engine version, and terminology version.

`EvaluationContext` validates that every rule's threshold reference exists and is populated, and that each threshold's `unit` matches the canonical unit of the observable it thresholds. `resolve_threshold(snapshot, observable, ref)` first finds exactly one active, unexpired matching goal (active means the evaluation timestamp lies in `[effective_date, expires_at)`), then falls back to the profile threshold. A resolved goal's `unit` must match the threshold's unit; the engine compares numbers in one canonical unit and never rescales a target (design §6.1). More than one matching goal raises `AmbiguousGoalOfCareError`; never choose by recency or narrowness.

- [ ] **Step 1: Write failing tests**

Cover incomplete citations, unpopulated thresholds, a threshold whose unit mismatches its observable's canonical unit (refused), hard-stop tenant disablement, cross-source-family context, profile pinning, profile fallback, one active goal winning, expired goals being ignored, a goal whose unit mismatches the threshold (refused), and two active goals raising `AmbiguousGoalOfCareError`.

- [ ] **Step 2: Run focused tests to verify failure**

Run: `uv run pytest tests/engine/test_content.py -v`

Expected: collection failure because `noor.engine.content` does not exist.

- [ ] **Step 3: Implement content models and threshold resolution**

Keep `AmbiguousGoalOfCareError` an engine exception with no patient data in its message. The evaluator records only `type(exception).__name__`.

- [ ] **Step 4: Verify**

Run: `uv run pytest tests/engine/test_content.py tests/engine/test_rules.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/noor/engine/content.py tests/engine/test_content.py
git commit -m "feat(engine): threshold, profile, release, and evaluation context"
```

---

### Task 5: Outcome and evaluation-record contracts

**Files:**
- Create: `src/noor/engine/records.py`
- Create: `tests/engine/test_records.py`

**Interfaces:**
- Consumes: `Severity`, `Rule`, `Pins`.
- Produces: `Outcome`, `DegradedBecause`, `RequirementReason`, `RequirementVerdict`, `EvaluationRecord`.

`RequirementVerdict` carries `observable`, `verdict`, `reason`, and optional `latest_age_days`; `verdict` is a closed enum with `usable` and `unusable`. `RequirementReason` is the exact eight-value enum in the global constraints. `EvaluationRecord` carries `rule_id`, `rule_version`, `outcome`, `authored_severity`, `effective_severity`, `degraded_because`, `failure_reason`, `requirement_verdicts`, and `pins`. `failure_reason` is required exactly for `evaluation_failed` and contains only the exception type name. No record field may contain `correlation_id` or `latency_ms`.

- [ ] **Step 1: Write failing tests**

Cover all six outcomes, the three degradation causes, outcome-specific severity rules, failure reason presence/absence, closed reason values, immutable records, and explicit absence of run-header fields.

- [ ] **Step 2: Run focused tests to verify failure**

Run: `uv run pytest tests/engine/test_records.py -v`

Expected: collection failure because `noor.engine.records` does not exist.

- [ ] **Step 3: Implement the models and cross-field validators**

Ensure `evaluation_failed` always caps effective severity below `stop_and_review`; a failed or degraded record can never carry a blocking action because blocks live on the rule and are applied outside the engine.

- [ ] **Step 4: Verify**

Run: `uv run pytest tests/engine/test_records.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/noor/engine/records.py tests/engine/test_records.py
git commit -m "feat(engine): outcome and evaluation-record contracts"
```

---

### Task 6: Implement per-rule evaluation and degradation

**Files:**
- Create: `src/noor/engine/evaluate.py`
- Create: `tests/engine/test_evaluate.py`
- Create: `tests/engine/test_degradation.py`

**Interfaces:**
- Consumes: `EvaluationContext`, `Snapshot`, `RequestedAction`, `Rule`, and record models.
- Produces: `evaluate(context: EvaluationContext, snapshot: Snapshot, requested_actions: tuple[RequestedAction, ...]) -> tuple[EvaluationRecord, ...]`.

Implement this exact order per rule:

1. Governance suppression produces `suppressed_by_governed_policy` and stops.
2. Scope produces `out_of_scope` and stops without reading requirements.
3. Requirements select the latest observation for the declared observable, then apply status, quality, freshness, source preference, context, mapping, and observable checks. Unusable requirements follow `on_unusable` and produce the closed `RequirementReason`.
4. Conditions evaluate the expression tree. A numeric leaf reads **only the requirement-validated value** of its observable (its `fact` is guaranteed to be in `requires` by the load-time validator, design §9.1 amendment 5), never a raw or unusable observation; it resolves a `threshold_ref` or `literal` and compares in the canonical unit. Drug conditions inspect current medications or requested actions; allergy conditions apply the SSOT verification semantics; scope conditions inspect only declared snapshot facts.
5. Evidence grade caps effective severity while retaining `triggered` and `degraded_because=evidence_grade`. The cap is one shared function — `interruptive_review if authored == stop_and_review else authored` (design §7.1) — applied once, so a record carries exactly one `degraded_because` and no double demotion.

Catch exceptions around each rule, including `AmbiguousGoalOfCareError`, and emit `evaluation_failed` with `type(exception).__name__`, `degraded_because=rule_raised`, and no message or traceback. Continue every remaining rule. Sort records by `rule_id` before returning.

- [ ] **Step 1: Write failing behaviour tests**

Cover the six outcomes, suppression-before-scope, scope-before-requirements, latest observation and freshness boundaries, accepted quality filtering, withdrawn source, ambiguous mapping, missing context, exact requested-action matching, active medication matching, allergy confirmed/unconfirmed/refuted/entered-in-error, literal and threshold comparisons, boolean composition, goal conflict, and sorted records.

- [ ] **Step 2: Run focused tests to verify failure**

Run: `uv run pytest tests/engine/test_evaluate.py tests/engine/test_degradation.py -v`

Expected: collection failure because `noor.engine.evaluate` does not exist.

- [ ] **Step 3: Implement the evaluator**

Keep helper functions private to `evaluate.py` unless a model contract requires reuse. Do not add a clock, random id, logging side effect, retry, or mutation of the snapshot, context, rules, or requested actions.

- [ ] **Step 4: Run focused tests**

Run: `uv run pytest tests/engine/test_evaluate.py tests/engine/test_degradation.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/noor/engine/evaluate.py tests/engine/test_evaluate.py tests/engine/test_degradation.py
git commit -m "feat(engine): per-rule evaluation and degradation"
```

---

### Task 7: Failure isolation and invariant tests

**Files:**
- Create: `tests/engine/test_failure.py`
- Create: `tests/engine/test_invariants.py`
- Create: `tests/engine/test_properties.py`
- Modify: `tests/test_import_direction.py`

**Interfaces:** Tests the public contracts from Tasks 2–6 and extends the device-boundary guard.

- [ ] **Step 1: Write failing invariant tests**

Cover: rule order does not affect output; identical snapshot plus requested actions plus release serialises byte-identically; changing only requested actions changes only the relevant `drug_requested` result; evaluating one rule alone equals evaluating it in a batch; one raising rule does not silence the remaining rules; failed rules never block; and hypothesis-generated expression inputs never escape the closed record contract.

- [ ] **Step 2: Extend the seam test**

Add exact checks that engine source does not name `visit_state`, `encounter_state`, `narrative`, or trigger identity; `Snapshot` and `EvaluationContext` have none of those fields; and `RequestedAction.model_fields` equals `{"kind", "subject"}`. Temporarily inject each forbidden field/name to prove each guard fails, then remove the injection.

- [ ] **Step 3: Run invariant tests to verify failures**

Run: `uv run pytest tests/engine/test_failure.py tests/engine/test_invariants.py tests/engine/test_properties.py tests/test_import_direction.py -v`

Expected: any missing implementation branch or seam violation fails with a behavioural assertion.

- [ ] **Step 4: Implement only the changes required by failing tests**

Do not weaken assertions, add exclusions, or compare exception messages. Use JSON serialisation of the immutable records for byte-identical comparisons.

- [ ] **Step 5: Run the complete test suite**

Run: `uv run pytest --cov --cov-report=term-missing --cov-fail-under=100`

Expected: PASS at 100% branch coverage.

- [ ] **Step 6: Commit**

```bash
git add tests/engine/test_failure.py tests/engine/test_invariants.py tests/engine/test_properties.py tests/test_import_direction.py
git commit -m "test(engine): failure isolation and invariant coverage"
```

---

### Task 8: Full verification, graph refresh, and plan self-review

**Files:** None unless verification exposes a defect.

- [ ] **Step 1: Run CI commands in order**

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Expected: all five commands pass.

- [ ] **Step 2: Refresh the knowledge graph**

Run: `graphify update .`

Expected: graphify updates `graphify-out/` without changing source behaviour.

- [ ] **Step 3: Inspect the final diff**

Run:

```bash
git diff --stat main...HEAD
```

Confirm that only the engine implementation, tests, SSOT/design/plan documents, and graph refresh outputs changed.

- [ ] **Step 4: Commit verification updates if required**

```bash
git commit -am "chore: verify engine evaluator phase"
```

## Definition Of Done

- `src/noor/engine/` contains the five modules and all models are frozen and closed.
- `evaluate()` is deterministic, pure, sorted, and returns one record per rule.
- All eleven engine invariants and claims 4, 10, 19, 20, 34, 35, 36, 43, 45, 47, and 48 have named tests.
- The design decisions (spec §3) and the six SSOT amendments (spec §9.1) are represented in code, tests, the SSOT, and this plan.
- No catalogue loader or clinical rule content is added.
- All five CI commands pass with 100% branch coverage.
- The graph is refreshed after code changes.
- The branch reaches `main` through a pull request with the existing `CODEOWNERS` and branch protection.

## Self-Review Checklist

- Spec coverage: sections 3–8 map to Tasks 2–7; the six §9.1 amendments are reflected in the SSOT, this plan's constraints, and the affected task steps; section 10 maps to Task 8.
- Placeholder scan: no task depends on a future unspecified model, operator, reason, or workflow field.
- Type consistency: `Snapshot`, `Rule`, `EvaluationContext`, `EvaluationRecord`, and `evaluate()` signatures are defined before later tasks consume them.
- Catalogue boundary: Python factories are used only in tests; YAML loading and content remain step 5/6 work.
