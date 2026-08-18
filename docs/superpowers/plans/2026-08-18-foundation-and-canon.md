# Foundation + `canon` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the repository foundation (tooling, CI, the device-boundary seam test) and the complete `canon` data-validity layer — SSOT §14 steps 1–3.

**Architecture:** Pure Python under `src/noor/`. `canon` is a set of pure functions (no I/O, no clock, no DB) that turn an `ObservationCapture` into a `CanonicalObservation` carrying a four-state quality verdict. The observable registry is validated YAML content loaded through a schema-only loader in `catalogue`. Time enters only as data (timestamps on captures, explicit `resolved_at` arguments). Dependency direction is `canon` ← `engine` ← `catalogue` ← `app`, enforced by an AST-scanning test from the first commit (SSOT §4.2).

**Tech Stack:** Python 3.12+, uv, Pydantic v2, PyYAML (`safe_load` only), pytest + hypothesis, ruff, mypy `--strict`, GitHub Actions.

**Spec:** `docs/cds-architecture.md` (SSOT). Testing rules: `docs/testing-standards.md`. Where anything in this plan disagrees with the SSOT, **the SSOT wins** — stop and ask.

**Scope:** This plan covers §14 steps 1–3 only: repository foundation, the import-direction seam test, and all of `canon` (observable registry, unit resolution, plausibility, delta review, quality states, quality resolution). It does **not** build the engine (step 4), the catalogue compiler (step 5), or any persistence (step 7). Those are separate plans.

## Global Constraints

Every task implicitly includes these. Values are verbatim from the SSOT.

- Python ≥ 3.12; uv manages the project; `mypy --strict` runs on `canon/`, `engine/`, `catalogue/` (§3.1).
- Four quality states, exactly: `accepted`, `needs_repeat_or_verification`, `rejected`, `clinically_exceptional_accepted` (§6.2).
- `accepted_via`: exactly `unremarkable | repeat_confirmed | clinician_verified` (§6.2).
- Unit resolution: exactly `explicit | inferred_from_code | ambiguous`; `ambiguous` is a hard failure — the value never receives a canonical value and never reaches the engine (§6.3).
- A treatment threshold is never reused as a data-entry validator; the three boundary types are stored and versioned independently (§6.4). `canon` never names or reads a threshold — the seam test enforces that mechanically (Task 2) and the registry schema has nowhere to put one (Task 4).
- Every canonical value shows its work: a converted value carries the versioned conversion that produced it (§5 "derived, shows its work", §6.3).
- Delta review compares like with like only and never mutates, converts, replaces, or suppresses a value (§6.1).
- Content is loaded with a schema-only YAML loader (`yaml.safe_load`); an object-constructing tag is a build failure, not a warning (§7.5).
- All timestamps are timezone-aware and normalised to UTC at the model boundary (§2.6).
- `canon` performs no I/O and reads no clock — the seam test enforces this (§4.2, §8.4 invariant 8 applied to the whole boundary).
- Tests: Arrange-Act-Assert, sentence names, behaviour not implementation, boundary values over happy paths, no flakiness, hypothesis is seeded and its database is committed (`docs/testing-standards.md`).
- Never assert `not_triggered` where `indeterminate` is meant; here the analogue is: never assert `rejected` where `needs_repeat_or_verification` is meant, or vice versa.
- Commit at the end of every task. The PR is the four-eyes clinical approval mechanism (§7.5), so history must be reviewable task by task.
- Execute this plan on a branch, never on `main`. Every task commits to that branch; the branch reaches `main` by pull request, which is what makes Task 4's registry content four-eyes approved (§7.5, §14 step 1). Branch protection and `CODEOWNERS` are configured in Task 2 — before any content exists to protect.

## Assumptions and interpretations (read before executing)

The SSOT is precise; these are the few places this plan had to choose a reading. Each is stated, not hidden. If you disagree with any, stop and correct the plan before executing.

1. **How `clinically_exceptional_accepted` is reached (§6.2).** The SSOT says a
   repeat-resolved observation "becomes `accepted` with `accepted_via:
   repeat_confirmed`", and separately that `clinically_exceptional_accepted` "is
   what stops the plausibility gate from suppressing a genuine emergency". This
   plan reads those literally:
   - `confirm_repeat` → always `accepted` / `repeat_confirmed`.
   - `verify_by_clinician` on a value outside the *operational* envelope (which
     includes every physiologic-envelope rejection, since operational ⊆
     physiologic) → `clinically_exceptional_accepted` / `clinician_verified`;
     otherwise `accepted` / `clinician_verified`.
   So the exceptional state marks clinician-attested extreme values, and a
   mistype (`rejected`) and a real extreme value never share a state at capture:
   extreme-but-possible → `needs_repeat_or_verification`, impossible/unparseable
   → `rejected`.
   This reading is asymmetric, and the asymmetry is stated rather than hidden:
   pulse 220 confirmed by a repeat resolves to `accepted` / `repeat_confirmed`,
   while the same 220 verified by a clinician resolves to
   `clinically_exceptional_accepted` / `clinician_verified`. Both are in
   `ACCEPTED_FAMILY`, so nothing is suppressed either way, and §11.9's
   "proportion of clinically important changes after verification" loses nothing:
   envelope position is recomputable at any time from the stored canonical value
   and the versioned envelopes, so that counter reads position from the data, not
   from the state name. Deriving the exceptional state from envelope position in
   *both* paths would be one line in `confirm_repeat`; it is not done because
   §6.2 says a repeat-resolved observation "becomes `accepted` with
   `accepted_via: repeat_confirmed`" and the SSOT's literal sentence wins. If the
   clinical content owner prefers the symmetric reading, that is an SSOT change
   first, then a one-line change here.
2. **Rejected-but-verifiable.** `verify_by_clinician` is refused for
   `parse_failure`, `unit_ambiguous`, `mapping_unusable`, and
   `missing_required_context` rejections (there is no trustworthy value or the
   fix is re-capture). It is allowed for `outside_physiologic_envelope`
   rejections and any `needs_repeat_or_verification` observation.
3. **Resolutions are separate append-only records.** Observations are write-once
   (§5), so a quality-state change is not an edit. `canon` produces
   `QualityResolution` records; folding them into an effective state is the
   store's job (persistence plan), not canon's. The literal §6.2 sentence — a
   repeat-resolved observation *reads* as `accepted` with `accepted_via:
   repeat_confirmed` and a pointer to the confirming observation — is therefore
   proven by the fold, not by `confirm_repeat` alone; it is named in the handoff
   list at the end of this plan so the persistence plan carries a claim for it.
4. **Registry envelope numbers are interim content.** They are data-validity
   bounds (§6.4), not treatment thresholds (§7.3), so the citation gates do not
   apply — but they are clinical content owned by the named owner and change only
   via PR (§7.5). The starter values are conservative plausibility bounds, to be
   reviewed by the clinical content owner.
5. **Canonical units are declared, not assumed** (§6.6): glucose canonical
   `mmol/L`, creatinine `umol/L`, temperature `Cel`, BP `mm[Hg]`. Display always
   defaults to the as-reported unit (§6.6) — a UI concern, not canon's.
6. **Unit strings match the registry exactly.** No aliasing in the MVP: `"mmol/l"`
   is not `"mmol/L"`. An unrecognised spelling resolves `ambiguous`.
7. **`absent_reason` captures are refused by `canonicalise`.** Absence-with-reason
   is a valid stored fact (§5) but has no value to validate; the store records it
   verbatim. Canon validates *values*.
8. **Decimal separator is `.` only.** `"7,4"` is unparseable, not "7.4 with a
   comma". Strict parsing is the safety control.
9. **`code_unit_map` entries are illustrative.** The LOINC codes in the starter
   registry exist to exercise `inferred_from_code`; the terminology charter
   (§3.3) owns code-system verification when it lands, and CI gate 17 will
   enforce charter coverage of cited systems. `code_unit_map` stores bare
   `system|code` and no display strings deliberately: §2.4 keeps reproduced
   display strings out of distributable content, and §3.3's LOINC licence
   condition — the identifier and its official display name preserved alongside
   every mapping — is met on the observation, where `source_code.display` and
   `mapping.source_display` are carried verbatim (§5). Task 10 asserts they
   survive canon; an Arabic label never overwrites either (§3.3).
10. **Dependency direction:** `canon` ← `engine` ← `catalogue` ← `app`.
    `catalogue` does file I/O (its job is loading content); `canon` and `engine`
    never do. The seam test bans I/O and clock access in `canon` as well as
    `engine` — slightly stronger than §4.2's letter, exactly its spirit.
11. **Only two source statuses are unusable.** §13.1 gate 1 names *status*
    alongside units and time, so `canonicalise` reads `source_status`:
    `cancelled` and `entered_in_error` are refused outright
    (`source_status_unusable`, no canonical value — the source withdrew the
    record and there is nothing to resurrect). `registered`, `preliminary`,
    `final`, `amended`, and `corrected` all pass through unchanged. Whether a
    preliminary result is *usable for a decision* is a per-rule freshness
    question answered at evaluation time (§5.1, §7.1), never an intrinsic
    property of the observation.
12. **Three §5 fields, three separate decisions.** `recorded_at` is absent — the
    store stamps it (§5), and canon has no clock (§4.2). `encounter_id` is
    present, carried verbatim, and never read: a rule cannot ask which encounter
    a fact came from (§8.1), but the model is closed (`extra="forbid"`), so if
    canon's output could not carry it the app would need a wrapper around canon's
    output to store one inert §5 field. `mapping.confidence` is omitted: §5 gives
    it no type or vocabulary, canon's only mapping rule is status-based, and it
    arrives with the terminology charter (§3.3). Nothing in this plan depends on
    it.
13. **Quantity observables only.** Every registry field this plan builds —
    `canonical_ucum`, `accepted_units`, both envelopes, `delta_policy`,
    `repeat_tolerance` — presumes a measured quantity, and `canonicalise` parses
    a decimal. §6.6's Curated Clinical Signal Set (bounded coded symptoms, signs,
    and exam findings, which §5 says "cross the boundary through canon") does
    **not** fit this schema: it has no canonical unit and no envelopes, and
    `canonicalise` would reject one twice over (`parse_failure` +
    `unit_ambiguous`). It is not built here and is listed in the deferral list
    below with the schema change it needs.
14. **One renal observable, and `crcl` is deferred rather than dismissed.** The
    starter registry declares `egfr` and not `crcl`. §5.2 is categorical that the
    two are distinct observables and that a rule uses the one its product label
    specifies: a label written against Cockcroft-Gault CrCl "may not be evaluated
    against CKD-EPI eGFR", because the two diverge most in exactly the patients
    home care serves — elderly, low body weight, low muscle mass. §10.4 gate 15
    makes the catalogue compiler refuse a renal-dosing rule that omits
    `renal_metric` or names eGFR where the label says CrCl.

    The local SPC snapshot confirms `crcl` is **required, not hypothetical.**
    Reading `docs/research/saudi-local-db.json` (485 SPC-bearing products), the
    labels for pioglitazone's fixed combinations, liraglutide, gliclazide,
    carvedilol, hydralazine, clopidogrel, ticagrelor, tirofiban, atorvastatin and
    milrinone state every renal threshold in CrCl mL/min and contain no
    eGFR-based threshold at all; digoxin goes further and derives its maintenance
    dose from CrCl with an in-label Cockcroft-Gault estimate. Metformin and
    sitagliptin state theirs in GFR, and empagliflozin's own dose table is headed
    "eGFR [ml/min/1.73 m²] **or** CrCL [ml/min]". Two drugs use neither:
    spironolactone gates on serum creatinine in mg/dL (initiate ≤ 2.5,
    discontinue > 4.0) and digoxin's estimate starts from serum creatinine — both
    served by the `creatinine` entry this registry already declares with its
    mg/dL ↔ µmol/L conversion.

    What defers is the registry entry, not the question. No rule exists yet, so
    no rule needs the observable yet, and canon refusing an unregistered `crcl`
    as an unknown observable is the §5.2-correct outcome — the failure §5.2
    forbids is accepting a CrCl value *as* `egfr`, which an absent entry makes
    impossible. One thing the unit strings will *not* do is catch that failure
    for us. `egfr`'s canonical unit is `mL/min/{1.73_m2}`, and the braces are a
    UCUM annotation carrying no arithmetic meaning, so UCUM reduces it to plain
    `mL/min` — the same dimension `crcl` would declare. Converting between the
    two genuinely needs body-surface area, but no unit check can tell them apart,
    which is why §5.2 states the separation as a rule about *observables* rather
    than about units. The eventual entry is purely additive: one registry row and
    one line in the observable enumeration, no schema change. Lab-reported and Noor-derived
    values are already distinguishable at capture by `entry_mode` (`interfaced`
    vs `noor_derived`, §5), canon overwrites nothing, and §5.2's "never silently
    recomputed under a different equation" guarantee is the append-only store's.
    Equation provenance (`reported_equation`, the CKD-EPI 2021 default) is
    content-plan work, not canon's.

## File structure

```
pyproject.toml                          # uv project: deps, ruff, mypy, pytest config
uv.lock                                 # generated by `uv lock`
.gitignore                              # .hypothesis/ is deliberately NOT ignored
.github/workflows/ci.yml                # lint, format, typecheck boundary, test
.github/CODEOWNERS                      # content/ requires a code owner who is not the author (§7.5)
src/noor/__init__.py                    # docstring only
src/noor/canon/__init__.py              # docstring only
src/noor/canon/models.py                # §5 observation model + §6.2 quality verdicts
src/noor/canon/registry.py              # §6.6 registry Pydantic models
src/noor/canon/units.py                 # §6.3 unit resolution + conversions
src/noor/canon/parse.py                 # §6.1 layer 1: parsing, transposition pattern
src/noor/canon/plausibility.py          # §6.1 layer 2: the two envelopes
src/noor/canon/delta.py                 # §6.1 layer 3: like-with-like delta review
src/noor/canon/pipeline.py              # canonicalise(): the three layers, ordered
src/noor/canon/resolution.py            # §6.2/§6.5: QualityResolution, confirm_repeat, verify_by_clinician
src/noor/engine/__init__.py             # docstring only (empty until the engine plan)
src/noor/catalogue/__init__.py          # docstring only
src/noor/catalogue/registry_loader.py   # schema-only YAML load of the registry
src/noor/app/__init__.py                # docstring only (empty until the app plans)
content/observables/registry.yaml       # starter registry: 10 observables
tests/test_smoke.py                     # layout + interpreter sanity
tests/test_import_direction.py          # the seam (§4.2)
tests/conftest.py                       # factories, real-registry fixture, hypothesis profiles
tests/canon/test_models.py
tests/canon/test_registry.py
tests/catalogue/test_registry_loader.py
tests/canon/test_units.py
tests/canon/test_conversion_roundtrip.py  # §12.6 claim 41
tests/canon/test_parse.py
tests/canon/test_plausibility.py
tests/canon/test_delta.py
tests/canon/test_pipeline.py
tests/canon/test_resolution.py
tests/canon/test_properties.py          # hypothesis: nothing crosses uncanonicalised
```

---

### Task 1: Repository skeleton, tooling, and a green empty suite

SSOT §14 step 1: "`git init`, repository skeleton, `uv`, `ruff`, `mypy`, CI." (The repo already exists; this task adds the buildable skeleton.)

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/noor/__init__.py`, `src/noor/canon/__init__.py`, `src/noor/engine/__init__.py`, `src/noor/catalogue/__init__.py`, `src/noor/app/__init__.py`
- Create: `tests/test_smoke.py`
- Generate: `uv.lock` (via `uv lock`; never edit by hand)

**Interfaces:**
- Produces: the importable packages `noor`, `noor.canon`, `noor.engine`, `noor.catalogue`, `noor.app`; the commands `uv run pytest`, `uv run ruff check .`, `uv run mypy src/noor/canon src/noor/engine src/noor/catalogue` — every later task relies on these.

- [ ] **Step 0: Create the working branch**

Nothing in this plan commits to `main`. §7.5 makes the pull request the four-eyes approval, and §14 step 1 calls that "a prerequisite, not housekeeping".

```bash
git switch -c feat/foundation-and-canon
```

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "noor"
version = "0.1.0"
description = "Project Noor — a clinical decision support engine for supervised home visits"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.7",
    "pyyaml>=6.0.2",
]

[dependency-groups]
dev = [
    "hypothesis>=6.112",
    "mypy>=1.11",
    "pytest>=8.3",
    "pytest-cov>=6",
    "ruff>=0.6",
    "types-pyyaml>=6.0.12",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/noor"]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["B", "E", "F", "I", "RUF", "SIM", "UP"]

[tool.mypy]
strict = true
mypy_path = "src"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.coverage.run]
branch = true
source = ["src/noor"]

[tool.coverage.report]
# Empty, not the default ["pragma: no cover"]: a pragma cannot silence the 100%
# branch gate. An unreachable line is a design smell — simplify the code.
exclude_lines = []
```

- [ ] **Step 2: Write `.gitignore`**

```
.venv/
__pycache__/
*.py[cod]
.mypy_cache/
.ruff_cache/
.pytest_cache/
dist/
*.egg-info/

# .hypothesis/ is COMMITTED on purpose: hypothesis is seeded and its example
# database is part of the repo (docs/testing-standards.md).
```

- [ ] **Step 3: Write the five package `__init__.py` files**

`src/noor/__init__.py`:
```python
"""Project Noor — a clinical decision support engine for supervised home visits."""
```

`src/noor/canon/__init__.py`:
```python
"""canon — the data-validity layer (SSOT §6). Pure: no I/O, no clock, no database."""
```

`src/noor/engine/__init__.py`:
```python
"""engine — the evaluator (SSOT §8). Pure: no I/O, no clock, no database."""
```

`src/noor/catalogue/__init__.py`:
```python
"""catalogue — loader, compiler, and validator for clinical content (SSOT §7)."""
```

`src/noor/app/__init__.py`:
```python
"""app — FastAPI, persistence, and the clinical workflow (SSOT §11).

Lives OUTSIDE the device boundary (§2.2). canon, engine, and catalogue never
import this package; the seam test in tests/test_import_direction.py enforces it.
"""
```

- [ ] **Step 4: Write the smoke test**

`tests/test_smoke.py`:
```python
"""Layout sanity: the module map of SSOT §4.1 exists and imports."""

import importlib
import sys


def test_the_interpreter_is_at_least_python_312():
    # Arrange / Act / Assert
    assert sys.version_info >= (3, 12)


def test_the_ssot_module_layout_exists_and_imports():
    # Arrange
    modules = ("noor", "noor.canon", "noor.engine", "noor.catalogue", "noor.app")

    # Act / Assert
    for name in modules:
        module = importlib.import_module(name)
        assert module.__doc__, f"{name} must carry a docstring stating its boundary role"
```

- [ ] **Step 5: Lock, sync, and run everything**

Run: `uv lock`
Expected: creates `uv.lock` without errors.

Run: `uv sync`
Expected: creates `.venv`, installs the project editable plus dev dependencies.

Run: `uv run pytest`
Expected: `2 passed` (both smoke tests).

Run: `uv run ruff check .`
Expected: `All checks passed!`

Run: `uv run mypy src/noor/canon src/noor/engine src/noor/catalogue`
Expected: `Success: no issues found` (empty packages type-check trivially).

- [ ] **Step 6: Commit**

```powershell
git add pyproject.toml uv.lock .gitignore src tests
git commit -m "chore: repository skeleton with uv, ruff, mypy, pytest (SSOT §14 step 1)"
```

---

### Task 2: CI and the import-direction seam test

SSOT §14 step 1 verification: "CI runs green on an empty suite; the import-direction test exists and passes (§4.2)." This test is the mechanical half of the device boundary. It must exist **before** there is meaningful code to police.

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/CODEOWNERS`
- Create: `tests/test_import_direction.py`

**Interfaces:**
- Consumes: the package layout and tooling from Task 1.
- Produces: the seam test every later task must keep green; CI that runs lint, format-check, mypy on the boundary packages, and the test suite on every push and PR; branch protection and `CODEOWNERS`, so Task 4's registry content cannot land without review (§7.5).

- [ ] **Step 1: Write the failing seam test**

`tests/test_import_direction.py`:
```python
"""The device-boundary seam test (SSOT §4.2).

`app` imports from `canon`, `engine`, and `catalogue` — never the reverse.
`canon` and `engine` are pure: no database, no HTTP, no filesystem, no clock
(§8.4 invariant 8 applied to the whole boundary). `canon` additionally never
names a treatment threshold: §6.4's three boundary types are separate, and
`docs/testing-standards.md` requires a test that proves they are not read from
one another. This test exists from the first commit, before there is anything to
import (§14 step 1).
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "noor"

BOUNDARY_PACKAGES = ("canon", "engine", "catalogue")
PURE_PACKAGES = ("canon", "engine")

FORBIDDEN_IMPORT_ROOTS_IN_PURE = frozenset(
    {
        "sqlalchemy",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "fastapi",
        "starlette",
        "httpx",
        "requests",
        "aiohttp",
        "socket",
        "os",
        "pathlib",
        "shutil",
        "io",
        "time",
    }
)

# Attribute calls that read the wall clock. Time enters the boundary as data
# (§4.2): timestamps on captures, explicit arguments — never a `now()` call.
FORBIDDEN_CLOCK_CALLS_IN_PURE = frozenset(
    {"now", "utcnow", "today", "time", "monotonic", "perf_counter"}
)

# §6.4: a treatment threshold is never reused as a data-entry validator. `canon`
# validates data; thresholds are the engine's, from a compiled snapshot. Any
# identifier naming one inside canon means the two have been wired together.
FORBIDDEN_SUBSTRINGS_IN_CANON = ("threshold", "target_range")


def _python_files(package: str) -> list[Path]:
    directory = SRC / package
    if not directory.exists():
        return []
    return sorted(directory.rglob("*.py"))


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


def _called_attributes(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]


def _identifiers(path: Path) -> list[str]:
    """Every name the code *uses* — not comments or docstrings, which may say
    "threshold" while explaining why there isn't one."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.extend(alias.name for alias in node.names)
    return names


@pytest.mark.parametrize("package", BOUNDARY_PACKAGES)
def test_boundary_packages_never_import_app(package: str):
    # Arrange / Act
    offenders = [
        (path, module)
        for path in _python_files(package)
        for module in _imported_modules(path)
        if module == "noor.app" or module.startswith("noor.app.")
    ]

    # Assert
    assert not offenders, f"{package} must never import app (SSOT §4.2): {offenders}"


@pytest.mark.parametrize("package", PURE_PACKAGES)
def test_pure_packages_import_no_io_or_clock_modules(package: str):
    # Arrange / Act
    offenders = [
        (path, module)
        for path in _python_files(package)
        for module in _imported_modules(path)
        if module.split(".")[0] in FORBIDDEN_IMPORT_ROOTS_IN_PURE
    ]

    # Assert
    assert not offenders, (
        f"pure package {package} must not import I/O or clock modules "
        f"(SSOT §4.2, §8.4.8): {offenders}"
    )


@pytest.mark.parametrize("package", PURE_PACKAGES)
def test_pure_packages_never_read_the_wall_clock(package: str):
    # Arrange / Act
    offenders = [
        (path, attribute)
        for path in _python_files(package)
        for attribute in set(_called_attributes(path)) & FORBIDDEN_CLOCK_CALLS_IN_PURE
    ]

    # Assert
    assert not offenders, (
        f"pure package {package} reads the wall clock; time enters as data "
        f"(SSOT §4.2): {offenders}"
    )


def test_canon_never_names_a_treatment_threshold():
    # Arrange / Act — §6.4: the three boundary types are separate, and the
    # testing standards require a test that they are not read from one another.
    # canon's envelopes are data-validity bounds; a threshold here would mean a
    # clinical decision boundary had leaked into data entry.
    offenders = [
        (path, name)
        for path in _python_files("canon")
        for name in _identifiers(path)
        if any(substring in name.lower() for substring in FORBIDDEN_SUBSTRINGS_IN_CANON)
    ]

    # Assert
    assert not offenders, (
        f"canon must never read a treatment threshold (SSOT §6.4): {offenders}"
    )
```

- [ ] **Step 2: Run the test to verify it passes against the empty packages**

Run: `uv run pytest tests/test_import_direction.py -v`
Expected: PASS — 8 tests pass trivially (empty packages import nothing). A guard that can only fail is useless; a guard green from day one catches the first breach. To prove the test has teeth, temporarily add `import os` to `src/noor/engine/__init__.py`, re-run (expected: FAIL naming `engine` and `os`), then revert. Do the same with `bp_threshold = 140` in `src/noor/canon/__init__.py` (expected: FAIL naming `canon` and `bp_threshold`), then revert.

- [ ] **Step 3: Write the CI workflow**

`.github/workflows/ci.yml`:
```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv and Python
        uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: uv sync --frozen

      - name: Lint
        run: uv run ruff check .

      - name: Format
        run: uv run ruff format --check .

      - name: Type-check the device boundary
        run: uv run mypy src/noor/canon src/noor/engine src/noor/catalogue

      - name: Test
        run: uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
        env:
          CI: "true"
```

(The testing standards set 100% branch coverage on canon/engine/catalogue; the empty `app/`, `engine/`, and `catalogue` `__init__` files stay covered via the smoke test's imports. If a line is genuinely unreachable, simplify the code — do not lower the bar.)

- [ ] **Step 4: Verify the exact CI commands pass locally**

Run: `uv run ruff check .`
Expected: `All checks passed!`

Run: `uv run ruff format --check .`
Expected: all files formatted (run `uv run ruff format .` first if this fails, then re-check).

Run: `uv run mypy src/noor/canon src/noor/engine src/noor/catalogue`
Expected: `Success: no issues found`.

Run: `uv run pytest`
Expected: all tests pass (smoke + seam).

- [ ] **Step 5: Write `.github/CODEOWNERS`**

§7.5: "the pull request *is* the four-eyes approval". A PR only approves clinical content if the right eyes are required on it. Both handles below were verified on 2026-08-18 as collaborators with push access: `@Ph1losophR` is the clinical content owner and `@ph1losophrr` is the second clinical approver, Dr. Ahmed Sabry (§10.3). **The two differ by a single trailing character — copy them exactly.** An unresolvable handle silently disables the rule.

GitHub requires only *one* listed code owner to approve and forbids self-approval, so whichever of the two authors the PR is excluded and the other must review it. That is §7.5's four eyes, enforced mechanically rather than by convention.

```
# Clinical content requires review from a code owner other than the author (SSOT §7.5).
# @Ph1losophR is the clinical content owner; @ph1losophrr is the second clinical
# approver (§10.2, §10.3). The registry's envelopes and conversions are clinical
# content (§6.4, §6.6).
/content/                 @Ph1losophR @ph1losophrr
/docs/cds-architecture.md @Ph1losophR @ph1losophrr
```

- [ ] **Step 6: Enable branch protection on `main`**

§14 step 1 names git-as-governance "a prerequisite, not housekeeping". Without protection, `main` accepts a direct push and the PR gate is decorative. Run once. Feasibility was confirmed on 2026-08-18: the repository is `Ph1losophR/Project-Noor`, public, and the authenticated account holds `ADMIN`, so protected branches are available and `main` is currently unprotected.

The body goes in as JSON rather than as `-F` fields. `restrictions` must be `null`, which `-F restrictions=` sends as an empty string instead, and the nested `contexts` array is not worth trusting to field-path parsing.

```bash
gh api -X PUT repos/Ph1losophR/Project-Noor/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  --input - <<'JSON'
{
  "required_status_checks": {"strict": true, "contexts": ["verify"]},
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "require_code_owner_reviews": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
```

Verify: `gh api repos/Ph1losophR/Project-Noor/branches/main/protection --jq '.required_pull_request_reviews.require_code_owner_reviews'`
Expected: `true`.

If `gh` is unavailable or you lack admin rights, stop and get it done in the GitHub UI (Settings → Branches → Add rule on `main`): require a PR before merging, require 1 approval, require review from Code Owners, require the `verify` status check, include administrators, forbid force pushes and deletions. **Do not proceed to Task 4** — that is where clinical content first lands, and it must land through a protected branch.

- [ ] **Step 7: Commit**

```powershell
git add .github tests/test_import_direction.py
git commit -m "ci: github actions workflow, CODEOWNERS, and the §4.2 import-direction seam test"
```

---

### Task 3: The observation model and quality verdicts

SSOT §5 (the observation model) restricted to what `canon` produces and consumes, plus the §6.2 quality vocabulary. Every model is frozen and closed (`extra="forbid"`) — the same closed-contract discipline §4.2 imposes on the snapshot.

**Files:**
- Create: `src/noor/canon/models.py`
- Create: `tests/conftest.py`
- Create: `tests/canon/test_models.py`

**Interfaces:**
- Consumes: nothing beyond Pydantic.
- Produces (used by every later task):
  - `NoorModel` — base class: `frozen=True, extra="forbid"`.
  - Enums: `UnitResolution`, `QualityState`, `AcceptedVia`, `RejectionReason`, `SuspicionReason`, `NotComparableReason`, `SourceStatus`, `EntryMode`, `InformantRole`, `MappingStatus`, `Setting`, `Posture`, `Arm`, `CuffSize`.
  - `ACCEPTED_FAMILY: frozenset[QualityState]` — `{accepted, clinically_exceptional_accepted}`.
  - `WITHDRAWN_SOURCE_STATUSES: frozenset[SourceStatus]` — `{cancelled, entered_in_error}`.
  - Models: `SourceCode`, `Informant`, `MethodContext`, `CaptureContext`, `MappingInfo`, `ReportedValue`, `ObservationCapture`, `ConversionApplied`, `CanonicalQuantity`, `DeltaVerdict`, `QualityVerdict`, `CanonicalObservation`.
  - `CanonicalQuantity(value, ucum, conversion_applied: ConversionApplied | None)`; `ConversionApplied(from_unit, add, multiply, precision, rounding, version)`.
  - `DeltaVerdict(comparable, compared_to=None, change=None, suspicious=False, not_comparable_reason=None)` — validated: comparable ⇒ baseline + change; not comparable ⇒ reason only.
  - `CanonicalObservation(**capture.model_dump(), canonical=..., quality=...)` is how the pipeline builds output. An accepted-family state without a canonical value is a validation error.
  - conftest: `REPO_ROOT`, `T0`, `make_capture(...)` (with `value=`/`unit=` shorthands), hypothesis profile registration.

- [ ] **Step 1: Write the failing tests**

`tests/conftest.py`:
```python
"""Shared builders and fixtures (docs/testing-standards.md: factories live here)."""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from hypothesis import settings

from noor.canon.models import EntryMode, ObservationCapture, ReportedValue, SourceStatus

settings.register_profile("ci", derandomize=True)
if os.environ.get("CI"):
    settings.load_profile("ci")

REPO_ROOT = Path(__file__).resolve().parent.parent

T0 = datetime(2026, 6, 12, 8, 20, tzinfo=timezone.utc)


def make_capture(**overrides: Any) -> ObservationCapture:
    """A well-formed glucose capture; override anything.

    `value` and `unit` are shorthands for the `as_reported` pair, which is what
    almost every canon test varies. Anything else goes straight through.
    """
    fields: dict[str, Any] = {
        "observable": "glucose",
        "source_system": "test-lis",
        "source_identifier": "OBS-1",
        "source_status": SourceStatus.final,
        "effective_time": T0,
        "entry_mode": EntryMode.staff_transcribed,
        "as_reported": ReportedValue(value="5.5", unit="mmol/L"),
    }
    if "value" in overrides or "unit" in overrides:
        fields["as_reported"] = ReportedValue(
            value=overrides.pop("value", "5.5"), unit=overrides.pop("unit", "mmol/L")
        )
    fields.update(overrides)
    return ObservationCapture(**fields)


```

`tests/canon/test_models.py`:
```python
"""The §5 observation model: closed, immutable, UTC, with the §5.4/§5 invariants."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.canon.models import (
    AcceptedVia,
    CanonicalObservation,
    DeltaVerdict,
    EntryMode,
    Informant,
    InformantRole,
    NotComparableReason,
    QualityState,
    QualityVerdict,
    RejectionReason,
    ReportedValue,
    SuspicionReason,
    UnitResolution,
)
from tests.conftest import make_capture


def test_effective_time_is_normalised_to_utc():
    # Arrange / Act
    capture = make_capture(
        effective_time=datetime(2026, 6, 12, 11, 20, tzinfo=timezone(timedelta(hours=3)))
    )

    # Assert — 11:20 at +03:00 is 08:20 UTC (§2.6)
    assert capture.effective_time.tzinfo is timezone.utc
    assert capture.effective_time.hour == 8
    assert capture.effective_time.minute == 20


def test_a_naive_datetime_is_refused():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_capture(effective_time=datetime(2026, 6, 12, 8, 20))


def test_patient_reported_entry_requires_an_informant():
    # Arrange / Act / Assert — §5.4: this is not optional
    with pytest.raises(ValidationError):
        make_capture(entry_mode=EntryMode.patient_reported, informant=None)


def test_patient_reported_entry_with_an_informant_is_accepted():
    # Arrange / Act
    capture = make_capture(
        entry_mode=EntryMode.patient_reported,
        informant=Informant(role=InformantRole.medicine_manager, person_id="MM-17"),
    )

    # Assert
    assert capture.informant is not None
    assert capture.informant.role is InformantRole.medicine_manager


def test_absent_reason_is_set_instead_of_a_value_never_alongside_one():
    # Arrange / Act / Assert — §5: absence with a stated reason is not a value
    with pytest.raises(ValidationError):
        make_capture(
            as_reported=ReportedValue(value="5.5", unit="mmol/L"),
            absent_reason="not_done",
        )


def test_the_model_is_closed_to_undeclared_fields():
    # Arrange / Act / Assert — the §4.2 closed-contract discipline, applied to captures
    with pytest.raises(ValidationError):
        make_capture(ward="north")


def test_the_model_is_immutable():
    # Arrange
    capture = make_capture()

    # Act / Assert — observations are write-once (§5); the model makes it literal
    with pytest.raises(ValidationError):
        capture.observable = "pulse"  # type: ignore[misc]


def test_an_accepted_verdict_must_carry_how_it_got_there():
    # Arrange / Act / Assert — §6.2: accepted_via is not optional
    with pytest.raises(ValidationError):
        QualityVerdict(state=QualityState.accepted, unit_resolution=UnitResolution.explicit)


def test_a_rejected_verdict_must_name_why():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        QualityVerdict(state=QualityState.rejected, unit_resolution=UnitResolution.explicit)


def test_a_flagged_verdict_must_name_what_is_suspected():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        QualityVerdict(
            state=QualityState.needs_repeat_or_verification,
            unit_resolution=UnitResolution.explicit,
        )


def test_a_consistent_rejected_verdict_is_accepted():
    # Arrange / Act
    verdict = QualityVerdict(
        state=QualityState.rejected,
        unit_resolution=UnitResolution.ambiguous,
        rejection_reasons=[RejectionReason.unit_ambiguous],
    )

    # Assert
    assert verdict.state is QualityState.rejected
    assert verdict.accepted_via is None


def test_a_consistent_flagged_verdict_is_accepted():
    # Arrange / Act
    verdict = QualityVerdict(
        state=QualityState.needs_repeat_or_verification,
        unit_resolution=UnitResolution.explicit,
        suspicions=[SuspicionReason.delta_exceeded],
    )

    # Assert
    assert verdict.suspicions == [SuspicionReason.delta_exceeded]


def test_accepted_via_unremarkable_round_trips():
    # Arrange / Act
    verdict = QualityVerdict(
        state=QualityState.accepted,
        unit_resolution=UnitResolution.explicit,
        accepted_via=AcceptedVia.unremarkable,
    )

    # Assert
    assert verdict.accepted_via is AcceptedVia.unremarkable


def test_an_accepted_observation_must_carry_a_canonical_value():
    # Arrange
    capture = make_capture()
    quality = QualityVerdict(
        state=QualityState.accepted,
        unit_resolution=UnitResolution.explicit,
        accepted_via=AcceptedVia.unremarkable,
    )

    # Act / Assert — §6.3 as a type invariant, not a convention: nothing accepted
    # reaches the engine without a canonical value
    with pytest.raises(ValidationError):
        CanonicalObservation(**capture.model_dump(), canonical=None, quality=quality)


def test_a_comparable_delta_names_its_baseline_and_its_change():
    # Arrange / Act
    delta = DeltaVerdict(comparable=True, compared_to="OBS-0", change=Decimal("0.6"))

    # Assert — the delta is a recorded fact, not a flag (§5)
    assert delta.suspicious is False
    assert delta.not_comparable_reason is None


def test_a_comparable_delta_without_a_baseline_is_refused():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        DeltaVerdict(comparable=True, change=Decimal("0.6"))


def test_an_incomparable_delta_records_why_nothing_was_compared():
    # Arrange / Act — §11.9's delta-check rate needs "not compared" to be a fact
    delta = DeltaVerdict(
        comparable=False,
        not_comparable_reason=NotComparableReason.no_prior_observation,
    )

    # Assert
    assert delta.compared_to is None
    assert delta.change is None


def test_an_incomparable_delta_that_names_a_baseline_is_refused():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        DeltaVerdict(
            comparable=False,
            compared_to="OBS-0",
            not_comparable_reason=NotComparableReason.no_comparable_prior,
        )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/canon/test_models.py -v`
Expected: FAIL — collection error, `noor.canon.models` does not exist.

- [ ] **Step 3: Write `src/noor/canon/models.py`**

```python
"""The observation model (SSOT §5) and canon's quality verdicts (§6.2).

Every model is frozen and closed: an observation is written once and never
overwritten, and an undeclared field cannot enter the record.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class NoorModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class UnitResolution(StrEnum):
    explicit = "explicit"
    inferred_from_code = "inferred_from_code"
    ambiguous = "ambiguous"


class QualityState(StrEnum):
    accepted = "accepted"
    needs_repeat_or_verification = "needs_repeat_or_verification"
    rejected = "rejected"
    clinically_exceptional_accepted = "clinically_exceptional_accepted"


ACCEPTED_FAMILY: frozenset[QualityState] = frozenset(
    {QualityState.accepted, QualityState.clinically_exceptional_accepted}
)


class AcceptedVia(StrEnum):
    unremarkable = "unremarkable"
    repeat_confirmed = "repeat_confirmed"
    clinician_verified = "clinician_verified"


class RejectionReason(StrEnum):
    mapping_unusable = "mapping_unusable"
    source_status_unusable = "source_status_unusable"
    parse_failure = "parse_failure"
    unit_ambiguous = "unit_ambiguous"
    missing_required_context = "missing_required_context"
    outside_physiologic_envelope = "outside_physiologic_envelope"


class SuspicionReason(StrEnum):
    outside_operational_envelope = "outside_operational_envelope"
    decimal_transposition_suspected = "decimal_transposition_suspected"
    unit_changed_from_prior = "unit_changed_from_prior"
    delta_exceeded = "delta_exceeded"


class NotComparableReason(StrEnum):
    """Why delta review compared nothing. "Not compared" is a fact of record, not
    a silent pass (§5), and §11.9's delta-check rate is computed from it."""

    no_prior_observation = "no_prior_observation"  # none of this observable at all
    no_comparable_prior = "no_comparable_prior"  # priors exist, none like-with-like


class SourceStatus(StrEnum):
    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"


# The source withdrew the record. There is no value to validate and nothing to
# resurrect, so canon refuses it before the three layers run (§13.1 gate 1 names
# status alongside units and time). Every other status passes through: whether a
# preliminary result is usable for a decision is a per-rule freshness question
# answered at evaluation time (§5.1), not an intrinsic property of the value.
WITHDRAWN_SOURCE_STATUSES: frozenset[SourceStatus] = frozenset(
    {SourceStatus.cancelled, SourceStatus.entered_in_error}
)


class EntryMode(StrEnum):
    interfaced = "interfaced"
    staff_transcribed = "staff_transcribed"
    patient_reported = "patient_reported"
    device_memory = "device_memory"
    noor_derived = "noor_derived"


class InformantRole(StrEnum):
    patient = "patient"
    medicine_manager = "medicine_manager"


class MappingStatus(StrEnum):
    mapped = "mapped"
    ambiguous = "ambiguous"
    unmapped = "unmapped"


class Setting(StrEnum):
    office = "office"
    home = "home"
    ambulatory = "ambulatory"


class Posture(StrEnum):
    sitting = "sitting"
    supine = "supine"
    standing = "standing"


class Arm(StrEnum):
    left = "left"
    right = "right"


class CuffSize(StrEnum):
    small = "small"
    standard = "standard"
    large = "large"
    thigh = "thigh"


class SourceCode(NoorModel):
    system: str = Field(min_length=1)
    code: str = Field(min_length=1)
    display: str | None = None


class Informant(NoorModel):
    role: InformantRole
    person_id: str = Field(min_length=1)


class MethodContext(NoorModel):
    device_class: str | None = None
    specimen: str | None = None
    assay: str | None = None


class CaptureContext(NoorModel):
    """Per-observable context (SSOT §6.6). BP needs all of it; the registry says so."""

    posture: Posture | None = None
    arm: Arm | None = None
    cuff_size: CuffSize | None = None
    rest_duration_seconds: int | None = Field(default=None, ge=0)
    reading_ordinal: int | None = Field(default=None, ge=1)
    is_average: bool | None = None


class MappingInfo(NoorModel):
    """How the source code became a Noor observable (SSOT §5)."""

    status: MappingStatus = MappingStatus.mapped
    source_display: str | None = None
    terminology_version: str | None = None


class ReportedValue(NoorModel):
    """Exactly as captured. The value stays a string until parse validates it."""

    value: str | None = None
    unit: str | None = None


def _utc(value: datetime | None) -> datetime | None:
    return None if value is None else value.astimezone(timezone.utc)


class ObservationCapture(NoorModel):
    """Canon's input: one observation exactly as captured (SSOT §5).

    `recorded_at` is deliberately absent — the store stamps it (§5).
    `encounter_id` is carried and never read: a rule cannot ask which encounter a
    fact came from (§8.1), but the model is closed, so canon's output has to be
    able to hold the one inert §5 field the workflow adds.
    """

    observable: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    source_identifier: str = Field(min_length=1)
    source_version: int = Field(default=1, ge=1)
    source_code: SourceCode | None = None
    source_status: SourceStatus
    encounter_id: str | None = None
    effective_time: AwareDatetime
    issued_at: AwareDatetime | None = None
    received_at: AwareDatetime | None = None
    entry_mode: EntryMode
    informant: Informant | None = None
    method: MethodContext = MethodContext()
    setting: Setting | None = None
    context: CaptureContext = CaptureContext()
    as_reported: ReportedValue
    absent_reason: str | None = None
    mapping: MappingInfo = MappingInfo()
    context_flags: list[str] = []
    raw_payload: dict = {}

    @field_validator("effective_time", "issued_at", "received_at")
    @classmethod
    def _normalise_to_utc(cls, value: datetime | None) -> datetime | None:
        return _utc(value)

    @model_validator(mode="after")
    def _patient_reported_requires_an_informant(self) -> Self:
        if self.entry_mode is EntryMode.patient_reported and self.informant is None:
            raise ValueError("patient_reported observations name their informant (SSOT §5.4)")
        return self

    @model_validator(mode="after")
    def _absent_reason_replaces_the_value(self) -> Self:
        if self.absent_reason is not None and self.as_reported.value is not None:
            raise ValueError("absent_reason is set INSTEAD of a value, never alongside it (§5)")
        return self


class ConversionApplied(NoorModel):
    """The conversion that produced a canonical value (SSOT §6.3: "every
    conversion … carries its own provenance").

    Copied onto the value, not referenced: content is versioned and mutable by PR,
    so a stored observation must still say which factor it was computed with. If
    `0.055507` is ever corrected, `version` is how the affected rows are found.
    """

    from_unit: str = Field(min_length=1)
    add: Decimal
    multiply: Decimal
    precision: int = Field(ge=0)
    rounding: str = Field(min_length=1)
    version: str = Field(min_length=1)


class CanonicalQuantity(NoorModel):
    """Derived, and it shows its work (§5, §6.3).

    `conversion_applied` is None exactly when the reported unit was already the
    canonical unit — an identity conversion has no work to show.
    """

    value: Decimal
    ucum: str = Field(min_length=1)
    conversion_applied: ConversionApplied | None = None


class DeltaVerdict(NoorModel):
    """What delta review compared, or why it compared nothing (§5, §6.1).

    Always recorded when the three layers ran: `comparable=False` with a reason is
    the record that nothing was compared, which is what §11.9's delta-check rate
    counts. `QualityVerdict.delta is None` means something else — delta review
    never ran, because the value was rejected before layer 3.
    """

    comparable: bool
    compared_to: str | None = None  # source_identifier of the prior
    change: Decimal | None = None
    suspicious: bool = False
    not_comparable_reason: NotComparableReason | None = None

    @model_validator(mode="after")
    def _the_verdict_says_what_it_compared(self) -> Self:
        if self.comparable:
            if (
                self.compared_to is None
                or self.change is None
                or self.not_comparable_reason is not None
            ):
                raise ValueError("a comparable delta names its baseline and its change (§5)")
        elif (
            self.compared_to is not None
            or self.change is not None
            or self.not_comparable_reason is None
        ):
            raise ValueError("an incomparable delta names its reason and nothing else")
        return self


class QualityVerdict(NoorModel):
    """Canon's intrinsic verdict on one observation (SSOT §6.2)."""

    state: QualityState
    unit_resolution: UnitResolution
    accepted_via: AcceptedVia | None = None
    rejection_reasons: list[RejectionReason] = []
    suspicions: list[SuspicionReason] = []
    delta: DeltaVerdict | None = None

    @model_validator(mode="after")
    def _the_verdict_explains_itself(self) -> Self:
        if self.state in ACCEPTED_FAMILY and self.accepted_via is None:
            raise ValueError("an accepted observation carries how it got there (§6.2)")
        if self.state is QualityState.rejected and not self.rejection_reasons:
            raise ValueError("a rejected observation names why")
        if self.state is QualityState.needs_repeat_or_verification and not self.suspicions:
            raise ValueError("a flagged observation names what is suspected")
        return self


class CanonicalObservation(ObservationCapture):
    """Canon's output: the verbatim capture, its canonical value, its quality verdict.

    `canonical` is None exactly when the value could not be made safe to evaluate —
    most sharply when `unit_resolution` is `ambiguous` (§6.3). The converse is an
    invariant, not a hope: an accepted-family observation always carries a
    canonical value, which is what lets `delta` and the engine read it without a
    None check they could get wrong.
    """

    canonical: CanonicalQuantity | None
    quality: QualityVerdict

    @model_validator(mode="after")
    def _an_accepted_observation_carries_a_canonical_value(self) -> Self:
        if self.quality.state in ACCEPTED_FAMILY and self.canonical is None:
            raise ValueError("an accepted observation carries a canonical value (§6.3)")
        return self
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/canon/test_models.py -v`
Expected: PASS — 18 tests.

Run: `uv run mypy src/noor/canon`
Expected: `Success: no issues found`.

- [ ] **Step 5: Commit**

```powershell
git add src/noor/canon/models.py tests/conftest.py tests/canon/test_models.py
git commit -m "feat(canon): observation model and quality verdicts (SSOT §5, §6.2)"
```

---

### Task 4: The observable registry schema, the starter registry, and the safe loader

SSOT §6.6: the registry declares, per observable, canonical UCUM unit, accepted units and conversions with precision and rounding, both envelopes, delta policy, required context/method fields, and a named owner. §6.4: the envelope types are stored and versioned independently. §7.5: schema-only YAML loading.

**Files:**
- Create: `src/noor/canon/registry.py`
- Create: `src/noor/catalogue/registry_loader.py`
- Create: `content/observables/registry.yaml`
- Create: `tests/canon/test_registry.py`
- Create: `tests/catalogue/test_registry_loader.py`
- Modify: `tests/conftest.py` (add the real-registry fixture and a synthetic-entry factory)

**Interfaces:**
- Consumes: `NoorModel` (Task 3).
- Produces:
  - `Envelope(low: Decimal, high: Decimal, version: str)` — inclusive bounds in the canonical unit.
  - `Conversion(from_unit, add=0, multiply=1, precision, rounding="ROUND_HALF_UP", tolerance, canonical_tolerance, version)` — canonical = `(value + add) * multiply`, quantised to `precision`; `tolerance` is the round-trip bound in the **source** unit and `canonical_tolerance` the bound in the **canonical** unit, because §6.3 requires reversibility "in both directions" (§12.6 claim 41); `version` is the conversion's own content version, copied onto every value it produces (§6.3 provenance).
  - `DeltaPolicy(max_abs_change, within_hours, compare_context: list[str], compare_device_class: bool)`.
  - `ObservableEntry(...)` — fields exactly as in the model code below.
  - `ObservableRegistry.entries: dict[str, ObservableEntry]` and `.entry(observable) -> ObservableEntry` (raises `UnknownObservableError`).
  - `CONTEXT_FIELDS`, `METHOD_FIELDS` — the legal names for `required_context`/`compare_context` and `required_method`.
  - `load_registry(path: Path) -> ObservableRegistry` in `noor.catalogue.registry_loader`.
  - conftest: `registry` fixture (the real content file), `make_entry(**overrides)`.

- [ ] **Step 1: Write the failing tests**

`tests/canon/test_registry.py`:
```python
"""The registry validates itself at load (SSOT §6.4, §6.6)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.canon.registry import (
    Conversion,
    DeltaPolicy,
    Envelope,
    ObservableEntry,
    ObservableRegistry,
    UnknownObservableError,
)
from tests.conftest import make_entry


def test_a_well_formed_entry_validates():
    # Arrange / Act
    entry = make_entry()

    # Assert
    assert entry.observable == "test_obs"
    assert entry.canonical_ucum == "mmol/L"


def test_the_canonical_unit_must_be_an_accepted_unit():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(canonical_ucum="mg/dL", accepted_units=["mmol/L"])


def test_the_operational_envelope_must_sit_inside_the_physiologic_envelope():
    # Arrange — operational low below the physiologic floor
    bad_operational = Envelope(low=Decimal("1"), high=Decimal("8"), version="t1")

    # Act / Assert — the two boundary types are versioned independently but
    # nested (§6.4): an operational bound outside "cannot be generated" is a
    # registry authoring error, caught at load
    with pytest.raises(ValidationError):
        make_entry(operational=bad_operational)


def test_an_envelope_must_be_ordered():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        Envelope(low=Decimal("8"), high=Decimal("2"), version="t1")


def test_the_two_envelope_types_are_versioned_independently():
    # Arrange — §6.4: stored and versioned independently, and neither is a
    # treatment threshold. Nothing derives one version from the other.
    entry = make_entry(
        physiologic=Envelope(low=Decimal("2"), high=Decimal("10"), version="physio-2026-01"),
        operational=Envelope(low=Decimal("4"), high=Decimal("8"), version="oper-2026-07"),
    )

    # Assert
    assert entry.physiologic.version == "physio-2026-01"
    assert entry.operational.version == "oper-2026-07"


def test_the_registry_declares_no_treatment_threshold_field():
    # Arrange / Act — the other half of the boundary-separation proof (§6.4,
    # docs/testing-standards.md): the data-validity schema has nowhere to put a
    # clinical decision boundary, so no code can read one from here
    fields = set(ObservableEntry.model_fields)

    # Assert
    assert not {name for name in fields if "threshold" in name or "target" in name}


def test_a_conversion_must_convert_from_an_accepted_non_canonical_unit():
    # Arrange
    bad = Conversion(
        from_unit="mmol/L",
        precision=2,
        tolerance=Decimal("0.5"),
        canonical_tolerance=Decimal("0.01"),
        version="t1",
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        make_entry(conversions=[bad])


def test_a_conversion_multiplier_must_be_positive():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        Conversion(
            from_unit="mg/dL",
            multiply=Decimal("0"),
            precision=2,
            tolerance=Decimal("0.5"),
            canonical_tolerance=Decimal("0.01"),
            version="t1",
        )


def test_a_code_unit_map_entry_must_name_an_accepted_unit():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(code_unit_map={"http://loinc.org|9999-9": "furlong"})


def test_a_code_unit_map_key_must_be_system_pipe_code():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(code_unit_map={"4548-4": "%"})


def test_required_context_must_name_known_fields():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(required_context=["mood"])


def test_required_method_must_name_known_fields():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_entry(required_method=["reagent_lot"])


def test_a_delta_policy_must_not_name_unknown_context_fields():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        DeltaPolicy(max_abs_change=Decimal("1"), within_hours=1, compare_context=["mood"])


def test_registry_keys_must_match_their_entries():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        ObservableRegistry(entries={"wrong_key": make_entry(observable="test_obs")})


def test_registry_lookup_raises_unknown_observable_for_a_missing_id():
    # Arrange
    registry = ObservableRegistry(entries={"test_obs": make_entry()})

    # Act / Assert
    with pytest.raises(UnknownObservableError):
        registry.entry("tsh")
```

`tests/catalogue/test_registry_loader.py`:
```python
"""Content loads through a schema-only YAML loader (SSOT §7.5)."""

import pytest

from noor.catalogue.registry_loader import load_registry
from tests.conftest import REGISTRY_PATH


def test_the_real_registry_loads_and_declares_the_starter_observables():
    # Arrange / Act
    registry = load_registry(REGISTRY_PATH)

    # Assert
    assert set(registry.entries) == {
        "hba1c_ngsp",
        "hba1c_ifcc",
        "glucose",
        "systolic_bp",
        "diastolic_bp",
        "pulse",
        "body_temperature",
        "weight",
        "egfr",
        "creatinine",
    }
    for observable, entry in registry.entries.items():
        assert entry.owner, f"{observable} must name an owner (§6.6)"


def test_ngsp_and_ifcc_hba1c_are_distinct_observables():
    # Arrange / Act
    registry = load_registry(REGISTRY_PATH)

    # Assert — §5: never two units of one observable
    assert registry.entry("hba1c_ngsp").canonical_ucum == "%"
    assert registry.entry("hba1c_ifcc").canonical_ucum == "mmol/mol"


def test_an_object_constructing_yaml_tag_is_a_build_failure(tmp_path):
    # Arrange — §7.5: never a warning, a refusal
    hostile = tmp_path / "registry.yaml"
    hostile.write_text(
        'observables: !!python/object/apply:os.system ["echo owned"]\n',
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(Exception) as excinfo:
        load_registry(hostile)
    assert excinfo.type.__module__ == "yaml.constructor" or isinstance(excinfo.value, ValueError)


def test_a_registry_without_an_observables_list_is_refused(tmp_path):
    # Arrange
    bad = tmp_path / "registry.yaml"
    bad.write_text("not_observables: []\n", encoding="utf-8")

    # Act / Assert
    with pytest.raises(ValueError):
        load_registry(bad)


def test_duplicate_observable_ids_are_refused(tmp_path):
    # Arrange
    bad = tmp_path / "registry.yaml"
    bad.write_text(
        "observables:\n"
        "  - {observable: glucose, owner: a}\n"
        "  - {observable: glucose, owner: b}\n",
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(ValueError, match="duplicate"):
        load_registry(bad)
```

conftest additions — merge these imports into the existing import block at the top of `tests/conftest.py` (ruff enforces import order), then append the fixture and factory at the end of the file:
```python
from decimal import Decimal

from noor.canon.registry import (
    DeltaPolicy,
    Envelope,
    ObservableEntry,
    ObservableRegistry,
)
from noor.catalogue.registry_loader import load_registry

REGISTRY_PATH = REPO_ROOT / "content" / "observables" / "registry.yaml"


@pytest.fixture
def registry() -> ObservableRegistry:
    """The real content/observables/registry.yaml, loaded and validated."""
    return load_registry(REGISTRY_PATH)


def make_entry(**overrides: Any) -> ObservableEntry:
    """A synthetic registry entry with tight envelopes for boundary tests.

    Physiologic [2, 10], operational [4, 8], both in canonical mmol/L.
    """
    fields: dict[str, Any] = {
        "observable": "test_obs",
        "owner": "test-owner",
        "canonical_ucum": "mmol/L",
        "accepted_units": ["mmol/L"],
        "physiologic": Envelope(low=Decimal("2"), high=Decimal("10"), version="t1"),
        "operational": Envelope(low=Decimal("4"), high=Decimal("8"), version="t1"),
        "delta_policy": DeltaPolicy(max_abs_change=Decimal("3"), within_hours=24),
        "repeat_tolerance": Decimal("0.5"),
    }
    fields.update(overrides)
    return ObservableEntry(**fields)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/canon/test_registry.py tests/catalogue/test_registry_loader.py -v`
Expected: FAIL — collection error, `noor.canon.registry` does not exist.

- [ ] **Step 3: Write `src/noor/canon/registry.py`**

```python
"""The observable registry: per-observable data-validity declarations (SSOT §6.6).

The registry declares — never assumes — canonical units, accepted units and
their conversions, the two validity envelopes (§6.4), delta policy, required
context/method fields, and a named owner per observable.
"""

from decimal import Decimal
from typing import Literal, Self

from pydantic import Field, model_validator

from noor.canon.models import NoorModel


class UnknownObservableError(KeyError):
    """A capture named an observable the registry does not govern."""


class Envelope(NoorModel):
    """Inclusive bounds in the canonical unit, versioned independently (§6.4)."""

    low: Decimal
    high: Decimal
    version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if not self.low < self.high:
            raise ValueError("an envelope's low must be below its high")
        return self


class Conversion(NoorModel):
    """canonical = (value + add) * multiply, quantised to `precision` (§6.3).

    `tolerance` is the round-trip bound in the SOURCE unit and
    `canonical_tolerance` the bound in the CANONICAL unit: §6.3 requires
    reversibility "in both directions", and a single bound can only express one of
    them (§12.6 claim 41).

    `version` is this conversion's own content version. Every canonical value it
    produces carries it (`ConversionApplied`), so a stored value can always be
    traced to the factor that produced it and a later correction to a factor can
    identify the values it affected. Bump it in the same PR that changes any of
    `add`, `multiply`, `precision`, or `rounding`.
    """

    from_unit: str = Field(min_length=1)
    add: Decimal = Decimal("0")
    multiply: Decimal = Decimal("1")
    precision: int = Field(ge=0)
    rounding: Literal["ROUND_HALF_UP", "ROUND_HALF_EVEN"] = "ROUND_HALF_UP"
    tolerance: Decimal = Field(gt=0)
    canonical_tolerance: Decimal = Field(gt=0)
    version: str = Field(min_length=1)

    @model_validator(mode="after")
    def _positive_multiplier(self) -> Self:
        if self.multiply <= 0:
            raise ValueError("a conversion multiplier must be positive")
        return self


CONTEXT_FIELDS = frozenset(
    {"setting", "posture", "arm", "cuff_size", "rest_duration_seconds", "reading_ordinal", "is_average"}
)
METHOD_FIELDS = frozenset({"device_class", "specimen", "assay"})


class DeltaPolicy(NoorModel):
    """Like-with-like comparison rules (§6.1 layer 3)."""

    max_abs_change: Decimal = Field(gt=0)
    within_hours: int = Field(gt=0)
    compare_context: list[str] = []
    compare_device_class: bool = True

    @model_validator(mode="after")
    def _known_context_fields(self) -> Self:
        unknown = set(self.compare_context) - CONTEXT_FIELDS
        if unknown:
            raise ValueError(f"delta policy names unknown context fields: {sorted(unknown)}")
        return self


class ObservableEntry(NoorModel):
    """One observable's data-validity declaration (SSOT §6.6).

    Quantity observables only (assumption 13): §6.6's Curated Clinical Signal Set
    has no canonical unit and no envelopes, and is not modelled here. Nothing in
    this schema is a treatment threshold — §6.4's three boundary types are
    separate, and there is deliberately nowhere here to put a clinical decision
    boundary.
    """

    observable: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    owner: str = Field(min_length=1)
    canonical_ucum: str = Field(min_length=1)
    accepted_units: list[str] = Field(min_length=1)
    conversions: list[Conversion] = []
    code_unit_map: dict[str, str] = {}
    physiologic: Envelope
    operational: Envelope
    delta_policy: DeltaPolicy
    repeat_tolerance: Decimal = Field(gt=0)
    required_context: list[str] = []
    required_method: list[str] = []

    @model_validator(mode="after")
    def _internally_consistent(self) -> Self:
        if self.canonical_ucum not in self.accepted_units:
            raise ValueError("the canonical unit must be an accepted unit")
        for conversion in self.conversions:
            if conversion.from_unit == self.canonical_ucum:
                raise ValueError("a conversion from the canonical unit is identity; omit it")
            if conversion.from_unit not in self.accepted_units:
                raise ValueError(f"conversion from unaccepted unit {conversion.from_unit!r}")
        for key, unit in self.code_unit_map.items():
            if "|" not in key:
                raise ValueError("code_unit_map keys are 'system|code'")
            if unit not in self.accepted_units:
                raise ValueError(f"code_unit_map names unaccepted unit {unit!r}")
        if not (
            self.physiologic.low <= self.operational.low
            and self.operational.high <= self.physiologic.high
        ):
            raise ValueError("the operational envelope must sit inside the physiologic one")
        unknown = (set(self.required_context) - CONTEXT_FIELDS) | (
            set(self.required_method) - METHOD_FIELDS
        )
        if unknown:
            raise ValueError(f"required fields that do not exist: {sorted(unknown)}")
        return self


class ObservableRegistry(NoorModel):
    entries: dict[str, ObservableEntry]

    @model_validator(mode="after")
    def _keys_match_entries(self) -> Self:
        for key, entry in self.entries.items():
            if key != entry.observable:
                raise ValueError(f"registry key {key!r} does not match entry {entry.observable!r}")
        return self

    def entry(self, observable: str) -> ObservableEntry:
        try:
            return self.entries[observable]
        except KeyError:
            raise UnknownObservableError(observable) from None
```

`src/noor/catalogue/registry_loader.py`:
```python
"""Loads registry content into validated models (SSOT §7.4).

Schema-only YAML (§7.5): anything `yaml.safe_load` refuses is a build failure.
Decimal scalars in content files are quoted strings, so they load exactly —
a YAML float would carry binary error into clinical bounds.
"""

from pathlib import Path

import yaml

from noor.canon.registry import ObservableRegistry


def load_registry(path: Path) -> ObservableRegistry:
    """Load and validate an observable registry file (content/observables/registry.yaml)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("observables"), list):
        raise ValueError(f"{path}: expected a top-level 'observables' list")
    entries: dict[str, dict] = {}
    for item in data["observables"]:
        name = item["observable"]
        if name in entries:
            raise ValueError(f"{path}: duplicate observable id {name!r}")
        entries[name] = item
    return ObservableRegistry.model_validate({"entries": entries})
```

`content/observables/registry.yaml`:
```yaml
# The observable registry (SSOT §6.6). One entry per observable Noor can reason
# about. Envelopes are DATA-VALIDITY bounds (§6.4) — "could this value be real",
# never "is this value controlled". Treatment thresholds live separately in
# content/thresholds/ and are never read here (§6.4).
#
# Values are owned by the named owner and change only via pull request (§7.5).
# Envelope, delta, and tolerance figures are conservative plausibility-grade
# starting points pending clinical-owner review. Decimal scalars are quoted so
# they load as exact strings, not binary floats.
#
# Every conversion carries its own `version`, copied onto each value it produces
# (§6.3 provenance). Changing add/multiply/precision/rounding without bumping
# `version` in the same PR breaks the trail from a stored value back to the factor
# that produced it. `tolerance` bounds the round trip in the source unit,
# `canonical_tolerance` in the canonical unit — §6.3 requires both directions.
#
# Quantity observables only. §6.6's Curated Clinical Signal Set (coded symptoms,
# signs, exam findings) has no canonical unit and no envelopes; it needs a schema
# discriminator that does not exist yet (see the plan's assumption 13).
observables:
  - observable: hba1c_ngsp
    owner: Youssef Sabry
    canonical_ucum: "%"
    accepted_units: ["%"]
    conversions: []
    code_unit_map:
      "http://loinc.org|4548-4": "%"
    physiologic: {low: "1.0", high: "30.0", version: "2026-08-18"}
    operational: {low: "3.0", high: "20.0", version: "2026-08-18"}
    delta_policy: {max_abs_change: "2.0", within_hours: 2160, compare_context: [], compare_device_class: false}
    repeat_tolerance: "0.3"
    required_context: []
    required_method: []

  - observable: hba1c_ifcc
    owner: Youssef Sabry
    canonical_ucum: "mmol/mol"
    accepted_units: ["mmol/mol"]
    conversions: []
    code_unit_map:
      "http://loinc.org|59261-8": "mmol/mol"
    physiologic: {low: "1", high: "305", version: "2026-08-18"}
    operational: {low: "20", high: "195", version: "2026-08-18"}
    delta_policy: {max_abs_change: "20", within_hours: 2160, compare_context: [], compare_device_class: false}
    repeat_tolerance: "3"
    required_context: []
    required_method: []

  - observable: glucose
    owner: Youssef Sabry
    canonical_ucum: "mmol/L"
    accepted_units: ["mmol/L", "mg/dL"]
    conversions:
      - {from_unit: "mg/dL", add: "0", multiply: "0.055507", precision: 2, rounding: "ROUND_HALF_UP", tolerance: "0.5", canonical_tolerance: "0.01", version: "2026-08-18"}
    code_unit_map: {}
    physiologic: {low: "0.3", high: "70.0", version: "2026-08-18"}
    operational: {low: "1.5", high: "35.0", version: "2026-08-18"}
    delta_policy: {max_abs_change: "8.0", within_hours: 4, compare_context: [], compare_device_class: true}
    repeat_tolerance: "0.6"
    required_context: []
    required_method: []

  - observable: systolic_bp
    owner: Youssef Sabry
    canonical_ucum: "mm[Hg]"
    accepted_units: ["mm[Hg]"]
    conversions: []
    code_unit_map: {}
    physiologic: {low: "40", high: "320", version: "2026-08-18"}
    operational: {low: "70", high: "260", version: "2026-08-18"}
    delta_policy:
      max_abs_change: "40"
      within_hours: 168
      compare_context: ["setting", "posture", "arm", "cuff_size"]
      compare_device_class: true
    repeat_tolerance: "10"
    required_context: ["setting", "posture", "arm", "cuff_size", "rest_duration_seconds", "reading_ordinal", "is_average"]
    required_method: ["device_class"]

  - observable: diastolic_bp
    owner: Youssef Sabry
    canonical_ucum: "mm[Hg]"
    accepted_units: ["mm[Hg]"]
    conversions: []
    code_unit_map: {}
    physiologic: {low: "20", high: "220", version: "2026-08-18"}
    operational: {low: "40", high: "160", version: "2026-08-18"}
    delta_policy:
      max_abs_change: "30"
      within_hours: 168
      compare_context: ["setting", "posture", "arm", "cuff_size"]
      compare_device_class: true
    repeat_tolerance: "8"
    required_context: ["setting", "posture", "arm", "cuff_size", "rest_duration_seconds", "reading_ordinal", "is_average"]
    required_method: ["device_class"]

  - observable: pulse
    owner: Youssef Sabry
    canonical_ucum: "/min"
    accepted_units: ["/min"]
    conversions: []
    code_unit_map: {}
    physiologic: {low: "15", high: "260", version: "2026-08-18"}
    operational: {low: "35", high: "200", version: "2026-08-18"}
    delta_policy: {max_abs_change: "50", within_hours: 2, compare_context: [], compare_device_class: true}
    repeat_tolerance: "8"
    required_context: []
    required_method: []

  - observable: body_temperature
    owner: Youssef Sabry
    canonical_ucum: "Cel"
    accepted_units: ["Cel", "[degF]"]
    conversions:
      - {from_unit: "[degF]", add: "-32", multiply: "0.5555556", precision: 1, rounding: "ROUND_HALF_UP", tolerance: "0.4", canonical_tolerance: "0.1", version: "2026-08-18"}
    code_unit_map: {}
    physiologic: {low: "22.0", high: "46.0", version: "2026-08-18"}
    operational: {low: "33.0", high: "42.5", version: "2026-08-18"}
    delta_policy: {max_abs_change: "1.5", within_hours: 24, compare_context: [], compare_device_class: true}
    repeat_tolerance: "0.3"
    required_context: []
    required_method: []

  - observable: weight
    owner: Youssef Sabry
    canonical_ucum: "kg"
    accepted_units: ["kg"]
    conversions: []
    code_unit_map: {}
    physiologic: {low: "1.0", high: "400.0", version: "2026-08-18"}
    operational: {low: "20.0", high: "300.0", version: "2026-08-18"}
    delta_policy: {max_abs_change: "5.0", within_hours: 720, compare_context: [], compare_device_class: true}
    repeat_tolerance: "0.5"
    required_context: []
    required_method: []

  - observable: egfr
    owner: Youssef Sabry
    # The braces are load-bearing. UCUM reads "." as multiplication, not a decimal
    # point, so the tempting "mL/min/1.73m2" resolves to per-73 m2 — off by a factor
    # of 42. "{...}" is a UCUM annotation with no arithmetic meaning; this is the
    # form LOINC and FHIR use for eGFR. Do not "simplify" it.
    canonical_ucum: "mL/min/{1.73_m2}"
    accepted_units: ["mL/min/{1.73_m2}"]
    conversions: []
    code_unit_map: {}
    physiologic: {low: "1", high: "200", version: "2026-08-18"}
    operational: {low: "5", high: "150", version: "2026-08-18"}
    delta_policy: {max_abs_change: "20", within_hours: 2160, compare_context: [], compare_device_class: false}
    repeat_tolerance: "3"
    required_context: []
    required_method: []

  - observable: creatinine
    owner: Youssef Sabry
    canonical_ucum: "umol/L"
    accepted_units: ["umol/L", "mg/dL"]
    conversions:
      - {from_unit: "mg/dL", add: "0", multiply: "88.4", precision: 1, rounding: "ROUND_HALF_UP", tolerance: "0.02", canonical_tolerance: "0.1", version: "2026-08-18"}
    code_unit_map: {}
    physiologic: {low: "5", high: "2000", version: "2026-08-18"}
    operational: {low: "20", high: "1200", version: "2026-08-18"}
    delta_policy: {max_abs_change: "60", within_hours: 2160, compare_context: [], compare_device_class: false}
    repeat_tolerance: "15"
    required_context: []
    required_method: []
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/canon/test_registry.py tests/catalogue/test_registry_loader.py -v`
Expected: PASS — 20 tests.

Run: `uv run mypy src/noor/canon src/noor/catalogue`
Expected: `Success: no issues found`.

- [ ] **Step 5: Commit**

```powershell
git add src/noor/canon/registry.py src/noor/catalogue/registry_loader.py content tests
git commit -m "feat(canon): observable registry schema, starter registry, safe YAML loader (SSOT §6.6, §7.5)"
```

---

### Task 5: Unit resolution

SSOT §6.3: `explicit | inferred_from_code | ambiguous`; ambiguous is a hard failure. The HbA1c rule: never infer percent versus mmol/mol from the value alone — resolution must be blind to the value.

**Files:**
- Create: `src/noor/canon/units.py`
- Create: `tests/canon/test_units.py`

**Interfaces:**
- Consumes: `UnitResolution`, `SourceCode` (Task 3); `ObservableEntry` (Task 4).
- Produces:
  - `UnknownUnitError(ValueError)`.
  - `resolve_unit(reported_unit: str | None, source_code: SourceCode | None, entry: ObservableEntry) -> tuple[UnitResolution, str | None]`.
  - `to_canonical(value: Decimal, unit: str, entry: ObservableEntry) -> CanonicalQuantity` (raises `UnknownUnitError`; quantises through conversions only).
  - `from_canonical(quantity: CanonicalQuantity, unit: str, entry: ObservableEntry) -> Decimal` (inverse; exists for the round-trip property).

- [ ] **Step 1: Write the failing tests**

`tests/canon/test_units.py`:
```python"""Unit resolution is a hard safety control (SSOT §6.3)."""

from decimal import Decimal

import pytest

from noor.canon.models import SourceCode, UnitResolution
from noor.canon.registry import Conversion
from noor.canon.units import UnknownUnitError, resolve_unit, to_canonical
from tests.conftest import make_entry


LOINC_HBA1C = SourceCode(system="http://loinc.org", code="4548-4")


def test_a_reported_accepted_unit_resolves_explicitly():
    # Arrange
    entry = make_entry(accepted_units=["mmol/L", "mg/dL"])

    # Act
    resolution, unit = resolve_unit("mg/dL", None, entry)

    # Assert
    assert resolution is UnitResolution.explicit
    assert unit == "mg/dL"


def test_an_unrecognised_unit_is_ambiguous():
    # Arrange — "mg%" is a real-world spelling drift; never guessed (§6.3)
    entry = make_entry(accepted_units=["mmol/L", "mg/dL"])

    # Act
    resolution, unit = resolve_unit("mg%", None, entry)

    # Assert
    assert resolution is UnitResolution.ambiguous
    assert unit is None


def test_a_reported_unit_conflicting_with_the_code_implied_unit_is_ambiguous():
    # Arrange — the source says %, the code says mmol/mol: somebody is wrong
    entry = make_entry(
        accepted_units=["%", "mmol/mol"],
        code_unit_map={"http://loinc.org|59261-8": "mmol/mol"},
    )
    ifcc_code = SourceCode(system="http://loinc.org", code="59261-8")

    # Act
    resolution, unit = resolve_unit("%", ifcc_code, entry)

    # Assert
    assert resolution is UnitResolution.ambiguous
    assert unit is None


def test_an_absent_unit_is_inferred_from_the_source_code():
    # Arrange
    entry = make_entry(
        accepted_units=["%"],
        canonical_ucum="%",
        code_unit_map={"http://loinc.org|4548-4": "%"},
    )

    # Act
    resolution, unit = resolve_unit(None, LOINC_HBA1C, entry)

    # Assert
    assert resolution is UnitResolution.inferred_from_code
    assert unit == "%"


def test_an_absent_unit_and_an_unknown_code_is_ambiguous():
    # Arrange
    entry = make_entry(code_unit_map={})
    unknown = SourceCode(system="http://loinc.org", code="0000-0")

    # Act
    resolution, unit = resolve_unit(None, unknown, entry)

    # Assert
    assert resolution is UnitResolution.ambiguous


def test_an_absent_unit_and_no_code_is_ambiguous():
    # Arrange / Act
    resolution, unit = resolve_unit(None, None, make_entry())

    # Assert
    assert resolution is UnitResolution.ambiguous


def test_resolution_never_looks_at_the_value():
    # Arrange — 42 "looks like" mmol/mol and 7.4 "looks like" %; §6.3 forbids
    # inferring either. Both hba1c observables carry exactly one accepted unit,
    # so a missing unit with no code is ambiguous even so.
    ngsp = make_entry(observable="hba1c_ngsp", canonical_ucum="%", accepted_units=["%"])
    ifcc = make_entry(
        observable="hba1c_ifcc", canonical_ucum="mmol/mol", accepted_units=["mmol/mol"]
    )

    # Act / Assert
    assert resolve_unit(None, None, ngsp)[0] is UnitResolution.ambiguous
    assert resolve_unit(None, None, ifcc)[0] is UnitResolution.ambiguous


def test_identity_conversion_preserves_the_value_exactly():
    # Arrange
    entry = make_entry()

    # Act
    quantity = to_canonical(Decimal("7.40"), "mmol/L", entry)

    # Assert — identity is not quantised; the as-reported precision survives
    assert quantity.value == Decimal("7.40")
    assert quantity.ucum == "mmol/L"
    assert quantity.conversion_applied is None  # no conversion, no work to show


def test_a_declared_conversion_records_the_provenance_of_its_result():
    # Arrange — §6.3: every conversion carries its own provenance, so a stored
    # canonical value can be traced to the exact factor that produced it
    entry = make_entry(
        accepted_units=["mmol/L", "mg/dL"],
        conversions=[
            Conversion(
                from_unit="mg/dL",
                multiply=Decimal("0.055507"),
                precision=2,
                tolerance=Decimal("0.5"),
                canonical_tolerance=Decimal("0.01"),
                version="glucose-mgdl-v1",
            )
        ],
    )

    # Act
    quantity = to_canonical(Decimal("90"), "mg/dL", entry)

    # Assert
    assert quantity.value == Decimal("5.00")
    applied = quantity.conversion_applied
    assert applied is not None
    assert applied.from_unit == "mg/dL"
    assert applied.add == Decimal("0")
    assert applied.multiply == Decimal("0.055507")
    assert applied.precision == 2
    assert applied.rounding == "ROUND_HALF_UP"
    assert applied.version == "glucose-mgdl-v1"


def test_an_unconvertible_unit_raises():
    # Arrange / Act / Assert
    with pytest.raises(UnknownUnitError):
        to_canonical(Decimal("100"), "mg/dL", make_entry())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/canon/test_units.py -v`
Expected: FAIL — collection error, `noor.canon.units` does not exist.

- [ ] **Step 3: Write `src/noor/canon/units.py`**

```python
"""Unit resolution and registry-declared conversion (SSOT §6.3).

Resolution is blind to the value: NGSP % and IFCC mmol/mol are distinct
observables (§5), and no magnitude ever hints at a unit.
"""

from decimal import Decimal

from noor.canon.models import CanonicalQuantity, ConversionApplied, SourceCode, UnitResolution
from noor.canon.registry import ObservableEntry


class UnknownUnitError(ValueError):
    """A unit survived to conversion without a registry declaration — a defect,
    not data. resolve_unit runs first; this should be unreachable."""


def resolve_unit(
    reported_unit: str | None,
    source_code: SourceCode | None,
    entry: ObservableEntry,
) -> tuple[UnitResolution, str | None]:
    """Resolve the unit a value arrived in (§6.3).

    explicit: the source stated a unit the registry accepts, consistent with any
    code-implied unit. inferred_from_code: no stated unit, and the source code
    maps to exactly one. ambiguous: everything else — a hard failure.
    """
    code_unit: str | None = None
    if source_code is not None:
        code_unit = entry.code_unit_map.get(f"{source_code.system}|{source_code.code}")

    if reported_unit is not None:
        if reported_unit in entry.accepted_units and (code_unit is None or code_unit == reported_unit):
            return UnitResolution.explicit, reported_unit
        return UnitResolution.ambiguous, None
    if code_unit is not None:
        return UnitResolution.inferred_from_code, code_unit
    return UnitResolution.ambiguous, None


def to_canonical(value: Decimal, unit: str, entry: ObservableEntry) -> CanonicalQuantity:
    """Convert a resolved unit to the canonical UCUM unit (§6.6).

    A converted value carries the conversion that produced it: §6.3 requires that
    every conversion carry its own provenance, so `5.00 mmol/L` can always be
    traced back to the declared factor and version that made it. An identity
    conversion carries none — there is no work to show.
    """
    if unit == entry.canonical_ucum:
        return CanonicalQuantity(value=value, ucum=entry.canonical_ucum)
    for conversion in entry.conversions:
        if conversion.from_unit == unit:
            scaled = (value + conversion.add) * conversion.multiply
            quantum = Decimal(1).scaleb(-conversion.precision)
            return CanonicalQuantity(
                value=scaled.quantize(quantum, rounding=conversion.rounding),
                ucum=entry.canonical_ucum,
                conversion_applied=ConversionApplied(
                    from_unit=conversion.from_unit,
                    add=conversion.add,
                    multiply=conversion.multiply,
                    precision=conversion.precision,
                    rounding=conversion.rounding,
                    version=conversion.version,
                ),
            )
    raise UnknownUnitError(f"{entry.observable}: no conversion declared from {unit!r}")


def from_canonical(quantity: CanonicalQuantity, unit: str, entry: ObservableEntry) -> Decimal:
    """The exact inverse of `to_canonical`, before quantisation.

    Exists for the round-trip property test (§12.6 claim 41) and for displayed
    conversions (§6.3: convert only with displayed conversion and provenance).
    """
    if unit == quantity.ucum:
        return quantity.value
    for conversion in entry.conversions:
        if conversion.from_unit == unit:
            return (quantity.value / conversion.multiply) - conversion.add
    raise UnknownUnitError(f"{entry.observable}: no conversion declared back to {unit!r}")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/canon/test_units.py -v`
Expected: PASS — 10 tests.

Run: `uv run mypy src/noor/canon`
Expected: `Success: no issues found`.

- [ ] **Step 5: Commit**

```powershell
git add src/noor/canon/units.py tests/canon/test_units.py
git commit -m "feat(canon): unit resolution and declared conversions (SSOT §6.3)"
```

---

### Task 6: The conversion round-trip property

SSOT §12.6 claim 41: "For every registry conversion, convert a value out and back → the original is recovered within the declared precision." §6.3 requires that reversibility "in both directions", so the property is stated twice — once starting from the source unit (bounded by `tolerance`) and once from the canonical unit (bounded by `canonical_tolerance`). Both are property tests over the **real** registry, so a conversion added later is tested automatically. The §R-11 failure this exists to catch is the Fahrenheit-for-Celsius class of error.

**Files:**
- Create: `tests/canon/test_conversion_roundtrip.py`

**Interfaces:**
- Consumes: `to_canonical`, `from_canonical` (Task 5); `load_registry` (Task 4); `CanonicalQuantity` (Task 3).
- Produces: the standing claim-41 proof for every registry conversion, in both directions, now and as the registry grows.

- [ ] **Step 1: Write the failing test (it fails only if the registry or conversions are wrong)**

`tests/canon/test_conversion_roundtrip.py`:
```python
"""Every registry conversion is reversible within its declared precision
(SSOT §12.6 claim 41, §6.3). Parametrised over the REAL registry: a conversion
added to content/observables/registry.yaml is tested here automatically.
§6.3 requires reversibility in BOTH directions, so there are two properties: one
bounded by `tolerance` in the source unit, one by `canonical_tolerance`."""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from noor.canon.models import CanonicalQuantity
from noor.canon.units import UnknownUnitError, from_canonical, to_canonical
from tests.conftest import REGISTRY_PATH
from noor.catalogue.registry_loader import load_registry

REGISTRY = load_registry(REGISTRY_PATH)
CONVERSIONS = [
    (observable, conversion)
    for observable, entry in REGISTRY.entries.items()
    for conversion in entry.conversions
]


def test_the_registry_declares_conversions_to_test():
    # Arrange / Act / Assert — a registry with zero conversions makes this file
    # vacuous; fail loudly instead of passing vacuously
    assert CONVERSIONS, "no registry conversions declared — claim 41 has no object"


def test_glucose_mg_dl_converts_to_mmol_l_as_declared():
    # Arrange
    entry = REGISTRY.entry("glucose")

    # Act
    quantity = to_canonical(Decimal("90"), "mg/dL", entry)

    # Assert — 90 mg/dL × 0.055507 = 4.99563, quantised to 2dp
    assert quantity.value == Decimal("5.00")
    assert quantity.ucum == "mmol/L"


def test_creatinine_mg_dl_converts_to_umol_l_as_declared():
    # Arrange
    entry = REGISTRY.entry("creatinine")

    # Act
    quantity = to_canonical(Decimal("1.0"), "mg/dL", entry)

    # Assert
    assert quantity.value == Decimal("88.4")
    assert quantity.ucum == "umol/L"


def test_fahrenheit_converts_to_celsius_as_declared():
    # Arrange — the §R-11 incident class: °F mistaken for °C
    entry = REGISTRY.entry("body_temperature")

    # Act
    quantity = to_canonical(Decimal("98.6"), "[degF]", entry)

    # Assert
    assert quantity.value == Decimal("37.0")
    assert quantity.ucum == "Cel"


def test_from_canonical_in_a_canonical_unit_returns_the_value():
    # Arrange
    entry = REGISTRY.entry("glucose")
    quantity = to_canonical(Decimal("5.5"), "mmol/L", entry)

    # Act / Assert
    assert from_canonical(quantity, "mmol/L", entry) == Decimal("5.5")


def test_from_canonical_to_an_undeclared_unit_raises():
    # Arrange
    entry = REGISTRY.entry("glucose")
    quantity = to_canonical(Decimal("5.5"), "mmol/L", entry)

    # Act / Assert
    with pytest.raises(UnknownUnitError):
        from_canonical(quantity, "mg%", entry)


@pytest.mark.parametrize(
    "observable,conversion",
    CONVERSIONS,
    ids=[f"{observable}:{conversion.from_unit}" for observable, conversion in CONVERSIONS],
)
@given(
    value=st.decimals(
        min_value=Decimal("0.1"),
        max_value=Decimal("2000"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    )
)
def test_every_registry_conversion_round_trips_within_declared_precision(
    observable, conversion, value
):
    # Arrange
    entry = REGISTRY.entry(observable)

    # Act
    canonical = to_canonical(value, conversion.from_unit, entry)
    recovered = from_canonical(canonical, conversion.from_unit, entry)

    # Assert — the declared precision is the whole contract (§12.6 claim 41)
    assert canonical.ucum == entry.canonical_ucum
    assert abs(recovered - value) <= conversion.tolerance
    # …and the result says which conversion produced it (§6.3 provenance)
    assert canonical.conversion_applied is not None
    assert canonical.conversion_applied.version == conversion.version


@pytest.mark.parametrize(
    "observable,conversion",
    CONVERSIONS,
    ids=[f"{observable}:{conversion.from_unit}" for observable, conversion in CONVERSIONS],
)
@given(
    value=st.decimals(
        min_value=Decimal("0.1"),
        max_value=Decimal("2000"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    )
)
def test_every_registry_conversion_round_trips_from_the_canonical_side(
    observable, conversion, value
):
    # Arrange — the other direction. §6.3 says reversible "in both directions",
    # and the source-unit tolerance cannot express the canonical-side bound. The
    # starting value is quantised to the conversion's own precision because that
    # is the only shape a stored canonical value ever has.
    entry = REGISTRY.entry(observable)
    canonical_value = value.quantize(Decimal(1).scaleb(-conversion.precision))
    canonical = CanonicalQuantity(value=canonical_value, ucum=entry.canonical_ucum)

    # Act
    out = from_canonical(canonical, conversion.from_unit, entry)
    back = to_canonical(out, conversion.from_unit, entry)

    # Assert
    assert back.ucum == entry.canonical_ucum
    assert abs(back.value - canonical_value) <= conversion.canonical_tolerance
```

- [ ] **Step 2: Run the test**

Run: `uv run pytest tests/canon/test_conversion_roundtrip.py -v`
Expected: PASS. This test has no failing-before phase in the TDD sense — the units it exercises were built in Task 5; its job is to stand guard over the registry. If it fails, the registry or the conversion code is wrong: debug which, and fix that one.

- [ ] **Step 3: Commit**

```powershell
git add tests/canon/test_conversion_roundtrip.py
git commit -m "test(canon): registry conversion round-trip property (SSOT §12.6 claim 41)"
```

---

### Task 7: Value parsing and the decimal/transposition pattern

SSOT §6.1 layer 1: invalid characters, impossible unit/value combinations, decimal and transposition patterns. (Impossible unit/value combinations are caught by unit resolution plus the envelopes — Tasks 5 and 8; this task is the lexical layer.)

**Files:**
- Create: `src/noor/canon/parse.py`
- Create: `tests/canon/test_parse.py`

**Interfaces:**
- Consumes: `ObservableEntry` (Task 4).
- Produces:
  - `parse_value(raw: str) -> Decimal | None` — strict plain-decimal notation; `None` when unparseable. Leading/trailing whitespace is stripped.
  - `decimal_transposition_suspected(value: Decimal, entry: ObservableEntry) -> bool` — answers the pattern question only; the pipeline decides when to ask it (Task 10).

- [ ] **Step 1: Write the failing tests**

`tests/canon/test_parse.py`:
```python
"""Layer 1 of canon: parsing and decimal/transposition patterns (SSOT §6.1)."""

from decimal import Decimal

from noor.canon.parse import decimal_transposition_suspected, parse_value
from tests.conftest import make_entry


def test_a_plain_decimal_parses():
    # Arrange / Act / Assert
    assert parse_value("7.4") == Decimal("7.4")


def test_an_integer_parses():
    # Arrange / Act / Assert
    assert parse_value("140") == Decimal("140")


def test_a_negative_parses():
    # Arrange / Act / Assert — the parse layer does not judge plausibility
    assert parse_value("-2") == Decimal("-2")


def test_surrounding_whitespace_is_stripped():
    # Arrange / Act / Assert
    assert parse_value("  5.5\t") == Decimal("5.5")


def test_a_comma_decimal_separator_is_unparseable():
    # Arrange / Act / Assert — never silently read "7,4" as 7.4 or 74
    assert parse_value("7,4") is None


def test_a_double_decimal_point_is_unparseable():
    # Arrange / Act / Assert
    assert parse_value("7.4.2") is None


def test_letters_are_unparseable():
    # Arrange / Act / Assert
    assert parse_value("abc") is None


def test_scientific_notation_is_unparseable():
    # Arrange / Act / Assert — not a format a human enters for a vital
    assert parse_value("1e3") is None


def test_an_empty_string_is_unparseable():
    # Arrange / Act / Assert
    assert parse_value("") is None
    assert parse_value("   ") is None


def test_a_bare_sign_or_dot_is_unparseable():
    # Arrange / Act / Assert
    assert parse_value("-") is None
    assert parse_value(".") is None
    assert parse_value("+7") is None


def test_a_value_ten_times_too_large_matches_the_transposition_pattern():
    # Arrange — synthetic entry: operational [4, 8]
    entry = make_entry()

    # Act / Assert — 74 is outside; 7.4 is inside
    assert decimal_transposition_suspected(Decimal("74"), entry) is True


def test_a_value_ten_times_too_small_matches_the_transposition_pattern():
    # Arrange
    entry = make_entry()

    # Act / Assert — 0.5 is outside [4, 8]; 5.0 is inside
    assert decimal_transposition_suspected(Decimal("0.5"), entry) is True


def test_an_in_envelope_value_does_not_match_the_pattern():
    # Arrange
    entry = make_entry()

    # Act / Assert — neither 55 nor 0.55 lands in [4, 8]
    assert decimal_transposition_suspected(Decimal("5.5"), entry) is False


def test_an_extreme_value_with_no_plausible_shift_does_not_match_the_pattern():
    # Arrange
    entry = make_entry()

    # Act / Assert — 900 and 90 are both outside [4, 8]: extreme, not a slip
    assert decimal_transposition_suspected(Decimal("900"), entry) is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/canon/test_parse.py -v`
Expected: FAIL — collection error, `noor.canon.parse` does not exist.

- [ ] **Step 3: Write `src/noor/canon/parse.py`**

```python
"""Layer 1 of canon: parsing and decimal/transposition patterns (SSOT §6.1).

Strict plain-decimal notation only. A comma separator, a stray character, or
scientific notation is unparseable — never "probably meant 7.4".
"""

import re
from decimal import Decimal

from noor.canon.registry import ObservableEntry

_VALUE_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")


def parse_value(raw: str) -> Decimal | None:
    """Parse an as-reported value, or return None when it is unparseable.

    The pattern is total: anything it matches, Decimal accepts.
    """
    text = raw.strip()
    if not _VALUE_PATTERN.fullmatch(text):
        return None
    return Decimal(text)


def decimal_transposition_suspected(value: Decimal, entry: ObservableEntry) -> bool:
    """True when sliding the decimal point one place would move the value inside
    the operational envelope — the classic 7.4-recorded-as-74 mistype.

    Answers the pattern question only; the pipeline asks it only for values
    already outside the operational envelope.
    """
    operational = entry.operational
    return any(
        operational.low <= shifted <= operational.high
        for shifted in (value * 10, value / 10)
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/canon/test_parse.py -v`
Expected: PASS — 14 tests.

- [ ] **Step 5: Commit**

```powershell
git add src/noor/canon/parse.py tests/canon/test_parse.py
git commit -m "feat(canon): strict value parsing and decimal-transposition pattern (SSOT §6.1)"
```

---

### Task 8: Plausibility envelopes

SSOT §6.1 layer 2 and §6.4: a physiologic envelope ("could the instrument or person generate this?") and a narrower operational envelope, declared per observable in the canonical unit, inclusive bounds, and never a diagnosis.

**Files:**
- Create: `src/noor/canon/plausibility.py`
- Create: `tests/canon/test_plausibility.py`

**Interfaces:**
- Consumes: `ObservableEntry` (Task 4).
- Produces: `EnvelopePosition` (`within_operational | outside_operational | outside_physiologic`) and `locate(value: Decimal, entry: ObservableEntry) -> EnvelopePosition`.

- [ ] **Step 1: Write the failing tests**

`tests/canon/test_plausibility.py`:
```python"""The two envelopes (SSOT §6.1 layer 2, §6.4). Bounds are inclusive and
declared in the canonical unit. Synthetic entry: physiologic [2, 10],
operational [4, 8] — every boundary row is exercised (testing standards)."""

from decimal import Decimal

from noor.canon.plausibility import EnvelopePosition, locate
from tests.conftest import make_entry


def test_an_ordinary_value_is_within_operational():
    # Arrange / Act / Assert
    assert locate(Decimal("6"), make_entry()) is EnvelopePosition.within_operational


def test_the_operational_low_bound_is_inclusive():
    # Arrange / Act / Assert
    assert locate(Decimal("4"), make_entry()) is EnvelopePosition.within_operational


def test_the_operational_high_bound_is_inclusive():
    # Arrange / Act / Assert
    assert locate(Decimal("8"), make_entry()) is EnvelopePosition.within_operational


def test_just_below_the_operational_floor_is_outside_operational():
    # Arrange / Act / Assert
    assert locate(Decimal("3.9"), make_entry()) is EnvelopePosition.outside_operational


def test_just_above_the_operational_ceiling_is_outside_operational():
    # Arrange / Act / Assert
    assert locate(Decimal("8.1"), make_entry()) is EnvelopePosition.outside_operational


def test_the_physiologic_low_bound_is_inclusive():
    # Arrange / Act / Assert — at the physiologic bound but below operational
    assert locate(Decimal("2"), make_entry()) is EnvelopePosition.outside_operational


def test_the_physiologic_high_bound_is_inclusive():
    # Arrange / Act / Assert
    assert locate(Decimal("10"), make_entry()) is EnvelopePosition.outside_operational


def test_below_the_physiologic_floor_cannot_be_generated():
    # Arrange / Act / Assert
    assert locate(Decimal("1.9"), make_entry()) is EnvelopePosition.outside_physiologic


def test_above_the_physiologic_ceiling_cannot_be_generated():
    # Arrange / Act / Assert
    assert locate(Decimal("10.1"), make_entry()) is EnvelopePosition.outside_physiologic
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/canon/test_plausibility.py -v`
Expected: FAIL — collection error, `noor.canon.plausibility` does not exist.

- [ ] **Step 3: Write `src/noor/canon/plausibility.py`**

```python
"""Layer 2 of canon: the two envelopes (SSOT §6.1, §6.4).

The physiologic envelope asks "could the instrument or person generate this?"
The operational envelope asks "is this the sort of value we expect to act on?"
Neither produces a diagnosis.
"""

from decimal import Decimal
from enum import StrEnum

from noor.canon.registry import ObservableEntry


class EnvelopePosition(StrEnum):
    within_operational = "within_operational"
    outside_operational = "outside_operational"
    outside_physiologic = "outside_physiologic"


def locate(value: Decimal, entry: ObservableEntry) -> EnvelopePosition:
    """Position of a canonical value against the entry's inclusive envelopes."""
    if not (entry.physiologic.low <= value <= entry.physiologic.high):
        return EnvelopePosition.outside_physiologic
    if not (entry.operational.low <= value <= entry.operational.high):
        return EnvelopePosition.outside_operational
    return EnvelopePosition.within_operational
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/canon/test_plausibility.py -v`
Expected: PASS — 9 tests.

- [ ] **Step 5: Commit**

```powershell
git add src/noor/canon/plausibility.py tests/canon/test_plausibility.py
git commit -m "feat(canon): physiologic and operational envelopes (SSOT §6.1, §6.4)"
```

---

### Task 9: Delta review

SSOT §14 step 3: "like-with-like comparison only; a suspicious delta produces `needs_repeat_or_verification` and never mutates a value." Like-with-like means: same observable, same canonical unit (guaranteed — one canonical unit per observable), the registry's named context fields equal, device class equal, and the prior inside the policy's time window. Only accepted-quality priors are baselines — a flagged or rejected value proves nothing about the next one.

Two things this task makes true that the shape of `DeltaVerdict` alone does not:

- **`source_version` is read, not just stored.** §5 versions a source record so a correction supersedes what it corrects. A superseded v1 is therefore *not* a baseline — comparing against a value the source has already replaced would flag a delta the source never reported. `current_versions` reduces the prior set to one row per `(source_system, source_identifier)`, keeping the highest `source_version`.
- **"Not compared" is recorded, never absent.** `review_delta` always returns a verdict; where it once returned `None` it now returns `comparable=False` with a `NotComparableReason`. §11.9's delta-check rate is the proportion of captures that *were* compared, which is only computable if the uncompared ones say so.

**Files:**
- Create: `src/noor/canon/delta.py`
- Create: `tests/canon/test_delta.py`
- Modify: `tests/conftest.py` (add `make_canonical`)

**Interfaces:**
- Consumes: `CanonicalObservation`, `ObservationCapture`, `DeltaVerdict`, `NotComparableReason`, `ACCEPTED_FAMILY` (Task 3); `ObservableEntry` (Task 4).
- Produces:
  - `current_versions(priors: Iterable[CanonicalObservation]) -> list[CanonicalObservation]` — one row per `(source_system, source_identifier)`, the highest `source_version` (§5). Used by Task 10 as well as here.
  - `is_comparable(prior: CanonicalObservation, capture: ObservationCapture, entry: ObservableEntry) -> bool`.
  - `review_delta(value: Decimal, capture: ObservationCapture, priors: Iterable[CanonicalObservation], entry: ObservableEntry) -> DeltaVerdict` — `value` is the capture's canonical value. Always returns a verdict; `comparable=False` with a reason when nothing was compared.
  - conftest: `make_canonical(*, state=..., rejection_reasons=..., **capture_overrides)`.

- [ ] **Step 1: Write the failing tests**

First, merge these imports into the existing import block at the top of `tests/conftest.py` (ruff enforces import order), then append `make_canonical` at the end of the file:
```python
from noor.canon.models import (
    AcceptedVia,
    CanonicalObservation,
    CanonicalQuantity,
    DeltaVerdict,
    QualityState,
    QualityVerdict,
    RejectionReason,
    SuspicionReason,
    UnitResolution,
)


def make_canonical(
    *,
    state: QualityState = QualityState.accepted,
    rejection_reasons: list[RejectionReason] | None = None,
    canonical_value: str | None = None,
    canonical_ucum: str | None = None,
    delta: DeltaVerdict | None = None,
    **capture_overrides: Any,
) -> CanonicalObservation:
    """A canonical observation as the pipeline would emit it; override anything.

    The quality verdict is built consistently with the state (§6.2). Canonical
    value defaults to the capture's as-reported value and unit — say what the
    test needs via canonical_value / canonical_ucum.
    """
    capture = make_capture(**capture_overrides)

    def quantity() -> CanonicalQuantity:
        return CanonicalQuantity(
            value=Decimal(canonical_value or capture.as_reported.value or "0"),
            ucum=canonical_ucum or capture.as_reported.unit or "mmol/L",
        )

    if state is QualityState.rejected:
        reasons = rejection_reasons or [RejectionReason.outside_physiologic_envelope]
        valueless = {
            RejectionReason.parse_failure,
            RejectionReason.unit_ambiguous,
            RejectionReason.mapping_unusable,
            RejectionReason.source_status_unusable,
        }
        canonical = None if valueless & set(reasons) else quantity()
        quality = QualityVerdict(
            state=state,
            unit_resolution=UnitResolution.explicit,
            rejection_reasons=reasons,
        )
    elif state is QualityState.needs_repeat_or_verification:
        canonical = quantity()
        quality = QualityVerdict(
            state=state,
            unit_resolution=UnitResolution.explicit,
            suspicions=[SuspicionReason.delta_exceeded],
            delta=delta,
        )
    else:
        canonical = quantity()
        quality = QualityVerdict(
            state=state,
            unit_resolution=UnitResolution.explicit,
            accepted_via=AcceptedVia.unremarkable,
            delta=delta,
        )
    return CanonicalObservation(**capture.model_dump(), canonical=canonical, quality=quality)
```

`tests/canon/test_delta.py`:
```python
"""Layer 3 of canon: delta review compares like with like only (SSOT §6.1),
and a suspicious delta never mutates anything. Where nothing was comparable the
verdict says so with a reason — §11.9 counts compared and uncompared captures,
so "not compared" has to be a recorded fact."""

from datetime import timedelta
from decimal import Decimal

from noor.canon.delta import review_delta
from noor.canon.models import (
    Arm,
    CaptureContext,
    CuffSize,
    MethodContext,
    NotComparableReason,
    Posture,
    QualityState,
    Setting,
)
from tests.conftest import T0, make_canonical, make_capture


def glucose_prior(value: str, *, hours_before: float = 1, device: str = "accu-chek", **kw):
    return make_canonical(
        value=value,
        effective_time=T0 - timedelta(hours=hours_before),
        method=MethodContext(device_class=device),
        source_identifier=f"PRIOR-{value}-{hours_before}h",
        **kw,
    )


def glucose_capture(value: str, *, device: str = "accu-chek", **kw):
    return make_capture(
        value=value,
        effective_time=T0,
        method=MethodContext(device_class=device),
        source_identifier="CURRENT",
        **kw,
    )


def test_a_comparable_prior_produces_a_recorded_delta(registry):
    # Arrange — glucose: max 8.0 mmol/L within 4h, device class compared
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("6.0")

    # Act
    delta = review_delta(Decimal("6.0"), capture, [prior], entry)

    # Assert
    assert delta.comparable is True
    assert delta.compared_to == prior.source_identifier
    assert delta.change == Decimal("0.5")
    assert delta.suspicious is False


def test_a_delta_beyond_the_registry_bound_is_suspicious(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("14.0")

    # Act
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)

    # Assert
    assert delta.comparable is True
    assert delta.suspicious is True


def test_a_delta_exactly_at_the_registry_bound_is_not_suspicious(registry):
    # Arrange — boundary row: at, not over
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("13.5")

    # Act
    delta = review_delta(Decimal("13.5"), capture, [prior], entry)

    # Assert
    assert delta.change == Decimal("8.0")
    assert delta.suspicious is False


def test_a_superseded_prior_is_not_a_baseline(registry):
    # Arrange — §5: a correction supersedes what it corrects. The source sent
    # 5.5, then corrected the same record to 13.9. Only v2 is the baseline;
    # comparing against v1 would flag a +8.5 jump the source never reported.
    entry = registry.entry("glucose")
    superseded = make_canonical(
        value="5.5",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
        source_version=1,
    )
    correction = make_canonical(
        value="13.9",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
        source_version=2,
    )
    capture = glucose_capture("14.0")

    # Act — oldest version first, so the reducer has to replace, not just keep
    delta = review_delta(Decimal("14.0"), capture, [superseded, correction], entry)

    # Assert
    assert delta.compared_to == "PRIOR-1"
    assert delta.change == Decimal("0.1")
    assert delta.suspicious is False


def test_a_superseded_prior_is_not_a_baseline_whichever_order_it_arrives_in(registry):
    # Arrange — the same two versions, newest first: the reducer must keep what
    # it has rather than let v1 overwrite v2. Sources do not promise an order.
    entry = registry.entry("glucose")
    versions = [
        make_canonical(
            value=value,
            effective_time=T0 - timedelta(hours=1),
            method=MethodContext(device_class="accu-chek"),
            source_identifier="PRIOR-1",
            source_version=version,
        )
        for value, version in (("13.9", 2), ("5.5", 1))
    ]
    capture = glucose_capture("14.0")

    # Act
    delta = review_delta(Decimal("14.0"), capture, versions, entry)

    # Assert
    assert delta.change == Decimal("0.1")
    assert delta.suspicious is False


def test_a_prior_from_a_different_device_class_is_not_comparable(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", device="cgm-different-class")
    capture = glucose_capture("14.0")

    # Act
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)

    # Assert — a prior of this observable exists, none like with like
    assert delta.comparable is False
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior
    assert delta.change is None


def test_a_prior_older_than_the_policy_window_is_not_comparable(registry):
    # Arrange — glucose window is 4h
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", hours_before=5)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_flagged_prior_is_not_a_baseline(registry):
    # Arrange — a needs_repeat observation proves nothing about the next one
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", state=QualityState.needs_repeat_or_verification)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_rejected_prior_is_not_a_baseline(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5", state=QualityState.rejected)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_later_observation_is_not_a_prior(registry):
    # Arrange — results land out of order; "prior" means earlier effective_time
    entry = registry.entry("glucose")
    later = glucose_prior("5.5", hours_before=-1)
    capture = glucose_capture("14.0")

    # Act / Assert
    delta = review_delta(Decimal("14.0"), capture, [later], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_prior_of_another_observable_is_ignored(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = make_canonical(observable="pulse", value="80", unit="/min")
    capture = glucose_capture("14.0")

    # Act
    delta = review_delta(Decimal("14.0"), capture, [prior], entry)

    # Assert — nothing of this observable was on record at all
    assert delta.comparable is False
    assert delta.not_comparable_reason is NotComparableReason.no_prior_observation


def test_the_most_recent_comparable_prior_wins(registry):
    # Arrange
    entry = registry.entry("glucose")
    older = glucose_prior("4.0", hours_before=3)
    newer = glucose_prior("5.5", hours_before=1)
    capture = glucose_capture("6.0")

    # Act
    delta = review_delta(Decimal("6.0"), capture, [older, newer], entry)

    # Assert
    assert delta.compared_to == newer.source_identifier


def bp(observable: str, value: str, *, context: CaptureContext, setting: Setting, **kw):
    defaults = {
        "observable": observable,
        "value": value,
        "unit": "mm[Hg]",
        "setting": setting,
        "context": context,
        "method": MethodContext(device_class="home-bp-monitor"),
    }
    defaults.update(kw)
    return make_canonical(**defaults)


def test_a_bp_delta_requires_matching_context(registry):
    # Arrange — §6.6: BP is meaningless without posture, arm, cuff; never pooled
    entry = registry.entry("systolic_bp")
    sitting = CaptureContext(
        posture=Posture.sitting, arm=Arm.left, cuff_size=CuffSize.standard,
        rest_duration_seconds=300, reading_ordinal=1, is_average=False,
    )
    standing = CaptureContext(
        posture=Posture.standing, arm=Arm.left, cuff_size=CuffSize.standard,
        rest_duration_seconds=60, reading_ordinal=1, is_average=False,
    )
    prior = bp("systolic_bp", "160", context=sitting, setting=Setting.home,
               effective_time=T0 - timedelta(hours=2))
    capture = make_capture(
        observable="systolic_bp", value="118", unit="mm[Hg]",
        setting=Setting.home, context=standing,
        method=MethodContext(device_class="home-bp-monitor"),
        effective_time=T0,
    )

    # Act / Assert — sitting vs standing is not like with like
    delta = review_delta(Decimal("118"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_a_bp_delta_with_matching_context_is_recorded(registry):
    # Arrange
    entry = registry.entry("systolic_bp")
    context = CaptureContext(
        posture=Posture.sitting, arm=Arm.left, cuff_size=CuffSize.standard,
        rest_duration_seconds=300, reading_ordinal=1, is_average=False,
    )
    prior = bp("systolic_bp", "160", context=context, setting=Setting.home,
               effective_time=T0 - timedelta(hours=2))
    capture = make_capture(
        observable="systolic_bp", value="118", unit="mm[Hg]",
        setting=Setting.home, context=context,
        method=MethodContext(device_class="home-bp-monitor"),
        effective_time=T0,
    )

    # Act
    delta = review_delta(Decimal("118"), capture, [prior], entry)

    # Assert — |−42| > 40: suspicious
    assert delta.comparable is True
    assert delta.change == Decimal("-42")
    assert delta.suspicious is True


def test_a_prior_with_incomplete_context_is_not_comparable(registry):
    # Arrange — cuff size unknown on the prior: cannot claim like-with-like
    entry = registry.entry("systolic_bp")
    incomplete = CaptureContext(
        posture=Posture.sitting, arm=Arm.left, cuff_size=None,
        rest_duration_seconds=300, reading_ordinal=1, is_average=False,
    )
    complete = CaptureContext(
        posture=Posture.sitting, arm=Arm.left, cuff_size=CuffSize.standard,
        rest_duration_seconds=300, reading_ordinal=1, is_average=False,
    )
    prior = bp("systolic_bp", "160", context=incomplete, setting=Setting.home,
               effective_time=T0 - timedelta(hours=2))
    capture = make_capture(
        observable="systolic_bp", value="118", unit="mm[Hg]",
        setting=Setting.home, context=complete,
        method=MethodContext(device_class="home-bp-monitor"),
        effective_time=T0,
    )

    # Act / Assert
    delta = review_delta(Decimal("118"), capture, [prior], entry)
    assert delta.not_comparable_reason is NotComparableReason.no_comparable_prior


def test_delta_review_never_mutates_either_observation(registry):
    # Arrange
    entry = registry.entry("glucose")
    prior = glucose_prior("5.5")
    capture = glucose_capture("14.0")

    # Act
    review_delta(Decimal("14.0"), capture, [prior], entry)

    # Assert — the testing standard: assert the stored value is unchanged,
    # not merely that a flag was set
    assert prior.as_reported.value == "5.5"
    assert prior.canonical is not None and prior.canonical.value == Decimal("5.5")
    assert capture.as_reported.value == "14.0"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/canon/test_delta.py -v`
Expected: FAIL — collection error, `noor.canon.delta` does not exist.

- [ ] **Step 3: Write `src/noor/canon/delta.py`**

```python
"""Layer 3 of canon: delta review (SSOT §6.1 layer 3).

Compares like with like only: same observable, same canonical unit (guaranteed
— one canonical unit per observable), the registry's named context fields
equal, device class equal, and the prior inside the policy's window. Only
accepted-quality priors are baselines, and only current versions — §5 versions
a source record so a correction supersedes what it corrects. A suspicious delta
is a review trigger, never a correction: nothing here mutates a value.
"""

from collections.abc import Iterable
from datetime import timedelta
from decimal import Decimal

from noor.canon.models import (
    ACCEPTED_FAMILY,
    CanonicalObservation,
    DeltaVerdict,
    NotComparableReason,
    ObservationCapture,
)
from noor.canon.registry import ObservableEntry


def current_versions(
    priors: Iterable[CanonicalObservation],
) -> list[CanonicalObservation]:
    """The latest version of each source record (SSOT §5).

    A source may correct a record it already sent; the correction carries the
    same `source_identifier` and a higher `source_version`. Only the current
    version is a fact — the superseded one is history, and comparing against it
    would report a change the source never made.
    """
    latest: dict[tuple[str, str], CanonicalObservation] = {}
    for prior in priors:
        key = (prior.source_system, prior.source_identifier)
        seen = latest.get(key)
        if seen is None or prior.source_version > seen.source_version:
            latest[key] = prior
    return list(latest.values())


def is_comparable(
    prior: CanonicalObservation,
    capture: ObservationCapture,
    entry: ObservableEntry,
) -> bool:
    """True when `prior` may serve as the delta baseline for `capture`."""
    if prior.observable != capture.observable:
        return False
    if prior.quality.state not in ACCEPTED_FAMILY:
        return False
    if not prior.effective_time < capture.effective_time:
        return False
    window = timedelta(hours=entry.delta_policy.within_hours)
    if capture.effective_time - prior.effective_time > window:
        return False
    if entry.delta_policy.compare_device_class:
        if prior.method.device_class is None or capture.method.device_class is None:
            return False
        if prior.method.device_class != capture.method.device_class:
            return False
    for field in entry.delta_policy.compare_context:
        prior_value = getattr(prior, field) if field == "setting" else getattr(prior.context, field)
        new_value = getattr(capture, field) if field == "setting" else getattr(capture.context, field)
        if prior_value is None or new_value is None or prior_value != new_value:
            return False
    return True


def review_delta(
    value: Decimal,
    capture: ObservationCapture,
    priors: Iterable[CanonicalObservation],
    entry: ObservableEntry,
) -> DeltaVerdict:
    """Compare a canonical value against the most recent comparable accepted prior.

    Always returns a verdict. When nothing was comparable the verdict says so
    and why — "not compared" is a fact of record, not a silent pass (§5), and
    §11.9's delta-check rate is the proportion that were.
    """
    known = current_versions(priors)
    latest: CanonicalObservation | None = None
    for prior in known:
        if not is_comparable(prior, capture, entry):
            continue
        if latest is None or prior.effective_time > latest.effective_time:
            latest = prior
    if latest is None:
        had_any = any(prior.observable == capture.observable for prior in known)
        return DeltaVerdict(
            comparable=False,
            not_comparable_reason=(
                NotComparableReason.no_comparable_prior
                if had_any
                else NotComparableReason.no_prior_observation
            ),
        )
    # An accepted-family observation carries a canonical value — CanonicalObservation
    # refuses to exist otherwise (models.py) — and is_comparable admitted only those.
    assert latest.canonical is not None
    change = value - latest.canonical.value
    return DeltaVerdict(
        comparable=True,
        compared_to=latest.source_identifier,
        change=change,
        suspicious=abs(change) > entry.delta_policy.max_abs_change,
    )
```

`assert` rather than `# pragma: no cover`: pragmas cannot silence the coverage gate — Task 1 sets `exclude_lines = []`, so the pragma would be inert and the line would simply be uncovered. coverage.py counts `assert` as a simple statement, not a branch, so this narrows the type for `mypy --strict` without leaving an uncoverable arm. The invariant it asserts is enforced by a model validator with its own test (Task 3), so the assert is a restatement, not the check.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/canon/test_delta.py -v`
Expected: PASS — 16 tests.

Run: `uv run mypy src/noor/canon`
Expected: `Success: no issues found`.

- [ ] **Step 5: Commit**

```powershell
git add src/noor/canon/delta.py tests/canon/test_delta.py tests/conftest.py
git commit -m "feat(canon): like-with-like delta review (SSOT §6.1, §14 step 3)"
```

---

### Task 10: The `canonicalise` pipeline

SSOT §6: every observation passes through `canon` before it becomes a fact; there is no capture path around it. This task wires the three layers (Tasks 5, 7, 8, 9) into the one public entry point, applies the quality-state rules (§6.2), the required-context rule (§6.6), the unit-change check (§6.1), and the mapping rule (§5: an ambiguous or unmapped mapping reaches canon as unusable).

Two §5 source fields are *read* here, not merely carried (§13.1 gate 1 lists "source/time/status" alongside units):

- **`source_status`.** A `cancelled` or `entered_in_error` record is one the source withdrew. It is rejected with `source_status_unusable` and no canonical value — canonicalising it would turn a retraction into a fact. Every other status (`registered`, `preliminary`, `final`, `amended`, `corrected`) canonicalises normally; how *recent* or how *final* a value must be to drive a given rule is a per-rule §5.1/§7.1 question, not canon's (assumption 11).
- **`source_version`.** The unit-change baseline goes through `current_versions` (Task 9) for the same reason delta review does: a superseded v1 is history, so a v1 in mg/dL that a v2 corrected to mmol/L must not raise a unit-change flag against a mmol/L capture.

**Files:**
- Create: `src/noor/canon/pipeline.py`
- Create: `tests/canon/test_pipeline.py`

**Interfaces:**
- Consumes: everything from Tasks 3–9, including `WITHDRAWN_SOURCE_STATUSES` and `NotComparableReason` (Task 3) and `current_versions` (Task 9).
- Produces:
  - `canonicalise(capture: ObservationCapture, registry: ObservableRegistry, priors: Iterable[CanonicalObservation] = ()) -> CanonicalObservation` — the one entry point. Raises `UnknownObservableError` for an ungoverned observable, `AbsentObservationError` for an `absent_reason` capture. Pure: no I/O, no clock.
  - `AbsentObservationError(ValueError)`.

- [ ] **Step 1: Write the failing tests**

`tests/canon/test_pipeline.py`:
```python
"""The canon pipeline (SSOT §6): the three layers, the four quality states,
and the guarantee that a value without a safe canonical form never becomes
a fact."""

from datetime import timedelta
from decimal import Decimal

import pytest

from noor.canon.models import (
    Arm,
    CaptureContext,
    CuffSize,
    MappingInfo,
    MappingStatus,
    MethodContext,
    NotComparableReason,
    Posture,
    QualityState,
    RejectionReason,
    ReportedValue,
    Setting,
    SourceCode,
    SourceStatus,
    SuspicionReason,
    UnitResolution,
)
from noor.canon.pipeline import AbsentObservationError, canonicalise
from noor.canon.registry import UnknownObservableError
from tests.conftest import T0, make_canonical, make_capture


def bp_capture(value: str, **kw):
    """A fully-contextualised systolic BP capture (SSOT §6.6)."""
    fields = {
        "observable": "systolic_bp",
        "value": value,
        "unit": "mm[Hg]",
        "setting": Setting.home,
        "context": CaptureContext(
            posture=Posture.sitting,
            arm=Arm.left,
            cuff_size=CuffSize.standard,
            rest_duration_seconds=300,
            reading_ordinal=1,
            is_average=False,
        ),
        "method": MethodContext(device_class="home-bp-monitor"),
    }
    fields.update(kw)
    overrides = {k: fields.pop(k) for k in ("value", "unit")}
    return make_capture(as_reported=ReportedValue(**overrides), **fields)


def test_an_ordinary_capture_is_accepted_unremarkable(registry):
    # Arrange
    capture = make_capture()

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.quality.accepted_via == "unremarkable"
    assert result.quality.unit_resolution is UnitResolution.explicit
    assert result.canonical is not None
    assert result.canonical.value == Decimal("5.5")
    assert result.canonical.ucum == "mmol/L"
    assert result.canonical.conversion_applied is None  # already canonical
    assert result.quality.delta is not None  # "not compared" is recorded, not absent
    assert result.quality.delta.comparable is False
    assert result.quality.delta.not_comparable_reason is NotComparableReason.no_prior_observation
    assert result.as_reported.value == "5.5"  # the verbatim value survives (§5)


def test_a_converted_value_preserves_the_original_unit_and_shows_its_work(registry):
    # Arrange — §6.3: preserve the original unit; convert with provenance
    capture = make_capture(value="90", unit="mg/dL")

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.canonical is not None
    assert result.canonical.value == Decimal("5.00")
    assert result.canonical.ucum == "mmol/L"
    assert result.as_reported.value == "90"
    assert result.as_reported.unit == "mg/dL"
    # The stored value can be traced to the factor that produced it (§5, §6.3)
    declared = next(
        c for c in registry.entry("glucose").conversions if c.from_unit == "mg/dL"
    )
    applied = result.canonical.conversion_applied
    assert applied is not None
    assert applied.from_unit == "mg/dL"
    assert applied.multiply == declared.multiply
    assert applied.version == declared.version


def test_a_code_implied_unit_is_recorded_as_inferred(registry):
    # Arrange
    capture = make_capture(
        observable="hba1c_ngsp",
        as_reported=ReportedValue(value="7.4", unit=None),
        source_code=SourceCode(system="http://loinc.org", code="4548-4"),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.quality.unit_resolution is UnitResolution.inferred_from_code
    assert result.canonical is not None
    assert result.canonical.value == Decimal("7.4")
    assert result.canonical.ucum == "%"


def test_an_ambiguous_unit_is_a_hard_failure_with_no_canonical_value(registry):
    # Arrange — §6.3: the one capture-time hard stop
    capture = make_capture(as_reported=ReportedValue(value="5.5", unit=None))

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == [RejectionReason.unit_ambiguous]
    assert result.quality.unit_resolution is UnitResolution.ambiguous
    assert result.canonical is None  # never receives a canonical value


def test_an_unparseable_value_is_rejected(registry):
    # Arrange
    capture = make_capture(as_reported=ReportedValue(value="7,4", unit="mmol/L"))

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == [RejectionReason.parse_failure]
    assert result.canonical is None


def test_an_ambiguous_mapping_reaches_canon_as_unusable(registry):
    # Arrange — §5: never a silent best guess
    capture = make_capture(mapping=MappingInfo(status=MappingStatus.ambiguous))

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == [RejectionReason.mapping_unusable]
    assert result.canonical is None


def test_a_withdrawn_source_record_is_refused(registry):
    # Arrange — §5: the source retracted this. Canonicalising it would turn a
    # retraction into a fact.
    capture = make_capture(source_status=SourceStatus.entered_in_error)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == [RejectionReason.source_status_unusable]
    assert result.canonical is None


def test_a_cancelled_source_record_is_refused(registry):
    # Arrange — the other withdrawn status; both rows of the boundary
    capture = make_capture(source_status=SourceStatus.cancelled)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.rejection_reasons == [RejectionReason.source_status_unusable]


def test_a_corrected_source_record_is_canonicalised_normally(registry):
    # Arrange — a correction is the value that stands, not a withdrawal
    # (assumption 11); freshness is a per-rule §5.1 question, not canon's.
    capture = make_capture(source_status=SourceStatus.corrected)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.canonical is not None
    assert result.canonical.value == Decimal("5.5")


def test_a_preliminary_source_record_is_canonicalised_normally(registry):
    # Arrange — canon does not gate on finality (assumption 11)
    capture = make_capture(source_status=SourceStatus.preliminary)

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted


def test_an_unusable_mapping_and_an_unusable_status_are_both_named(registry):
    # Arrange — two independent §5 refusals on one capture; neither hides the other
    capture = make_capture(
        mapping=MappingInfo(status=MappingStatus.ambiguous),
        source_status=SourceStatus.cancelled,
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert set(result.quality.rejection_reasons) == {
        RejectionReason.mapping_unusable,
        RejectionReason.source_status_unusable,
    }
    assert result.canonical is None


def test_a_bp_capture_missing_required_context_is_rejected(registry):
    # Arrange — §6.6: BP without posture is meaningless
    capture = make_capture(
        observable="systolic_bp",
        as_reported=ReportedValue(value="120", unit="mm[Hg]"),
        setting=Setting.home,
        context=CaptureContext(posture=None, arm=Arm.left, cuff_size=CuffSize.standard),
        method=MethodContext(device_class="home-bp-monitor"),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert RejectionReason.missing_required_context in result.quality.rejection_reasons
    assert result.canonical is not None  # the value exists; the context does not


def test_a_bp_capture_missing_required_method_fields_is_rejected(registry):
    # Arrange — §6.6: the device class is required method context for BP
    capture = make_capture(
        observable="systolic_bp",
        as_reported=ReportedValue(value="120", unit="mm[Hg]"),
        setting=Setting.home,
        context=CaptureContext(
            posture=Posture.sitting,
            arm=Arm.left,
            cuff_size=CuffSize.standard,
            rest_duration_seconds=300,
            reading_ordinal=1,
            is_average=False,
        ),
        method=MethodContext(device_class=None),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert RejectionReason.missing_required_context in result.quality.rejection_reasons


def test_a_physiologically_impossible_value_is_rejected_but_kept(registry):
    # Arrange — 80 mmol/L glucose cannot be generated (physiologic ceiling 70)
    capture = make_capture(value="80", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry)

    # Assert — the value is kept so a clinician can resurrect it (§6.2)
    assert result.quality.state is QualityState.rejected
    assert result.quality.rejection_reasons == [RejectionReason.outside_physiologic_envelope]
    assert result.canonical is not None
    assert result.canonical.value == Decimal("80")


def test_an_extreme_but_possible_value_is_flagged_not_rejected(registry):
    # Arrange — pulse 220: outside operational [35, 200], inside physiologic
    capture = make_capture(observable="pulse", value="220", unit="/min")

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert result.quality.suspicions == [SuspicionReason.outside_operational_envelope]
    assert result.canonical is not None
    assert result.canonical.value == Decimal("220")


def test_a_real_but_extreme_value_and_a_mistyped_value_land_in_different_states(registry):
    # Arrange — §14 step 2's verification, §6.2's reason for four states:
    # systolic 300 is a genuine-emergency value; "abc" is a mistype
    extreme = bp_capture("300")
    mistyped = bp_capture("abc")

    # Act
    extreme_result = canonicalise(extreme, registry)
    mistyped_result = canonicalise(mistyped, registry)

    # Assert — never the same system outcome
    assert extreme_result.quality.state is QualityState.needs_repeat_or_verification
    assert mistyped_result.quality.state is QualityState.rejected
    assert extreme_result.quality.state != mistyped_result.quality.state


def test_a_decimal_transposition_pattern_adds_a_suspicion(registry):
    # Arrange — glucose 40 mmol/L: outside operational, and 4.0 would be inside
    capture = make_capture(value="40", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert SuspicionReason.outside_operational_envelope in result.quality.suspicions
    assert SuspicionReason.decimal_transposition_suspected in result.quality.suspicions


def test_a_unit_changed_from_the_patients_prior_record_is_flagged(registry):
    # Arrange — §6.1 layer 1: the prior was mg/dL, today's says mmol/L
    prior = make_canonical(
        value="100",
        unit="mg/dL",
        canonical_value="5.55",
        canonical_ucum="mmol/L",
        effective_time=T0 - timedelta(hours=1),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="5.5", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry, priors=[prior])

    # Assert
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert result.quality.suspicions == [SuspicionReason.unit_changed_from_prior]


def test_a_unit_matching_the_patients_prior_record_is_unremarkable(registry):
    # Arrange — same unit as the prior: no suspicion
    prior = make_canonical(
        value="100",
        unit="mg/dL",
        canonical_value="5.55",
        canonical_ucum="mmol/L",
        effective_time=T0 - timedelta(hours=1),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="101", unit="mg/dL")

    # Act
    result = canonicalise(capture, registry, priors=[prior])

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.quality.suspicions == []


def test_a_later_observation_is_not_a_unit_change_baseline(registry):
    # Arrange — results land out of order; only earlier priors count
    later = make_canonical(
        value="100",
        unit="mg/dL",
        canonical_value="5.55",
        canonical_ucum="mmol/L",
        effective_time=T0 + timedelta(hours=1),
        source_identifier="LATER-1",
    )
    capture = make_capture(value="5.5", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry, priors=[later])

    # Assert — no earlier prior, so no unit-change suspicion
    assert result.quality.state is QualityState.accepted


def test_a_superseded_prior_is_not_the_unit_change_baseline(registry):
    # Arrange — §5: the source sent 100 mg/dL, then corrected the same record to
    # 5.55 mmol/L. Today's mmol/L capture matches the version that stands, so
    # there is no unit change to flag. Newest first: arrival order is not sorted.
    versions = [
        make_canonical(
            value=value,
            unit=unit,
            canonical_value="5.55",
            canonical_ucum="mmol/L",
            effective_time=T0 - timedelta(hours=1),
            source_identifier="PRIOR-1",
            source_version=version,
        )
        for value, unit, version in (("5.55", "mmol/L", 2), ("100", "mg/dL", 1))
    ]
    capture = make_capture(value="5.5", unit="mmol/L")

    # Act
    result = canonicalise(capture, registry, priors=versions)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.quality.suspicions == []


def test_priors_may_be_a_generator(registry):
    # Arrange — canonicalise reads the priors twice (unit change, then delta);
    # a one-shot iterable must not read empty on the second pass
    prior = make_canonical(
        value="5.5",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="14.0", method=MethodContext(device_class="accu-chek"))

    # Act
    result = canonicalise(capture, registry, priors=(p for p in [prior]))

    # Assert — the delta was found on the second pass
    assert result.quality.suspicions == [SuspicionReason.delta_exceeded]


def test_a_suspicious_delta_is_flagged_and_recorded(registry):
    # Arrange
    prior = make_canonical(
        value="5.5",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="14.0", method=MethodContext(device_class="accu-chek"))

    # Act
    result = canonicalise(capture, registry, priors=[prior])

    # Assert
    assert result.quality.state is QualityState.needs_repeat_or_verification
    assert result.quality.suspicions == [SuspicionReason.delta_exceeded]
    assert result.quality.delta is not None
    assert result.quality.delta.compared_to == "PRIOR-1"
    assert result.quality.delta.change == Decimal("8.5")


def test_a_clean_delta_is_recorded_without_flagging(registry):
    # Arrange
    prior = make_canonical(
        value="5.5",
        effective_time=T0 - timedelta(hours=1),
        method=MethodContext(device_class="accu-chek"),
        source_identifier="PRIOR-1",
    )
    capture = make_capture(value="6.0", method=MethodContext(device_class="accu-chek"))

    # Act
    result = canonicalise(capture, registry, priors=[prior])

    # Assert — a delta that ran and passed is a fact of record, not silence
    assert result.quality.state is QualityState.accepted
    assert result.quality.delta is not None
    assert result.quality.delta.suspicious is False


def test_every_rejection_reason_is_named_when_several_apply(registry):
    # Arrange — unparseable value AND an unrecognised unit
    capture = make_capture(as_reported=ReportedValue(value="abc", unit="mg%"))

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.rejected
    assert set(result.quality.rejection_reasons) == {
        RejectionReason.parse_failure,
        RejectionReason.unit_ambiguous,
    }


def test_an_unknown_observable_is_refused_loudly(registry):
    # Arrange — an ungoverned observable is a system error, not a clinical one
    capture = make_capture(observable="tsh")

    # Act / Assert
    with pytest.raises(UnknownObservableError):
        canonicalise(capture, registry)


def test_an_absent_reason_capture_has_nothing_to_canonicalise(registry):
    # Arrange — §5: absence-with-reason is stored verbatim by the caller
    capture = make_capture(
        as_reported=ReportedValue(value=None, unit=None),
        absent_reason="not_done",
    )

    # Act / Assert
    with pytest.raises(AbsentObservationError):
        canonicalise(capture, registry)


def test_context_flags_pass_through_and_the_value_is_never_corrected(registry):
    # Arrange — §5.3: the flag prompts review; it does not adjust a number
    capture = make_capture(
        observable="hba1c_ngsp",
        value="7.4",
        unit="%",
        context_flags=["a1c_interpretation_caution"],
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert
    assert result.quality.state is QualityState.accepted
    assert result.canonical is not None
    assert result.canonical.value == Decimal("7.4")
    assert result.context_flags == ["a1c_interpretation_caution"]


def test_a_code_display_name_is_carried_but_never_required(registry):
    # Arrange — §3.3: LOINC display names carry a licence condition, so the
    # registry keys code_unit_map on bare "system|code" and stores no display
    # text (assumption 9). A display arriving on a capture is the source's data:
    # canon carries it verbatim and never needs it to resolve anything.
    capture = make_capture(
        observable="hba1c_ngsp",
        as_reported=ReportedValue(value="7.4", unit=None),
        source_code=SourceCode(
            system="http://loinc.org", code="4548-4", display="Hemoglobin A1c/Hemoglobin.total"
        ),
        mapping=MappingInfo(source_display="HbA1c", terminology_version="LOINC 2.77"),
    )

    # Act
    result = canonicalise(capture, registry)

    # Assert — resolved from the code alone; both displays survive untouched
    assert result.quality.unit_resolution is UnitResolution.inferred_from_code
    assert result.source_code is not None
    assert result.source_code.display == "Hemoglobin A1c/Hemoglobin.total"
    assert result.mapping.source_display == "HbA1c"
    assert result.mapping.terminology_version == "LOINC 2.77"


def test_the_capture_is_never_mutated(registry):
    # Arrange
    capture = make_capture(value="40", unit="mmol/L")

    # Act
    canonicalise(capture, registry)

    # Assert — §6.1: never silently converts, replaces, or suppresses
    assert capture.as_reported.value == "40"
    assert capture.as_reported.unit == "mmol/L"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/canon/test_pipeline.py -v`
Expected: FAIL — collection error, `noor.canon.pipeline` does not exist.

- [ ] **Step 3: Write `src/noor/canon/pipeline.py`**

```python
"""The canon pipeline (SSOT §6.1). Every observation captured during a visit
passes through here before it becomes a fact — there is no path around it
(§11.5 step 2). Pure: no I/O, no clock; time arrives on the captures.
"""

from collections.abc import Iterable

from noor.canon.delta import current_versions, review_delta
from noor.canon.models import (
    ACCEPTED_FAMILY,
    WITHDRAWN_SOURCE_STATUSES,
    AcceptedVia,
    CanonicalObservation,
    CanonicalQuantity,
    DeltaVerdict,
    MappingStatus,
    ObservationCapture,
    QualityState,
    QualityVerdict,
    RejectionReason,
    SuspicionReason,
    UnitResolution,
)
from noor.canon.parse import decimal_transposition_suspected, parse_value
from noor.canon.plausibility import EnvelopePosition, locate
from noor.canon.registry import ObservableEntry, ObservableRegistry
from noor.canon.units import resolve_unit, to_canonical


class AbsentObservationError(ValueError):
    """An absent_reason observation carries no value; there is nothing to
    canonicalise (§5). The store records it verbatim without a canon verdict."""


def _missing_required_fields(capture: ObservationCapture, entry: ObservableEntry) -> list[str]:
    missing: list[str] = []
    for field in entry.required_context:
        value = getattr(capture, field) if field == "setting" else getattr(capture.context, field)
        if value is None:
            missing.append(field)
    for field in entry.required_method:
        if getattr(capture.method, field) is None:
            missing.append(field)
    return missing


def _unusable_source(capture: ObservationCapture) -> list[RejectionReason]:
    """§5's two "this record cannot be used at all" conditions.

    Both are properties of the record rather than of the value, so they are
    decided before parsing and neither hides the other.
    """
    reasons: list[RejectionReason] = []
    if capture.mapping.status is not MappingStatus.mapped:
        reasons.append(RejectionReason.mapping_unusable)
    if capture.source_status in WITHDRAWN_SOURCE_STATUSES:
        reasons.append(RejectionReason.source_status_unusable)
    return reasons


def _unit_changed_from_prior(
    capture: ObservationCapture,
    priors: Iterable[CanonicalObservation],
) -> bool:
    """§6.1 layer 1: the unit changed from the patient's prior accepted record."""
    if capture.as_reported.unit is None:
        return False
    candidates = [
        prior
        for prior in current_versions(priors)
        if prior.observable == capture.observable
        and prior.quality.state in ACCEPTED_FAMILY
        and prior.as_reported.unit is not None
        and prior.effective_time < capture.effective_time
    ]
    if not candidates:
        return False
    latest = max(candidates, key=lambda prior: prior.effective_time)
    return capture.as_reported.unit != latest.as_reported.unit


def canonicalise(
    capture: ObservationCapture,
    registry: ObservableRegistry,
    priors: Iterable[CanonicalObservation] = (),
) -> CanonicalObservation:
    """Run the three canon layers over one capture.

    `priors` are the patient's existing canonical observations; non-matching
    observables are ignored. The capture is never mutated (§6.1).
    """
    entry = registry.entry(capture.observable)
    # Read once: the priors are walked twice below, and a caller may pass a
    # generator — which would come back empty on the second walk.
    known_priors = tuple(priors)

    if capture.absent_reason is not None:
        raise AbsentObservationError(
            f"{capture.observable}: absent_reason observations carry no value to canonicalise"
        )

    unit_resolution, resolved_unit = resolve_unit(
        capture.as_reported.unit, capture.source_code, entry
    )

    unusable = _unusable_source(capture)
    if unusable:
        quality = QualityVerdict(
            state=QualityState.rejected,
            unit_resolution=unit_resolution,
            rejection_reasons=unusable,
        )
        return CanonicalObservation(**capture.model_dump(), canonical=None, quality=quality)

    rejection_reasons: list[RejectionReason] = []
    suspicions: list[SuspicionReason] = []
    canonical: CanonicalQuantity | None = None
    delta: DeltaVerdict | None = None

    parsed = parse_value(capture.as_reported.value) if capture.as_reported.value else None
    if parsed is None:
        rejection_reasons.append(RejectionReason.parse_failure)

    if unit_resolution is UnitResolution.ambiguous:
        rejection_reasons.append(RejectionReason.unit_ambiguous)

    if _missing_required_fields(capture, entry):
        rejection_reasons.append(RejectionReason.missing_required_context)

    if parsed is not None and resolved_unit is not None:
        canonical = to_canonical(parsed, resolved_unit, entry)
        position = locate(canonical.value, entry)
        if position is EnvelopePosition.outside_physiologic:
            rejection_reasons.append(RejectionReason.outside_physiologic_envelope)
        elif position is EnvelopePosition.outside_operational:
            suspicions.append(SuspicionReason.outside_operational_envelope)
            if decimal_transposition_suspected(canonical.value, entry):
                suspicions.append(SuspicionReason.decimal_transposition_suspected)

    if not rejection_reasons and canonical is not None:
        if _unit_changed_from_prior(capture, known_priors):
            suspicions.append(SuspicionReason.unit_changed_from_prior)
        delta = review_delta(canonical.value, capture, known_priors, entry)
        if delta.suspicious:
            suspicions.append(SuspicionReason.delta_exceeded)

    if rejection_reasons:
        quality = QualityVerdict(
            state=QualityState.rejected,
            unit_resolution=unit_resolution,
            rejection_reasons=rejection_reasons,
        )
    elif suspicions:
        quality = QualityVerdict(
            state=QualityState.needs_repeat_or_verification,
            unit_resolution=unit_resolution,
            suspicions=suspicions,
            delta=delta,
        )
    else:
        quality = QualityVerdict(
            state=QualityState.accepted,
            unit_resolution=unit_resolution,
            accepted_via=AcceptedVia.unremarkable,
            delta=delta,
        )
    return CanonicalObservation(**capture.model_dump(), canonical=canonical, quality=quality)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/canon/test_pipeline.py -v`
Expected: PASS — 30 tests.

Run: `uv run mypy src/noor/canon`
Expected: `Success: no issues found`.

- [ ] **Step 5: Commit**

```powershell
git add src/noor/canon/pipeline.py tests/canon/test_pipeline.py
git commit -m "feat(canon): the canonicalise pipeline — three layers, four quality states (SSOT §6, §14 step 2)"
```

---

### Task 11: Quality resolution — repeat confirmation and clinician verification

SSOT §6.2: a `needs_repeat_or_verification` observation that a repeat resolves becomes `accepted` with `accepted_via: repeat_confirmed` and a pointer to the confirming observation; it never silently becomes indistinguishable from a value nobody looked at. §6.5: repeat before action, conditional. §6.2: `clinically_exceptional_accepted` stops the plausibility gate suppressing a genuine emergency. Observations are write-once (§5), so resolutions are separate append-only records; the store folds them into effective state (persistence plan).

**Files:**
- Create: `src/noor/canon/resolution.py`
- Create: `tests/canon/test_resolution.py`

**Interfaces:**
- Consumes: Tasks 3, 4, 8.
- Produces:
  - `ResolutionError(ValueError)`.
  - `ResolutionKind` (`repeat_confirmed | clinician_verified`).
  - `QualityResolution` — fields: `observation` (source_identifier of the resolved observation), `kind`, `clinician_id`, `confirming_observation: str | None`, `resolved_at` (aware, normalised UTC), `resulting_state: QualityState`, `accepted_via: AcceptedVia`.
  - `confirm_repeat(flagged, repeat, entry, *, clinician_id, resolved_at) -> QualityResolution`.
  - `verify_by_clinician(observation, entry, *, clinician_id, resolved_at) -> QualityResolution`.

- [ ] **Step 1: Write the failing tests**

`tests/canon/test_resolution.py`:
```python
"""Quality resolution (SSOT §6.2, §6.5): append-only, named, and never silent."""

from datetime import datetime, timedelta, timezone

import pytest

from noor.canon.models import (
    AcceptedVia,
    Arm,
    CaptureContext,
    CuffSize,
    MethodContext,
    Posture,
    QualityState,
    RejectionReason,
    Setting,
    SourceStatus,
)
from noor.canon.resolution import (
    ResolutionError,
    ResolutionKind,
    confirm_repeat,
    verify_by_clinician,
)
from tests.conftest import make_canonical

RESOLVED_AT = datetime(2026, 6, 12, 9, 0, tzinfo=timezone.utc)


def test_a_concordant_repeat_confirms_a_flagged_value(registry):
    # Arrange — glucose repeat_tolerance is 0.6 mmol/L
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        value="30.0",
        source_identifier="FLAGGED-1",
    )
    repeat = make_canonical(value="29.5", source_identifier="REPEAT-1")

    # Act
    resolution = confirm_repeat(
        flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT
    )

    # Assert — §6.2: accepted via repeat_confirmed, with the pointer
    assert resolution.observation == "FLAGGED-1"
    assert resolution.kind is ResolutionKind.repeat_confirmed
    assert resolution.confirming_observation == "REPEAT-1"
    assert resolution.clinician_id == "RN-7"
    assert resolution.resulting_state is QualityState.accepted
    assert resolution.accepted_via is AcceptedVia.repeat_confirmed


def test_a_discordant_repeat_confirms_nothing(registry):
    # Arrange — |28.0 − 30.0| = 2.0 > 0.6 tolerance
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification, value="30.0"
    )
    repeat = make_canonical(value="28.0")

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_that_is_not_accepted_quality_cannot_confirm(registry):
    # Arrange — a flagged repeat is another question, not an answer
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification, value="30.0"
    )
    repeat = make_canonical(
        state=QualityState.needs_repeat_or_verification, value="29.5"
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_of_a_different_observable_cannot_confirm(registry):
    # Arrange
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification, value="30.0"
    )
    repeat = make_canonical(observable="pulse", value="29.5", unit="/min")

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_in_a_different_posture_cannot_confirm(registry):
    # Arrange — the reading ordinal may differ; the posture may not
    entry = registry.entry("systolic_bp")
    sitting = CaptureContext(
        posture=Posture.sitting, arm=Arm.left, cuff_size=CuffSize.standard,
        rest_duration_seconds=300, reading_ordinal=1, is_average=False,
    )
    standing = CaptureContext(
        posture=Posture.standing, arm=Arm.left, cuff_size=CuffSize.standard,
        rest_duration_seconds=60, reading_ordinal=2, is_average=False,
    )
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        observable="systolic_bp", value="250", unit="mm[Hg]",
        setting=Setting.home, context=sitting,
        method=MethodContext(device_class="home-bp-monitor"),
    )
    repeat = make_canonical(
        observable="systolic_bp", value="248", unit="mm[Hg]",
        setting=Setting.home, context=standing,
        method=MethodContext(device_class="home-bp-monitor"),
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_repeat_from_a_different_device_class_cannot_confirm(registry):
    # Arrange
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        value="30.0",
        method=MethodContext(device_class="accu-chek"),
    )
    repeat = make_canonical(
        value="29.5", method=MethodContext(device_class="cgm-different-class")
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(flagged, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_an_unflagged_observation_has_nothing_to_confirm(registry):
    # Arrange
    entry = registry.entry("glucose")
    unremarkable = make_canonical(value="5.5")
    repeat = make_canonical(value="5.5")

    # Act / Assert
    with pytest.raises(ResolutionError):
        confirm_repeat(unremarkable, repeat, entry, clinician_id="RN-7", resolved_at=RESOLVED_AT)


def test_a_clinician_verified_envelope_rejection_becomes_clinically_exceptional(registry):
    # Arrange — §6.2: the gate must not suppress a genuine emergency
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.outside_physiologic_envelope],
        value="80",
    )

    # Act
    resolution = verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)

    # Assert
    assert resolution.resulting_state is QualityState.clinically_exceptional_accepted
    assert resolution.accepted_via is AcceptedVia.clinician_verified
    assert resolution.kind is ResolutionKind.clinician_verified
    assert resolution.clinician_id == "MD-3"


def test_a_clinician_verified_ordinary_flagged_value_becomes_accepted(registry):
    # Arrange — delta-flagged but the value sits inside the operational envelope
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification, value="6.0"
    )

    # Act
    resolution = verify_by_clinician(flagged, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)

    # Assert
    assert resolution.resulting_state is QualityState.accepted
    assert resolution.accepted_via is AcceptedVia.clinician_verified


def test_a_clinician_verified_flagged_extreme_value_becomes_clinically_exceptional(registry):
    # Arrange — pulse 220: outside operational, confirmed real by a named clinician
    entry = registry.entry("pulse")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification,
        observable="pulse",
        value="220",
        unit="/min",
    )

    # Act
    resolution = verify_by_clinician(flagged, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)

    # Assert
    assert resolution.resulting_state is QualityState.clinically_exceptional_accepted


def test_a_parse_failure_can_never_be_verified(registry):
    # Arrange — there is no value to stand behind; re-capture is the fix
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.parse_failure],
        value="abc",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_a_unit_ambiguous_rejection_can_never_be_verified(registry):
    # Arrange — §6.3: resolve the unit in the home, not afterwards
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.unit_ambiguous],
        value="5.5",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_a_context_rejection_can_never_be_verified(registry):
    # Arrange — context is recorded at capture, not attested afterwards
    entry = registry.entry("systolic_bp")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.missing_required_context],
        observable="systolic_bp",
        value="120",
        unit="mm[Hg]",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_an_accepted_observation_has_nothing_to_verify(registry):
    # Arrange
    entry = registry.entry("glucose")
    unremarkable = make_canonical(value="5.5")

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(unremarkable, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_a_withdrawn_source_status_rejection_can_never_be_verified(registry):
    # Arrange — §5: the source retracted the record. A clinician can attest that a
    # value is real; nobody can attest that a withdrawn record was not withdrawn.
    entry = registry.entry("glucose")
    rejected = make_canonical(
        state=QualityState.rejected,
        rejection_reasons=[RejectionReason.source_status_unusable],
        source_status=SourceStatus.entered_in_error,
        value="5.5",
    )

    # Act / Assert
    with pytest.raises(ResolutionError):
        verify_by_clinician(rejected, entry, clinician_id="MD-3", resolved_at=RESOLVED_AT)


def test_the_resolution_timestamp_is_normalised_to_utc(registry):
    # Arrange
    entry = registry.entry("glucose")
    flagged = make_canonical(
        state=QualityState.needs_repeat_or_verification, value="6.0"
    )
    riyadh_noon = datetime(2026, 6, 12, 12, 0, tzinfo=timezone(timedelta(hours=3)))

    # Act
    resolution = verify_by_clinician(flagged, entry, clinician_id="MD-3", resolved_at=riyadh_noon)

    # Assert — §2.6: stored UTC
    assert resolution.resolved_at.tzinfo is timezone.utc
    assert resolution.resolved_at.hour == 9
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/canon/test_resolution.py -v`
Expected: FAIL — collection error, `noor.canon.resolution` does not exist.

- [ ] **Step 3: Write `src/noor/canon/resolution.py`**

```python
"""Quality resolution (SSOT §6.2, §6.5).

Observations are write-once (§5), so a resolution is a separate append-only
record, not an edit. A repeat that resolves a flag must be concordant and
like-with-like; a clinician verification names the clinician. A resolved value
outside the operational envelope becomes clinically_exceptional_accepted — the
state that stops the plausibility gate from suppressing a genuine emergency —
and a confirmed ordinary value becomes accepted. Either way, the record keeps
how it got there.
"""

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import AwareDatetime, Field, field_validator

from noor.canon.models import (
    ACCEPTED_FAMILY,
    AcceptedVia,
    CanonicalObservation,
    NoorModel,
    QualityState,
    RejectionReason,
)
from noor.canon.plausibility import EnvelopePosition, locate
from noor.canon.registry import ObservableEntry


class ResolutionError(ValueError):
    """A resolution that does not meet its bar is refused, not approximated."""


class ResolutionKind(StrEnum):
    repeat_confirmed = "repeat_confirmed"
    clinician_verified = "clinician_verified"


class QualityResolution(NoorModel):
    observation: str = Field(min_length=1)  # source_identifier of the resolved observation
    kind: ResolutionKind
    clinician_id: str = Field(min_length=1)
    confirming_observation: str | None = None  # the repeat's source_identifier (§6.2)
    resolved_at: AwareDatetime
    resulting_state: QualityState
    accepted_via: AcceptedVia

    @field_validator("resolved_at")
    @classmethod
    def _normalise_to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)


def confirm_repeat(
    flagged: CanonicalObservation,
    repeat: CanonicalObservation,
    entry: ObservableEntry,
    *,
    clinician_id: str,
    resolved_at: datetime,
) -> QualityResolution:
    """Resolve a needs_repeat_or_verification observation against a concordant repeat.

    The repeat must itself be accepted-quality, the same observable, in the same
    context (reading ordinal and averaging aside) and device class, and within
    the registry's repeat tolerance. A discordant repeat confirms nothing.
    """
    if flagged.quality.state is not QualityState.needs_repeat_or_verification:
        raise ResolutionError(f"nothing to confirm: state is {flagged.quality.state}")
    if repeat.quality.state not in ACCEPTED_FAMILY or repeat.canonical is None:
        raise ResolutionError("the repeat must itself be accepted-quality")
    if flagged.canonical is None or repeat.observable != flagged.observable:
        raise ResolutionError("the repeat must be the same observable with a canonical value")
    context_fields = {"reading_ordinal", "is_average"}
    if flagged.context.model_dump(exclude=context_fields) != repeat.context.model_dump(
        exclude=context_fields
    ):
        raise ResolutionError("the repeat must be measured in the same context")
    if flagged.setting != repeat.setting:
        raise ResolutionError("the repeat must be measured in the same setting")
    if flagged.method.device_class != repeat.method.device_class:
        raise ResolutionError("the repeat must come from the same device class")
    if abs(repeat.canonical.value - flagged.canonical.value) > entry.repeat_tolerance:
        raise ResolutionError("the repeat does not confirm the flagged value")
    return QualityResolution(
        observation=flagged.source_identifier,
        kind=ResolutionKind.repeat_confirmed,
        clinician_id=clinician_id,
        confirming_observation=repeat.source_identifier,
        resolved_at=resolved_at,
        resulting_state=QualityState.accepted,
        accepted_via=AcceptedVia.repeat_confirmed,
    )


def verify_by_clinician(
    observation: CanonicalObservation,
    entry: ObservableEntry,
    *,
    clinician_id: str,
    resolved_at: datetime,
) -> QualityResolution:
    """A named clinician attests that a questioned or envelope-rejected value is real.

    Parse, unit, mapping, context, and withdrawn-status rejections can never be
    verified — the fix is re-capture, not attestation, and no attestation makes a
    record the source retracted un-retracted. An accepted observation has nothing
    to verify. Both guards below already refuse those: they carry no canonical
    value, and their reasons are not the envelope rejection.
    """
    if observation.canonical is None:
        raise ResolutionError("an observation without a canonical value cannot be verified")
    if observation.quality.state is QualityState.rejected and (
        observation.quality.rejection_reasons != [RejectionReason.outside_physiologic_envelope]
    ):
        raise ResolutionError("only an envelope rejection can be clinician-verified; re-capture")
    if observation.quality.state not in (
        QualityState.needs_repeat_or_verification,
        QualityState.rejected,
    ):
        raise ResolutionError(f"nothing to verify: state is {observation.quality.state}")
    # A verified value outside the operational envelope is clinically exceptional
    # (§6.2); a verified ordinary value is simply accepted.
    resulting_state = (
        QualityState.accepted
        if locate(observation.canonical.value, entry) is EnvelopePosition.within_operational
        else QualityState.clinically_exceptional_accepted
    )
    return QualityResolution(
        observation=observation.source_identifier,
        kind=ResolutionKind.clinician_verified,
        clinician_id=clinician_id,
        resolved_at=resolved_at,
        resulting_state=resulting_state,
        accepted_via=AcceptedVia.clinician_verified,
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/canon/test_resolution.py -v`
Expected: PASS — 16 tests.

Run: `uv run mypy src/noor/canon`
Expected: `Success: no issues found`.

- [ ] **Step 5: Commit**

```powershell
git add src/noor/canon/resolution.py tests/canon/test_resolution.py
git commit -m "feat(canon): quality resolution — repeat confirmation and clinician verification (SSOT §6.2, §6.5)"
```

---

### Task 12: Fuzzing the boundary

The testing standards are explicit: hypothesis's property is a boundary claim, not a per-case one — **nothing crosses into the engine uncanonicalised**. This task states that claim as a property over arbitrary input, plus determinism (the engine's replay guarantee in §8.4 starts with a deterministic canon).

**Files:**
- Create: `tests/canon/test_properties.py`

**Interfaces:**
- Consumes: everything.
- Produces: the two standing properties. When later modules consume canonical observations, their tests may assume every invariant asserted here.

- [ ] **Step 1: Write the failing test (it should pass immediately — if it fails, an earlier task is wrong)**

`tests/canon/test_properties.py`:
```python
"""Nothing crosses the boundary uncanonicalised (SSOT §3.1, §6).

A boundary claim, not a per-case one: over arbitrary value strings, unit
strings, observables, mapping states, and source statuses, the four-state
contract holds and an accepted observation always has a resolved unit, a
canonical value inside the operational envelope, a status the source has not
withdrawn, and no unexplained passage.
"""

import string
from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from noor.canon.models import (
    ACCEPTED_FAMILY,
    WITHDRAWN_SOURCE_STATUSES,
    MappingInfo,
    MappingStatus,
    QualityState,
    RejectionReason,
    ReportedValue,
    SourceStatus,
    UnitResolution,
)
from noor.canon.pipeline import canonicalise
from noor.canon.plausibility import EnvelopePosition, locate
from noor.catalogue.registry_loader import load_registry
from tests.conftest import REGISTRY_PATH, make_capture

REGISTRY = load_registry(REGISTRY_PATH)
OBSERVABLES = sorted(REGISTRY.entries)

VALUELESS_REJECTIONS = {
    RejectionReason.parse_failure,
    RejectionReason.unit_ambiguous,
    RejectionReason.mapping_unusable,
    RejectionReason.source_status_unusable,
}

value_strings = st.one_of(
    st.decimals(
        min_value=Decimal("-100"), max_value=Decimal("3000"), places=2,
        allow_nan=False, allow_infinity=False,
    ).map(str),
    st.text(alphabet=string.ascii_letters + string.digits + ".,+- \t", max_size=12),
)
unit_strings = st.one_of(
    st.sampled_from(
        ["mmol/L", "mg/dL", "%", "mm[Hg]", "/min", "kg", "Cel", "[degF]",
         "umol/L", "mL/min/{1.73_m2}", "mmol/mol"]
    ),
    st.text(alphabet=string.ascii_letters + string.digits + "/%[]", max_size=10),
)
mapping_statuses = st.sampled_from(list(MappingStatus))
source_statuses = st.sampled_from(list(SourceStatus))
observables = st.sampled_from(OBSERVABLES)


@given(
    observable=observables,
    value=value_strings,
    unit=unit_strings,
    mapping=mapping_statuses,
    status=source_statuses,
)
def test_nothing_crosses_the_boundary_uncanonicalised(observable, value, unit, mapping, status):
    # Arrange
    capture = make_capture(
        observable=observable,
        as_reported=ReportedValue(value=value, unit=unit),
        mapping=MappingInfo(status=mapping),
        source_status=status,
    )

    # Act — canon never raises on data, only on misuse
    result = canonicalise(capture, REGISTRY)

    # Assert
    assert result.as_reported == capture.as_reported  # never mutates (§6.1)
    if result.quality.state in ACCEPTED_FAMILY:
        # §14 step 2: no observation reaches the engine with an unresolved unit
        assert result.canonical is not None
        assert result.quality.unit_resolution is not UnitResolution.ambiguous
        assert result.quality.suspicions == []
        assert result.quality.accepted_via is not None
        # §5: a record the source withdrew never becomes a fact
        assert result.source_status not in WITHDRAWN_SOURCE_STATUSES
        entry = REGISTRY.entry(observable)
        assert locate(result.canonical.value, entry) is EnvelopePosition.within_operational
    if result.quality.state is QualityState.rejected:
        # a valueless rejection never carries a canonical value (§6.3)
        if set(result.quality.rejection_reasons) & VALUELESS_REJECTIONS:
            assert result.canonical is None


@given(observable=observables, value=value_strings, unit=unit_strings)
def test_canonicalise_is_deterministic(observable, value, unit):
    # Arrange
    capture = make_capture(observable=observable, as_reported=ReportedValue(value=value, unit=unit))

    # Act
    first = canonicalise(capture, REGISTRY)
    second = canonicalise(capture, REGISTRY)

    # Assert — replay starts here (§8.4 invariant 6's foundation)
    assert first == second
```

- [ ] **Step 2: Run the properties**

Run: `uv run pytest tests/canon/test_properties.py -v`
Expected: PASS. If either property fails, an earlier task has a bug — find it and fix it there; do not weaken the property.

- [ ] **Step 3: Run the full suite and the full gate set**

Run: `uv run pytest --cov --cov-report=term-missing --cov-fail-under=100`
Expected: all tests pass; coverage on `src/noor` is 100% branch (testing standards:
canon, engine, and catalogue carry that bar). A `# pragma: no cover` will not help —
Task 1 set `exclude_lines = []`. If a line is genuinely unreachable, simplify the
code — do not lower the bar.

Run: `uv run ruff check .`
Expected: `All checks passed!`

Run: `uv run ruff format --check .`
Expected: all files formatted.

Run: `uv run mypy src/noor/canon src/noor/engine src/noor/catalogue`
Expected: `Success: no issues found`.

- [ ] **Step 4: Commit**

```powershell
git add tests/canon/test_properties.py .hypothesis
git commit -m "test(canon): boundary fuzz — nothing crosses uncanonicalised; determinism (SSOT §3.1, §6)"
```

(Commit `.hypothesis/` — the example database is part of the repo per the testing standards. Add it this once; later runs update it as needed.)

---

## Exit verification — SSOT §14 steps 1–3

| §14 verify clause | Proven by |
|---|---|
| Step 1: CI runs green on an empty suite | Task 1 (suite green from the first commit) + Task 2 (`.github/workflows/ci.yml`) |
| Step 1: the import-direction test exists and passes (§4.2) | `tests/test_import_direction.py` (Task 2), green from the first commit |
| Step 1: content changes carry four-eyes approval (§7.5) | Task 2 steps 5–6: `.github/CODEOWNERS` + branch protection with `require_code_owner_reviews`, configured before Task 4 writes any content; the plan's own branch reaches `main` by PR |
| Step 2: no observation reaches the engine with an unresolved unit | `test_nothing_crosses_the_boundary_uncanonicalised` (Task 12) + `test_an_ambiguous_unit_is_a_hard_failure_with_no_canonical_value` (Task 10) |
| Step 2: a real-but-extreme value and a mistyped value land in different states (§6.2) | `test_a_real_but_extreme_value_and_a_mistyped_value_land_in_different_states` (Task 10); `clinically_exceptional_accepted` asserted in Task 11 |
| Step 2 / §13.1 gate 1: source status is read, not merely stored | `test_a_withdrawn_source_record_is_refused`, `test_a_cancelled_source_record_is_refused`, `test_a_corrected_source_record_is_canonicalised_normally` (Task 10) + the status dimension of Task 12's property |
| Step 2: a converted value shows its work (§5, §6.3) | `test_a_declared_conversion_records_the_provenance_of_its_result` (Task 5) + `test_a_converted_value_preserves_the_original_unit_and_shows_its_work` (Task 10) |
| Step 2: a treatment threshold is never a data-entry validator (§6.4) | `test_canon_never_names_a_treatment_threshold` (Task 2, with its teeth proven in step 4) + `test_the_registry_declares_no_treatment_threshold_field` and `test_the_two_envelope_types_are_versioned_independently` (Task 4) |
| Step 2: §12.6 claim 41 — every registry conversion reversible within declared precision, **in both directions** | `test_every_registry_conversion_round_trips_within_declared_precision` and `test_every_registry_conversion_round_trips_from_the_canonical_side` (Task 6) |
| Step 3: like-with-like comparison only | Task 9 (device class, context, setting, window, observable, quality-state exclusions, and current source version) |
| Step 3: a suspicious delta produces `needs_repeat_or_verification` and never mutates a value | `test_a_suspicious_delta_is_flagged_and_recorded` (Task 10) + `test_delta_review_never_mutates_either_observation` (Task 9) |
| §11.9: the delta-check rate is computable — "not compared" is a recorded fact | `DeltaVerdict.comparable` + `NotComparableReason` (Task 3, four validator tests) and the reason asserted on every uncompared case in Task 9 |

After the final task, also run `graphify update .` (AGENTS.md: keep the knowledge graph current after code changes).

## What this plan deliberately does not build

- `engine/` (the evaluator, §8) — next plan, §14 step 4.
- The catalogue compiler and §10.4 gates — §14 step 5.
- The snapshot model (§4.2's closed contract) — arrives with the engine plan.
- Persistence, encryption, access control, the three logs (§2.5, §2.6) — §14 step 7.
- Anything in §11 (visits, obligations, sweep, hatch) — §14 steps 8–13.
- `recorded_at` stamping and the storage of `QualityResolution` folds — the persistence plan.
- Orthostatic-BP pair linking (§6.6: supine/standing readings at one and three
  minutes, linked). The context model carries posture and ordinal now; the link
  itself arrives with the BP measurement-quality workflow (§14 step 14).
- **§6.6's Curated Clinical Signal Set** — the coded, non-quantity signals that
  cross the boundary through canon (symptoms, adherence, adverse-effect reports).
  `ObservableEntry` is quantity-only by construction (canonical UCUM unit,
  numeric envelopes, numeric delta policy), and `canonicalise` would refuse a
  coded signal twice over: `parse_failure` on a non-numeric value and
  `unit_ambiguous` on the absent unit. Adding it needs a schema change, not a
  new entry: a `kind: quantity | coded` discriminator on the registry entry, a
  coded value set per signal, and a `CanonicalCode` alternative to
  `CanonicalQuantity`. Deferred to the plan that has a consumer for it — §7.1's
  symptom-driven rules — so the shape is designed against real rule needs
  (assumption 13).
- **§5.2's `crcl` and equation provenance.** This plan registers `egfr` as a
  quantity observable and separates a reported eGFR from a Noor-derived one by
  `entry_mode` (assumption 14). It does not build three things, each owned by a
  later plan rather than by canon:
  - **`crcl` as a registry observable**, in `mL/min`. It is not interconvertible
    with `egfr` without body-surface area, and no unit check will catch a mix-up —
    UCUM reduces `egfr`'s annotated `mL/min/{1.73_m2}` to plain `mL/min`, so the
    separation rests on the observable identity alone (assumption 14).
    Assumption 14 lists the local-label evidence that
    this is required: ten ingredients in the snapshot state every renal threshold
    in CrCl with no eGFR threshold anywhere in the label. It arrives with the
    first rule that needs it, and adding it is one registry row.
  - **The equation identifier and version a derived value must carry**, with the
    §5.2 guarantee that historical values are never silently recomputed under a
    different equation. That is a property of the append-only store, which makes
    it enforceable rather than aspirational, so it lands with the persistence
    work in §14 step 6.
  - **§10.4 gate 15** — the catalogue compiler refusing a renal-dosing rule that
    omits `renal_metric` or names an eGFR observable where the source label
    specifies creatinine clearance, tested by **§12.6 claim 49** — and **§12.6
    claim 36**, that a CrCl-based
    rule with no weight is `indeterminate` and no eGFR is substituted. Both are
    the catalogue-compiler and rule-engine plans' work; neither is reachable
    while no rule exists.
- **`mapping.confidence`.** §5's mapping record names status, source display, and
  terminology version; a confidence score has no declared type, scale, or
  vocabulary anywhere in the SSOT, and canon has no rule that would read one.
  Adding an uninterpretable number to a closed model is worse than omitting it
  (assumption 12). If a mapping pipeline later produces a score, it arrives with
  the semantics that make it actionable.
- **The immutability half of write-once (§5).** Canon's models are frozen, which
  makes an in-process mutation impossible; nothing here prevents an `UPDATE` on a
  stored row. Append-only enforcement — and therefore the storage side of "a
  correction supersedes rather than overwrites" that `current_versions` reads —
  is the persistence plan's.

### Claims the persistence plan must carry

`QualityResolution` (Task 11) is a record, not a state change: §5 makes
observations write-once, so folding a resolution into effective state belongs to
the store. Two SSOT claims therefore have no test in this plan and must not be
lost:

- **§6.2's repeat-confirmed fold.** An observation whose resolution is
  `repeat_confirmed` presents as `accepted` with `accepted_via:
  repeat_confirmed` and a pointer to the confirming observation — never
  indistinguishable from a value nobody looked at. Task 11 produces exactly the
  record that fold needs (`observation`, `confirming_observation`,
  `resulting_state`, `accepted_via`); the fold itself, and the test that a
  confirmed value is distinguishable from an unremarkable one, are the
  persistence plan's.
- **§11.9's seven capture-quality counters.** Every input they need is written
  here — quality state, `accepted_via`, `DeltaVerdict.comparable`,
  `not_comparable_reason`, `suspicions`, and the resolution records — but the
  counters themselves are queries over stored data, so they are computed where
  the data lives.



