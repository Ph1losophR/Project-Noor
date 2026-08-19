# Whole-Branch Review Remediation Design

## Goal

Close the four review findings in the canon registry, quality-verdict, and unit
conversion boundaries without changing their public names, construction inputs, or
SSOT behavior.

## Design

- Registry declaration collections are normalized after Pydantic validation to
  immutable tuples and read-only mappings. YAML lists and dictionaries remain
  accepted, and values retain ordinary iteration and lookup behavior.
- `QualityVerdict` rejects accepted-family states carrying rejection reasons and
  rejects resolved outcomes carrying `unit_ambiguous`. Its existing pre-resolution
  equivalence and ambiguous-unit hard-failure checks remain authoritative.
- `ObservableEntry` requires each accepted noncanonical unit to have a conversion
  declaration, preventing a resolved unit from reaching a later conversion failure.
- `from_canonical` validates recorded provenance source units as accepted
  noncanonical units before the canonical identity path. Recorded factors and
  version remain historical provenance and continue to drive reverse arithmetic.

## Verification

Add focused AAA tests for each mutation and contradiction boundary, then run the
focused canon/catalogue tests, the full 100-percent coverage suite, strict mypy for
the requested source packages, ruff check, and ruff format check. Do not modify
graphify output.
