# Design — `catalogue`: loader, compiler, validator (SSOT §14 step 5)

**Status:** approved 2026-08-24, pending implementation plan.
**SSOT:** `docs/cds-architecture.md`. Where this design disagrees with the SSOT,
the SSOT wins — stop and ask.
**Predecessor:** `docs/superpowers/plans/2026-08-22-engine-evaluator.md`
(§14 step 4, executed and merged in `#2`; suite green at 360 tests, 100% branch
coverage).

Throughout, `§N` cites the SSOT and `section N` cites this document. The two
numbering schemes overlap and the distinction is load-bearing. A bare
"amendment N" is an entry in section 10's list; the SSOT's own numbered
amendments are always written with their section, as in "§7.1 amendment 5".

## 1. Goal

Build `src/noor/catalogue/` — the loader, compiler, and validator that turn a
content directory into a validated `EvaluationContext`, refusing any content that
violates §10.4. This satisfies §14 step 5's verify clause: §12.6 claims 18, 20,
21, 42, and 49 in full, and claim 29 in part — its operational-policy half moves
to steps 8–12 for the reason section 9.1 gives. It stops short of §10.4 **gate** 9
(release comparison), which the SSOT itself orders into step 15 because it needs a
golden set.

The diff is not purely `catalogue`. Closing the authoring spaces forced three
`engine` changes that closing them without would have made unsafe: one §4.2 field
(`Snapshot.medications_reconciled_at`, approved as an explicit §0 exception), one
resolution branch in `evaluate.py` (`active_medications` resolves against that
stamp, not through `_latest_observation`), and two validator changes in
`engine/rules.py`. Section 9 is the argument for all three; sections 8 and 10 are
the inventory.

`catalogue` imports `canon` and `engine`; nothing imports `catalogue` except
`app`, which does not exist yet (§4.1, §4.2). The compiler performs the one
filesystem read the boundary permits above `engine` — content load — and no
other I/O, no clock, and no network.

## 2. Scope

**In scope.** Seven modules under `src/noor/catalogue/`; the remaining single-rule
and cross-file §10.4 gates not already enforced by `engine` models (3, 8, 12, 13,
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
| Medication metadata beyond the one freshness stamp — dose, route, indication, per-entry assertion times | §14 step 6+ — section 9 adds only `medications_reconciled_at`, the minimum `max_age_days` needs |

## 3. Decisions taken

Five scoping decisions, made 2026-08-24 and settled with the user:

1. **Loader + compiler + gates on one branch, one PR** — mirroring the canon and
   engine plans. The design note, plan, code, and the seven SSOT amendments
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
5. **`Requirement.observable` is the registered observables plus
   `active_medications`** (section 9). The compiler refuses anything else.
   `active_medications` resolves against a new list-level reconciliation stamp on
   `Snapshot`, and a `drug_active` leaf must declare it — §7.1's canonical example
   rule becomes loadable *and* enforceable. Approved as an explicit §0 exception
   for the §4.2 data contract on 2026-08-24, recorded as amendment 5.

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

## 6. Gate 12 — the SSOT's concern is right, its instrument is not

§4.2 point 2 says the compiler validates rule field references against the
snapshot's exported JSON Schema, and gives its reason: "A name-matching check
would be defeated by the first author who wrote `encounter.state` instead of
`encounter_id`."

**The concern is correct, and the first draft of this design was wrong to call it
subsumed.** A rule that names something which does not exist does not fail loudly.
It silently never matches, or silently schedules nothing. No alert, no error, no
one notices — the worst failure mode a CDS engine has.

**The instrument is the wrong one.** A JSON Schema of the snapshot cannot reach the
values that need closing: `conditions` is `frozenset[str]` and `medications` is
`tuple[SnapshotMedication, ...]`, so the schema sees the *fields* and never the
concept ids or ingredient ids inside them. Two of the eight reference sites below
are not snapshot fields at all — `requested_actions` is a parameter of
`evaluate()`, not a member of `Snapshot`. The pass would walk a schema and find
nothing.

**The right instrument is one closure per reference site, against the registry that
owns that name's space.** Every place a rule names something that must exist:

| Site | Space it names | Closed by |
|---|---|---|
| `Expression.fact` | observable | observable registry |
| `Expression.threshold_ref` | threshold | `EvaluationContext` — already enforced |
| `Expression.concept` | condition concept | `conditions.yaml` (section 5.1) |
| `Expression.ingredient_id` | ingredient | `ingredients.yaml` (section 5.1) |
| `Expression.minimum` / `maximum` | — (ints) | no name to get wrong |
| `Requirement.observable` | observable | allowlist (section 9) |
| `Monitor.observable` | observable | observable registry — **was unguarded** |
| `OrderBlock.order_of` | ingredient | `ingredients.yaml` — **was unguarded** |

The last two were missed when this design was first written; finding them is why
the verification mattered. Both are authored strings that **no engine code reads
today** — `evaluate.py` references neither `monitors` nor `order_of`. They are
declarative, consumed by §11 app code that arrives in steps 8–12. That makes them
*more* dangerous, not less:

- A rule is approved by four eyes **once**, at step 6. A human reading
  `observable: creatinin` in a YAML diff will not catch it.
- The typo then lies dormant until an app consumes it, and surfaces as a renal
  recheck that is never scheduled (`Monitor`) or a hard stop that blocks nothing
  (`OrderBlock`) — long after the approver signed, on a time-delayed path no test
  of the rule's *firing* behaviour covers. Gate 8's boundary rows test firing.

Closing both costs two lines against registries this step already loads.

That `order_of` names an ingredient is verified, not assumed:
`RequestedAction.subject` is what `order_of` matches (its own docstring says so),
and `evaluate.py:368` compares `action.subject == ingredient_id`. Same space, same
valueset.

**Deliberately not added:** a coherence gate requiring a hard stop's blocked
ingredient to appear in its own `when`. It reads well and it is wrong — a
cross-allergy rule (`when: allergy penicillin` → `blocks: amoxicillin`)
legitimately blocks a drug its trigger never names. A gate that refuses correct
clinical content is its own safety problem, because authors route around it.

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
| 12 — `drug_active` leaf must declare `active_medications` | `engine/rules.py` validator | extends the existing gate-12 validator (section 9) |
| 12 — every authored name-reference closed, all eight sites | `valuesets.py` + compiler | section 6 — replaces the JSON-Schema pass |
| 12 — `Monitor.observable`, `OrderBlock.order_of` closures | compiler | section 6 — previously unguarded |
| 1, 2, 4, 5, 6, 7, 10, 14 | already in `engine` models | single-rule / single-release; landed in step 4 |
| 9 — release comparison | **out** — §14 step 15 | needs the golden set |

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

## 9. `active_medications` — the SSOT conflict, and its resolution

Closing the `Requirement.observable` string space exposes a genuine contradiction
in the SSOT:

- §7.1's canonical example rule declares
  `requires: [{observable: active_medications, max_age_days: 1}]`.
- `active_medications` is not in the observable registry (ten measured
  observables), and `_resolve_requirement` resolves every requirement through
  `_latest_observation`, which searches `snapshot.observations` only.
- `SnapshotMedication` carries `ingredient_id` and `mapping_status` — **no
  time** — so `max_age_days: 1` on it was unenforceable in principle, not merely
  unimplemented.

Today a requirement on `active_medications` resolves `no_result` → unusable → the
rule is *always* `indeterminate`, silently.

**The problem is larger than §7.1's example.**
`_every_compared_observable_is_declared_in_requires` walks `when` for **numeric
operators only**, so a `drug_active: metformin` leaf needs no requirement at all.
Every medication-safety rule — the whole step-6 domain — reads the medication list
with no declared freshness posture and no way to declare one. And
`_drug_active` on an empty `medications` tuple returns `False`: "the patient takes
nothing." §5.5 rule 2 already ruled on precisely this shape — *"An unasked patient
and a cleared patient are opposite facts, and neither is ever inferred from an
empty list"* — and `_allergy` honours it by raising `_CannotAssessSafely` on
`not_asked`. Medications have no equivalent. That asymmetry is a false negative on
the safest-sounding path: the rule concludes the patient is not on the drug and
stays silent.

**Resolution.** Approved 2026-08-24 as an explicit §0 exception for the §4.2 data
contract:

1. **`Snapshot.medications_reconciled_at: AwareDatetime | None`** — when the
   medication list was last reconciled or verified, **never** when it was
   transmitted. If the device stamps send-time, `max_age_days: 1` always passes and
   the check is worse than absent.
2. **`active_medications` joins the `Requirement.observable` allowlist** as the one
   non-registry entry, resolving against that stamp rather than through
   `_latest_observation`. It produces a verdict and no value — `_resolve_manifest`
   already tolerates a requirement that populates nothing, and no numeric leaf may
   name it, since gate 12 constrains compared facts to the registry. `None`
   resolves `unusable / no_result`; a stamp older than `max_age_days` resolves
   `unusable / stale` through `_first_failure`'s existing comparison.
3. **A `drug_active` leaf must declare an `active_medications` requirement**,
   extending `_every_compared_observable_is_declared_in_requires` to the one drug
   operator that reads patient state. This is §7.1 amendment 5's own argument — "a
   threshold never runs against data of undeclared age and grade" — applied to the
   medication list, and it is what routes the empty-list case through a verdict
   instead of a silent `False`.

**Why list-level, not per-entry.** A per-medication `asserted_at` was considered
and is worse on both counts. It cannot express the empty-list case at all — no
entries, no stamps — which is the highest-risk case. And on a merged feed
(discharge summary, pharmacy fill, home visit) the oldest entry is some ancient
discharge medication, so a `min(asserted_at)` freshness test would never be
satisfiable, making `max_age_days` dead in practice. Reconciliation is an act over
the list; the stamp belongs where the act is.

`drug_requested` is **not** covered by point 3: it reads the `requested_actions`
parameter, not the medication list, and the action under consideration is by
definition current.

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
4. **§4.2 point 2** — the snapshot JSON-Schema field-reference pass is replaced by
   one closure per reference site, against the registry owning that name's space
   (section 6 enumerates all eight). The schema cannot reach values inside
   `frozenset[str]` / `tuple[...]` collections, and two sites are not snapshot
   fields. Gate 12's *concern* is unchanged and now more completely met; only its
   instrument changes.
5. **§7.1 / §7.3 / §4.2** — a `drug_active` leaf must declare an
   `active_medications` requirement, which resolves against a new list-level
   `Snapshot.medications_reconciled_at` stamp (last reconciled, never
   transmitted). §7.1's example becomes loadable and enforceable. **This is an
   explicit §0 approval for the §4.2 data contract**, granted 2026-08-24
   (section 9).
6. **§12.6 claim 29 / §14 step 5** — claim 29's operational-policy half moves to
   §14 steps 8–12, with the packages that own those schemas. Step 5 proves the
   refusal pattern on `Profile`'s existing required fields (section 9.1).
7. **§7.1 amendment 5** — its scope widens from "every numerically compared
   observable" to "every observable a rule reads as patient state," which adds the
   `drug_active` leaf. The rationale is unchanged and quoted verbatim from the
   existing validator: a rule never runs against data of undeclared age and grade.

## 11. Testing

Per `docs/testing-standards.md` and CLAUDE.md: Arrange-Act-Assert, sentence
names, behaviour not implementation, 100% branch coverage with no exclusions.

- **Fixture content trees under `tmp_path`.** Invalid content is authored in the
  test, never in `content/`. One refusal test per remaining gate, each injecting
  exactly one violation into an otherwise-valid tree so the assertion names the
  gate, not an unrelated failure.
- **Named claim tests:** 18 (compiler refuses a rule referencing visit/trigger
  state), 20 (closed snapshot contract, both halves — the second as **one refusal
  test per reference site in section 6's table**, including a `Monitor.observable`
  typo and an `OrderBlock.order_of` typo, each of which passes every existing
  validator today), 21 (`!!python/...` tag refused with no object
  constructed), 29 (a profile omitting a required declared field is refused, not
  defaulted — the refusal pattern on `Profile`'s existing fields; the
  operational-policy fields are steps 8–12, section 9.1), 42 (free text /
  narrative reference refused), 49 (renal rule omits `renal_metric` → refused;
  declares `egfr` against a CrCl-stated threshold → refused).
- **The real `content/` tree compiles clean** — a test that
  `compile_release` succeeds on the committed infrastructure content.
- **The medication-freshness path (section 9), four behaviour tests in
  `tests/engine/`** — this is new evaluator behaviour, so it is tested where
  `evaluate` is tested, not in the compiler suite:
  - a `drug_active` rule with no `active_medications` requirement is refused at
    load (the gate);
  - `medications_reconciled_at: None` resolves `unusable / no_result`, and the rule
    degrades to `indeterminate` rather than concluding the patient takes nothing —
    the §5.5 rule 2 parity test, and the one that would have caught the silent
    false negative;
  - a stamp older than `max_age_days` resolves `unusable / stale`; a stamp exactly
    `max_age_days` old stays usable, matching `_first_failure`'s existing boundary;
  - an **empty** `medications` tuple with a *fresh* stamp is a usable verdict and
    `drug_active` correctly returns `False` — reconciled-and-takes-nothing is a
    real, distinct fact from never-asked, and must not degrade.
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

Plus: the seven SSOT amendments (section 10) are written into
`docs/cds-architecture.md`; `content/valuesets/` and
`content/terminology/charter.yaml` exist and compile; the four cleanups
(section 8) are done; and the branch reaches `main` through a pull request under
the existing `CODEOWNERS` and branch protection.
