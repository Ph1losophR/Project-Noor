# CLAUDE.md — Project Noor

Project Noor is a Clinical Decision Support (CDS) engine for home healthcare in
Saudi Arabia, aimed at chronic disease management (diabetes and hypertension).

## Current State

No application code, database, dependencies, or test suite exists yet. The repo
holds design and research documents only.

- **SSOT: `docs/cds-architecture.md`**.
- The closed research programme is archived under `docs/research/archive/` and
  cited inline as (§R-N), with the file mapping in SSOT §17. There is no
  section-10 file — its project constraints are stated directly in SSOT §1 and
  §10.3. The research checklist has been retired.
- **The only clinical-content sources are two primary files under
  `docs/research/`:**
  - `saudi-essential-medicines-list-2023.md` — the user's own conversion of the
    SEML 2023 PDF; authoritative for exactly two claims: whether an ingredient
    is listed, and its strengths and dose forms.
  - `saudi-local-db.json` — the curated 2025-10-23 snapshot of the SFDA drug
    portal; authoritative for product metadata and SPC text.
  Clinical content authoring may proceed from these local sources. Every
  per-ingredient pin (product, registration number, and SPC revision date, read
  from inside the SPC text) carries **official-SDI reconciliation pending** while
  the e-service is unavailable. A complete local SPC citation can pass CI gate 2;
  a later contradiction is a content incident under SSOT §11.9.
  **A pin is valid only if the SPC text names the pinned product in its own §1
  and §4.1.** At least one snapshot document is spliced: registration
  `82-171-20` (NORACTONE, spironolactone 25 mg) carries a real spironolactone
  §1–§3 and then the entire AVORES 400 mg moxifloxacin label from §4.1 onward.
  Do not pin it — the other three spironolactone products are clean.
- `docs/superpowers/specs/` is empty; the SSOT is the only architectural
  document.
- **Git repository initialized** (commit `1910530`, remote
  `github.com/Ph1losophR/Project-Noor`). SSOT §7.5 makes git the
  clinical-content governance mechanism — a pull request *is* the four-eyes
  approval, and git holds the permanent approver record. Branch protection and
  the CI rendering-posting job remain unconfigured.

Do not infer that any component, table, endpoint, or dependency exists because a
document describes it — **including the SSOT.** It describes the target, not the
present. Verify against the filesystem.

## SSOT Integrity Rules

In force.

- Read it before writing any code. Do not deviate from it without explicit user approval.
- **Conflict resolution:** if a user prompt contradicts the SSOT, prioritize the SSOT
  and ask the user to resolve the conflict. Never silently bypass or override it.
- **Security-critical constants** are architectural decisions, not implementation
  details. Never modify them without explicit user approval. In this project they
  are enumerated in SSOT §0: auth timeouts, RBAC definitions, and break-glass and
  access-log invariants (all defined in §2.6), audit-record content,
  fail-open/fail-closed policies, the severity ladder (§9.1), the degradation
  invariant (§8.3), the erasure model (§2.5), the device boundary's data contract
  (§4.2), the visit state machine and its transition gates (§11.2), the
  obligation closure invariant (§11.8), the emergency-hatch invariant (§11.7),
  and the CI governance gates (§10.4). SSOT §0 is authoritative if this list
  drifts.

## Behavioral Guidelines

These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask me clarifying questions.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First
Keep solutions as simple as possible while meeting all requirements. Avoid unnecessary complexity or premature abstraction.
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- Ask yourself: "Would a senior engineer say this is overly complicated?" If yes, simplify.
- Apply this mindset recursively to sub-components, intermediate files, and generated test code.
- If a simpler, more direct solution exists, propose it.

### 3. Surgical Changes
Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution
Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

### 5. Skill & MCP Use
- ALWAYS use skills & MCPs. There is always a skill or MCP for every task within this project. Find the most suitable skill/MCP and use it to complete the task.
- If you cant find a skill for the specific task currently installed, use `find-skills`
- If there's > 1 skill/MCP that does the same task, ask the user which skill/MCP to use.
- You may need to use > 1 skill/MCP to complete the task. This is expected. Use as many as needed.

### 6. Before Implementing Any Business Logic
Run the unit suite. If any unit test fails, fix it before proceeding. Never push
forward with a broken suite.

## Important Commands

None yet. The stack is decided in SSOT §3 — Python 3.12+, uv, FastAPI,
Pydantic v2, PostgreSQL, SQLAlchemy/Alembic, pytest, ruff, mypy — but nothing is
installed and no command has been run. Document commands here as they become
real. Do not copy commands from other projects or invent them.

## Testing

Read `docs/testing-standards.md` before writing any test. It says *how*
to test; the SSOT says *what must be true*. Where they disagree, **the SSOT
wins** — SSOT §12 is authoritative on the validation ladder,
boundary-plus-pairwise case selection, and release comparison.

No test, fixture, or test database exists yet. The standards describe the suite
to be built, not one that runs.

### Behavioral Rules
- Every test follows Arrange-Act-Assert. No exceptions.
- Test names are sentences that describe the behavior being verified.
- Test behavior, not implementation. Never assert that a specific internal function was called.
- New CDS rule = new table-driven test row. The test is written first and must fail before the rule is implemented.
- Invalid state machine transitions are tested as rigorously as valid ones.
- If a test is hard to write, stop and fix the source code — not the test.
- No test is left flaky. Fix it or delete it.

## graphify

This project uses a knowledge graph at `graphify-out/` with god nodes, community
structure, and cross-file relationships. It will be empty until there is code.

Rules:
- For codebase questions, first run `graphify query "<question>"` when `graphify-out/graph.json` exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If `graphify-out/wiki/index.md` exists, use it for broad navigation instead of raw source browsing.
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

---

`AGENTS.md` is an identical copy of this file. Edit both together.
