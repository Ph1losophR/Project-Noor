# Project Noor — Testing Standards

**Status:** Reference. Subordinate to `docs/cds-architecture.md` (the SSOT).

This document says *how* to test. The SSOT says *what must be true*. Where they
disagree, the SSOT wins and this file is wrong — fix it here, not there.

Section references in the form (§N) point at the SSOT.

**The full suite described here does not exist yet.** The repository has the
foundation layout and seam tests, and `canon` complete with its own tests: the
observation and registry models, unit resolution and conversion round-trips, all
three §6.1 layers, the `canonicalise` pipeline, quality resolution, and hypothesis
properties — plus a schema-only registry loader in `catalogue`. Nothing above the
device boundary is built: no rule schema or rule compilation, no `engine`, no
HTTP layer, no database. Rungs 2–8 below therefore describe no running test, and
`tests/app/`, `tests/release/`, `content/rules/`, and `content/golden/` do not
exist. These are the standards the suite will be built to. Verify against the
filesystem before assuming otherwise.

---

## Core mental model

Tests are not a safety net added after the fact. They are **executable
documentation of intended system behaviour**. If all source were deleted, the
suite alone should communicate what the system is supposed to do.

For Noor there is a second reason, and it is the more important one. The SSOT's
safety argument rests on a set of invariants — the device boundary holds, the
engine is deterministic, a hard stop never blocks an emergency, a rule with
unusable data degrades instead of blocking. **An invariant that is not a test is
a comment.** The suite *is* the safety case.

---

## The validation ladder

The SSOT §12.1 defines eight rungs. They replace the conventional test pyramid,
which does not describe this system: the engine is a pure function, so the layer
that would be "slow integration tests" elsewhere is fast here, and the layer that
carries the most clinical risk is content, which is data rather than code.

| # | Rung | Kind | Lives in |
|---|---|---|---|
| 1 | Schema and compile validation | Automated, CI merge gate | `tests/catalogue/` |
| 2 | Rule-unit rows | Automated, data-driven | `content/rules/<id>.cases.yaml` |
| 3 | Golden patient cases | Automated, data-driven | `content/golden/*.yaml` |
| 4 | State-machine tests | Automated, table-driven | `tests/app/` |
| 5 | Integration | Automated, HTTP | `tests/app/` |
| 6 | Release comparison | Automated, release gate | `tests/release/` |
| 7 | Independent clinical validation | Human | Governance record, not the repo |
| 8 | Shadow mode | Human + telemetry | Deployment, not the repo |

Rungs 1–6 run in CI. Rungs 7–8 are clinical governance and cannot be automated;
they are listed so nobody mistakes a green suite for clinical validation.

Cutting across all of them is a set of **invariant tests** that do not belong to
any rung because they constrain the system rather than its behaviour on a case.
Those are below.

---

## The FIRST properties

- **Fast** — the engine does no I/O (§8.4.8), so engine tests run in
  microseconds. A slow engine test means something crossed the seam.
- **Independent** — no test depends on another having run. Order is arbitrary.
  This is not merely hygiene: §8.4.5 makes order-independence a property of the
  system under test, so an order-dependent *test* hides an order-dependent
  *engine*.
- **Repeatable** — same inputs, same result, always. No `datetime.now()`, no
  randomness, no external calls. Time enters as an explicit `evaluated_at` on the
  snapshot (§4.2). `hypothesis` is seeded and its database committed.
- **Self-validating** — binary pass/fail. No log inspection.
- **Timely** — for rules, more than timely: the case rows are written *before* the
  rule and must fail (§12.1 rung 2).

---

## What to test

### Test behaviour, not implementation

Test what a unit does, not how. If you refactor internals and tests break without
behaviour changing, the tests were wrong.

```python
# GOOD — tests behaviour
assert record.outcome == "indeterminate"
assert record.effective_severity == "interruptive_review"

# BAD — tests implementation
assert engine._resolve_requirements.called_with(manifest)
```

### Test boundaries, not the happy path

- eGFR exactly at the contraindication threshold — not above, not below. At.
- A requirement whose latest observation is exactly `max_age_days` old, and one
  day older.
- A `stop_and_review` rule whose data requirements are unmet (§8.3).
- A value whose unit cannot be resolved (§6.3).
- A genuinely extreme but real value, next to a mistyped one (§6.2).

The happy path is the least interesting thing to verify.

### Test the four outcomes as four outcomes

The evaluator produces `triggered`, `not_triggered`, `indeterminate`, and
`suppressed_by_governed_policy` (§8.2). **A test that accepts `not_triggered`
where `indeterminate` is correct is a bug in the test**, and it is the specific
bug the outcome taxonomy exists to prevent. Assert the exact outcome. Never
assert "did not fire".

### Test invalid transitions harder than valid ones

The content release lifecycle is
`draft → technical_validation → clinical_review → approved → scheduled → active → retired`
(§10.1). Every valid transition must succeed; every invalid one must be rejected
with the correct error. Invalid transitions are the more important half.

---

## Test structure: Arrange-Act-Assert

Every test. No exceptions.

```python
def test_metformin_rule_is_indeterminate_when_egfr_is_older_than_its_window():
    # Arrange
    snapshot = snapshot_with(
        observations=[egfr(value=52, effective_time="2025-11-04T08:00:00+03:00")],
        medications=["metformin"],
        evaluated_at="2026-06-12T09:00:00+03:00",  # 220 days later
    )

    # Act
    run = evaluate(context, snapshot, requested_actions=[])

    # Assert
    record = run.record_for("metformin-egfr-contraindicated")
    assert record.outcome == "indeterminate"
    assert record.requirement_verdicts[0].observable == "egfr"
    assert record.requirement_verdicts[0].verdict == "unusable"
```

`evaluate(context, snapshot, requested_actions) -> EvaluationRun` is the one
entry point (§8.1). Test through it. Do not reach into evaluator internals.

---

## Test naming

Test names are sentences. They must tell you what broke without reading the body.

```python
# GOOD
test_stop_and_review_with_unmet_requirements_degrades_to_interruptive_review
test_catalogue_refuses_a_rule_citing_an_unpopulated_threshold
test_ambiguous_unit_resolution_never_produces_a_canonical_value
test_hard_stop_blocks_only_the_named_order_action

# BAD
test_engine_1
test_degradation
test_units
```

---

## Rung 1 — Schema and compile validation

The catalogue is machine-checked before anything runs. §10.4 lists seventeen
conditions that refuse a merge. **Each gate gets a test that feeds the compiler
deliberately bad content and asserts the refusal** — a gate with no test proving
it refuses is not a gate.

| Gate | Test asserts the compiler refuses |
|---|---|
| 1 | a rule citing a threshold whose `status` is `unpopulated` |
| 2 | a threshold missing organisation, document, version, or locator |
| 3 | `severity: stop_and_review` with `role_doubling: true` |
| 4 | `severity: stop_and_review` with no `clinical_approver` |
| 5 | a `then` omitting `meaning`, `action`, or `uncertainty` |
| 6 | a `blocks` clause that does not name an order action |
| 7 | a profile resolving thresholds across two `source_family` values |
| 8 | a rule with no `*.cases.yaml`, or missing at/below/above rows for any threshold it references |
| 9 | a release whose comparison diff is unexplained by its manifest |
| 10 | `severity: stop_and_review` with any requirement `on_unusable: silent` |
| 11 | a rule reading encounter state, visit state, or trigger identity in `scope` or `when` |
| 12 | a rule naming a field absent from the snapshot schema, or an operator outside the evaluator's vocabulary |
| 13 | a content file that fails a schema-only YAML load, including any object-constructing tag |
| 14 | a rule referencing a drug without declaring `drug_scope_level` |
| 15 | a renal-dosing rule omitting `renal_metric`, or naming an eGFR observable where its source specifies creatinine clearance |
| 16 | `severity: stop_and_review` matching an allergy without requiring `verification_status: confirmed` and `severity: severe` |
| 17 | a rule citing a code system absent from the terminology charter, or one whose charter entry has no licence status |

Gate 9 is rung 6; the other sixteen are pure catalogue tests. Gate 13 is the one
to write first — it is the only gate that refuses a file the loader would
otherwise *execute*, and `tests/catalogue/` already covers it for the observable
registry (§7.5).

Assert on the *refusal*, not on a message string. A test that pins error prose
breaks on rewording and teaches nothing.

---

## Rung 2 — Rule-unit rows

Every rule has `content/rules/<id>.cases.yaml`. **Cases are data, not Python.**
A single `pytest` parametrize discovers every `*.cases.yaml` in the tree (§7.4),
so adding a rule is two YAML files and zero Python.

### Case file shape

The SSOT constrains what a case file must express (gate 8) without fixing its
schema. The minimum below satisfies the gates. The authoritative schema is the
Pydantic model in `catalogue/`, which does not exist yet — when it does, it wins.

```yaml
rule: metformin-egfr-contraindicated
rule_version: 1.0.0

cases:
  - description: "eGFR just below the contraindication floor → triggered"
    threshold_ref: metformin.egfr_absolute_contraindication
    boundary: just_below                 # at | just_below | just_above
    given:
      observations:
        - {observable: egfr, value: 29, ucum: "mL/min/{1.73_m2}", age_days: 14,
           source_status: final, quality: accepted}
      medications: [metformin]
      context: [ckd_chronicity_confirmed]
    expect:
      outcome: triggered
      effective_severity: stop_and_review
      blocks: {order_of: metformin}

  - description: "eGFR exactly at the floor → not triggered"
    threshold_ref: metformin.egfr_absolute_contraindication
    boundary: at
    given:
      observations:
        - {observable: egfr, value: 30, ucum: "mL/min/{1.73_m2}", age_days: 14,
           source_status: final, quality: accepted}
      medications: [metformin]
    expect:
      outcome: not_triggered

  - description: "eGFR stale beyond the rule's 90-day window → indeterminate"
    given:
      observations:
        - {observable: egfr, value: 29, ucum: "mL/min/{1.73_m2}", age_days: 214,
           source_status: final, quality: accepted}
      medications: [metformin]
    expect:
      outcome: indeterminate
      effective_severity: interruptive_review     # §8.3
      degraded_because: requirements_unmet
      unmet: [egfr]
```

`description` is mandatory. It is what a clinician reviewer reads, and it is what
appears when the row fails.

### Case selection: boundary plus pairwise

Explicitly **not** exhaustive. A published CDS pathway with 26 decision points
yields 3,120 combinations; 100 well-chosen cases exercised the major pathways at
roughly 1% combination coverage (§12.3).

**Minimum per threshold: three rows — at, just below, just above.** CI gate 8
enforces this; do not treat the minimum as the target.

Beyond the boundary rows, cover pairwise combinations of the dimensions that
actually interact — scope inclusion/exclusion, requirement usability, quality
state, and source status. Do not cross-product every field.

Every rule additionally needs at least one row per unmet-requirement path it
declares, because that is where §8.3 is exercised.

---

## Rung 3 — Golden patient cases

`content/golden/*.yaml` holds whole patient snapshots and the complete expected
finding set — not one rule's verdict but everything the catalogue produces for
that patient.

Golden cases catch what rule-unit rows cannot: interaction between rules,
findings that appear when they should not, and findings that quietly stop
appearing. They are the input to release comparison (rung 6).

Assert the **whole** finding set, ordered deterministically. A golden case that
asserts only the findings it cares about cannot detect an extra finding, which is
half of what it exists for.

---

## Rung 4 — State-machine tests

The visit state machine (§11.2) decides one thing above all: whether
observations may be written. A wrong transition therefore does not merely
mis-label a visit — it either creates clinical facts in a state that has no
encounter to hold them, or loses facts a clinician captured.

Table-driven over the transition matrix, and **the invalid transitions carry the
same weight as the valid ones**: every (state, event) pair gets a row, and a pair
absent from §11.2's diagram asserts a refusal. A suite that only walks the happy
paths through the diagram proves the arrows exist, not that nothing else does.

What these tests must pin, beyond arrow-by-arrow coverage:

- **Observations are writable in `in_progress` and nowhere else.** Every other
  state refuses the write.
- **Every path into `completed` passes through `submitted`,** including the
  escalated one. There is exactly one completion gate (§11.2), so a second path
  into `completed` is a missing gate, not an extra arrow.
- **`interrupted_for_emergency` is entered with no gate of any kind** from
  `scheduled` or `in_progress` (§11.7). A test that has to satisfy a precondition
  to reach the emergency hatch has already broken the invariant.
- **The terminal states are terminal.** `completed`, `cancelled`, and `abandoned`
  refuse every event, and `abandoned` keeps its partial observations (§5).
- **Entering `escalated` names a person and stamps a due time** (§11.2, §11.8).
  Naming a role alone is a refusal.

These live in `tests/app/` because the machine governs the encounter, which sits
outside the device boundary (§2.2) — but the state machine itself is a §0
security-critical constant, so a transition table change is an SSOT change first.

---

## Rung 5 — Integration

Through the HTTP layer, with real FastAPI, SQLAlchemy, and PostgreSQL. Use
FastAPI's `AsyncClient` — full request/response including middleware and Pydantic
validation, without starting a server.

What integration must prove beyond the lower rungs:

- Golden cases produce the same finding set through HTTP as in-process.
- **Evaluation records persist for rules that did not fire** (§8.2). This is the
  single most important integration assertion in the system; §9.3's zero-firing
  surveillance is built on it and it is not retrofittable.
- An override cannot be submitted without a reason code (§9.2).
- The card renders evidence and data status **before** recommendation (§7.2).
  This is the primary automation-bias mitigation and it is enforced by the
  renderer, so it is tested at the renderer.

### Authentication

**No auth provider is chosen.** The SSOT names authentication timeouts and RBAC
definitions as security-critical constants (§0) but selects no implementation,
and §13.2 gate 6 forbids encoding a supervisor-sign-off model from job title
until a provider states one in writing.

Consequently: do not import an auth SDK into tests, and do not build fixtures
around one. When auth is decided, its tests are written then. Any RBAC test
written before that decision is testing an assumption.

---

## Rung 6 — Release comparison

Run catalogue *vN* and *vN+1* over the full golden set and diff. **Any finding
that changes or disappears must be explained in the release manifest, or the
release is blocked** (§12.2).

This is build-time detection of the silent-non-firing failure mode, complementing
the runtime detection in §8.2. The dominant CDS failure is the alert that stops
firing: users reliably notice a spurious alert and reliably fail to notice an
expected one that never appears (§8.2).

The harness itself needs a test: plant a deliberately broken rule in a test
release and assert that both release comparison and zero-firing surveillance
catch it (§14 step 10).

---

## Rungs 7 and 8 — not automated

**Independent clinical validation** is a clinician who did not author the rule
reviewing it against the generated plain-language rendering (§7.5). The record
lives in governance, not in the repo. No test substitutes for it.

**Shadow mode** evaluates without displaying and compares against clinician
action.

**Calibrated-reliance audit** (§12.5) seeds deliberately wrong *and* deliberately
correct advice to measure whether clinicians over- or under-rely on Noor.
Training cases include deliberately wrong and incomplete examples.

A green suite is not clinical validation. Do not let anyone report it as one.

---

## Invariant tests

These constrain the system rather than its behaviour on any case. They are the
executable form of the SSOT's safety argument.

### The seam

`app` imports from `canon`, `engine`, and `catalogue`. **Never the reverse**
(§4.2).

One test scans the import graph and fails the suite if `engine` acquires a
database session, a wall clock, an HTTP client, or a filesystem read. The SSOT is
blunt about its weight: *"This single test is what keeps the device boundary
real."* It is also what makes evaluation deterministic and replayable.

It exists from the first commit, before there is anything to import (§14 step 1).

### The engine invariants

§8.4. Each is a named test.

| # | Invariant |
|---|---|
| 1 | Only `stop_and_review` may block, and only the named order action |
| 2 | No rule loads with an incomplete citation |
| 3 | No rule loads referencing an `unpopulated` threshold |
| 4 | `stop_and_review` rules cannot be tenant-disabled |
| 5 | Evaluation order never affects output |
| 6 | Identical snapshot + identical catalogue release ⇒ byte-identical records |
| 7 | No rule reads another rule's output |
| 8 | The engine performs no I/O and reads no clock |
| 9 | A rule is a pure function of the snapshot and the catalogue |
| 10 | No rule reads encounter state |

Invariant 1 needs its own negative tests, because the scope of a block is the
part that gets eroded: a hard stop must never block visit documentation, note
submission, emergency activation, or the encounter itself (§7.1c). Write those as
explicit assertions, not as an absence.

Invariants 5 and 6 are proven by running an identical snapshot twice in shuffled
rule order and comparing serialised records byte-for-byte (§14 step 4).

Invariant 9 preserves portability for a future on-device evaluator (§15.1). It is
tested now even though nothing consumes it yet, because it is cheap to keep and
expensive to recover.

### The degradation invariant

§8.3 is short enough to test exhaustively and important enough to warrant it:

> A rule whose severity is `stop_and_review` and whose data requirements are not
> met degrades to `interruptive_review`, carries "cannot assess safely", and
> names the specific unmet requirement. It never blocks.

Tests: the effective severity degrades; the record carries
`degraded_because: requirements_unmet`; `authored_severity` still reads
`stop_and_review`; the specific unmet requirement is named in
`requirement_verdicts`; nothing is blocked. Authors cannot opt out, so there is
also a test that no configuration produces an opt-out.

---

## Testing `canon`

`canon` lands before any threshold logic (§13.1 gate 1), so its tests are the
first real tests in the project.

This is where `hypothesis` earns its place (§3.1). The property is a boundary
claim, not a per-case one: **nothing crosses into the engine uncanonicalised.**

Required properties and cases:

- **Unit resolution.** `unit_resolution: ambiguous` is a hard failure (§6.3). A
  value whose unit cannot be resolved never receives a canonical value and never
  reaches the engine. An **absent** resolution — canon refused the record before
  resolution ran — bars a canonical value the same way, so state the property
  positively: a canonical value carries a resolved unit. Property-test this over
  generated inputs, not just examples.
- **HbA1c.** Never infer percent versus mmol/mol from the value alone. NGSP % and
  IFCC mmol/mol are distinct observables, not two units of one (§5, §6.3).
- **Glucose.** Original unit preserved; conversion only with displayed conversion
  and provenance. Both mg/dL and mmol/L accepted.
- **Quality states.** Four, not three (§6.2). A genuinely extreme real value and a
  mistyped value must land in **different** states — this is the test that stops
  the plausibility gate from suppressing an emergency. Assert
  `clinically_exceptional_accepted` explicitly.
- **Delta review.** Compares like with like only: same observable, unit, context,
  device class, reasonable interval. A suspicious delta raises
  `needs_repeat_or_verification` and **never mutates a value** — assert the
  stored value is unchanged, not just that a flag was set.
- **Immutability.** An observation is written once. A correction is a new
  observation with a higher `source_version` (§5). Assert the prior row survives.
- **Derived values.** A lab's `reported_egfr` and a `noor_derived_egfr` never
  overwrite each other, and historical values are never recomputed under a
  different equation (§5.2).
- **Boundary separation.** A treatment threshold is never reused as a data-entry
  validator (§6.4). The three boundary types are versioned independently; a test
  proves they are not read from one another.
- **Never corrects HbA1c.** A context flag prompts review. It does not adjust a
  number (§5.3).

---

## Database test strategy

**Transaction rollback** for anything touching the database:

```python
@pytest.fixture
async def db_session(async_engine):
    async with async_engine.begin() as conn:
        await conn.begin_nested()
        session = AsyncSession(bind=conn)
        yield session
        await session.rollback()  # DB state never changes
```

Each test runs inside a transaction that rolls back. Fast, isolated, no cleanup.

A **separate seeded test database** for full API flow tests. Never a development
database.

The observation store is append-only (§5). Tests must not exercise `UPDATE` paths
that the schema is supposed to forbid — if such a path exists, that is a schema
bug, and the test that finds it belongs in the migration suite.

---

## Test layout

```
tests/
  conftest.py               # snapshot builders, observation factories, db_session
  canon/                    # unit + hypothesis properties
  engine/
    test_invariants.py      # the invariants, each named
    test_degradation.py     # §8.3
    test_determinism.py     # shuffled order, byte-identical records
  catalogue/
    test_gates.py           # one refusal test per §10.4 gate
  content/
    test_cases.py           # the single parametrize over content/rules/*.cases.yaml
    test_golden.py          # the single parametrize over content/golden/*.yaml
  app/                      # integration, through HTTP
  release/                  # release comparison harness
  test_import_direction.py  # the seam (§4.2) — top level, it constrains everything
```

`tests/` sits at the repository root, mirroring `src/noor/` (§4.1).

`test_cases.py` and `test_golden.py` are the only Python that content authors
never touch. Everything clinical lives in `content/`.

---

## Coverage targets

| Module | Target |
|---|---|
| `engine/` | 100% branch. All §8.4 invariants as named tests. |
| `canon/` | 100% branch, plus hypothesis properties on unit resolution and quality states |
| `catalogue/` | 100% branch. One refusal test per §10.4 gate. |
| Content rules | Every threshold: at, just below, just above (gate 8) |
| Release lifecycle (§10.1) | All valid transitions, all invalid transitions |
| `app/` routers | Boundary conditions and key business rules |

Line coverage is a vanity metric. Branch coverage is what matters.

`mypy --strict` runs on `canon`, `engine`, and `catalogue` (§3.1). A type error
there is a failing build, not a warning.

**Speed target:** the full unit and integration suite under two minutes. The
engine is pure; if engine tests are slow, the seam has been breached.

---

## Non-negotiables

**No flaky tests.** A test that passes sometimes without a code change is
actively harmful — it trains everyone to ignore red builds. Fix it or delete it.
No middle ground. In this system a flaky engine test is additionally a *finding*:
§8.4.5 and §8.4.6 say the engine is deterministic, so flakiness there means the
invariant is false.

**Hard-to-write tests signal bad code.** Excessive setup, mocking, or contortion
means the problem is in the source — too many dependencies, too many
responsibilities, hidden coupling. Fix the code.

**Never mock the engine.** It is a pure function over data. If a test needs to
mock it, the test is at the wrong layer.

**Never assert on an internal call.** §8.4 invariants are about observable
outputs. `assert engine._foo.called` is banned outright.

**Never let a test assert `not_triggered` for a case that should be
`indeterminate`.** This is the failure mode the whole outcome taxonomy exists to
prevent, and a lazy test reintroduces it.

---

## Adding a new CDS rule

1. Write `content/rules/<id>.cases.yaml` first — at, just below, and just above
   every threshold the rule will reference, plus a row for each unmet-requirement
   path.
2. Run it. **It must fail.** A row that passes before the rule exists is testing
   nothing.
3. Write `content/rules/<id>.yaml`, including complete `governance` and full
   citations.
4. Run it. It must pass, and the compiler must accept it (§10.4).
5. Run the full suite, including golden cases. Nothing else may change.
6. Any golden-case finding that changed or disappeared is explained in the
   release manifest, or the release is blocked (§12.2).
7. Open a pull request. **The PR is the four-eyes clinical approval** (§7.5); the
   approver is recorded permanently in git.

No rule ships without its rows. No exceptions.

For `stop_and_review` specifically: a second credentialed clinical approver is
required and `role_doubling: true` is refused (§10.3). No amount of test coverage
substitutes for that signature.

---

## Out of scope for this document

Not omissions — decisions recorded elsewhere.

- **Auth and RBAC tests.** No provider is chosen (§3.5, §13.2 gate 6).
- **Offline/field-client parity tests.** No field client is in MVP scope; the
  parity invariant is carried as a schema obligation (§8.4.9, §15.1).
- **FHIR conformance tests.** No EMR to adapt to; `fhir.resources` is an adapter
  dependency (§3.4).
- **Risk-model validation.** Risk models are deferred (§15.2).
- **Synthea as a validation cohort.** Synthea is for plumbing and adversarial
  fixtures only. Its Massachusetts demographics make it unsuitable as a Saudi
  validation cohort, and it is never described as one (§12.4).
