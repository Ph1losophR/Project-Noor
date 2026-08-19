# Final Whole-Branch Review Fix Report

## Status

All four actionable findings from the final whole-branch review are closed.
The approved assumption concerning `MappingInfo.confidence` was preserved: no
field was added and the closed model was not changed for it.

Implementation commit: `3e1136a` (`fix(canon): close remaining branch review findings`)

## Finding 1: Registry Immutability

`ObservableRegistry.entries` is now annotated as a read-only mapping and is
copied into a `MappingProxyType` after Pydantic validation. Loader dictionaries
remain valid constructor inputs, and the existing `entry()` lookup plus mapping
iteration behavior remain available. A serializer converts the internal proxy
back to a normal dictionary for model dumps.

The existing immutable collection coverage for `ObservableEntry` remains in
place. `test_registry_entries_are_immutable_after_validation` now verifies that
the registry's outer mapping rejects item assignment and `clear()`, while lookup
and model dumping still work.

## Finding 2: Quality Verdict Consistency

`QualityVerdict` now rejects these state-specific contradictions:

- `rejected` with `accepted_via`
- `needs_repeat_or_verification` with `rejection_reasons`

The existing accepted-family, rejection-reason, suspicion, unit-resolution,
pre-resolution, ambiguous-unit, and canonical-value invariants were retained.
The two invalid combinations have dedicated behavior tests, and existing valid
verdict tests continue to pass.

## Finding 3: Duplicate Conversion Sources

`ObservableEntry` now rejects duplicate `Conversion.from_unit` declarations
before conversion selection can become order-dependent. The new behavior test
constructs an entry with two declarations for the same source unit and asserts
Pydantic validation refuses it.

## Finding 4: Testing Standards Documentation

Only the stale opening repository-state claim in `docs/testing-standards.md` was
updated. It now names the existing foundation, observation-model,
registry-loader, canon unit, registry, and conversion-round-trip tests. It also
retains the forward-looking statement that later canon behavior, engine and
catalogue behavior, and the database are not built.

The wording was checked against the actual paths under `tests/` and `src/noor/`.
There is no dedicated documentation-consistency test in the repository; the
claim was verified directly against those files. No unrelated documentation was
rewritten.

## Verification

Baseline before implementation:

- `uv run pytest`: 135 passed.

Focused validation:

- `uv run pytest tests/canon/test_models.py tests/canon/test_registry.py tests/canon/test_units.py tests/catalogue/test_registry_loader.py -q`: 112 passed.

Full required validation:

- `uv run pytest --cov --cov-report=term-missing --cov-fail-under=100`: 139 passed, 100.00% total coverage.
- `uv run mypy --strict src/noor/canon src/noor/engine src/noor/catalogue`: passed with no issues.
- `uv run ruff check .`: passed.
- `uv run ruff format --check .`: 35 files already formatted.

## Scope and Concerns

- No `MappingInfo.confidence` field or related model change was made.
- No `graphify-out/` file was staged or modified by the remediation commit.
- Pre-existing worktree changes remain outside the remediation, including
  `.coverage` and generated `graphify-out/` files. They were not reverted.
- Later canon behavior, engine behavior, catalogue behavior beyond the current
  loader, and database tests remain future work as documented.

## Commits

- `3e1136a` - implementation, tests, and the targeted documentation correction.
- A separate follow-up commit contains this report.
