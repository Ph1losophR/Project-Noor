# Whole-Branch Review Remediation Implementation Plan

> **For agentic workers:** Execute the listed behavior-test and verification steps in order.

**Goal:** Close all four review findings with minimal canon and test changes.

**Architecture:** Keep validation at model/registry boundaries. Normalize registry
collections only after Pydantic accepts normal YAML-shaped inputs. Keep reverse
conversion provenance historical while validating only its source-unit identity.

**Tech Stack:** Python 3.12+, Pydantic v2, pytest, pytest-cov, mypy, ruff, uv.

## Global Constraints

- Preserve public field names, constructors, read/iteration behavior, and SSOT §6.2,
  §6.3, and §6.6 behavior.
- Do not lower coverage or add pragmas.
- Do not alter unrelated `graphify-out/` files.

### Task 1: Registry Immutability and Validation

**Files:**
- Modify: `src/noor/canon/registry.py`
- Test: `tests/canon/test_registry.py`

- [ ] Add mutation tests for accepted units, conversions, code-unit mapping,
  compare context, required context, and required method.
- [ ] Normalize those fields to immutable containers after validation.
- [ ] Reject every accepted noncanonical unit without one conversion declaration.
- [ ] Run the focused registry tests.

### Task 2: Verdict Consistency

**Files:**
- Modify: `src/noor/canon/models.py`
- Test: `tests/canon/test_models.py`

- [ ] Add tests for accepted-family rejection reasons and resolved
  `unit_ambiguous` combinations.
- [ ] Add the bidirectional consistency checks without changing the existing
  pre-resolution and ambiguous-unit invariants.
- [ ] Run the focused model tests.

### Task 3: Provenance Source-Unit Validation

**Files:**
- Modify: `src/noor/canon/units.py`
- Test: `tests/canon/test_units.py`

- [ ] Add a test for bogus provenance on a requested canonical unit.
- [ ] Reject provenance whose source is not an accepted noncanonical unit.
- [ ] Preserve historical factors/version values for valid reverse conversion.
- [ ] Run the focused unit tests.

### Task 4: Full Verification and Report

**Files:**
- Create: `.superpowers/sdd/branch-review-fix-report.md`

- [ ] Run full coverage, strict mypy over the requested packages, ruff check, and
  ruff format check.
- [ ] Record findings, files, commands, results, concerns, and commit identifiers.
- [ ] Stage only remediation files and the report; commit the remediation.
