# Design — `engine`: the evaluator (SSOT §14 step 4)

**Status:** approved 2026-08-20, pending implementation plan.
**SSOT:** `docs/cds-architecture.md`. Where this design disagrees with the SSOT,
the SSOT wins — stop and ask.
**Predecessor:** `docs/superpowers/plans/2026-08-18-foundation-and-canon.md`
(§14 steps 1–3, executed; suite green at 262 tests, 100% branch coverage).

Throughout, `§N` cites the SSOT and `section N` cites this document. The two
numbering schemes overlap and the distinction is load-bearing.

## 1. Goal

Build `src/noor/engine/` — the evaluator, the outcome taxonomy, the degradation
invariant, and evaluation records — satisfying §14 step 4's verification clause:
engine invariants §8.4 (1)–(11), each as a test, plus §12.6 claims 4, 10, 19, 20,
34, 35, 36, 43, 45, 47, and 48.

The engine is pure: no I/O, no clock, no database, no network (§4.2, §8.4
invariant 8). Time enters as `evaluated_at` on the snapshot.

## 2. Scope

**In scope.** The four closed data contracts the evaluator needs — snapshot,
rule, threshold/profile/release, evaluation record — and `evaluate()` itself,
with §8.3 degradation and §8.5 per-rule failure semantics.

**Out of scope**, each with its owner:

| Deferred | Owner |
|---|---|
| `catalogue/` rule and threshold loaders; all §10.4 cross-file gates (7, 8, 9, 12, 15, 17) | §14 step 5 |
| Any rule or threshold **content**. Gate 2 refuses an uncited rule and a citation needs four-eyes clinical approval | §14 step 6 |
| `in_valueset`, date/window operators in `when`, named aggregations | The first rule that needs one (§4.3: growing the enum is a reviewed device change) |
| Product-level drug matching, ATC class views, formulary availability, SmPC propositions, dose achievability, Child-Pugh phenotype | The medication-knowledge plan (§3.2) |
| The `crcl` registry row and equation provenance | Already committed by the canon plan's assumption 14 to the plan that has a rule needing it |
| Persistence of records, the run header, `correlation_id`, `latency_ms`, whole-run fail-closed, and applying `blocked_by` to the planned-actions list (§11.6) | §14 step 7 |
| `mapping.confidence` | Unchanged from canon assumption 12 — the SSOT gives it no type, scale, or vocabulary |

## 3. Decisions taken

Four scoping decisions, made 2026-08-20 and settled:

1. **One plan for the whole of step 4** — contracts and evaluator on one branch,
   one PR, mirroring the canon plan's shape.
2. **Medication facts go in at the ingredient anchor only** —
   `ingredient_id` plus `mapping_status`. `drug_active` resolves as ingredient-set
   membership, which is §R-4's "narrowest defensible scope" and exactly what
   step 6's metformin/eGFR workflow needs. The full §3.2 identity model would add
   five models and two enums whose fields no rule may reference yet, and would
   force the `mapping.confidence` question a second time. `extra="forbid"` blocks
   unknown *inbound* keys; it does not freeze the schema against later fields, and
   the durable artefact is the §8.2 record pinning `snapshot_id` — not the
   snapshot's shape — so growing the model later is not a migration.
3. **Minimal operator vocabulary v1** — see section 5.2. Nothing in step 4's verify
   clause exercises value sets, window operators, or aggregations, and freshness
   windows are already carried by `max_age_days` in the `requires` manifest.
4. **No `catalogue/` work and no content in this plan.** Rules, thresholds, and
   profiles are constructed in Python by test factories.
5. **A `drug_requested` operator, and the engine reads a two-field projection of
   the planned action.** Without it a contraindicated *start* cannot be caught:
   §7.1's own rule keys on `drug_active`, which is false for a patient not yet on
   the drug, so a new metformin order for a patient at eGFR 25 records
   `not_triggered` and nothing blocks. The engine's `RequestedAction` carries
   `kind` and `subject` only — never `encounter_id`, `state`, `detail`, or
   `blocked_by` — so a rule can see *what is proposed* and never *where the
   encounter is*. Two SSOT amendments are pending on this (section 9).

## 4. Module layout

Five modules under `src/noor/engine/`.

The dependency direction `canon ← engine ← catalogue` (§4.1, enforced by
`tests/test_import_direction.py`) **forces** the rule, threshold, and profile
models into `engine/`: the engine cannot import `catalogue`, and §4.1 types the
engine as `(snapshot, catalogue) -> evaluation records`, so the models of what a
catalogue contains must sit where the engine can reach them. `catalogue/` gets
its schema-only YAML loaders at step 5, the same way `registry_loader.py`
followed the registry model in canon.

| Module | Holds |
|---|---|
| `snapshot.py` | `Snapshot`, `SnapshotMedication`, `AllergyRecord`, `AllergyStatus`, `GoalOfCare`, `RequestedAction` |
| `rules.py` | `Rule`, the closed `Operator` enum, `Scope`, `Requirement`, `Monitor`, `Then`, `Governance` |
| `content.py` | `Threshold`, `Citation`, `Profile`, `CatalogueRelease`, `EvaluationContext`, `Pins` |
| `records.py` | `Outcome`, `DegradedBecause`, `RequirementVerdict`, `EvaluationRecord` |
| `evaluate.py` | `evaluate()` |

All models extend `NoorModel` from `noor.canon.models` — `frozen=True,
extra="forbid"`. §4.2's closed-contract discipline is the same discipline canon
already applies to captures.

## 5. The contracts

### 5.1 `Snapshot` (§4.2, §5, §5.5, §5.6)

Closed. Every field is either a `canon` output or a patient fact carrying its own
provenance (§4.2 point 3).

```
snapshot_id: str                 # minted by app/, copied onto every record's pins
evaluated_at: AwareDatetime      # time enters as data (§4.2); the engine never calls now()
patient_id: str
age_years: int
observations: tuple[CanonicalObservation, ...]   # canon's model, verbatim
medications: tuple[SnapshotMedication, ...]      # ingredient_id + mapping_status
allergies: tuple[AllergyRecord, ...]             # §5.5, full record
allergy_status: AllergyStatus                    # no_known_allergy | not_asked | recorded
conditions: frozenset[str]                       # Noor condition concepts
goals_of_care: tuple[GoalOfCare, ...]            # §5.6
```

Rejected observations stay in the snapshot. A requirement's `min_quality` is what
filters them, and `requirement_verdicts` needs to be able to say *the latest
result exists and is rejected* — which is a different fact from *no result*.

`SnapshotMedication` is two fields: `ingredient_id` and `mapping_status`
(`MappingStatus` reused from `canon.models`). An `ambiguous` or `unmapped` entry
for a named ingredient makes the requirement unusable, so the rule degrades to
`indeterminate` rather than guessing — the same refusal canon makes on units
(§6.3), and §3.2's "never auto-map on name similarity alone".

`AllergyStatus` is a first-class field precisely because §5.5 rule 2 forbids
inferring "no known allergy" from an empty `allergies` tuple. An unasked patient
and a cleared patient are opposite facts.

`RequestedAction` is a **two-field projection** of §11.6's `planned_action`:
`kind` (`medication_start | medication_stop | medication_dose_change | lab_order |
referral | plan_change`) and `subject` (the thing `order_of` matches against).
Nothing else crosses. `encounter_id` would put encounter identity in front of a
rule; `state: draft | final` is workflow position and is exactly what invariant 10
forbids a rule to branch on; `detail` and `blocked_by` are `app/`'s.

The projection is what makes `drug_requested` defensible against invariant 10.
The invariant's stated risk is that "the moment a rule branches on visit state,
the workflow becomes part of the regulated device and every UI change re-opens
clinical validation" (§8.4). A UI change cannot alter what `medication_start` /
`metformin` means — that pair is clinical intent, not workflow position. The
narrow projection is the mechanism that keeps the distinction enforceable rather
than merely asserted, and the seam test checks it (section 8.2).

**Absent by construction, and tested as absent:** visit state, encounter state,
trigger identity, and any free-text narrative or chief complaint (§8.4 invariant
10, §8.1). `CanonicalObservation.encounter_id` rides inside the snapshot and is
never read — canon already carries it as an inert field.

### 5.2 `Rule` (§7.1) and the operator vocabulary (§4.3)

Fields as §7.1: `id`, `version`, `release_status`, `category`, `severity`,
`scope`, `drug_scope_level`, `requires`, `monitors`, `when`, `then`,
`governance`.

`Operator` is a **closed enum**. Pydantic rejects an unrecognised member at load,
which is what makes §10.4 gate 12 enforceable at step 5 and keeps §4.3's standing
objection answerable by the build rather than by assurance. Version 1:

- Boolean composition: `all`, `any`, `not`
- Numeric comparison against a `threshold_ref` or a literal: `lt`, `le`, `gt`,
  `ge`, `eq`, `ne`
- `drug_active` — ingredient-level membership in the patient's current therapy
- `drug_requested` — ingredient-level match against `requested_actions`, so a
  contraindicated *start* is catchable. `drug_scope_level` (§7.1(e)) governs it
  exactly as it governs `drug_active`; at v1 that is `ingredient`
- An allergy predicate carrying `verification_status` and `severity`, so §10.4
  gate 16 has a shape to check at step 5
- Scope predicates: condition membership, age bounds, boolean patient attributes

`Requirement.observable` holds a **snapshot fact key**, not only a canon
observable id. §7.1's own example writes `- observable: active_medications`
alongside `- observable: egfr`, so the field name is the SSOT's and its value
space is wider than the registry. `min_quality` and `max_age_days` apply only
where the fact resolves to an observation.

Single-rule §10.4 gates land as model validators here, which is what makes §8.4
invariants 2, 3, and 4 testable at step 4 — they are load-time refusals, not
evaluator behaviour. Cross-file gates stay step 5's.

### 5.3 `EvaluationContext` (§7.3, §10.5)

The pinned release: rules, thresholds keyed by `ref`, the tenant profile, and the
`Pins` copied onto every record — `catalogue_release`, `profile`,
`source_family`, `engine_version`, `terminology_version`.

`Threshold` carries §7.3's shape including `status`
(`unpopulated | populated | clinician_approved`), the full citation, and
`fallback_from`. Invariant 3 — no rule loads referencing an `unpopulated`
threshold — is a context-construction validator.

**No trigger field.** §8.1: a rule cannot ask which trigger invoked it, or
invariant 5 would not hold. The absence is structural, not conventional.

### 5.4 `EvaluationRecord` (§8.2)

`rule_id`, `rule_version`, `outcome`, `authored_severity`, `effective_severity`,
`degraded_because`, `failure_reason`, `requirement_verdicts`, `pins`.

Six outcomes: `triggered`, `not_triggered`, `indeterminate`, `out_of_scope`,
`suppressed_by_governed_policy`, `evaluation_failed`. Three `degraded_because`
values: `requirements_unmet`, `evidence_grade`, `rule_raised`.

`failure_reason` holds the **exception type name only** — never the message and
never a traceback (§8.5). A message can carry a formatted value and a traceback
carries memory addresses and line numbers, either of which would differ between
two runs of one snapshot and break invariant 6. It is `None` for every outcome
but `evaluation_failed`.

`correlation_id` and `latency_ms` are **excluded by construction**. Either one
inside the record breaks two invariants at once (§8.2): a freshly minted id and a
wall-clock reading differ on every run, so no two evaluations of one snapshot
could compare equal (invariant 6), and measuring elapsed time needs a clock
(invariant 8). They belong to the run header, stamped by `app/` at step 7.

## 6. `evaluate()`

```
evaluate(context: EvaluationContext, snapshot: Snapshot,
         requested_actions: tuple[RequestedAction, ...]) -> tuple[EvaluationRecord, ...]
```

Per rule, independently, holding no cross-rule state (invariants 5 and 7):

1. **Governance suppression** (§10.5) → `suppressed_by_governed_policy`, stop.
2. **Scope** (§8.2) → `out_of_scope`, stop. Requirements are never read.
3. **Requirements** — each produces a `RequirementVerdict`. Any unusable
   requirement with `on_unusable: indeterminate` → `indeterminate` plus §8.3
   degradation.
4. **Conditions** → `triggered` or `not_triggered`.

A rule that raises at any step is caught and recorded as `evaluation_failed`
(section 7 below). Records are returned sorted by `rule_id`.

**`requested_actions` enters the engine as rule input and nothing else.** It is
read by `drug_requested` inside `when`, and by no other part of the evaluator.
Applying a block — setting `blocked_by` on a planned action so it cannot be marked
`final` (§11.6) — is a join `app/` performs at step 7 between the triggered
records and their rules' `then.blocks.order_of`. The engine cannot write encounter
state, and §11.6 gives the list to the encounter, so the engine has no business
mutating it.

Invariant 1 is therefore enforced **at load rather than at application**: only a
`stop_and_review` rule may carry `blocks`, and `blocks` may name only an order
action. A rule that cannot express a non-order block cannot perform one, whatever
`app/` does downstream. That is a stronger guarantee than checking at the point of
application, and it is testable inside the device boundary.

**Deviation from §8.1's signature, approved 2026-08-20.** §8.1 types the call
`-> EvaluationRun`, but §8.2 is explicit that the run header is `app/`'s and that
`correlation_id` and `latency_ms` must not be engine output. `evaluate()`
therefore returns the record tuple, and `app/` wraps it in the run header at step
7. Faithful to §8.2; a naming departure from §8.1's signature line.

**Ordering assumption — suppression precedes scope.** A governance disablement is
a property of the release and the profile, patient-independent. Zero-firing
surveillance (§11.9) should see a suppression whether or not the patient was in
scope; the reverse order hides suppressions behind `out_of_scope`.

**Ordering is load-bearing at step 2 and the SSOT says why** (§8.2): folding
`out_of_scope` into `indeterminate` would open a `carried_forward` obligation for
every non-applicable rule on every patient, and folding it into `not_triggered`
would destroy the discrimination between "sixty in-scope patients, none matched"
and "a profile edit narrowed scope to nobody".

### 6.1 Threshold resolution (§7.3)

Strict precedence, and the order is the point:

1. An active, unexpired `goal_of_care` for **this patient on this observable**.
2. The profile's pinned `source_family` threshold.

A rule resolving against a goal records which one. §5.6 exists for named
accountability; a card showing a frail patient's 150 target without saying whose
decision that was is worse than showing the guideline number. The engine never
deduces a goal of care from past readings.

## 7. Degradation and failure

### 7.1 Degradation (§8.3) — three causes, three records

| Cause | Outcome | `degraded_because` | Severity effect |
|---|---|---|---|
| Input absent or unusable | `indeterminate` | `requirements_unmet` | `stop_and_review` → `interruptive_review` |
| Input present, lower evidentiary grade | `triggered` | `evidence_grade` | capped below `stop_and_review` |
| The rule raised | `evaluation_failed` | `rule_raised` | capped below `stop_and_review` |

Evidence grade **caps severity and never manufactures indeterminacy** (claim 48).
An unconfirmed allergy is data Noor has, graded — reporting "cannot assess
safely" about a finding the engine did in fact reach is the more dangerous
falsehood, because it reads as a defect and invites a clinician to substitute
judgment for a finding Noor is holding.

Authors cannot opt out. A `stop_and_review` rule whose requirements are unmet
degrades and never blocks.

### 7.2 Failure (§8.5) — a single rule raises

Caught per rule. Recorded as `evaluation_failed` with the exception type and the
rule version. **Every remaining rule still runs** (invariant 11, claim 43) — one
malformed threshold must not silence the other fifty-nine.

**Never retried.** A retry that succeeds against an unchanged snapshot has
disproved invariant 6, which makes it a defect report, not a recovery.

Whole-run fail-closed (§8.5's second level), the surveillance event, and the
`carried_forward` obligation are `app/`'s at steps 7 and 11. The engine's
contract is only that a raising rule never ends the run.

## 8. Testing

`docs/testing-standards.md` governs *how*; §12 governs *what must be true*.
Arrange-Act-Assert, sentence names, behaviour not implementation, boundary values,
100% branch coverage with no exclusions.

New files, all under `tests/engine/` beside the existing `tests/canon/` and
`tests/catalogue/`: `test_snapshot.py`, `test_rules.py`, `test_content.py`,
`test_records.py`, `test_evaluate.py`, `test_invariants.py`,
`test_degradation.py`, `test_failure.py`, `test_properties.py`. Factories
(`make_snapshot`, `make_rule`, `make_threshold`, `make_context`) extend
`tests/conftest.py`.

### 8.1 Verify-clause coverage

| §14 step 4 clause | Proven by |
|---|---|
| Invariant 1 — only `stop_and_review` blocks, and only the named order action | Load-time validators: a non-`stop_and_review` rule carrying `blocks` is refused; `blocks` may name only an order action (§10.4 gate 6). `test_rules.py` |
| Invariants 2, 3, 4 — load-time refusals | `Rule` and `EvaluationContext` validators, tested in `test_rules.py` / `test_content.py` |
| Invariant 5 — evaluation order never affects output | Evaluate one snapshot twice under two rule orderings; record tuples compare equal |
| Invariant 6 — identical snapshot + requested actions + release ⇒ byte-identical records | Serialised record tuples compare equal; header excluded by construction. Also a negative: varying `requested_actions` alone *does* change a `drug_requested` rule's record, which is why amendment (2) is needed |
| Invariant 7 — no rule reads another rule's output | Each rule evaluated alone against the same snapshot yields the record it yields in the batch |
| Invariant 8 — no I/O, no clock | `tests/test_import_direction.py`, already covering `engine` |
| Invariant 9 — a rule is a pure function of snapshot and catalogue | Same seam test plus determinism |
| Invariant 10 — no encounter state, no narrative; the planned-action projection is `kind` + `subject` only | The seam-test extension in section 8.2 |
| Invariant 11 — a raising rule never ends the run | `test_failure.py` |
| Claim 4 / 10 — a removed datum degrades a `stop_and_review` to `indeterminate` at `interruptive_review`, never `not_triggered`; the record count equals every rule considered, no outcome excluded | `test_degradation.py`, `test_evaluate.py` |
| Claim 19 — scope resolves before requirements | `test_evaluate.py`: an out-of-scope rule with an unusable requirement records `out_of_scope` |
| Claim 20 — the snapshot refuses an undeclared field | `test_snapshot.py` |
| Claim 34 / 35 — an unconfirmed allergy degrades a `stop_and_review` rather than blocking; an unasked allergy history is `indeterminate` and never reads as "no known allergy" | `test_degradation.py` |
| Claim 36 — a CrCl rule with no weight is `indeterminate` and never silently substitutes an eGFR | `test_evaluate.py`: a rule requiring `crcl` against a snapshot holding `egfr` and `creatinine` |
| Claim 43 — one raising rule yields `evaluation_failed` without silencing the rest | `test_failure.py` |
| Claim 45 — determinism under a second evaluation of one snapshot | `test_invariants.py` |
| Claim 47 — a `refuted` or `entered_in_error` allergy is `not_triggered` whatever the authored severity, so nothing reaches rendering | `test_evaluate.py` |
| Claim 48 — evidence grade caps `effective_severity` without ever producing `indeterminate` | `test_degradation.py` |

Beyond the verify clause, decision 5 owes two tests of its own in
`test_evaluate.py`, since neither case appears in §14 step 4's list:

- A patient **not** on metformin with eGFR 25 and a planned `medication_start` of
  metformin: the `drug_requested` rule records `triggered` at `stop_and_review`.
  Same patient with an empty `requested_actions`: `not_triggered`. That pair is
  the whole point of the operator.
- A patient **on** metformin with eGFR 25 and nothing planned: the `drug_active`
  continuation rule still records `triggered`, so the discontinuation advice
  survives a visit where no order is proposed. This is the case the withdrawn
  assumption would have silenced.

### 8.2 Seam-test extension (invariant 10)

Three additions to `tests/test_import_direction.py`, mirroring
`test_canon_never_names_a_treatment_threshold`:

1. `engine` source may not name `visit_state`, `encounter_state`, or `narrative`.
   **Precise names, not the substring `encounter`** —
   `CanonicalObservation.encounter_id` legitimately rides inside the snapshot.
   `trigger` is on the list too: §8.1 forbids a rule asking which trigger invoked
   it.
2. `Snapshot` and `EvaluationContext` field sets contain no such field, the same
   shape as `test_the_registry_declares_no_treatment_threshold_field`. A rule
   cannot ask what it cannot see.
3. **`RequestedAction`'s field set is exactly `{kind, subject}`** — an equality
   assertion, not a subset one, so adding `encounter_id`, `state`, `detail`, or
   `blocked_by` later fails the suite rather than passing quietly. This is the
   only thing standing between the amendment as approved and the amendment as
   implemented, so it is asserted narrowly and deliberately.

All three must be proved to have teeth by temporary injection, as Task 2 did.

## 9. Assumptions

1. **Suppression precedes scope** (section 6). Patient-independent facts are
   recorded regardless of scope so surveillance can see them.
2. **`Requirement.observable` holds snapshot fact keys**, per §7.1's own example.
3. **`evaluate()` returns records, not an `EvaluationRun`** (section 6), per
   §8.2's split.
4. **Rejected observations are present in the snapshot**, so `min_quality` can
   filter them and a verdict can distinguish "latest is rejected" from "no
   result".
5. **`engine_version` is a module constant**, copied into `Pins`. Reading it is
   not a clock read and not I/O.
6. **The engine's `RequestedAction` is `kind` + `subject` only** (section 5.1). The
   projection is the mechanism, not a convention.

An earlier draft carried a seventh assumption — that an order-blocking rule with
no matching requested action records `out_of_scope`. It is **withdrawn**, and
`drug_requested` is why. A start rule whose `drug_requested` does not match is
simply `not_triggered`: the rule was in scope, the data was usable, and the
condition did not hold. No new outcome semantics are needed, and the withdrawn
version would have suppressed the discontinuation advice of a continuation rule
whose finding was real.

### 9.1 Two SSOT amendments, pending explicit approval

Neither invariant is named in §0's list, but §8.4 states that invariant 10 is what
keeps §11 outside the device boundary, and §0 protects the device boundary's data
contract (§4.2). Both are therefore treated as protected. **No implementation
starts until these are approved and committed.**

**(1) §8.4 invariant 10 — permit the projection.** Current text: "No rule reads
encounter state or free-text narrative. A rule cannot ask which visit state,
trigger, or workflow step invoked it, and it cannot see the patient's textual
complaint." Proposed addition:

> A rule may read the `kind` and `subject` of a planned action passed as
> `requested_actions` (§8.1, §11.6), and nothing else from that list — not
> `encounter_id`, not `state`, not `detail`, not `blocked_by`. That pair is
> clinical intent, invariant under any UI change, and §8.1 already supplies it to
> the evaluator. The remaining fields are encounter state and stay outside.

Nothing is removed. Visit state, trigger, workflow step, and narrative remain
unreadable.

**(2) §8.4 invariant 6 — name the third input.** Current text: "Identical snapshot
+ identical catalogue release ⇒ byte-identical evaluation *records*." With
`drug_requested`, records vary with `requested_actions`, so the sentence is false
as written. Proposed:

> Identical snapshot + identical requested actions + identical catalogue release ⇒
> byte-identical evaluation *records*.

This preserves the intent exactly — determinism over the whole input — and the
scoping sentence about the run header is unaffected. The alternative, folding
`requested_actions` into the `Snapshot`, was rejected: §11.6 assigns the list to
the encounter and §8.1 keeps the argument separate.

Additive, unprotected, and not blocking: §7.1 should gain a `drug_requested`
example line so the operator is documented where authors will look for it.

If any of these is wrong, correct it before the implementation plan is written.

## 10. Definition of done

CI's five commands green, in order, at 100% branch coverage:

```
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Every row of the table in section 8.1 has a passing named test. The branch reaches
`main` by pull request — §7.5's four-eyes approval, enforced by `CODEOWNERS` and
branch protection. `graphify update .` after the final task.
