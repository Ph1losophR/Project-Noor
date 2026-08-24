# Design — `catalogue`: loader, compiler, validator (SSOT §14 step 5)

**Status:** approved 2026-08-24, pending implementation plan.
**SSOT:** `docs/cds-architecture.md`. Where this design disagrees with the SSOT,
the SSOT wins — stop and ask.
**Predecessor:** `docs/superpowers/plans/2026-08-22-engine-evaluator.md`
(§14 step 4, executed and merged in `#2`; suite green at 360 tests, 100% branch
coverage).

Throughout, `§N` cites the SSOT and `section N` cites this document. The two
numbering schemes overlap and the distinction is load-bearing.

## 1. Goal

Build `src/noor/catalogue/` — the loader, compiler, and validator that turn a
content directory into a validated `EvaluationContext`, refusing any content that
violates §10.4. This satisfies §14 step 5's verify clause: §12.6 claims 18, 20,
21, 42, and 49 in full, and claim 29 in part — its operational-policy half moves
to steps 8–12 for the reason section 9.1 gives. It stops short of §10.4 **gate** 9
(release comparison), which the SSOT itself orders into step 15 because it needs a
golden set.

`catalogue` imports `canon` and `engine`; nothing imports `catalogue` except
`app`, which does not exist yet (§4.1, §4.2). The compiler performs the one
filesystem read the boundary permits above `engine` — content load — and no
other I/O, no clock, and no network.

## 2. Scope

**In scope.** Seven modules under `src/noor/catalogue/`; the remaining single-rule
and cross-file §10.4 gates not already enforced by `engine` models (3, 8, 13,
15a, 15b, 16, 17); two closed valueset registries and a terminology charter that
close the `concept`, `ingredient_id`, and code-system authoring spaces; the
`content/valuesets/` and `content/terminology/charter.yaml` infrastructure
content; the `*.cases.yaml` boundary-coverage harness; and four cleanups of dead
or superseded engine code (section 8).

**Out of scope**, each with its owner:

| Deferred | Owner |
|---|---|
| Gate 9 / release comparison (§12.2) over the golden set | §14 step 15 — the SSOT's own ordering; needs a golden set |
| The §7.5 plain-language rendering generator and the CI job that posts it into the PR | Its own spec. **Step 6 content is not governance-complete without it** (the approver signs against the rendering, not the diff) — flagged, not silently dropped |
| Any rule, threshold, valueset-of-clinical-content, golden, or profile **content** with clinical meaning. Gate 2 refuses an uncited rule and a citation needs four-eyes approval | §14 step 6 |
| The `in_valueset` operator, date/window operators, named aggregations | The first rule that needs one (§4.3: growing the enum is a reviewed device change). **The section 5 valuesets are compile-time authoring registries, not this operator** |
| The `crcl` registry row and equation provenance | Already committed by the canon plan's assumption 14 to the plan that has a rule needing it |
| Persistence, the run header, `correlation_id`, `latency_ms` | §14 step 7 |
| Claim 29's **operational-policy** half — refusing a profile that omits the escalation policy, ageing thresholds, or per-kind obligation defaults (§10.5) | §14 steps 8–12 — those fields are §11 app-layer data the packages that consume them own; see section 9.1 |
| Closing `Requirement.observable` to non-measured data families (`active_medications`, allergy history) and the `SnapshotMedication` effective time that would make `max_age_days` on them enforceable | Deferred; see section 9 and amendment 5 |

## 3. Decisions taken

Five scoping decisions, made 2026-08-24 and settled with the user:

1. **Loader + compiler + gates on one branch, one PR** — mirroring the canon and
   engine plans. The design note, plan, code, and the six SSOT amendments
   (section 10) travel to `main` together, so the §7.5 four-eyes review covers
   the amendments and the code at once.
2. **`concept` and `ingredient_id` are closed by seeded-on-demand valuesets**
   (section 5). `content/valuesets/conditions.yaml` and `ingredients.yaml` become
   closed id registries mirroring the observable registry. The compiler refuses a
   rule naming a concept or ingredient absent from them. Seeded with only the
   entries the SSOT already names — no SEML 2023 transcription in an
   infrastructure step. Growing a set is a reviewed content PR, like a threshold.
3. **Gate 15 uses a registry marker plus a threshold field** (section 5), not
   free-text matching. The registry marks which observables are renal metrics;
   the threshold states which metric its cited number is in; the compiler refuses
   a renal rule that omits `renal_metric` and one whose `renal_metric` disagrees
   with its threshold. This finally makes `renal_metric` carry information it does
   not carry today, where a validator only permits it to equal its own
   requirement's observable.
4. **Infrastructure content only lands in `content/`.** The two valuesets and the
   charter are committed; no rules, thresholds, or golden cases. The compiler and
   the `*.cases.yaml` harness are proven entirely against synthetic YAML fixtures
   built under `tmp_path`. `content/` stays clinically clean, and step 6 remains
   "the first real rule" exactly as the SSOT defines it.
5. **`Requirement.observable` is an allowlist of registered observables only**
   (section 9). The compiler refuses anything else. §7.1's canonical example rule,
   which requires `active_medications`, knowingly does not load until the
   medication list carries an effective time — recorded as amendment 5, so the
   contradiction is visible at merge rather than silent at evaluation.

## 4. Module layout

```
src/noor/catalogue/
  content_yaml.py    # _ContentLoader, lifted out of registry_loader.py.
                     #   The one schema-only YAML door (§7.5, gate 13).
  registry_loader.py # unchanged behaviour; imports the shared loader.
  valuesets.py       # ConditionValueset, IngredientValueset — closed id registries.
  terminology.py     # TerminologyCharter, per-system licence status (gate 17).
  loader.py          # per-kind load: rules, thresholds, profiles, releases.
  cases.py           # CaseFile / CaseRow, and gate 8's boundary-coverage check.
  compiler.py        # compile_release(content_dir, release_id) -> EvaluationContext.

content/
  valuesets/conditions.yaml       # NEW — closed condition-concept ids.
  valuesets/ingredients.yaml      # NEW — closed ingredient ids.
  terminology/charter.yaml        # NEW — LOINC, SNOMED CT licence status.
  observables/registry.yaml       # MODIFIED — renal_metric marker on egfr, creatinine.
```

`content_yaml.py` is named so no reader has to wonder whether a module called
`yaml.py` shadows PyYAML. The compiler is the only public entry point; everything
else is loader detail it composes.

**Why the split.** Each module answers one question a bug report asks by name:
"which YAML door let this in" → `content_yaml.py`; "why did this ingredient not
match" → `valuesets.py`; "why was this cases file rejected" → `cases.py`. A single
`loader.py` doing all of it would be the file that grows until nobody holds it in
context.

## 5. The content-schema additions

### 5.1 Valuesets (§7.4, closes the `concept` / `ingredient_id` spaces)

```yaml
# content/valuesets/conditions.yaml
concepts:
  - type_2_diabetes
  - on_dialysis
  - cognitive_impairment
```

`ConditionValueset` and `IngredientValueset` are `NoorModel`s wrapping a
`frozenset[str]` of ids, loaded through `content_yaml.py`, refusing a duplicate id
the way `registry_loader` already refuses a duplicate observable. Seeded with only
the concepts the SSOT names in §7.1 and §5.5 (`type_2_diabetes`, `on_dialysis`,
`cognitive_impairment`); `ingredients.yaml` starts empty or with the single
ingredient §7.1's example rule names.

**These are compile-time authoring registries.** They close the string space an
author writes into, so `{condition: on_dialysys}` (a typo) is refused at merge
rather than silently never matching at evaluation. They are **not** the
`in_valueset` runtime operator — no operator is added, and `Operator` is
untouched.

### 5.2 Terminology charter (§3.3, gate 17)

```yaml
# content/terminology/charter.yaml
code_systems:
  - system: LOINC
    licence: "LOINC and RELMA Terms of Use"
    licence_status: perpetual_no_fee_conditional
    edition: "2.77"
    effective_time: "2025-02-20"
    module: observation_codes
    owner: "clinical-terminology-lead"
    review_cadence_days: 180
    attribution_notice: "<the §3.3 prescribed notice>"
  - system: SNOMED-CT
    licence: "SFDA / MLDS national licence"
    licence_status: outstanding          # §13.2 item 3 — MLDS licence not yet held
    edition: "unknown"
    effective_time: null
    module: condition_concepts
    owner: "clinical-terminology-lead"
    review_cadence_days: 90
    attribution_notice: null
```

`TerminologyCharter` names, per code system, the six things §3.3 enumerates — the
licence and its current status, the edition/release, the effective time, the
module, a named owner, and the review cadence — plus the attribution notice the
licence obliges. Gate 17 refuses a rule citing a code system the charter does not
name, or a charter entry with no licence status. `effective_time` and
`attribution_notice` are nullable because a system whose licence is `outstanding`
has neither yet; every other field is required, so an entry cannot be added
without an owner and a cadence. SNOMED CT is recorded `outstanding`; §2.4's rule
(valuesets carry `system` + `code`, no reproduced displays) is what keeps the
catalogue distributable meanwhile, and this step reproduces no displays.

### 5.3 Renal-metric marker (§6.6 and §7.3, gate 15)

- Registry entries gain `renal_metric: egfr | crcl | null` (two lines, on `egfr`
  and `creatinine` today) — this marks *which observables are renal metrics*.
- `Threshold` gains `states_metric: egfr | crcl | null` in `engine/content.py` —
  which metric the cited number is expressed in.
- `Requirement.renal_metric` (already on the model, `engine/rules.py`) stays where
  it is: it declares which metric *the rule intends*. Its current validator is
  replaced — see cleanup 4.

The compiler's gate-15 pass: any rule whose `requires` names a registry-marked
renal observable **must** declare `renal_metric` (15a); and that `renal_metric`
**must** equal the `states_metric` of every threshold the rule references (15b).
eGFR and CrCl diverge by weight — this is the §12.6 claim 36 divergence the gate
exists to stop — and no substring of a citation is read to catch it.

## 6. What I am deliberately not building

**Gate 12's JSON-Schema field-reference pass (§4.2 point 2).** §4.2 point 2 was
written before §4.3.1 fixed the expression shape as one closed model. After that,
a separate pass validating rule field references against the snapshot's exported
JSON Schema has nothing left to catch: each operator has a Pydantic-fixed field
set, `fact` is closed by the observable registry, `concept` and `ingredient_id`
become closed by section 5's valuesets, and `age` reads one declared scalar. The
pass would be dead code. §12.6 claim 20's second half — "a rule referencing a
field absent from the snapshot schema is refused" — still gets a named test,
satisfied by the closed `Expression` plus the three registries rather than by a
schema walk. This is recorded as amendment 4, not skipped in silence.

## 7. The compiler

```python
def compile_release(content_dir: Path, release_id: str) -> EvaluationContext:
    ...
```

Order:

1. Load the three registries — observable, condition valueset, ingredient
   valueset — and the terminology charter, each through `content_yaml.py`.
2. Load `thresholds/*.yaml`, `rules/*.yaml`, `profiles/<name>.yaml`,
   `releases/<release_id>.yaml`. **Every `engine` model validator fires here** —
   `Rule`, `Threshold`, `CatalogueRelease` already enforce gates 1, 2, 4, 5, 6,
   7, 10, 14 as construction refusals, plus the two new single-rule gates 3 and
   16 (section 4 table).
3. Cross-file gates the whole tree is needed for: 8 (every rule has a
   `*.cases.yaml` with at, just-below, and just-above rows per referenced
   threshold), 15a/15b (renal metric), 17 (code system in charter), and the
   `concept` / `ingredient_id` / `Requirement.observable` closures against the
   registries.
4. Construct and return the `EvaluationContext`, whose own validators (source
   family not blended, every threshold populated and commensurable) are the last
   refusals.

Bad content raises at the first gate it trips. The function has no partial-success
mode: a content tree either compiles whole or is refused.

### Gate map

| Gate | Lands in | Why there |
|---|---|---|
| 3 — hard stop + `role_doubling: true` | `engine/rules.py` validator | single-rule; joins its five siblings |
| 16 — hard-stop allergy needs `confirmed` + `severe` | `engine/rules.py` validator | single-rule; walks `when` for allergy leaves |
| 13 — schema-only YAML | `content_yaml.py` | one loader, every content kind |
| 8 — cases file + boundary rows | `cases.py`, called by compiler | needs the filesystem |
| 15a — renal rule must declare `renal_metric` | `compiler.py` | needs the registry marker |
| 15b — `renal_metric` vs threshold `states_metric` | `compiler.py` | cross-file |
| 17 — code system in charter | `terminology.py` + compiler | needs the charter |
| `concept` / `ingredient_id` / `Requirement.observable` closure | `valuesets.py` + compiler | new (section 5, section 9) |
| 1, 2, 4, 5, 6, 7, 10, 14 | already in `engine` models | single-rule / single-release; landed in step 4 |
| 9 — release comparison | **out** — §14 step 15 | needs the golden set |
| 12 — JSON-Schema field pass | **not built** — section 6 | subsumed by the closed `Expression` |

## 8. Cleanups this diff touches

Surgical, each traceable to a file this step already edits (CLAUDE.md rule 3):

1. Delete the no-op `_goal_units_match_threshold_units` at `engine/content.py`
   (its own docstring calls it a placeholder) — `Threshold` is edited in that file
   for `states_metric` anyway, and the real goal/threshold unit check already
   lives in `resolve_threshold` via `ForeignGoalUnitError`.
2. Delete `FORBIDDEN_REQUIREMENT_OBSERVABLES` and its denylist validator in
   `engine/rules.py`, superseded by section 9's allowlist — an allowlist subsumes
   a denylist, which is §4.2's own argument.
3. Refresh `CLAUDE.md` and `AGENTS.md`: "Current State" still says there is no
   engine and points at the (now recreated) `docs/superpowers/specs/`. Both files
   are edited together, per their footer.
4. Replace `_renal_metric_matches_observable` at `engine/rules.py:289`. Today it
   only permits `renal_metric` to equal its own requirement's `observable`, which
   makes the field carry no information and would wrongly refuse the legitimate
   `observable: creatinine, renal_metric: crcl` case — exactly the case gate 15
   exists to govern. It is superseded by the registry marker plus `states_metric`
   (section 5.3), so it is deleted, not kept alongside them.

## 9. `Requirement.observable` — the one SSOT conflict, and its resolution

Closing the `Requirement.observable` string space exposes a genuine contradiction
in the SSOT, which decision 5 resolves:

- §7.1's canonical example rule declares
  `requires: [{observable: active_medications, max_age_days: 1}]`.
- `active_medications` is not in the observable registry (ten measured
  observables), and `engine/evaluate.py` resolves every requirement by searching
  `snapshot.observations`.
- `SnapshotMedication` carries only `ingredient_id` and `mapping_status` — **no
  timestamp** — so `max_age_days: 1` on it is unenforceable in principle, not
  merely unimplemented.

Today a requirement on `active_medications` therefore resolves `no_result` →
unusable → the rule is *always* `indeterminate`, silently.

**Resolution (decision 5):** the compiler's allowlist is the registered
observables only. Anything else is refused at compile time. §7.1's example is not
loadable as written until `SnapshotMedication` gains an effective time — recorded
as amendment 5 with a deferred item, so the gap is visible at merge. Widening the
allowlist to non-measured data families, or adding the medication timestamp now,
were both considered and declined: the timestamp is a §4.2 device-boundary
data-contract change, which §0 makes a security-critical constant needing its own
approval, and it does not belong in an infrastructure step.

`drug_active` / `drug_requested` leaves are unaffected — they read
`ingredient_id` against `snapshot.medications` directly and declare no requirement.

### 9.1 Claim 29 — the second conflict, and its resolution

§14 step 5's verify clause names §12.6 claim 29: "a tenant profile omitting an
operational policy is refused at load, never silently defaulted (§10.5)." The
engine's `Profile` cannot carry that test today:

- `Profile` holds `name`, `version`, `source_family`, and `disablements` — the
  four things `evaluate()` reads.
- §10.5's operational policy is the role-routing table (§11.8), the calendar dates
  (§11.3), the emergency pathway content (§13.2 item 7), the escalation policy
  (§11.2), the obligation ageing thresholds (§11.9), and the per-action-kind
  obligation defaults (§11.6). **Every one is a §11 app-layer concern**, consumed
  by packages that do not exist until steps 8–12. The engine reads none of them.

Adding them to `Profile` now would create required fields whose only purpose is to
be validated — never read — which is the speculative scaffolding CLAUDE.md rule 2
and the engine design's decision 2 both refuse.

**Resolution:** step 5 proves the *refusal pattern* — a profile omitting a
required declared field is refused at load, never silently defaulted — against the
fields `Profile` already carries. Claim 29's operational-policy half moves to the
app packages that own those schemas (steps 8–12), recorded as amendment 6 so the
deferral is a decision in the record rather than a claim quietly unmet. This is a
deliberate, narrow deviation from step 5's verify clause; it is the only one.

## 10. SSOT amendments this design carries

Each goes through the same §7.5 four-eyes PR as the code:

1. **§6.6** — observable registry entries carry
   `renal_metric: egfr | crcl | null`.
2. **§7.3** — `Threshold` carries `states_metric: egfr | crcl | null`. With
   amendment 1, gate 15 gets both halves without matching free text.
3. **§7.4** — `content/valuesets/` closes the `concept` and `ingredient_id`
   authoring spaces; `content/terminology/charter.yaml` is where gate 17's
   attribution obligations are recorded. Explicitly not the `in_valueset`
   operator.
4. **§4.2 point 2** — the JSON-Schema field-reference pass is reconciled as
   subsumed by §4.3.1's closed `Expression` plus the three registries. Recorded,
   not built (section 6).
5. **§7.1 / §10.4 gate 12** — requirement observables are an allowlist of
   registered observables; §7.1's `active_medications` example is not loadable
   until the medication list carries an effective time (deferred, section 9).
6. **§12.6 claim 29 / §14 step 5** — claim 29's operational-policy half moves to
   §14 steps 8–12, with the packages that own those schemas. Step 5 proves the
   refusal pattern on `Profile`'s existing required fields (section 9.1).

## 11. Testing

Per `docs/testing-standards.md` and CLAUDE.md: Arrange-Act-Assert, sentence
names, behaviour not implementation, 100% branch coverage with no exclusions.

- **Fixture content trees under `tmp_path`.** Invalid content is authored in the
  test, never in `content/`. One refusal test per remaining gate, each injecting
  exactly one violation into an otherwise-valid tree so the assertion names the
  gate, not an unrelated failure.
- **Named claim tests:** 18 (compiler refuses a rule referencing visit/trigger
  state), 20 (closed snapshot contract, both halves — the second via the closed
  `Expression` and registries), 21 (`!!python/...` tag refused with no object
  constructed), 29 (a profile omitting a required declared field is refused, not
  defaulted — the refusal pattern on `Profile`'s existing fields; the
  operational-policy fields are steps 8–12, section 9.1), 42 (free text /
  narrative reference refused), 49 (renal rule omits `renal_metric` → refused;
  declares `egfr` against a CrCl-stated threshold → refused).
- **The real `content/` tree compiles clean** — a test that
  `compile_release` succeeds on the committed infrastructure content.
- **The `*.cases.yaml` parametrize harness** is proven against a fixture tree with
  a threshold and its three boundary rows, and against a fixture missing a row
  (refused). It discovers zero cases in the real `content/` tree today, and that
  is an asserted passing state, not an oversight.
- **Seam test extended** (`tests/test_import_direction.py`): `catalogue` may read
  the filesystem (it is above the device boundary) but still may not acquire a
  clock, an HTTP client, or a database session; `engine` and `canon` remain as
  constrained as before.

`CaseRow` is the one schema here designed without a live consumer — no rule exists
to write cases for. It is kept to the minimum gate 8 needs (the observable values
that place a row at / just below / just above a threshold, the expected outcome,
and the expected severity) and sized to be cheap for step 6 to extend.

## 12. Assumptions

1. **The compiler is the filesystem boundary above `engine`.** `catalogue` reads
   content files; `engine` and `canon` read nothing. The seam test enforces this.
2. **Seeded-on-demand valuesets are authoritative for what may be authored, not
   for clinical truth.** A concept's presence in `conditions.yaml` means a rule
   may name it, not that it is clinically validated — that is the rule's own
   citation and approval.
3. **The charter reproduces no code-system display strings** (§2.4), so it is
   distributable with SNOMED CT `outstanding`.
4. **`compile_release` takes an explicit `release_id`**, not "the newest" — there
   is no clock and no ordering authority in `catalogue`.
5. **Gate 8's boundary rows are checked structurally**, against the thresholds a
   rule references; whether a row's expected outcome is *clinically* right is a
   golden-case and four-eyes question (step 6), not a compiler one.

If any of these is wrong, correct it before the implementation plan is written.

## 13. Definition of done

CI's five commands green, in order, at 100% branch coverage:

```
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Plus: the six SSOT amendments (section 10) are written into
`docs/cds-architecture.md`; `content/valuesets/` and
`content/terminology/charter.yaml` exist and compile; the four cleanups
(section 8) are done; and the branch reaches `main` through a pull request under
the existing `CODEOWNERS` and branch protection.
