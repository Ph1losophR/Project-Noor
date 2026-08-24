# `catalogue` Loader / Compiler / Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `src/noor/catalogue/` — the loader, compiler, and validator that turn a content directory into a validated `EvaluationContext`, refusing any content that violates SSOT §10.4.

**Architecture:** Seven small modules, each answering one question a bug report asks by name. One schema-only YAML door (`content_yaml.py`) that every content kind passes through; three closed id registries (observables, condition concepts, ingredients) plus a terminology charter that close the string spaces a rule author writes into; per-kind loaders that hand raw documents to the existing `engine` Pydantic models, whose validators *are* the single-rule gates; and one public entry point, `compile_release(content_dir, release_id)`, that runs the cross-file gates and returns the context. Bad content raises at the first gate it trips — there is no partial-success mode.

**Tech Stack:** Python 3.12, uv, Pydantic v2 (`NoorModel`: `frozen=True`, `extra="forbid"`), PyYAML (`SafeLoader` subclass only), pytest + hypothesis, ruff, mypy `--strict`.

**Spec:** `docs/superpowers/specs/2026-08-24-catalogue-loader-compiler-design.md` (approved 2026-08-24).
**SSOT:** `docs/cds-architecture.md`. Where this plan disagrees with the SSOT, the SSOT wins — stop and ask.

Throughout, `§N` cites the SSOT, `spec section N` cites the design note, and `Task N` cites this plan.

## Global Constraints

- **Branch:** all work lands on `design/catalogue-loader-compiler` (already checked out, clean, two commits: `58f7f5d`, `1e5ed76`). Never commit to `main`; the branch reaches `main` through one pull request under the existing `CODEOWNERS` and branch protection.
- **Import direction (§4.2):** `canon <- engine <- catalogue <- app`. `catalogue` may import `canon` and `engine`. Nothing imports `catalogue` except `app`, which does not exist.
- **`catalogue` is the filesystem boundary above `engine`.** `catalogue` reads content files. It acquires **no clock, no HTTP client, no database session** — `compile_release` takes an explicit `release_id` precisely because there is no ordering authority here (spec assumption 4). `canon` and `engine` stay as constrained as they are today: no filesystem, no clock, no I/O.
- **Schema-only YAML (§7.5):** content loads through `_ContentLoader` (a `yaml.SafeLoader` subclass) and nothing else. An object-constructing tag is remote code execution inside the device boundary. No module may call `yaml.load` with any other loader, and no module may call `yaml.unsafe_load` or `yaml.full_load`.
- **Decimal scalars in content YAML are quoted strings.** A YAML float carries binary error into clinical bounds. `value: "30"`, never `value: 30`.
- **`content/` stays clinically clean** (spec decision 4). Only infrastructure content is committed: the two valuesets, the charter, the tenant profile, and an empty release. No rule, threshold, golden case, or citation. Every compiler and cases-harness behaviour is proven against synthetic fixture trees under `tmp_path`.
- **Security-critical constants (§0)** are never modified without explicit user approval. This plan carries exactly one such change — `Snapshot.medications_reconciled_at`, an addition to the §4.2 device-boundary data contract, **approved by the user on 2026-08-24** (spec section 9, amendment 5). Nothing else in §0's list is touched.
- **Testing (`docs/testing-standards.md`):** Arrange-Act-Assert with the comment markers, test names that are sentences describing behaviour, behaviour not implementation, no assertion that an internal function was called. New gate = new failing test first.
- **Coverage is branch coverage at 100% with `exclude_lines = []`.** Every branch this plan adds needs a test. There is no pragma escape.
- **CI's five commands, in order,** are the definition of done for every task:

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

- **ruff line-length is 100.**
- After the last task, run `graphify update .` to refresh the knowledge graph.

---

## Deviations from the spec

Seven places where implementation-level verification found the spec understated, overstated, or mis-stated something. Each is a correction inside the approved mechanism, not a change to it, so none needs re-approval — but each is recorded here so the reviewer sees it.

1. **The renal marker goes on `egfr` only, not on `creatinine`.** Spec section 5.3 and the module-layout comment say "on `egfr` and `creatinine` today". Creatinine is CrCl's *input*, not a renal metric: marking it `crcl` would force a creatinine-delta or AKI rule to declare a metric it does not use, and would bless the exact input-to-metric conflation gate 15 exists to catch. A gate that refuses or mis-shapes correct clinical content is its own safety problem — spec section 6 makes that argument itself, about the coherence gate it declined to add. `crcl` gets its own marker when its registry row lands, which spec section 2 already defers. Both halves of claim 49 stay testable without it: 15a fires on an `egfr` requirement with no `renal_metric`, and 15b compares `Requirement.renal_metric` against `Threshold.states_metric`.

2. **The renal marker requires editing `canon`, not just `catalogue` and `engine`.** Spec section 1 says the diff is `catalogue` plus three `engine` changes. `NoorModel` sets `extra="forbid"` and `load_registry` passes each observable document straight into `ObservableEntry.model_validate`, so a `renal_metric:` key in `registry.yaml` is a **load refusal** until `ObservableEntry` declares the field. The marker is a field on `src/noor/canon/registry.py`. The field is a declarative marker with no clinical bound in it, so §6.4's separation (canon never names a treatment threshold) still holds — `renal_metric` names a *metric identity*, not a decision boundary, and `tests/test_import_direction.py::test_canon_never_names_a_treatment_threshold` passes unchanged because the identifier contains neither "threshold" nor "target_range".

3. **`_resolve_manifest` does *not* already tolerate a valueless usable requirement.** Spec section 9 point 2 says it does. It does not: `engine/evaluate.py:419` is `assert observation is not None  # usable means an observation was selected`, so a *usable* `active_medications` verdict would raise `AssertionError`. Only the *unusable* path tolerates a requirement that populates nothing. Task 5 restructures the loop — unusable decided first, then usable-with-an-observation populates — which removes the assert and makes a valueless usable verdict a no-op. The spec's conclusion is right; its stated reason is wrong.

4. **The stale check cannot reuse `_first_failure`.** Spec section 9 point 2 says a stamp older than `max_age_days` resolves "through `_first_failure`'s existing comparison". `_first_failure` takes a `CanonicalObservation` and there is none. Task 5 writes the comparison inline with the identical `elapsed > timedelta(days=max_age_days)` semantics, so exactly `max_age_days` old stays usable — the same boundary, in a second place, with a test pinning the parity.

5. **The charter needs a `uri` field, and an empty release must be committed.**
   - Gate 17 refuses "a rule citing a code system the charter does not name". No `Rule`, `Expression`, `Requirement`, `Threshold`, or `Citation` field names a code system — the only live code-system citation site in the repo is the observable registry's `code_unit_map` keys (`http://loinc.org|4548-4` on `hba1c_ngsp`, `http://loinc.org|59261-8` on `hba1c_ifcc`). Gate 17 therefore enforces: every system URI appearing in any `code_unit_map` key is named in the charter. Joining on the human name (`system: LOINC`) against the key prefix (`http://loinc.org`) cannot work, so `CodeSystemEntry` carries `uri` beside `system`. Without it the gate either never fires or fires wrongly.
   - Spec section 11 asks for a test that "the real `content/` tree compiles clean", but spec decision 4 commits no profile and no release, and `compile_release` cannot build an `EvaluationContext` without them. Task 10 commits `content/profiles/riyadh-hh.yaml` and `content/releases/rel-2026-09-01.yaml` with **empty** rule and threshold lists. An empty release and a tenant profile carry no clinical claim — no rule, no number, no citation, no approver — so `content/` stays clinically clean and step 6 still adds the first real rule.

6. **The release manifest carries `terminology_version`, which the spec's manifest does not mention.** `Pins` declares six fields and five are `Field(min_length=1)`; `terminology_version` is one of them, and no content file in spec section 4's layout declares it. `compile_release` therefore could not construct an `EvaluationContext` at all without inventing that pin, and a pin the compiler invented would be a pin that lies — §8.2's pins exist so a card rendered last month can be traced to the content that produced it. Task 7 puts the field on `ReleaseDocument`, beside `catalogue_release` and `profile`, which already come from there: a release-level fact on the release-level document. `Profile` needs no equivalent, because `source_family` and `name@version` are already its own fields.

7. **Cleanup 3 reaches one paragraph beyond "Current State".** The spec scopes it to `CLAUDE.md`'s "Current State" section and its stale `docs/superpowers/specs/` pointer. The Testing section's second paragraph — "`canon`'s tests and fixtures exist … everything from rung 2 up does not" — is the same staleness from the same cause, one section lower, and it tells the next agent that the engine tests it is about to edit do not exist. Task 10 step 7 fixes it in the same commit. This is a scope extension of four lines, recorded because it is one.

---

## File Structure

**Created — `src/noor/catalogue/`**

| File | Responsibility |
|---|---|
| `content_yaml.py` | The one schema-only YAML door (§7.5, gate 13). `_ContentLoader` lifted out of `registry_loader.py`, plus `load_mapping` and the two shape-narrowing helpers every per-kind loader needs. |
| `valuesets.py` | `ConditionValueset`, `IngredientValueset` — closed id registries that close the `concept` and `ingredient_id` authoring spaces. |
| `terminology.py` | `CodeSystemEntry`, `TerminologyCharter`, and gate 17's charter check. |
| `loader.py` | Per-kind load: rules, thresholds, profiles, and the release document; plus release assembly. |
| `cases.py` | `CaseRow`, `CaseFile`, and gate 8's boundary-coverage check. |
| `compiler.py` | `compile_release(content_dir, release_id) -> EvaluationContext` — the only public entry point, and the cross-file gates. |

**Modified**

| File | Change |
|---|---|
| `src/noor/catalogue/registry_loader.py` | Imports the shared loader and shape helpers; behaviour unchanged. |
| `src/noor/canon/registry.py` | `ObservableEntry` gains `renal_metric` (deviation 2). |
| `src/noor/engine/content.py` | `Threshold` gains `states_metric`; the no-op `_goal_units_match_threshold_units` deleted (cleanup 1). |
| `src/noor/engine/snapshot.py` | `Snapshot` gains `medications_reconciled_at` (§0 exception, amendment 5). |
| `src/noor/engine/evaluate.py` | `_resolve_requirement` routes `active_medications` to a freshness resolver; `_resolve_manifest` restructured (deviation 3). |
| `src/noor/engine/rules.py` | `ACTIVE_MEDICATIONS` constant; gate 3 and gate 16 validators; gate 12's validator widened to `drug_active` (amendment 7); `_renal_metric_matches_observable` deleted (cleanup 4); `FORBIDDEN_REQUIREMENT_OBSERVABLES` and its denylist validator deleted (cleanup 2). |
| `content/observables/registry.yaml` | `renal_metric: egfr` on the `egfr` entry. |
| `tests/conftest.py` | `make_snapshot` stamps `medications_reconciled_at`; new `make_medication_requirement`; `make_rule` declares the `active_medications` requirement. |
| `tests/test_import_direction.py` | The clock and infrastructure bans extend to `catalogue`; the filesystem ban stays pure-only. |
| `CLAUDE.md`, `AGENTS.md` | "Current State" refreshed (cleanup 3). Edited together, per their footer. |
| `docs/cds-architecture.md` | The seven SSOT amendments (spec section 10). |

**Created — content**

| File | Contents |
|---|---|
| `content/valuesets/conditions.yaml` | Closed condition-concept ids. |
| `content/valuesets/ingredients.yaml` | Closed ingredient ids. |
| `content/terminology/charter.yaml` | LOINC and SNOMED CT licence status. |
| `content/profiles/riyadh-hh.yaml` | The tenant profile (deviation 5). |
| `content/releases/rel-2026-09-01.yaml` | An empty release (deviation 5). |

**Created — tests**

`tests/catalogue/` already exists as a package (`__init__.py`, `test_registry_loader.py`). This plan adds `conftest.py` (the valid fixture content tree), `test_content_yaml.py`, `test_valuesets.py`, `test_terminology.py`, `test_loader.py`, `test_cases.py`, `test_compiler.py`, and `test_content_tree.py` — the last being the only test that reads the committed `content/` directory rather than a tree under `tmp_path`.

---

## Task Order and Why

The order is forced in three places, and getting it wrong breaks the suite:

- **Task 5 must precede Task 6.** Task 6 adds the `active_medications` requirement to `make_rule`'s default. If the snapshot stamp and the resolution branch do not exist yet, every engine test degrades to `indeterminate`.
- **Cleanup 2 must land inside Task 9, not earlier.** Deleting the gate-11 denylist before the compiler's allowlist replaces it would ship a commit with gate 11 unenforced. The validator, its constant, and its test move together in Task 9's step 1 — splitting them across tasks either leaves the gate unenforced or leaves the validator's `raise` branch uncovered.
- **Tasks 1–3 precede Task 9.** The compiler composes all of them.

Tasks 1–4 are independent of each other and of 5–6.

---

### Task 1: The schema-only YAML door

Gate 13 is not a property any one loader can hold. It holds because exactly one module calls `yaml.load`, and every per-kind loader above reaches YAML through the three helpers here. `_ContentLoader` moves out of `registry_loader.py` verbatim.

**Files:**
- Create: `src/noor/catalogue/content_yaml.py`
- Modify: `src/noor/catalogue/registry_loader.py:1-57`
- Test: `tests/catalogue/test_content_yaml.py`

**Interfaces:**
- Consumes: nothing.
- Produces — the only YAML surface Tasks 2, 3, 7, 8, 9 may use:
  - `load_mapping(path: Path) -> dict[str, Any]`
  - `require_list(path: Path, document: dict[str, Any], key: str) -> list[Any]`
  - `require_mapping_items(path: Path, items: list[Any], id_key: str, noun: str) -> dict[str, dict[str, Any]]`
  - `_ContentLoader` stays private. Nothing outside this module imports `yaml`.

- [ ] **Step 1: Write the failing test**

Create `tests/catalogue/test_content_yaml.py`:

```python
"""The one schema-only YAML door every content kind passes through (SSOT §7.5).

Gate 13 holds because there is exactly one `yaml.load` call in the tree and
every per-kind loader reaches it through these three helpers. Stated once here,
relied on by `test_loader.py`, `test_valuesets.py`, and `test_terminology.py`.
"""

from pathlib import Path

import pytest
from yaml.constructor import ConstructorError

from noor.catalogue.content_yaml import load_mapping, require_list, require_mapping_items


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "content.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_a_well_formed_mapping_loads(tmp_path):
    # Arrange
    path = _write(tmp_path, "rules:\n  - id: metformin-egfr\n")

    # Act
    document = load_mapping(path)

    # Assert
    assert document == {"rules": [{"id": "metformin-egfr"}]}


def test_an_object_constructing_tag_is_refused_at_the_shared_door(tmp_path):
    # Arrange — §7.5, §12.6 claim 21: one tag is remote code execution inside the
    # device boundary, so the door refuses rather than warns, and no object is
    # constructed on the way to the refusal
    side_effect = tmp_path / "owned.txt"
    path = _write(
        tmp_path,
        f"rules: !!python/object/apply:builtins.open ['{side_effect.as_posix()}', 'w']\n",
    )

    # Act / Assert
    with pytest.raises(ConstructorError):
        load_mapping(path)
    assert not side_effect.exists()


def test_a_repeated_mapping_key_is_refused(tmp_path):
    # Arrange — stock PyYAML keeps the last of two identical keys silently, so
    # the approver signs one document and a different one runs
    path = _write(tmp_path, "rule:\n  severity: passive_task\n  severity: stop_and_review\n")

    # Act / Assert
    with pytest.raises(ConstructorError, match="duplicate keys: severity"):
        load_mapping(path)


def test_a_document_that_is_not_a_mapping_names_the_offending_file(tmp_path):
    # Arrange — a content author's error must say which file to open
    path = _write(tmp_path, "- one\n- two\n")

    # Act / Assert
    with pytest.raises(ValueError, match=r"content\.yaml: expected a top-level mapping"):
        load_mapping(path)


@pytest.mark.parametrize(
    "body",
    ["other: []\n", "rules: {}\n"],
    ids=["absent", "not-a-list"],
)
def test_a_missing_or_mistyped_top_level_list_names_the_key(tmp_path, body):
    # Arrange
    path = _write(tmp_path, body)

    # Act / Assert
    with pytest.raises(ValueError, match=r"content\.yaml: expected a top-level 'rules' list"):
        require_list(path, load_mapping(path), "rules")


def test_identified_items_come_back_keyed_by_their_id(tmp_path):
    # Arrange
    path = _write(tmp_path, "rules:\n  - {id: a, severity: passive_task}\n  - {id: b}\n")

    # Act
    items = require_mapping_items(
        path, require_list(path, load_mapping(path), "rules"), "id", "rule"
    )

    # Assert
    assert items == {"a": {"id": "a", "severity": "passive_task"}, "b": {"id": "b"}}


@pytest.mark.parametrize(
    "body",
    [
        "rules:\n  - just_a_string\n",
        "rules:\n  - {severity: passive_task}\n",
        "rules:\n  - {id: 7}\n",
    ],
    ids=["not-a-mapping", "no-id", "id-is-not-a-string"],
)
def test_an_item_that_is_not_an_identified_mapping_is_refused(tmp_path, body):
    # Arrange — gate 12 closes *string* id spaces, so a non-string id must not
    # become a dictionary key that silently never matches anything
    path = _write(tmp_path, body)

    # Act / Assert
    with pytest.raises(ValueError, match=r"content\.yaml: every rule must be a mapping"):
        require_mapping_items(path, require_list(path, load_mapping(path), "rules"), "id", "rule")


def test_two_items_sharing_an_id_are_refused(tmp_path):
    # Arrange — one id, two documents: the review saw both, only one would run
    path = _write(tmp_path, "rules:\n  - {id: a, severity: passive_task}\n  - {id: a}\n")

    # Act / Assert
    with pytest.raises(ValueError, match="duplicate rule 'a'"):
        require_mapping_items(path, require_list(path, load_mapping(path), "rules"), "id", "rule")
```

- [ ] **Step 2: Run the test and watch it fail**

```bash
uv run pytest tests/catalogue/test_content_yaml.py -q
```

Expected: collection error — `ModuleNotFoundError: No module named 'noor.catalogue.content_yaml'`.

- [ ] **Step 3: Write the module**

Create `src/noor/catalogue/content_yaml.py`. `_ContentLoader` is `registry_loader.py:18-38` moved without edit:

```python
"""The one schema-only YAML door every content kind passes through (SSOT §7.5).

Gate 13 ("all content loads through the schema-only loader") is not a property
any single loader can hold. It holds because exactly one module calls
`yaml.load`, and every per-kind loader above reaches YAML through the three
helpers here. An object-constructing tag is remote code execution inside the
device boundary, so the loader refuses rather than warns.

Decimal scalars in content files are quoted strings, so they load exactly — a
YAML float would carry binary error into clinical bounds.
"""

from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode


class _ContentLoader(yaml.SafeLoader):
    """The `SafeLoader` subclass §7.5 allows, refusing a repeated mapping key.

    Stock PyYAML keeps the last of two identical keys and says nothing. A content
    file with two `physiologic:` blocks would then load bounds the approver did
    not sign off on, while the pull-request diff showed both — defeating §7.5's
    claim that the four-eyes review sees what runs.
    """

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        mapping = super().construct_mapping(node, deep=deep)
        if len(mapping) != len(node.value):
            keys = [self.construct_object(key_node, deep=deep) for key_node, _ in node.value]
            repeated = sorted({str(key) for key in keys if keys.count(key) > 1})
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate keys: {', '.join(repeated)}",
                node.start_mark,
            )
        return mapping


def load_mapping(path: Path) -> dict[str, Any]:
    """Load one content file, refusing anything but a top-level mapping."""
    with path.open(encoding="utf-8") as content:
        document = yaml.load(content, _ContentLoader)
    if not isinstance(document, dict):
        raise ValueError(f"{path}: expected a top-level mapping")
    return document


def require_list(path: Path, document: dict[str, Any], key: str) -> list[Any]:
    """Read `key` off an already-loaded document, refusing anything but a list."""
    value = document.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{path}: expected a top-level {key!r} list")
    return value


def require_mapping_items(
    path: Path, items: list[Any], id_key: str, noun: str
) -> dict[str, dict[str, Any]]:
    """Key `items` by their id, refusing an unidentified item or a repeated id."""
    entries: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get(id_key), str):
            raise ValueError(f"{path}: every {noun} must be a mapping carrying {id_key!r}")
        identifier: str = item[id_key]
        if identifier in entries:
            raise ValueError(f"{path}: duplicate {noun} {identifier!r}")
        entries[identifier] = item
    return entries
```

- [ ] **Step 4: Run the test and watch it pass**

```bash
uv run pytest tests/catalogue/test_content_yaml.py -q
```

Expected: 11 passed.

- [ ] **Step 5: Route `registry_loader` through the shared door**

Replace the whole of `src/noor/catalogue/registry_loader.py` with:

```python
"""Loads registry content into validated models (SSOT §7.4).

Schema-only YAML (§7.5) is `content_yaml`'s job, not this module's: everything
here reaches a file through that one door.
"""

from pathlib import Path

from noor.canon.registry import ObservableRegistry
from noor.catalogue.content_yaml import load_mapping, require_list, require_mapping_items


def load_registry(path: Path) -> ObservableRegistry:
    """Load and validate an observable registry file (content/observables/registry.yaml)."""
    document = load_mapping(path)
    observables = require_list(path, document, "observables")
    entries = require_mapping_items(path, observables, "observable", "observable")
    return ObservableRegistry.model_validate({"entries": entries})
```

The four existing refusal tests in `tests/catalogue/test_registry_loader.py` keep passing unedited: the hostile tag and duplicate key still raise `ConstructorError`; `not_observables: []` now trips `require_list`; the duplicate-id message still contains "duplicate"; and the unidentified-entry message still reads `registry.yaml: every observable …`, which is what `test_an_entry_that_is_not_an_identified_mapping_names_the_offending_file` matches on.

- [ ] **Step 6: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Expected: all green, 100% branch coverage. If `content_yaml.py` shows a partial branch, a case above is missing — add it rather than reaching for a pragma.

- [ ] **Step 7: Commit**

```bash
git add src/noor/catalogue/content_yaml.py src/noor/catalogue/registry_loader.py \
        tests/catalogue/test_content_yaml.py
git commit -m "feat(catalogue): one schema-only YAML door for all content kinds

Gate 13 becomes structural: exactly one module calls yaml.load, and every
per-kind loader reaches it through load_mapping/require_list/
require_mapping_items. _ContentLoader moves out of registry_loader unchanged."
```

---

### Task 2: The closed condition and ingredient id spaces

Gate 12 refuses "an unknown observable, concept, or ingredient id". The registry already closes observables. These two files close the other two, and they are the join targets Task 9 checks `Expression.concept`, `Expression.ingredient_id`, and `OrderBlock.order_of` against.

**Files:**
- Create: `src/noor/catalogue/valuesets.py`
- Create: `content/valuesets/conditions.yaml`
- Create: `content/valuesets/ingredients.yaml`
- Test: `tests/catalogue/test_valuesets.py`

**Interfaces:**
- Consumes: `content_yaml.load_mapping`, `require_list`, `require_mapping_items` (Task 1).
- Produces:
  - `ConditionValueset(ids: frozenset[str])` and `IngredientValueset(ids: frozenset[str])` — distinct types so `--strict` refuses passing one where the other belongs, both carrying only `ids`.
  - `load_conditions(path: Path) -> ConditionValueset`
  - `load_ingredients(path: Path) -> IngredientValueset`
  - Task 9 reads membership as `concept in conditions.ids`.

- [ ] **Step 1: Write the failing test**

Create `tests/catalogue/test_valuesets.py`:

```python
"""The two closed id spaces a rule author writes into (SSOT §10.4 gate 12).

The observable registry closes the third. Without these, `concept: dibetes` is
a rule that silently never fires — the failure mode gate 12 exists to prevent.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from noor.catalogue.valuesets import (
    ConditionValueset,
    IngredientValueset,
    load_conditions,
    load_ingredients,
)

CONDITIONS_PATH = Path("content/valuesets/conditions.yaml")
INGREDIENTS_PATH = Path("content/valuesets/ingredients.yaml")


def test_the_committed_condition_valueset_loads_and_closes_its_ids():
    # Arrange / Act
    valueset = load_conditions(CONDITIONS_PATH)

    # Assert
    assert "type_2_diabetes" in valueset.ids
    assert "on_dialysis" in valueset.ids
    assert "dibetes" not in valueset.ids


def test_the_committed_ingredient_valueset_loads_and_closes_its_ids():
    # Arrange / Act
    valueset = load_ingredients(INGREDIENTS_PATH)

    # Assert
    assert "metformin" in valueset.ids
    assert "metfromin" not in valueset.ids


def test_a_valueset_entry_carries_a_label_for_the_four_eyes_review(tmp_path):
    # Arrange — §7.5: an approver reading `- on_dialysis` learns nothing, so the
    # committed shape is a mapping and the label rides beside the id
    path = tmp_path / "conditions.yaml"
    path.write_text(
        "concepts:\n  - {concept: on_dialysis, label: Receiving dialysis}\n",
        encoding="utf-8",
    )

    # Act
    valueset = load_conditions(path)

    # Assert
    assert valueset.ids == frozenset({"on_dialysis"})


@pytest.mark.parametrize(
    "identifier",
    ["Type2Diabetes", "type-2-diabetes", "2_diabetes", ""],
    ids=["camel-case", "kebab-case", "leading-digit", "empty"],
)
def test_an_id_outside_lower_snake_case_is_refused(identifier):
    # Arrange / Act / Assert — the id space is closed *and* shaped, so a
    # near-miss spelling cannot enter it from either side of a merge
    with pytest.raises(ValidationError, match="lower snake_case"):
        ConditionValueset(ids=frozenset({identifier}))


def test_the_two_valuesets_are_distinct_types():
    # Arrange / Act — mypy --strict is the real guard; this pins the runtime
    # half so a later merge of the two classes fails here
    conditions = ConditionValueset(ids=frozenset({"on_dialysis"}))
    ingredients = IngredientValueset(ids=frozenset({"metformin"}))

    # Assert
    assert not isinstance(conditions, IngredientValueset)
    assert not isinstance(ingredients, ConditionValueset)


def test_a_repeated_concept_id_is_refused(tmp_path):
    # Arrange
    path = tmp_path / "conditions.yaml"
    path.write_text(
        "concepts:\n  - {concept: on_dialysis}\n  - {concept: on_dialysis}\n",
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(ValueError, match="duplicate concept 'on_dialysis'"):
        load_conditions(path)


def test_a_repeated_ingredient_id_is_refused(tmp_path):
    # Arrange
    path = tmp_path / "ingredients.yaml"
    path.write_text(
        "ingredients:\n  - {ingredient: metformin}\n  - {ingredient: metformin}\n",
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(ValueError, match="duplicate ingredient 'metformin'"):
        load_ingredients(path)
```

- [ ] **Step 2: Run the test and watch it fail**

```bash
uv run pytest tests/catalogue/test_valuesets.py -q
```

Expected: `ModuleNotFoundError: No module named 'noor.catalogue.valuesets'`.

- [ ] **Step 3: Write the module**

Create `src/noor/catalogue/valuesets.py`:

```python
"""The closed id spaces a rule author writes into (SSOT §10.4 gate 12).

Three string spaces reach the engine from authored content: observables,
condition concepts, and ingredients. The observable registry (§6.6) closes the
first. These close the other two. An open space is not a typo risk — it is a
rule that loads, passes review, and silently never fires.

Two types, not one: `--strict` then refuses a condition valueset where an
ingredient valueset belongs, which is the mix-up a compiler with two identical
frozensets cannot see.
"""

import re
from pathlib import Path

from pydantic import field_validator

from noor.canon.model import NoorModel
from noor.catalogue.content_yaml import load_mapping, require_list, require_mapping_items

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class _Valueset(NoorModel):
    """A closed set of authored ids, shaped like every other id in the tree."""

    ids: frozenset[str]

    @field_validator("ids", mode="after")
    @classmethod
    def _ids_are_lower_snake_case(cls, value: frozenset[str]) -> frozenset[str]:
        malformed = sorted(entry for entry in value if not _ID_PATTERN.match(entry))
        if malformed:
            raise ValueError(f"valueset ids are lower snake_case: {malformed}")
        return value


class ConditionValueset(_Valueset):
    """The closed space `Expression.concept` may name."""


class IngredientValueset(_Valueset):
    """The closed space `Expression.ingredient_id` and `OrderBlock.order_of` may name."""


def load_conditions(path: Path) -> ConditionValueset:
    """Load the condition-concept valueset (content/valuesets/conditions.yaml)."""
    concepts = require_list(path, load_mapping(path), "concepts")
    return ConditionValueset(ids=frozenset(require_mapping_items(path, concepts, "concept", "concept")))


def load_ingredients(path: Path) -> IngredientValueset:
    """Load the ingredient valueset (content/valuesets/ingredients.yaml)."""
    ingredients = require_list(path, load_mapping(path), "ingredients")
    return IngredientValueset(
        ids=frozenset(require_mapping_items(path, ingredients, "ingredient", "ingredient"))
    )
```

Note: `load_conditions`'s return line is 101 characters. Split it the way `load_ingredients` is split — ruff's line-length is 100 and `ruff format` will not do it for you inside a call chain.

- [ ] **Step 4: Write the two content files**

`content/valuesets/conditions.yaml`:

```yaml
# The closed condition-concept space (SSOT §10.4 gate 12).
#
# A concept id names a patient state a rule may test with `op: condition`. It is
# not a diagnosis code and carries no clinical claim — the mapping from a coded
# problem list to these ids belongs to the app layer (§11), which does not exist.
# The label exists for the four-eyes review (§7.5): a reviewer reading a bare id
# cannot tell whether it is the concept the rule meant.
concepts:
  - concept: type_2_diabetes
    label: Type 2 diabetes mellitus
  - concept: type_1_diabetes
    label: Type 1 diabetes mellitus
  - concept: hypertension
    label: Essential hypertension
  - concept: chronic_kidney_disease
    label: Chronic kidney disease
  - concept: on_dialysis
    label: Receiving dialysis
  - concept: pregnant
    label: Pregnant
  - concept: breastfeeding
    label: Breastfeeding
```

`content/valuesets/ingredients.yaml`:

```yaml
# The closed ingredient space (SSOT §10.4 gate 12).
#
# An ingredient id names a drug substance a rule may test with `op: drug_active`
# or `op: drug_requested`, or block with `then.blocks.order_of`. Every id here
# is listed in docs/research/saudi-essential-medicines-list-2023.md, which is
# authoritative for exactly that: whether an ingredient is listed. No strength,
# no dose form, no clinical claim — those live in the SPC pin a rule's citation
# carries (§7.3), and no rule exists yet.
#
# `drug_scope_level: ingredient` is the only level v1 supports (§7.1(e)), so
# these ids are the whole drug vocabulary a v1 rule can reach.
ingredients:
  - ingredient: metformin
    label: Metformin
  - ingredient: gliclazide
    label: Gliclazide
  - ingredient: insulin_glargine
    label: Insulin glargine
  - ingredient: enalapril
    label: Enalapril
  - ingredient: amlodipine
    label: Amlodipine
  - ingredient: spironolactone
    label: Spironolactone
  - ingredient: amoxicillin
    label: Amoxicillin
  - ingredient: penicillin
    label: Penicillin
```

- [ ] **Step 5: Run the test and watch it pass**

```bash
uv run pytest tests/catalogue/test_valuesets.py -q
```

Expected: 12 passed.

- [ ] **Step 6: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add src/noor/catalogue/valuesets.py tests/catalogue/test_valuesets.py \
        content/valuesets/conditions.yaml content/valuesets/ingredients.yaml
git commit -m "feat(catalogue): closed condition and ingredient id spaces

Gate 12's other two string spaces. An open space is not a typo risk — it is a
rule that loads, passes four-eyes review, and silently never fires. Two types
rather than one so --strict catches a condition/ingredient mix-up."
```

---

### Task 3: The terminology charter

Gate 17 refuses a rule citing a code system the charter does not name. Deviation 5 establishes what "citing" means in this repo today: the observable registry's `code_unit_map` keys are the only live code-system citations, so the charter is joined to them by URI.

**Files:**
- Create: `src/noor/catalogue/terminology.py`
- Create: `content/terminology/charter.yaml`
- Test: `tests/catalogue/test_terminology.py`

**Interfaces:**
- Consumes: `content_yaml` helpers (Task 1); `noor.canon.registry.ObservableRegistry`.
- Produces:
  - `CodeSystemEntry(system: str, uri: str, licensed: bool, note: str)`
  - `TerminologyCharter(code_systems: tuple[CodeSystemEntry, ...])`
  - `load_charter(path: Path) -> TerminologyCharter`
  - `check_code_systems_are_chartered(charter: TerminologyCharter, registry: ObservableRegistry) -> None` — raises `ValueError` naming every uncharted URI. Task 9 calls it and lets the raise through.

**Deliberately not enforced:** `licensed: false` does not fail the build. §10.4 gate 17 refuses a system the charter does not *name*; it says nothing about licence state, and a gate that blocks a merge on a fact the SSOT never made blocking is a gate nobody can predict. The field is recorded because §7.5's review needs to see it, and because a licence lapse is a content incident (§11.9), not a compile error.

- [ ] **Step 1: Write the failing test**

Create `tests/catalogue/test_terminology.py`:

```python
"""The terminology charter and gate 17 (SSOT §10.4).

The registry's `code_unit_map` keys are the repo's only live code-system
citations: `http://loinc.org|4548-4` on hba1c_ngsp, `http://loinc.org|59261-8`
on hba1c_ifcc. Gate 17 joins those URIs to the charter, which is why a charter
entry carries a `uri` beside its human `system` name — "LOINC" does not join to
"http://loinc.org".
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from noor.catalogue.registry_loader import load_registry
from noor.catalogue.terminology import (
    CodeSystemEntry,
    TerminologyCharter,
    check_code_systems_are_chartered,
    load_charter,
)
from tests.conftest import REGISTRY_PATH

CHARTER_PATH = Path("content/terminology/charter.yaml")


def test_the_committed_charter_loads_and_names_loinc_with_its_uri():
    # Arrange / Act
    charter = load_charter(CHARTER_PATH)

    # Assert
    loinc = next(entry for entry in charter.code_systems if entry.system == "LOINC")
    assert loinc.uri == "http://loinc.org"
    assert loinc.note


def test_the_committed_charter_covers_every_system_the_real_registry_cites():
    # Arrange
    charter = load_charter(CHARTER_PATH)
    registry = load_registry(REGISTRY_PATH)

    # Act / Assert — gate 17 on the content that actually ships
    check_code_systems_are_chartered(charter, registry)


def test_a_registry_citing_an_uncharted_system_is_refused(tmp_path):
    # Arrange — the same registry shape, citing a system nobody chartered
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text(
        "observables:\n"
        "  - observable: glucose\n"
        "    owner: endocrinology\n"
        '    canonical_ucum: "mmol/L"\n'
        '    accepted_units: ["mmol/L"]\n'
        '    code_unit_map: {"http://example.org/private|G1": "mmol/L"}\n'
        '    physiologic: {low: "0.5", high: "60", version: v1}\n'
        '    operational: {low: "1", high: "40", version: v1}\n'
        "    delta_policy: {window_hours: 24, absolute: null, relative: null,"
        " compare_context: []}\n"
        '    repeat_tolerance: "0.1"\n',
        encoding="utf-8",
    )
    charter = load_charter(CHARTER_PATH)

    # Act / Assert
    with pytest.raises(ValueError, match=r"gate 17.*example\.org/private"):
        check_code_systems_are_chartered(charter, load_registry(registry_path))


def test_a_charter_entry_needs_a_uri_a_system_name_and_a_note():
    # Arrange / Act / Assert — an entry with no note is a licence claim nobody
    # can review (§7.5), and one with no uri cannot be joined to anything
    with pytest.raises(ValidationError):
        CodeSystemEntry(system="LOINC", uri="http://loinc.org", licensed=True, note="")


def test_a_charter_with_no_code_systems_is_refused():
    # Arrange / Act / Assert — an empty charter would pass gate 17 vacuously
    with pytest.raises(ValidationError):
        TerminologyCharter(code_systems=())


def test_two_charter_entries_sharing_a_uri_are_refused(tmp_path):
    # Arrange — two licence answers for one system, and no way to say which won
    path = tmp_path / "charter.yaml"
    path.write_text(
        "code_systems:\n"
        "  - {system: LOINC, uri: 'http://loinc.org', licensed: true, note: first}\n"
        "  - {system: LOINC copy, uri: 'http://loinc.org', licensed: false, note: second}\n",
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(ValueError, match="duplicate code system"):
        load_charter(path)


def test_an_unlicensed_system_still_passes_the_gate(tmp_path):
    # Arrange — gate 17 refuses a system the charter does not NAME. A licence
    # lapse is a content incident (§11.9), not a compile error, so this loads.
    path = tmp_path / "charter.yaml"
    path.write_text(
        "code_systems:\n"
        "  - {system: LOINC, uri: 'http://loinc.org', licensed: false,"
        " note: renewal outstanding}\n",
        encoding="utf-8",
    )

    # Act
    charter = load_charter(path)

    # Assert
    check_code_systems_are_chartered(charter, load_registry(REGISTRY_PATH))
    assert charter.code_systems[0].licensed is False
```

- [ ] **Step 2: Run the test and watch it fail**

```bash
uv run pytest tests/catalogue/test_terminology.py -q
```

Expected: `ModuleNotFoundError: No module named 'noor.catalogue.terminology'`.

- [ ] **Step 3: Write the module**

Create `src/noor/catalogue/terminology.py`:

```python
"""The terminology charter and §10.4 gate 17.

A code system carries a licence, and §7.5's four-eyes review has to be able to
see which systems the content leans on and on what terms. The charter is that
list. Gate 17 refuses content citing a system the charter does not name.

Citation sites, today: the observable registry's `code_unit_map` keys, which are
`system|code` with the system half a URI (§6.6). No `Rule`, `Expression`,
`Requirement`, `Threshold`, or `Citation` field names a code system, so this is
the whole join — and it is why an entry carries `uri` beside `system`: the
human name "LOINC" does not join to "http://loinc.org".
"""

from pathlib import Path

from pydantic import Field

from noor.canon.model import NoorModel
from noor.canon.registry import ObservableRegistry
from noor.catalogue.content_yaml import load_mapping, require_list, require_mapping_items


class CodeSystemEntry(NoorModel):
    """One code system the content is permitted to cite, and on what terms."""

    system: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    licensed: bool
    note: str = Field(min_length=1)


class TerminologyCharter(NoorModel):
    """Every code system the content may cite (SSOT §10.4 gate 17)."""

    code_systems: tuple[CodeSystemEntry, ...] = Field(min_length=1)


def load_charter(path: Path) -> TerminologyCharter:
    """Load the terminology charter (content/terminology/charter.yaml)."""
    systems = require_list(path, load_mapping(path), "code_systems")
    entries = require_mapping_items(path, systems, "uri", "code system")
    return TerminologyCharter.model_validate({"code_systems": tuple(entries.values())})


def check_code_systems_are_chartered(
    charter: TerminologyCharter, registry: ObservableRegistry
) -> None:
    """Refuse any code system the content cites and the charter does not name."""
    chartered = {entry.uri for entry in charter.code_systems}
    cited = {
        key.split("|", 1)[0]
        for entry in registry.entries.values()
        for key in entry.code_unit_map
    }
    uncharted = sorted(cited - chartered)
    if uncharted:
        raise ValueError(
            f"content cites code systems the terminology charter does not name "
            f"(§10.4 gate 17): {uncharted}"
        )
```

- [ ] **Step 4: Write the charter**

`content/terminology/charter.yaml`:

```yaml
# Every code system the content may cite (SSOT §10.4 gate 17).
#
# `uri` is the join key: the registry's code_unit_map keys are `system|code`
# with the system half a URI, and "LOINC" does not join to "http://loinc.org".
# `licensed` is recorded, not enforced — gate 17 refuses a system the charter
# does not NAME. A licence that lapses is a content incident under §11.9, and a
# build that fails on a fact the SSOT never made blocking is a build nobody can
# predict.
code_systems:
  - system: LOINC
    uri: http://loinc.org
    licensed: true
    note: >-
      Regenstrief's licence permits use in clinical software at no fee under
      registration. Cited today by the two HbA1c observables' code_unit_map
      entries, which are the registry's only coded unit hints.
  - system: SNOMED CT
    uri: http://snomed.info/sct
    licensed: true
    note: >-
      Covered by Saudi Arabia's SNOMED International member licence. Nothing
      cites it yet — condition concepts are local ids (content/valuesets/
      conditions.yaml) and the coded-problem-list mapping belongs to the app
      layer (§11), which does not exist.
```

- [ ] **Step 5: Run the test and watch it pass**

```bash
uv run pytest tests/catalogue/test_terminology.py -q
```

Expected: 7 passed.

- [ ] **Step 6: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

- [ ] **Step 7: Commit**

```bash
git add src/noor/catalogue/terminology.py tests/catalogue/test_terminology.py \
        content/terminology/charter.yaml
git commit -m "feat(catalogue): terminology charter and gate 17

Gate 17 joins the registry's code_unit_map system URIs to a charter of the code
systems the content may cite. Entries carry uri beside the human system name,
because 'LOINC' does not join to 'http://loinc.org'. Licence state is recorded,
not enforced — §10.4 makes naming blocking, not licensing."
```

---

### Task 4: The renal-metric marker, and one dead validator removed

Gate 15 has two halves. 15a — "a renal-dosing rule omits `renal_metric`" — needs a way to know which observables *are* renal metrics, which is a fact about the observable, so it lives on the registry entry. 15b — "names an eGFR observable in a rule whose source label specifies creatinine clearance" — needs the threshold to say which metric its source stated, which is a fact about the cited document, so it lives on `Threshold`. Neither belongs on `Requirement`, which is why cleanup 4's validator (Task 6) is wrong and goes.

Read **deviations 1 and 2** before starting: the marker goes on `egfr` only, and it is a `canon` field.

**Files:**
- Modify: `src/noor/canon/registry.py:107-118` (field), `:129-163` (validator)
- Modify: `content/observables/registry.yaml:137` (the `egfr` entry)
- Modify: `src/noor/engine/content.py:63-84` (field), `:297-307` (delete)
- Test: `tests/canon/test_registry.py`, `tests/engine/test_content.py`

**Interfaces:**
- Produces:
  - `ObservableEntry.renal_metric: Literal["egfr", "crcl"] | None = None`
  - `Threshold.states_metric: Literal["egfr", "crcl"] | None = None`
  - Task 9's gate 15a reads `registry.entry(obs).renal_metric`; its 15b compares `Requirement.renal_metric` against `Threshold.states_metric`.
- Consumes: nothing.

- [ ] **Step 1: Write the failing canon test**

Append to `tests/canon/test_registry.py`:

```python
def test_an_observable_may_declare_itself_a_renal_metric():
    # Arrange / Act — gate 15a needs to know which observables ARE renal
    # metrics, and that is a fact about the observable, not about any rule
    entry = make_entry(observable="egfr", renal_metric="egfr")

    # Assert
    assert entry.renal_metric == "egfr"


def test_an_observable_declares_no_renal_metric_by_default():
    # Arrange / Act — most observables are not renal metrics, and the marker is
    # opt-in: a missing marker is "not a renal metric", never "unknown"
    entry = make_entry(observable="potassium")

    # Assert
    assert entry.renal_metric is None


def test_a_renal_metric_outside_the_closed_pair_is_refused():
    # Arrange / Act / Assert — §5.2 knows two renal metrics; a third would be a
    # metric nothing downstream can reason about
    with pytest.raises(ValidationError):
        make_entry(observable="cystatin_c", renal_metric="cystatin_c")


def test_the_real_registry_marks_egfr_and_nothing_else_as_a_renal_metric():
    # Arrange / Act — creatinine is CrCl's INPUT, not a renal metric: marking it
    # would force a creatinine-delta rule to declare a metric it does not use,
    # and would bless the input-to-metric conflation gate 15 exists to catch
    registry = load_registry(REGISTRY_PATH)

    # Assert
    marked = {
        observable
        for observable, entry in registry.entries.items()
        if entry.renal_metric is not None
    }
    assert marked == {"egfr"}
    assert registry.entry("egfr").renal_metric == "egfr"
```

`tests/canon/test_registry.py` already imports `pytest`, `ValidationError`, and `make_entry`. It does not import `load_registry` or `REGISTRY_PATH` — add `from noor.catalogue.registry_loader import load_registry` and `from tests.conftest import REGISTRY_PATH` to the existing import block, matching how `tests/catalogue/test_registry_loader.py` does it. If the file's existing imports already cover them, leave them alone.

- [ ] **Step 2: Run the test and watch it fail**

```bash
uv run pytest tests/canon/test_registry.py -q -k renal
```

Expected: FAIL — `ValidationError: renal_metric — Extra inputs are not permitted`, from `NoorModel`'s `extra="forbid"`. This is deviation 2 demonstrating itself.

- [ ] **Step 3: Add the field to `ObservableEntry`**

In `src/noor/canon/registry.py`, add after `required_method` (line 118):

```python
    required_method: tuple[str, ...] = ()
    renal_metric: Literal["egfr", "crcl"] | None = None
```

Add `Literal` to the `typing` import if it is not already there. And extend the class docstring's second paragraph, so the next reader does not mistake this for a threshold:

```python
    """One observable's data-validity declaration (SSOT §6.6).

    Quantity observables only (assumption 13): §6.6's Curated Clinical Signal Set
    has no canonical unit and no envelopes, and is not modelled here. Nothing in
    this schema is a treatment threshold — §6.4's three boundary types are
    separate, and there is deliberately nowhere here to put a clinical decision
    boundary.

    `renal_metric` is a metric *identity*, not a boundary: it says this
    observable is one of §5.2's two renal metrics, so §10.4 gate 15a can tell
    that a rule requiring it is a renal-dosing rule. It carries no number and
    names no threshold.
    """
```

- [ ] **Step 4: Mark `egfr` in the real registry**

In `content/observables/registry.yaml`, add one line to the `egfr` entry (around line 137), beside `owner`:

```yaml
  - observable: egfr
    owner: nephrology
    renal_metric: egfr
```

Do not touch `creatinine`. Do not touch `canonical_ucum: "mL/min/{1.73_m2}"` — the braces are load-bearing UCUM annotation syntax.

- [ ] **Step 5: Run the canon test and watch it pass**

```bash
uv run pytest tests/canon/test_registry.py tests/catalogue -q
```

Expected: all pass.

- [ ] **Step 6: Write the failing `Threshold` test**

Append to `tests/engine/test_content.py`:

```python
def test_a_threshold_may_state_which_renal_metric_its_source_specified():
    # Arrange / Act — gate 15b compares the metric a rule uses against the one
    # the cited document specified, so the threshold has to carry it. §5.2: an
    # eGFR-stated bound is not a CrCl-stated bound, and 30 in one is not 30 in
    # the other.
    threshold = make_threshold(states_metric="egfr")

    # Assert
    assert threshold.states_metric == "egfr"


def test_a_threshold_states_no_renal_metric_by_default():
    # Arrange / Act — a blood-pressure threshold states no renal metric, and
    # absent means "not a renal bound", never "unknown"
    threshold = make_threshold()

    # Assert
    assert threshold.states_metric is None


def test_a_threshold_metric_outside_the_closed_pair_is_refused():
    # Arrange / Act / Assert
    with pytest.raises(ValidationError):
        make_threshold(states_metric="cystatin_c")
```

`tests/engine/test_content.py` already imports `pytest`, `ValidationError`, and `make_threshold`.

- [ ] **Step 7: Run it and watch it fail**

```bash
uv run pytest tests/engine/test_content.py -q -k states_metric
```

Expected: FAIL — `Extra inputs are not permitted`.

- [ ] **Step 8: Add the field to `Threshold` and delete the no-op validator**

In `src/noor/engine/content.py`, add to `Threshold` after `approved_at` (line 74):

```python
    approved_at: date | None = None
    states_metric: Literal["egfr", "crcl"] | None = None
```

Add `Literal` to the `typing` import if absent. Then extend the docstring:

```python
class Threshold(NoorModel):
    """One clinical decision boundary, cited and versioned (SSOT §7.3).

    `states_metric` records which renal metric the *cited document* specified.
    §10.4 gate 15b refuses a rule that measures one metric against a bound
    stated in the other — an eGFR of 30 and a creatinine clearance of 30 are
    different clinical facts, and §5.2 forbids treating them as one.
    """
```

Now delete `_goal_units_match_threshold_units` entirely — the whole of `content.py:297-307`, decorator included. It returns `self` unconditionally and its own docstring says it is "a placeholder for future enhancement when `Threshold` gains an observable field". `Threshold` just gained `states_metric`, which is not that field and does not make the check possible: a goal names an *observable*, `states_metric` names a *metric*, and neither implies the other. The check the docstring describes already happens where it can — `resolve_threshold` raises `ForeignGoalUnitError` when a resolved goal's unit differs from the threshold's (`content.py:330-331`), and `tests/engine/test_content.py` covers it. A validator that runs on every load and can never fail is not a safety net; it reads like one.

- [ ] **Step 9: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Expected: all green. Coverage should *improve* — the deleted validator's body was a covered line that proved nothing.

If `test_canon_never_names_a_treatment_threshold` fails, stop: the new identifier would have to contain "threshold" or "target_range", and `renal_metric` contains neither. A failure means something else in the diff went wrong.

- [ ] **Step 10: Commit**

```bash
git add src/noor/canon/registry.py src/noor/engine/content.py \
        content/observables/registry.yaml tests/canon/test_registry.py \
        tests/engine/test_content.py
git commit -m "feat(engine): renal-metric markers for gate 15, minus one dead validator

Gate 15a needs to know which observables are renal metrics (a fact about the
observable → canon's ObservableEntry); 15b needs the metric the cited document
stated (a fact about the citation → Threshold). Marked on egfr only: creatinine
is CrCl's input, not a renal metric, and marking it would bless the exact
conflation gate 15 exists to catch.

Deletes _goal_units_match_threshold_units, which returned self unconditionally
and described a check resolve_threshold already performs."
```

---

### Task 5: `medications_reconciled_at`, and the resolution path for it

This is the §0 exception, approved 2026-08-24. `_drug_active` returns `False` on an empty medication list, so a patient nobody asked about reads identically to a patient confirmed to be on nothing — the silent false negative §5.5 rule 2 outlaws for allergies and nothing outlawed for medications. The fix is medication parity with allergy: the list-level fact travels beside the list, a rule declares it as a requirement, and the existing degradation machinery does the rest.

**List-level, not per-entry.** A per-entry `asserted_at` cannot express the case that matters — an empty list has no entries to carry a stamp — and `min(asserted_at)` over a long-standing list would make `max_age_days` unsatisfiable for any patient on a stable regimen.

Read **deviations 3 and 4** before starting: the spec is wrong about `_resolve_manifest` already tolerating this, and the stale check cannot reuse `_first_failure`.

**Files:**
- Modify: `src/noor/engine/snapshot.py:188-198`
- Modify: `src/noor/engine/evaluate.py:410-424` (restructure), `:427-459` (route)
- Modify: `tests/conftest.py:261-280` (stamp), `:283-296` (new helper)
- Test: `tests/engine/test_snapshot.py`, `tests/engine/test_evaluate.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Snapshot.medications_reconciled_at: AwareDatetime | None = None` — `None` means "nobody asked", exactly as `AllergyStatus.not_asked` does.
  - `ACTIVE_MEDICATIONS = "active_medications"` in `noor.engine.rules` (added in Task 6; until then `evaluate.py` uses the string literal so this task stands alone — Task 6 step 8 swaps it for the constant).
  - `make_medication_requirement(**overrides) -> Requirement` in `tests/conftest.py` — `observable="active_medications"`, `max_age_days=180`, `on_unusable=OnUnusable.indeterminate`, and **no** `accepted_status`, `min_quality`, `prefer_source`, or `required_context`: those grade an observation, and there is no observation here.
  - `make_snapshot` now defaults `medications_reconciled_at=T0`.

- [ ] **Step 1: Write the failing snapshot test**

Append to `tests/engine/test_snapshot.py`:

```python
def test_a_snapshot_records_when_the_medication_list_was_last_reconciled():
    # Arrange / Act — §5.5 rule 2 applied to medications: an unasked patient and
    # a reconciled patient are opposite facts, and an empty list is not the
    # second one
    snapshot = make_snapshot(medications_reconciled_at=T0)

    # Assert
    assert snapshot.medications_reconciled_at == T0


def test_an_unreconciled_medication_list_is_the_default():
    # Arrange / Act — absent means nobody asked. The default cannot be "now":
    # that would assert reconciliation the boundary never saw.
    snapshot = make_snapshot(medications_reconciled_at=None)

    # Assert
    assert snapshot.medications_reconciled_at is None


def test_a_reconciliation_stamp_is_normalised_to_utc():
    # Arrange — the boundary normalises time the way it already does for
    # evaluated_at, so a comparison never straddles two offsets
    riyadh = timezone(timedelta(hours=3))
    stamped = T0.astimezone(riyadh)

    # Act
    snapshot = make_snapshot(medications_reconciled_at=stamped)

    # Assert
    assert snapshot.medications_reconciled_at is not None
    assert snapshot.medications_reconciled_at.utcoffset() == timedelta(0)
    assert snapshot.medications_reconciled_at == T0
```

Add `timezone` to the `datetime` import in that file if it is not already imported; `T0` and `make_snapshot` come from `tests.conftest`, which the file already imports from.

- [ ] **Step 2: Run it and watch it fail**

```bash
uv run pytest tests/engine/test_snapshot.py -q -k reconcil
```

Expected: FAIL — `Extra inputs are not permitted`.

- [ ] **Step 3: Add the field**

In `src/noor/engine/snapshot.py`, add after `goals_of_care` (line 197):

```python
    goals_of_care: tuple[GoalOfCare, ...] = ()
    medications_reconciled_at: AwareDatetime | None = None
```

Extend the existing `evaluated_at` normaliser to cover it, rather than adding a second validator:

```python
    @field_validator("evaluated_at", "medications_reconciled_at")
    @classmethod
    def _normalise_to_utc(cls, value: datetime | None) -> datetime | None:
        return value if value is None else value.astimezone(UTC)
```

And extend the class docstring's last paragraph:

```python
    `medications_reconciled_at` is the medication list's answer to
    `allergy_status`: `None` means nobody asked, and an empty `medications`
    tuple beside a stamp means someone asked and the answer was "none". §5.5
    rule 2 forbids inferring the second from the first, and `_drug_active`
    cannot tell them apart without this field.
    """
```

There is deliberately **no** consistency validator pairing the stamp with a non-empty list, unlike `_allergy_status_consistent_with_allergies`. All four combinations are real: a stamp with entries (reconciled, on drugs), a stamp with none (reconciled, on nothing), no stamp with none (nobody asked), and no stamp *with* entries (a list from an import nobody has since confirmed — which is precisely the state a rule should degrade on, not one the boundary should refuse to represent).

- [ ] **Step 4: Run it and watch it pass**

```bash
uv run pytest tests/engine/test_snapshot.py -q -k reconcil
```

Expected: 3 passed.

- [ ] **Step 5: Write the failing evaluation tests**

Append to `tests/engine/test_evaluate.py`. These use the local `metformin_snapshot` helper and `evaluate_one` already defined in that file:

```python
def test_an_unreconciled_medication_list_makes_a_drug_rule_indeterminate():
    # Arrange — the silent false negative this whole change exists to close: an
    # empty list from a patient nobody asked used to read exactly like a patient
    # confirmed to be on nothing, and the hard stop simply did not fire
    rule = make_rule(requires=(make_requirement(renal_metric="egfr"), make_medication_requirement()))
    snapshot = metformin_snapshot(medications=(), medications_reconciled_at=None)

    # Act
    record = evaluate_one(rule, snapshot)

    # Assert
    assert record.outcome is Outcome.indeterminate
    verdict = next(v for v in record.requirement_verdicts if v.observable == "active_medications")
    assert verdict.verdict is RequirementVerdictValue.unusable
    assert verdict.reason is RequirementReason.no_result


def test_a_reconciled_empty_medication_list_lets_the_rule_decide():
    # Arrange — someone asked and the answer was "on nothing", so drug_active is
    # a real False and the rule legitimately does not trigger
    rule = make_rule(requires=(make_requirement(renal_metric="egfr"), make_medication_requirement()))
    snapshot = metformin_snapshot(medications=(), medications_reconciled_at=T0)

    # Act
    record = evaluate_one(rule, snapshot)

    # Assert
    assert record.outcome is Outcome.not_triggered
    verdict = next(v for v in record.requirement_verdicts if v.observable == "active_medications")
    assert verdict.verdict is RequirementVerdictValue.usable
    assert verdict.reason is RequirementReason.met


def test_a_reconciliation_older_than_the_declared_window_is_stale():
    # Arrange — a list reconciled two years ago is not a current medication list
    rule = make_rule(
        requires=(
            make_requirement(renal_metric="egfr"),
            make_medication_requirement(max_age_days=180),
        )
    )
    snapshot = metformin_snapshot(medications_reconciled_at=T0 - timedelta(days=181))

    # Act
    record = evaluate_one(rule, snapshot)

    # Assert
    assert record.outcome is Outcome.indeterminate
    verdict = next(v for v in record.requirement_verdicts if v.observable == "active_medications")
    assert verdict.reason is RequirementReason.stale
    assert verdict.latest_age_days == 181


def test_a_reconciliation_exactly_at_the_window_edge_stays_usable():
    # Arrange — the same boundary _first_failure uses for observations: `>`, not
    # `>=`, so exactly max_age_days old is still usable. Two comparisons, one
    # semantics; this pins the parity.
    rule = make_rule(
        requires=(
            make_requirement(renal_metric="egfr"),
            make_medication_requirement(max_age_days=180),
        )
    )
    snapshot = metformin_snapshot(medications_reconciled_at=T0 - timedelta(days=180))

    # Act
    record = evaluate_one(rule, snapshot)

    # Assert
    verdict = next(v for v in record.requirement_verdicts if v.observable == "active_medications")
    assert verdict.verdict is RequirementVerdictValue.usable
    assert verdict.latest_age_days == 180


def test_a_medication_requirement_with_no_window_never_goes_stale():
    # Arrange — max_age_days is per-rule and optional (§7.1(a)); a rule that
    # declares no window accepts any stamp
    rule = make_rule(
        requires=(
            make_requirement(renal_metric="egfr"),
            make_medication_requirement(max_age_days=None),
        )
    )
    snapshot = metformin_snapshot(medications_reconciled_at=T0 - timedelta(days=4000))

    # Act
    record = evaluate_one(rule, snapshot)

    # Assert
    verdict = next(v for v in record.requirement_verdicts if v.observable == "active_medications")
    assert verdict.verdict is RequirementVerdictValue.usable


def test_a_future_dated_reconciliation_stamp_is_unusable():
    # Arrange — a stamp after the evaluation instant is a corrupt clock, handled
    # exactly as a future-dated observation is
    rule = make_rule(requires=(make_requirement(renal_metric="egfr"), make_medication_requirement()))
    snapshot = metformin_snapshot(medications_reconciled_at=T0 + timedelta(days=1))

    # Act
    record = evaluate_one(rule, snapshot)

    # Assert
    assert record.outcome is Outcome.indeterminate
    verdict = next(v for v in record.requirement_verdicts if v.observable == "active_medications")
    assert verdict.verdict is RequirementVerdictValue.unusable
    assert verdict.reason is RequirementReason.no_result


def test_a_medication_requirement_contributes_no_validated_value():
    # Arrange — a usable medication verdict populates nothing: there is no
    # observation, so nothing may be compared numerically against it
    rule = make_rule(
        requires=(make_requirement(renal_metric="egfr"), make_medication_requirement()),
        when=Expression(op=Operator.drug_active, ingredient_id="metformin"),
    )
    snapshot = metformin_snapshot(medications_reconciled_at=T0)

    # Act
    record = evaluate_one(rule, snapshot)

    # Assert — the rule fires on the drug leaf alone and no verdict claims a value
    assert record.outcome is Outcome.triggered
    assert {v.observable for v in record.requirement_verdicts} == {"egfr", "active_medications"}
```

`metformin_snapshot` must forward `**overrides` to `make_snapshot`. Check its signature at the top of the file; if it takes fixed arguments, widen it to `def metformin_snapshot(**overrides: Any) -> Snapshot:` passing them through, and leave its existing call sites untouched. Add `make_medication_requirement` to the `tests.conftest` import list, and `Expression`/`Operator` if the file does not already import them.

- [ ] **Step 6: Run them and watch them fail**

```bash
uv run pytest tests/engine/test_evaluate.py -q -k "reconcil or medication_requirement"
```

Expected: `ImportError: cannot import name 'make_medication_requirement'`. Add the helper (step 7), re-run, and now expect real failures: `AssertionError` out of `_resolve_manifest:419` for the usable cases and `RequirementReason.no_result` for everything else — `_latest_observation("active_medications", …)` finds no observation, because there never is one.

- [ ] **Step 7: Add the conftest helper and stamp the default snapshot**

In `tests/conftest.py`, add `"medications_reconciled_at": T0` to `make_snapshot`'s `fields` dict (after `goals_of_care`), and add this helper after `make_requirement`:

```python
def make_medication_requirement(**overrides: Any) -> Requirement:
    """The medication-list requirement a drug rule declares (§5.5 rule 2).

    No `accepted_status`, `min_quality`, `prefer_source`, or `required_context`:
    those grade an observation, and a reconciliation stamp is not one. Freshness
    and `on_unusable` are the whole contract.
    """
    fields: dict[str, Any] = {
        "observable": "active_medications",
        "max_age_days": 180,
        "on_unusable": OnUnusable.indeterminate,
    }
    fields.update(overrides)
    return Requirement(**fields)
```

Stamping `make_snapshot` by default is what keeps Task 6 from turning every existing engine test indeterminate. A test that wants the unasked case passes `medications_reconciled_at=None` explicitly — the same shape as the `allergy_status` default.

- [ ] **Step 8: Route medication requirements and restructure the manifest loop**

In `src/noor/engine/evaluate.py`, replace `_resolve_manifest` (lines 410-424) with:

```python
def _resolve_manifest(requirements: tuple[Requirement, ...], snapshot: Snapshot) -> _Manifest:
    verdicts: list[RequirementVerdict] = []
    validated: dict[str, Decimal] = {}
    graded: dict[str, bool] = {}
    degrades = False
    for requirement in requirements:
        verdict, observation = _resolve_requirement(requirement, snapshot)
        verdicts.append(verdict)
        if verdict.verdict is not RequirementVerdictValue.usable:
            if requirement.on_unusable is OnUnusable.indeterminate:
                degrades = True  # silent-unusable verdicts are recorded and proceed (§8.3)
        elif observation is not None:
            # A usable requirement that selected no observation populates nothing:
            # `active_medications` is a list-level fact, not a measurement, so
            # there is no value to compare and no evidence grade to carry.
            validated[requirement.observable] = _canonical_value(observation)
            graded[requirement.observable] = _evidence_is_graded(observation, requirement, snapshot)
    return _Manifest(tuple(verdicts), validated, graded, degrades)
```

That drops the `assert observation is not None`, which a usable medication verdict would trip. Then add the routing branch at the top of `_resolve_requirement` (line 430):

```python
def _resolve_requirement(
    requirement: Requirement, snapshot: Snapshot
) -> tuple[RequirementVerdict, CanonicalObservation | None]:
    if requirement.observable == "active_medications":
        return _resolve_medication_reconciliation(requirement, snapshot), None
    latest = _latest_observation(requirement.observable, snapshot)
    ...
```

And add the resolver beside it:

```python
def _resolve_medication_reconciliation(
    requirement: Requirement, snapshot: Snapshot
) -> RequirementVerdict:
    """Resolve the medication list's own freshness (§5.5 rule 2, §8.2).

    The list is not an observation: it has no unit, no quality state, and no
    source status, so none of `_first_failure`'s checks apply. What it has is a
    reconciliation instant, and that answers the one question `_drug_active`
    cannot: whether an empty list means "on nothing" or "nobody asked".

    The staleness comparison matches `_first_failure`'s exactly — `>`, so a list
    reconciled exactly `max_age_days` ago is still usable.
    """
    reconciled_at = snapshot.medications_reconciled_at
    if reconciled_at is None:
        return _verdict(
            requirement.observable,
            RequirementVerdictValue.unusable,
            RequirementReason.no_result,
            None,
        )
    elapsed = snapshot.evaluated_at - reconciled_at
    if elapsed < timedelta(0):
        # Future-dated reconciliation: corrupt timestamp, refuse to use it.
        return _verdict(
            requirement.observable,
            RequirementVerdictValue.unusable,
            RequirementReason.no_result,
            None,
        )
    if requirement.max_age_days is not None and elapsed > timedelta(days=requirement.max_age_days):
        return _verdict(
            requirement.observable,
            RequirementVerdictValue.unusable,
            RequirementReason.stale,
            elapsed.days,
        )
    return _verdict(
        requirement.observable, RequirementVerdictValue.usable, RequirementReason.met, elapsed.days
    )
```

Leave `_drug_active` alone. It keeps returning `False` for an empty list, which is correct *given* a reconciled list — the requirement is what establishes that, and a rule that omits it now fails gate 16 at load (Task 6).

- [ ] **Step 9: Run the evaluation tests and watch them pass**

```bash
uv run pytest tests/engine/test_evaluate.py -q
```

Expected: all pass, including the seven new ones. If a pre-existing test now fails, check the `medications_reconciled_at=T0` default landed in `make_snapshot` — nothing else in this task changes existing behaviour.

- [ ] **Step 10: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Expected: all green. The restructured loop has three branches (unusable-and-degrades, unusable-and-silent, usable-with-an-observation) plus usable-without-one; the seven new tests plus the existing silent-requirement tests cover all four.

- [ ] **Step 11: Commit**

```bash
git add src/noor/engine/snapshot.py src/noor/engine/evaluate.py tests/conftest.py \
        tests/engine/test_snapshot.py tests/engine/test_evaluate.py
git commit -m "feat(engine): medication-list reconciliation as a first-class fact

§0 device-boundary contract change, approved 2026-08-24. _drug_active returned
False for an empty medication list, so a patient nobody asked read exactly like
a patient confirmed to be on nothing — the silent false negative §5.5 rule 2
outlaws for allergies. Snapshot.medications_reconciled_at carries the
list-level fact; an active_medications requirement resolves against it and
degrades to indeterminate when it is absent, future-dated, or stale.

List-level, not per-entry: an empty list has no entry to carry a stamp, and
min(asserted_at) would make max_age_days unsatisfiable for a stable regimen.

_resolve_manifest's `assert observation is not None` goes: a usable
requirement may legitimately populate no value."
```

---

### Task 6: Gates 3 and 16, gate 12 widened, and the mis-placed gate-15 validator removed

Four single-rule changes, all on `Rule` or `Requirement`, all landing at load.

**Gate 3** (`stop_and_review` + `role_doubling: true`) and **gate 16** (a hard stop matching on an allergy without demanding `confirmed` + `severe`) are §10.4 gates nothing enforces today. **Amendment 7** widens gate 12's declaration check from numeric leaves to `drug_active` too. And **cleanup 4** deletes `_renal_metric_matches_observable`, which invented a constraint §10.4 never states.

**Why cleanup 4 is a deletion and not a fix.** Gate 15 is a *cross-file* gate: 15a needs the registry to know which observables are renal metrics, 15b needs the threshold to know which metric its source stated. Neither fact is visible to a `Requirement`. What the validator actually enforces — `renal_metric == observable` — makes `renal_metric` a redundant echo of `observable`, and it forbids the legitimate rule that requires `creatinine` and reasons about `crcl`. It reads as gate 15 without being it, which is worse than nothing: it makes the real gate look already-implemented. Task 9 implements gate 15 where the facts live.

**Files:**
- Modify: `src/noor/engine/rules.py:271-296` (delete validator), `:359-433` (three validators, one constant)
- Modify: `tests/conftest.py:327-360` (`make_rule` declares the medication requirement)
- Test: `tests/engine/test_rules.py`

**Interfaces:**
- Consumes: `make_medication_requirement` and the `active_medications` resolution path (Task 5).
- Produces:
  - `ACTIVE_MEDICATIONS: str = "active_medications"` in `noor.engine.rules` — the one spelling of the reserved observable. Task 9's allowlist and `evaluate.py` both import it.
  - `Requirement.renal_metric` survives with no validator; Task 9 reads it.

- [ ] **Step 1: Write the failing tests**

Append to `tests/engine/test_rules.py`:

```python
def test_a_hard_stop_cannot_have_its_author_approve_it():
    # Arrange / Act / Assert — gate 3: role_doubling is permitted below a hard
    # stop, but the highest severity in the system does not get to be
    # self-approved (§7.1(d), §10.4 gate 3)
    with pytest.raises(ValidationError, match="gate 3"):
        make_rule(governance=make_governance(role_doubling=True))


def test_role_doubling_remains_available_below_a_hard_stop():
    # Arrange — gate 3 binds stop_and_review alone, exactly as gate 10 does
    governance = make_governance(role_doubling=True)

    # Act
    rule = make_rule(severity=Severity.passive_task, governance=governance, then=make_then())

    # Assert
    assert rule.governance.role_doubling is True


@pytest.mark.parametrize(
    "filters",
    [
        {},
        {"verification_status": VerificationStatus.confirmed},
        {"severity": AllergySeverity.severe},
        {"verification_status": VerificationStatus.unconfirmed, "severity": AllergySeverity.severe},
        {"verification_status": VerificationStatus.confirmed, "severity": AllergySeverity.moderate},
    ],
    ids=["no-filters", "confirmed-only", "severe-only", "unconfirmed", "moderate"],
)
def test_a_hard_stop_on_an_allergy_demands_confirmed_and_severe(filters):
    # Arrange / Act / Assert — gate 16: a hard stop blocks an order, and §5.5's
    # table says only a confirmed severe record answers cleanly enough to
    # justify that. An unconfirmed or moderate record earns a softer severity.
    with pytest.raises(ValidationError, match="gate 16"):
        make_rule(
            requires=(),
            when=Expression(op=Operator.allergy, ingredient_id="amoxicillin", **filters),
        )


def test_a_hard_stop_on_a_fully_filtered_allergy_loads():
    # Arrange
    leaf = Expression(
        op=Operator.allergy,
        ingredient_id="amoxicillin",
        verification_status=VerificationStatus.confirmed,
        severity=AllergySeverity.severe,
    )

    # Act
    rule = make_rule(requires=(), when=leaf)

    # Assert
    assert rule.when.verification_status is VerificationStatus.confirmed


def test_a_softer_rule_may_match_an_unfiltered_allergy():
    # Arrange — gate 16 binds stop_and_review alone: surfacing an unconfirmed
    # allergy for review is exactly what interruptive_review is for
    leaf = Expression(op=Operator.allergy, ingredient_id="penicillin")

    # Act
    rule = make_rule(
        severity=Severity.interruptive_review, requires=(), when=leaf, then=make_then()
    )

    # Assert
    assert rule.when.verification_status is None


def test_a_nested_allergy_leaf_under_a_hard_stop_is_checked_too():
    # Arrange — burying the leaf under boolean composition hides nothing, the
    # same way it hides nothing from gate 12
    buried = Expression(
        op=Operator.any,
        children=(
            Expression(op=Operator.allergy, ingredient_id="penicillin"),
            Expression(op=Operator.drug_requested, ingredient_id="amoxicillin"),
        ),
    )

    # Act / Assert
    with pytest.raises(ValidationError, match="gate 16"):
        make_rule(requires=(), when=buried)


def test_a_drug_active_rule_must_declare_the_medication_list_it_reads():
    # Arrange / Act / Assert — amendment 7: drug_active reads the medication
    # list, so the list is data of declared freshness like any other. Without
    # this a rule silently treats "nobody asked" as "on nothing" (§5.5 rule 2).
    with pytest.raises(ValidationError, match="active_medications"):
        make_rule(requires=(make_requirement(renal_metric="egfr"),))


def test_drug_requested_needs_no_medication_requirement():
    # Arrange — a requested action arrives in the request, not from the
    # medication list, so there is no list freshness to declare
    rule = make_rule(
        requires=(),
        when=Expression(op=Operator.drug_requested, ingredient_id="metformin"),
    )

    # Assert
    assert rule.when.op is Operator.drug_requested


def test_a_nested_drug_active_leaf_needs_the_declaration_too():
    # Arrange
    buried = Expression(
        op=Operator.NOT,
        children=(Expression(op=Operator.drug_active, ingredient_id="metformin"),),
    )

    # Act / Assert
    with pytest.raises(ValidationError, match="active_medications"):
        make_rule(requires=(), when=buried)


def test_a_requirement_may_name_a_renal_metric_its_observable_does_not_echo():
    # Arrange / Act — gate 15 is a cross-file gate (Task 9): 15a needs the
    # registry to know which observables are renal metrics, 15b needs the
    # threshold to know which metric its source stated, and a Requirement can
    # see neither. A rule that requires creatinine and reasons about creatinine
    # clearance is legitimate content, and the deleted validator refused it.
    requirement = make_requirement(observable="creatinine", renal_metric="crcl")

    # Assert
    assert requirement.renal_metric == "crcl"
```

Add `make_governance` to the `tests.conftest` import if absent (it is already imported), and `VerificationStatus`/`AllergySeverity` are already imported from `noor.engine.snapshot`.

- [ ] **Step 2: Delete cleanup 4's test**

Delete `test_requirement_renal_metric_must_match_observable` (lines 498-527) — cleanup 4's test. It asserts the invented constraint, its local `from noor.engine.rules import ...` inside the function body is the only one in the file, and the behaviour it pins is the behaviour being removed. Line 325's `assert rule.requires[0].renal_metric == "egfr"` stays: `make_rule` still declares it.

**Gate 11's test stays exactly where it is.** `test_requirements_cannot_reference_encounter_narrative_or_trigger_state` (lines 415-427) and the validator it exercises both move in Task 9, together, in one commit. Deleting the test here while the validator remains would leave its `raise` branch uncovered and fail `--cov-fail-under=100` at step 7.

- [ ] **Step 3: Run the tests and watch them fail**

```bash
uv run pytest tests/engine/test_rules.py -q
```

Expected: the four gate-3/16 refusal tests fail with "DID NOT RAISE", and the two amendment-7 tests fail the same way. `test_a_requirement_may_name_a_renal_metric_its_observable_does_not_echo` fails with "they must match".

- [ ] **Step 4: Declare the medication requirement in `make_rule`**

In `tests/conftest.py`, change `make_rule`'s `requires` (line 337):

```python
        "requires": (make_requirement(renal_metric="egfr"), make_medication_requirement()),
```

`make_rule`'s default `when` carries a `drug_active` leaf, so after step 5 the default rule does not load without this. This is why Task 5 comes first.

- [ ] **Step 5: Implement the three validators and delete the fourth**

In `src/noor/engine/rules.py`, add the constant beside `FORBIDDEN_REQUIREMENT_OBSERVABLES` (line 117):

```python
# The reserved observable naming the medication list itself (§5.5 rule 2). Not a
# measurement: it has no unit, no quality state, and no source status, and its
# requirement declares only how fresh the reconciliation must be.
ACTIVE_MEDICATIONS = "active_medications"
```

Delete `Requirement._renal_metric_matches_observable` entirely — `rules.py:288-296`, decorator included — and extend the `Requirement` docstring so nobody re-adds it:

```python
class Requirement(NoorModel):
    """One entry of the data-requirement manifest (§7.1(a), §5.1).

    Each rule declares its own windows — there is no global TTL. `observable`
    holds a snapshot fact key; `on_unusable` chooses between proceeding without
    the fact and degrading to indeterminate (§8.3).

    `renal_metric` is checked at release compilation, not here: §10.4 gate 15
    needs the registry (which observables are renal metrics) and the threshold
    (which metric the cited source stated), and a requirement can see neither.
    It deliberately does not have to echo `observable` — a rule may require
    `creatinine` and reason about `crcl`.
    """
```

Then add the three validators to `Rule`, after `_a_hard_stop_never_sits_on_silenced_data`:

```python
    @model_validator(mode="after")
    def _a_hard_stop_is_never_self_approved(self) -> Self:
        if self.severity is Severity.stop_and_review and self.governance.role_doubling:
            raise ValueError(
                "a stop_and_review rule cannot declare role_doubling: true — the highest "
                "severity in the system is not self-approved (§7.1(d), §10.4 gate 3)"
            )
        return self

    @model_validator(mode="after")
    def _a_hard_stop_on_an_allergy_demands_a_confirmed_severe_match(self) -> Self:
        if self.severity is not Severity.stop_and_review:
            return self
        for node in walk_expression(self.when):
            if node.op is Operator.allergy and not (
                node.verification_status is VerificationStatus.confirmed
                and node.severity is AllergySeverity.severe
            ):
                raise ValueError(
                    f"a stop_and_review rule matching `allergy: {node.ingredient_id}` must "
                    f"require verification_status: confirmed and severity: severe — only a "
                    f"confirmed severe record answers cleanly enough to block an order "
                    f"(§5.5, §9.1, §10.4 gate 16)"
                )
        return self
```

And widen the existing gate-12 validator (line 409) to cover the drug leaf:

```python
    @model_validator(mode="after")
    def _every_compared_observable_is_declared_in_requires(self) -> Self:
        declared = {requirement.observable for requirement in self.requires}
        for node in walk_expression(self.when):
            if node.op in NUMERIC_OPERATORS and node.fact not in declared:
                raise ValueError(
                    f"`{node.fact}` is compared numerically but absent from requires — a "
                    f"threshold never runs against data of undeclared age and grade "
                    f"(§7.1, §10.4 gate 12)"
                )
            if node.op is Operator.drug_active and ACTIVE_MEDICATIONS not in declared:
                raise ValueError(
                    f"`drug_active: {node.ingredient_id}` reads the medication list but "
                    f"`{ACTIVE_MEDICATIONS}` is absent from requires — without it an empty "
                    f"list from a patient nobody asked reads as a patient on nothing "
                    f"(§5.5 rule 2, §7.1, §10.4 gate 12)"
                )
        return self
```

`drug_requested` is deliberately excluded: a requested action arrives with the request, not from the list.

`Operator`, `VerificationStatus`, `AllergySeverity`, and `walk_expression` are all already in scope in `rules.py`.

- [ ] **Step 6: Run the rules tests and watch them pass**

```bash
uv run pytest tests/engine/test_rules.py -q
```

Expected: all pass.

- [ ] **Step 7: Fix the requirement-count assertions the widened gate 12 moved**

`make_rule` now carries two requirements, so tests that unpacked exactly one verdict see two. Run the engine suite and fix each site by *selecting* the verdict it means rather than unpacking:

```bash
uv run pytest tests/engine -q
```

The known sites — verify each against the current file, since line numbers shift as you edit:
- `tests/engine/test_evaluate.py:176`, `:470`, `:495`, `:517` — `(verdict,) = record.requirement_verdicts` becomes
  `verdict = next(v for v in record.requirement_verdicts if v.observable == "egfr")`.
- `tests/engine/test_evaluate.py:753` — `len(...) == 2` becomes `== 3` **only if** that rule's `when` carries a `drug_active` leaf; read it first, and if it does not, leave it.
- `tests/engine/test_evaluate.py:977` — same check for `len(...) == 1`.
- `tests/engine/test_degradation.py:116` — the same `next(...)` change.
- `tests/engine/test_evaluate.py:454` — a `make_rule(requires=...)` override; if it drops the medication requirement while keeping a `drug_active` leaf, add `make_medication_requirement()` to the tuple.

A local rule helper in a test file that builds a `drug_active` rule without going through `make_rule` needs the same requirement added. `potassium_rule`, `hyperkalemia_hard_stop`, `allergy_rule`, and `allergy_snapshot` in `test_evaluate.py` are the ones to check; the allergy rules may also now need `confirmed`/`severe` filters if they are hard stops, which is gate 16 doing its job on the fixtures.

- [ ] **Step 8: Use the constant in `evaluate.py`**

Now that `ACTIVE_MEDICATIONS` exists, replace the string literal Task 5 left in `_resolve_requirement`:

```python
    if requirement.observable == ACTIVE_MEDICATIONS:
```

`evaluate.py` already imports from `noor.engine.rules`; add `ACTIVE_MEDICATIONS` to that import list.

- [ ] **Step 9: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Expected: all green at 100%. `tests/engine/test_properties.py` and `test_invariants.py` build rules too — if a hypothesis strategy generates a `drug_active` rule without the requirement, it now fails at construction, and the strategy needs the requirement added rather than the gate loosened.

- [ ] **Step 10: Commit**

```bash
git add src/noor/engine/rules.py src/noor/engine/evaluate.py tests/conftest.py tests/engine/
git commit -m "feat(engine): gates 3 and 16, gate 12 widened to drug_active

Gate 3: a stop_and_review rule cannot declare role_doubling: true. Gate 16: a
hard stop matching an allergy must demand confirmed + severe, since §5.5's
table says only that record answers cleanly enough to block an order. Both
bind stop_and_review alone, as gate 10 does.

Gate 12 widens: drug_active reads the medication list, so the rule declares
active_medications and the list's freshness is data of declared age like any
other.

Deletes Requirement._renal_metric_matches_observable. It enforced
renal_metric == observable, which §10.4 never states, makes renal_metric a
redundant echo, and refuses the legitimate rule that requires creatinine and
reasons about crcl. Gate 15 needs the registry and the threshold; it lands in
release compilation. Gate 11's test moves to the compiler suite next."
```

---

### Task 7: Per-kind loading

Rules, thresholds, profiles, and the release document. This module does no validation of its own beyond shape: the `engine` models' validators are the gates, and this hands them raw documents. What it adds is the *file layout* — which directory holds what, and which errors name which file.

**Files:**
- Create: `src/noor/catalogue/loader.py`
- Test: `tests/catalogue/test_loader.py`, `tests/catalogue/conftest.py`

**Interfaces:**
- Consumes: `content_yaml` helpers (Task 1); `noor.engine.rules.Rule`; `noor.engine.content.Threshold`, `Profile`, `CatalogueRelease`.
- Produces:
  - `load_rules(content_dir: Path) -> dict[str, Rule]` — every `*.yaml` under `content_dir/rules/`, keyed by rule id; **not** `*.cases.yaml`.
  - `load_thresholds(content_dir: Path) -> dict[str, Threshold]` — keyed by ref.
  - `load_profile(content_dir: Path, name: str) -> Profile`
  - `load_release_document(content_dir: Path, release_id: str) -> ReleaseDocument`
  - `ReleaseDocument(release_id, profile, terminology_version, rules: tuple[str, ...], thresholds: tuple[str, ...])` — the *manifest*: which rule ids and threshold refs this release includes, which profile it pins, and which terminology version it was built against. Task 9 turns it into a `CatalogueRelease` by resolving the ids, and copies `terminology_version` onto the §8.2 `Pins`.
- The content directory layout this fixes:

```
content/
  observables/registry.yaml
  valuesets/{conditions,ingredients}.yaml
  terminology/charter.yaml
  rules/<rule-id>.yaml            # one rule per file, plus <rule-id>.cases.yaml
  thresholds/<family>.yaml        # a `thresholds:` list per file
  profiles/<name>.yaml
  releases/<release-id>.yaml
```

- [ ] **Step 1: Write the fixture content tree**

Create `tests/catalogue/conftest.py`. Every compiler and loader test builds from this, varying one piece — the same discipline `tests/conftest.py` already uses, applied to files instead of models. It stays synthetic: `content/` carries no clinical claim (spec decision 4), so the numbers here are invented and belong under `tmp_path`.

```python
"""A valid synthetic content tree, and the knobs to make one piece invalid.

`content/` stays clinically clean (no rule, no threshold, no golden case), so
every compiler behaviour is proven here instead: `valid_content_dir` writes a
tree that compiles, and a test overwrites exactly one file to prove one gate.

The numbers are invented. `egfr < 30` is not cited here and is not a clinical
claim — it is a value that exercises a comparison.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

RULE_ID = "test-metformin-egfr"
THRESHOLD_REF = "test.metformin_egfr"
PROFILE_NAME = "test-profile"
RELEASE_ID = "rel-test-1"

REGISTRY: dict[str, Any] = {
    "observables": [
        {
            "observable": "egfr",
            "owner": "nephrology",
            "renal_metric": "egfr",
            "canonical_ucum": "mL/min/{1.73_m2}",
            "accepted_units": ["mL/min/{1.73_m2}"],
            "code_unit_map": {},
            "physiologic": {"low": "1", "high": "200", "version": "v1"},
            "operational": {"low": "3", "high": "150", "version": "v1"},
            "delta_policy": {
                "window_hours": 24,
                "absolute": None,
                "relative": None,
                "compare_context": [],
            },
            "repeat_tolerance": "1",
        }
    ]
}

CONDITIONS: dict[str, Any] = {"concepts": [{"concept": "type_2_diabetes", "label": "T2DM"}]}
INGREDIENTS: dict[str, Any] = {"ingredients": [{"ingredient": "metformin", "label": "Metformin"}]}
CHARTER: dict[str, Any] = {
    "code_systems": [
        {"system": "LOINC", "uri": "http://loinc.org", "licensed": True, "note": "test"}
    ]
}

GOVERNANCE: dict[str, Any] = {
    "clinical_owner": {"name": "Dr. Owner", "credential": "Internal Medicine"},
    "clinical_approver": {
        "name": "Dr. Approver",
        "credential": "Endocrinology",
        "approved_at": "2026-08-01",
    },
    "role_doubling": False,
    "effective_from": "2026-09-01",
    "next_review": "2027-09-01",
    "change_rationale": "Synthetic fixture.",
}

RULE: dict[str, Any] = {
    "id": RULE_ID,
    "version": "1.0.0",
    "release_status": "active",
    "category": "drug_safety",
    "severity": "stop_and_review",
    "drug_scope_level": "ingredient",
    "requires": [
        {
            "observable": "egfr",
            "on_unusable": "indeterminate",
            "max_age_days": 90,
            "renal_metric": "egfr",
        },
        {"observable": "active_medications", "on_unusable": "indeterminate", "max_age_days": 180},
    ],
    "monitors": [{"observable": "egfr", "due_in_days": 90, "reason": "renal function"}],
    "when": {
        "op": "all",
        "children": [
            {"op": "lt", "fact": "egfr", "threshold_ref": THRESHOLD_REF},
            {"op": "drug_active", "ingredient_id": "metformin"},
        ],
    },
    "then": {
        "blocks": {"order_of": "metformin"},
        "meaning": "Synthetic meaning.",
        "action": "Synthetic action.",
        "uncertainty": "Synthetic uncertainty.",
    },
    "governance": GOVERNANCE,
}

THRESHOLD: dict[str, Any] = {
    "ref": THRESHOLD_REF,
    "value": "30",
    "unit": "mL/min/{1.73_m2}",
    "source_family": "test-family",
    "status": "clinician_approved",
    "approved_by": "Dr. Approver",
    "approved_at": "2026-08-01",
    "states_metric": "egfr",
    "citation": {
        "organisation": "Synthetic",
        "document": "Synthetic guideline",
        "version": "2026",
        "locator": "§1",
        "jurisdiction": "international",
        "evidence_grade": "consensus",
        "review_date": "2027-01-01",
    },
}

PROFILE: dict[str, Any] = {
    "name": PROFILE_NAME,
    "version": "1.0.0",
    "source_family": "test-family",
    "disablements": [],
}

RELEASE: dict[str, Any] = {
    "release_id": RELEASE_ID,
    "profile": PROFILE_NAME,
    "terminology_version": "term-test-1",
    "rules": [RULE_ID],
    "thresholds": [THRESHOLD_REF],
}

CASES: dict[str, Any] = {
    "rule": RULE_ID,
    "cases": [
        {"name": "at the boundary", "observable": "egfr", "value": "30", "expected": "not_triggered"},
        {"name": "just below", "observable": "egfr", "value": "29.9", "expected": "triggered"},
        {"name": "just above", "observable": "egfr", "value": "30.1", "expected": "not_triggered"},
    ],
}


def write_yaml(path: Path, document: Any) -> None:
    """Write one content file, creating its directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")


@pytest.fixture
def valid_content_dir(tmp_path: Path) -> Path:
    """A content tree that compiles clean. Overwrite one file to break one gate."""
    write_yaml(tmp_path / "observables" / "registry.yaml", REGISTRY)
    write_yaml(tmp_path / "valuesets" / "conditions.yaml", CONDITIONS)
    write_yaml(tmp_path / "valuesets" / "ingredients.yaml", INGREDIENTS)
    write_yaml(tmp_path / "terminology" / "charter.yaml", CHARTER)
    write_yaml(tmp_path / "rules" / f"{RULE_ID}.yaml", RULE)
    write_yaml(tmp_path / "rules" / f"{RULE_ID}.cases.yaml", CASES)
    write_yaml(tmp_path / "thresholds" / "test-family.yaml", {"thresholds": [THRESHOLD]})
    write_yaml(tmp_path / "profiles" / f"{PROFILE_NAME}.yaml", PROFILE)
    write_yaml(tmp_path / "releases" / f"{RELEASE_ID}.yaml", RELEASE)
    return tmp_path
```

`yaml.safe_dump` here is a *test* writing a file, not content loading, so it is outside gate 13's scope — the gate constrains reading. The seam test's YAML ban applies to `src/`, and this is `tests/`.

- [ ] **Step 2: Write the failing loader test**

Create `tests/catalogue/test_loader.py`:

```python
"""Per-kind content loading: which directory holds what (SSOT §7.4).

Validation is not this module's job — the `engine` models' validators are the
single-rule gates, and this hands them raw documents. What it owns is the file
layout, and errors that name the file a content author has to open.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from noor.catalogue.loader import (
    load_profile,
    load_release_document,
    load_rules,
    load_thresholds,
)
from tests.catalogue.conftest import (
    PROFILE_NAME,
    RELEASE,
    RELEASE_ID,
    RULE,
    RULE_ID,
    THRESHOLD_REF,
    write_yaml,
)


def test_every_rule_file_in_the_rules_directory_loads_keyed_by_id(valid_content_dir):
    # Arrange / Act
    rules = load_rules(valid_content_dir)

    # Assert
    assert set(rules) == {RULE_ID}
    assert rules[RULE_ID].severity.value == "stop_and_review"


def test_a_cases_file_beside_a_rule_is_not_loaded_as_a_rule(valid_content_dir):
    # Arrange — `<rule-id>.cases.yaml` lives beside its rule (§12.3), and the
    # rule loader must not try to validate it as a Rule
    rules = load_rules(valid_content_dir)

    # Assert
    assert set(rules) == {RULE_ID}


def test_a_rule_directory_with_no_rules_loads_empty(tmp_path):
    # Arrange — an empty release is a legitimate starting state (§14 step 5
    # precedes step 6, which adds the first rule)
    (tmp_path / "rules").mkdir()

    # Act / Assert
    assert load_rules(tmp_path) == {}


def test_an_absent_rules_directory_loads_empty(tmp_path):
    # Arrange / Act / Assert — the directory appears when the first rule does
    assert load_rules(tmp_path) == {}


def test_two_rule_files_declaring_one_id_are_refused(valid_content_dir):
    # Arrange — one id, two files: the review saw both, only one would run
    write_yaml(valid_content_dir / "rules" / "duplicate.yaml", RULE)

    # Act / Assert
    with pytest.raises(ValueError, match=f"duplicate rule id '{RULE_ID}'"):
        load_rules(valid_content_dir)


def test_a_rule_that_fails_its_own_validators_names_its_file(valid_content_dir):
    # Arrange — gate 6 refuses a soft rule carrying blocks; the author needs to
    # know which of forty files to open
    broken = {**RULE, "severity": "passive_task"}
    write_yaml(valid_content_dir / "rules" / f"{RULE_ID}.yaml", broken)

    # Act / Assert
    with pytest.raises(ValueError, match=r"test-metformin-egfr\.yaml"):
        load_rules(valid_content_dir)


def test_thresholds_load_from_every_family_file_keyed_by_ref(valid_content_dir):
    # Arrange / Act
    thresholds = load_thresholds(valid_content_dir)

    # Assert
    assert set(thresholds) == {THRESHOLD_REF}
    assert thresholds[THRESHOLD_REF].unit == "mL/min/{1.73_m2}"


def test_a_threshold_value_loads_as_an_exact_decimal(valid_content_dir):
    # Arrange / Act — §7.5: decimal scalars are quoted strings, so "30" loads as
    # Decimal("30") and never as a float carrying binary error
    thresholds = load_thresholds(valid_content_dir)

    # Assert
    assert str(thresholds[THRESHOLD_REF].value) == "30"


def test_one_ref_declared_in_two_family_files_is_refused(valid_content_dir):
    # Arrange — a ref is a release's lookup key; two files claiming it is two
    # different bounds and no way to say which applies
    write_yaml(
        valid_content_dir / "thresholds" / "other-family.yaml",
        {"thresholds": [{**_threshold_document(valid_content_dir), "value": "45"}]},
    )

    # Act / Assert
    with pytest.raises(ValueError, match=f"duplicate threshold {THRESHOLD_REF!r}"):
        load_thresholds(valid_content_dir)


def _threshold_document(content_dir: Path) -> dict:
    from noor.catalogue.content_yaml import load_mapping, require_list

    path = content_dir / "thresholds" / "test-family.yaml"
    return require_list(path, load_mapping(path), "thresholds")[0]


def test_the_named_profile_loads(valid_content_dir):
    # Arrange / Act
    profile = load_profile(valid_content_dir, PROFILE_NAME)

    # Assert
    assert profile.name == PROFILE_NAME
    assert profile.source_family == "test-family"


def test_a_missing_profile_names_the_path_it_looked_for(valid_content_dir):
    # Arrange / Act / Assert — a release naming a profile nobody wrote
    with pytest.raises(FileNotFoundError, match="absent-profile"):
        load_profile(valid_content_dir, "absent-profile")


def test_the_release_document_lists_its_rules_thresholds_and_profile(valid_content_dir):
    # Arrange / Act
    document = load_release_document(valid_content_dir, RELEASE_ID)

    # Assert
    assert document.release_id == RELEASE_ID
    assert document.rules == (RULE_ID,)
    assert document.thresholds == (THRESHOLD_REF,)
    assert document.profile == PROFILE_NAME
    assert document.terminology_version == "term-test-1"


def test_a_release_document_whose_id_contradicts_its_filename_is_refused(valid_content_dir):
    # Arrange — the filename is how the release is found, so a mismatch means
    # `compile_release("rel-a")` would silently compile rel-b
    write_yaml(
        valid_content_dir / "releases" / f"{RELEASE_ID}.yaml",
        {**RELEASE, "release_id": "rel-something-else"},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="declares release_id"):
        load_release_document(valid_content_dir, RELEASE_ID)


def test_a_missing_release_names_the_path_it_looked_for(valid_content_dir):
    # Arrange / Act / Assert
    with pytest.raises(FileNotFoundError, match="rel-absent"):
        load_release_document(valid_content_dir, "rel-absent")


def test_a_release_naming_no_profile_is_refused(valid_content_dir):
    # Arrange — §10.5: a release without a tenant profile pins no source family
    write_yaml(
        valid_content_dir / "releases" / f"{RELEASE_ID}.yaml",
        {key: value for key, value in RELEASE.items() if key != "profile"},
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        load_release_document(valid_content_dir, RELEASE_ID)


def test_a_release_declaring_no_terminology_version_is_refused(valid_content_dir):
    # Arrange — §8.2 stamps the terminology version on every evaluation record,
    # and a release that declares none leaves the compiler inventing a pin
    write_yaml(
        valid_content_dir / "releases" / f"{RELEASE_ID}.yaml",
        {key: value for key, value in RELEASE.items() if key != "terminology_version"},
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        load_release_document(valid_content_dir, RELEASE_ID)
```

- [ ] **Step 3: Run it and watch it fail**

```bash
uv run pytest tests/catalogue/test_loader.py -q
```

Expected: `ModuleNotFoundError: No module named 'noor.catalogue.loader'`.

- [ ] **Step 4: Write the module**

Create `src/noor/catalogue/loader.py`:

```python
"""Per-kind content loading (SSOT §7.4).

This module validates nothing on its own. The `engine` models' validators are
the single-rule §10.4 gates, and everything here does is find the right files
and hand them over. What it owns is the layout — one rule per file under
`rules/`, thresholds grouped by family under `thresholds/`, one profile per
file, one release per file — and errors that name the file to open.

    content/
      rules/<rule-id>.yaml          plus <rule-id>.cases.yaml beside it
      thresholds/<family>.yaml      a `thresholds:` list per file
      profiles/<name>.yaml
      releases/<release-id>.yaml
"""

from pathlib import Path

from pydantic import Field, ValidationError

from noor.canon.model import NoorModel
from noor.catalogue.content_yaml import load_mapping, require_list, require_mapping_items
from noor.engine.content import Profile, Threshold
from noor.engine.rules import Rule

CASES_SUFFIX = ".cases.yaml"


class ReleaseDocument(NoorModel):
    """A release manifest: which content this release is made of (§7.4).

    Ids, not objects. Resolving them against the loaded rules and thresholds is
    release compilation's job, and an id that resolves to nothing is a gate, not
    a load error.

    `terminology_version` is here because §8.2's pins are release-level facts and
    this is the release-level document: `catalogue_release` and `profile` already
    come from here, and a pin the compiler invented would be a pin that lies.
    """

    release_id: str = Field(min_length=1)
    profile: str = Field(min_length=1)
    terminology_version: str = Field(min_length=1)
    rules: tuple[str, ...] = ()
    thresholds: tuple[str, ...] = ()


def load_rules(content_dir: Path) -> dict[str, Rule]:
    """Load every rule under `content_dir/rules/`, keyed by rule id."""
    rules: dict[str, Rule] = {}
    sources: dict[str, Path] = {}
    for path in sorted((content_dir / "rules").glob("*.yaml")):
        if path.name.endswith(CASES_SUFFIX):
            continue  # a rule's golden cases live beside it (§12.3)
        rule = _validate(path, Rule, load_mapping(path))
        if rule.id in rules:
            raise ValueError(f"{path}: duplicate rule id {rule.id!r}, also in {sources[rule.id]}")
        rules[rule.id] = rule
        sources[rule.id] = path
    return rules


def load_thresholds(content_dir: Path) -> dict[str, Threshold]:
    """Load every threshold under `content_dir/thresholds/`, keyed by ref."""
    thresholds: dict[str, Threshold] = {}
    for path in sorted((content_dir / "thresholds").glob("*.yaml")):
        documents = require_mapping_items(
            path, require_list(path, load_mapping(path), "thresholds"), "ref", "threshold"
        )
        for ref, document in documents.items():
            if ref in thresholds:
                raise ValueError(f"{path}: duplicate threshold {ref!r} across family files")
            thresholds[ref] = _validate(path, Threshold, document)
    return thresholds


def load_profile(content_dir: Path, name: str) -> Profile:
    """Load one tenant profile by name (§10.5)."""
    path = content_dir / "profiles" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"{path}: the release pins profile {name!r} and no file declares it")
    return _validate(path, Profile, load_mapping(path))


def load_release_document(content_dir: Path, release_id: str) -> ReleaseDocument:
    """Load one release manifest by id (§7.4)."""
    path = content_dir / "releases" / f"{release_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"{path}: no release declares {release_id!r}")
    document = _validate(path, ReleaseDocument, load_mapping(path))
    if document.release_id != release_id:
        raise ValueError(
            f"{path}: declares release_id {document.release_id!r} but the filename says "
            f"{release_id!r} — the filename is how a release is found"
        )
    return document


def _validate[ModelT: NoorModel](path: Path, model: type[ModelT], document: object) -> ModelT:
    """Validate one document, naming the file a content author has to open."""
    try:
        return model.model_validate(document)
    except ValidationError as error:
        raise ValueError(f"{path}: {error}") from error
```

`Path.glob` on a directory that does not exist returns an empty iterator rather than raising, which is why `test_an_absent_rules_directory_loads_empty` passes with no branch for it. The `_validate` re-raise is deliberate: a bare `ValidationError` says which *field* failed but not which of forty files carries it.

`def _validate[ModelT: NoorModel]` is PEP 695 generic syntax, available in 3.12 and what mypy `--strict` wants here. If mypy objects to the type-parameter syntax, use an explicit `TypeVar("ModelT", bound=NoorModel)` instead — the behaviour is identical.

- [ ] **Step 5: Run it and watch it pass**

```bash
uv run pytest tests/catalogue/test_loader.py -q
```

Expected: 17 passed.

- [ ] **Step 6: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

- [ ] **Step 7: Commit**

```bash
git add src/noor/catalogue/loader.py tests/catalogue/test_loader.py tests/catalogue/conftest.py
git commit -m "feat(catalogue): per-kind content loading

Rules, thresholds, profiles, and release manifests. Validates nothing itself —
the engine models' validators are the gates — but owns the file layout and
re-raises every failure naming the file to open. Adds the synthetic fixture
content tree every compiler test builds from, since content/ carries no
clinical claim."
```

---

### Task 8: The cases harness and gate 8

Gate 8 refuses "a rule with no `*.cases.yaml`, or cases that do not include at, just-below, and just-above rows for every threshold it references". §12.3's boundary-plus-pairwise selection, enforced.

**What "at, just-below, just-above" means here.** A case row states an observable and a value. The check is arithmetic against the threshold the rule references: some row's value equals it, some row's is lower, some row's is higher. This does **not** execute the cases — running them against the evaluator is §12's golden-case harness, and step 5 owns coverage of the boundary, not the run. That keeps `catalogue` free of the evaluator and makes the gate cheap enough to run on every merge.

**Files:**
- Create: `src/noor/catalogue/cases.py`
- Test: `tests/catalogue/test_cases.py`

**Interfaces:**
- Consumes: `content_yaml` helpers (Task 1); `noor.engine.rules.Rule`; `noor.engine.content.Threshold`.
- Produces:
  - `CaseRow(name: str, observable: str, value: Decimal, expected: str)`
  - `CaseFile(rule: str, cases: tuple[CaseRow, ...])`
  - `load_cases(content_dir: Path, rule_id: str) -> CaseFile | None` — `None` when no file exists; gate 8 turns that into the refusal, so the loader stays a loader.
  - `check_boundary_coverage(rule: Rule, cases: CaseFile | None, thresholds: Mapping[str, Threshold]) -> None` — raises `ValueError`. Task 9 calls it per rule.

- [ ] **Step 1: Write the failing test**

Create `tests/catalogue/test_cases.py`:

```python
"""Golden cases and §10.4 gate 8 (boundary coverage, §12.3).

The gate checks that the rows EXIST at, below, and above every threshold the
rule references. Running them against the evaluator is §12's golden-case
harness — a different job, and one that would drag the evaluator into
`catalogue`. Coverage is what a merge can afford to check on every push.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from noor.catalogue.cases import CaseFile, CaseRow, check_boundary_coverage, load_cases
from noor.catalogue.loader import load_rules, load_thresholds
from tests.catalogue.conftest import CASES, RULE_ID, THRESHOLD_REF, write_yaml


def _rule_and_thresholds(content_dir):
    return load_rules(content_dir)[RULE_ID], load_thresholds(content_dir)


def test_a_rules_cases_file_loads_beside_it(valid_content_dir):
    # Arrange / Act
    cases = load_cases(valid_content_dir, RULE_ID)

    # Assert
    assert cases is not None
    assert cases.rule == RULE_ID
    assert {row.value for row in cases.cases} == {
        Decimal("30"),
        Decimal("29.9"),
        Decimal("30.1"),
    }


def test_a_rule_with_no_cases_file_loads_as_none(valid_content_dir):
    # Arrange / Act / Assert — absence is the loader's answer; gate 8 turns it
    # into the refusal
    assert load_cases(valid_content_dir, "no-such-rule") is None


def test_boundary_rows_at_below_and_above_satisfy_the_gate(valid_content_dir):
    # Arrange
    rule, thresholds = _rule_and_thresholds(valid_content_dir)
    cases = load_cases(valid_content_dir, RULE_ID)

    # Act / Assert — the fixture tree is the passing case
    check_boundary_coverage(rule, cases, thresholds)


def test_a_rule_with_no_cases_file_at_all_is_refused(valid_content_dir):
    # Arrange
    rule, thresholds = _rule_and_thresholds(valid_content_dir)

    # Act / Assert — §12.3: a threshold nobody wrote a case for is a threshold
    # nobody proved fires at the number it names
    with pytest.raises(ValueError, match="gate 8"):
        check_boundary_coverage(rule, None, thresholds)


@pytest.mark.parametrize(
    ("dropped", "missing"),
    [("30", "at"), ("29.9", "just-below"), ("30.1", "just-above")],
)
def test_each_missing_boundary_row_is_named(valid_content_dir, dropped, missing):
    # Arrange — drop exactly one row and the gate says which one is gone
    thinned = {
        **CASES,
        "cases": [row for row in CASES["cases"] if row["value"] != dropped],
    }
    write_yaml(valid_content_dir / "rules" / f"{RULE_ID}.cases.yaml", thinned)
    rule, thresholds = _rule_and_thresholds(valid_content_dir)

    # Act / Assert
    with pytest.raises(ValueError, match=missing):
        check_boundary_coverage(rule, load_cases(valid_content_dir, RULE_ID), thresholds)


def test_rows_for_a_different_observable_do_not_cover_a_threshold(valid_content_dir):
    # Arrange — three rows on potassium prove nothing about an eGFR bound
    wrong = {
        **CASES,
        "cases": [{**row, "observable": "potassium"} for row in CASES["cases"]],
    }
    write_yaml(valid_content_dir / "rules" / f"{RULE_ID}.cases.yaml", wrong)
    rule, thresholds = _rule_and_thresholds(valid_content_dir)

    # Act / Assert
    with pytest.raises(ValueError, match="gate 8"):
        check_boundary_coverage(rule, load_cases(valid_content_dir, RULE_ID), thresholds)


def test_a_rule_referencing_no_threshold_needs_no_boundary_rows(valid_content_dir):
    # Arrange — a pure drug-interaction rule has no number to sit at the
    # boundary of, and gate 8 asks for rows "for every threshold it references"
    rule, thresholds = _rule_and_thresholds(valid_content_dir)
    bare = rule.model_copy(update={"when": rule.when.children[1]})

    # Act / Assert — a cases file is still expected; the boundary rows are not
    check_boundary_coverage(bare, CaseFile(rule=RULE_ID, cases=()), thresholds)


def test_a_cases_file_naming_a_different_rule_is_refused(valid_content_dir):
    # Arrange — a copy-pasted cases file that still names its source rule would
    # silently satisfy gate 8 for a rule it never exercised
    write_yaml(
        valid_content_dir / "rules" / f"{RULE_ID}.cases.yaml",
        {**CASES, "rule": "some-other-rule"},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="names rule"):
        load_cases(valid_content_dir, RULE_ID)


def test_a_case_value_loads_as_an_exact_decimal(valid_content_dir):
    # Arrange / Act — a float 29.9 would not compare equal to the boundary
    cases = load_cases(valid_content_dir, RULE_ID)

    # Assert
    assert cases is not None
    assert str(sorted(row.value for row in cases.cases)[0]) == "29.9"


def test_a_case_row_needs_a_name_a_value_and_an_expected_outcome():
    # Arrange / Act / Assert — a row nobody can read in a diff is not a golden
    # case (§7.5)
    with pytest.raises(ValidationError):
        CaseRow(name="", observable="egfr", value=Decimal("30"), expected="triggered")


def test_a_case_expects_an_outcome_from_the_declared_vocabulary():
    # Arrange / Act / Assert — §8.2's outcome vocabulary is closed, and a case
    # expecting "fires" proves nothing
    with pytest.raises(ValidationError):
        CaseRow(name="at", observable="egfr", value=Decimal("30"), expected="fires")
```

- [ ] **Step 2: Run it and watch it fail**

```bash
uv run pytest tests/catalogue/test_cases.py -q
```

Expected: `ModuleNotFoundError: No module named 'noor.catalogue.cases'`.

- [ ] **Step 3: Write the module**

Create `src/noor/catalogue/cases.py`:

```python
"""Golden cases and §10.4 gate 8 (boundary coverage, §12.3).

§12.3 selects cases at the boundary and one step either side. This checks the
rows EXIST — at the threshold, below it, above it — for every threshold a rule
references. It does not run them: executing a case against the evaluator is
§12's golden-case harness, a different job that would pull the evaluator into
`catalogue` and make a per-merge gate expensive. Coverage is what CI can afford
on every push; the run belongs to the validation ladder.
"""

from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import Field

from noor.canon.model import NoorModel
from noor.catalogue.content_yaml import load_mapping
from noor.engine.content import Threshold
from noor.engine.rules import Rule, walk_expression

CASE_OUTCOMES = ("triggered", "not_triggered", "indeterminate", "suppressed_by_governed_policy")


class CaseRow(NoorModel):
    """One golden case: an observable at a value, and the outcome it must produce."""

    name: str = Field(min_length=1)
    observable: str = Field(min_length=1)
    value: Decimal
    expected: Literal[CASE_OUTCOMES]


class CaseFile(NoorModel):
    """One rule's golden cases (§12.3)."""

    rule: str = Field(min_length=1)
    cases: tuple[CaseRow, ...] = ()


def load_cases(content_dir: Path, rule_id: str) -> CaseFile | None:
    """Load a rule's cases file, or None when it does not exist."""
    path = content_dir / "rules" / f"{rule_id}.cases.yaml"
    if not path.exists():
        return None
    case_file = CaseFile.model_validate(load_mapping(path))
    if case_file.rule != rule_id:
        raise ValueError(
            f"{path}: names rule {case_file.rule!r} but sits beside {rule_id!r} — a "
            f"copy-pasted cases file would satisfy gate 8 for a rule it never exercised"
        )
    return case_file


def check_boundary_coverage(
    rule: Rule, cases: CaseFile | None, thresholds: Mapping[str, Threshold]
) -> None:
    """Refuse a rule whose cases do not sit at and either side of every bound."""
    if cases is None:
        raise ValueError(
            f"rule {rule.id!r} has no `{rule.id}.cases.yaml` — a rule nobody wrote a case "
            f"for is a rule nobody proved (§12.3, §10.4 gate 8)"
        )
    for node in walk_expression(rule.when):
        if node.threshold_ref is None or node.fact is None:
            continue
        bound = thresholds[node.threshold_ref].value
        values = [row.value for row in cases.cases if row.observable == node.fact]
        missing = [
            label
            for label, covered in (
                ("at", any(value == bound for value in values)),
                ("just-below", any(value < bound for value in values)),
                ("just-above", any(value > bound for value in values)),
            )
            if not covered
        ]
        if missing:
            raise ValueError(
                f"rule {rule.id!r} references threshold {node.threshold_ref!r} on "
                f"`{node.fact}` with no {', '.join(missing)} case row — §12.3 selects at the "
                f"boundary and one step either side (§10.4 gate 8)"
            )
```

`thresholds[node.threshold_ref]` is a bare subscript on purpose: `EvaluationContext` already refuses a rule referencing an absent threshold, and Task 9 calls this *after* building the context. Guarding here would add a branch no content can reach.

`Literal[CASE_OUTCOMES]` unpacks a tuple constant into a `Literal`, which Pydantic accepts and mypy resolves when the tuple is a module-level `Final`. If mypy `--strict` objects, write the four strings inline in the `Literal` and keep `CASE_OUTCOMES` only if something else needs it.

- [ ] **Step 4: Run it and watch it pass**

```bash
uv run pytest tests/catalogue/test_cases.py -q
```

Expected: 13 passed.

- [ ] **Step 5: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

- [ ] **Step 6: Commit**

```bash
git add src/noor/catalogue/cases.py tests/catalogue/test_cases.py
git commit -m "feat(catalogue): golden-case loading and gate 8

Gate 8 checks that case rows exist at, below, and above every threshold a rule
references (§12.3's boundary selection). It does not run them — executing cases
against the evaluator is §12's golden-case harness, and pulling the evaluator
into catalogue would make a per-merge gate expensive."
```

### Task 9: The compiler and the cross-file gates

The step's public entry point, and every gate that needs more than one file to decide. Six of the eight gate-12 reference sites close here; the other two (`Expression.fact`, `Expression.threshold_ref`) are already closed by `EvaluationContext`, which is the last thing this function constructs.

**Cleanup 2 lands in this task and nowhere else.** `FORBIDDEN_REQUIREMENT_OBSERVABLES`, `_requirements_never_name_encounter_or_trigger_state`, and their test all move in step 1, in one commit, because they are one thing: a denylist replaced by an allowlist. Deleting the validator before the allowlist exists ships a commit with gate 11 unenforced; deleting the test before the validator leaves a `raise` branch uncovered and `--cov-fail-under=100` fails. Together, gate 11 goes from "these three names are forbidden" to "only registry observables and `active_medications` are permitted", which refuses `admission_trigger` and `encounter.state` alike — the exact defeat §4.2 point 2 warned a name-matching check would suffer.

**Files:**
- Create: `src/noor/catalogue/compiler.py`
- Modify: `src/noor/engine/rules.py:115-119` (delete the constant), `:421-432` (delete the validator)
- Modify: `tests/engine/test_rules.py:415-427` (delete the moved gate-11 test)
- Test: `tests/catalogue/test_compiler.py`

**Interfaces:**
- Consumes: `load_registry` (existing); `load_conditions`, `load_ingredients` → `.ids` (Task 2); `load_charter`, `check_code_systems_are_chartered` (Task 3); `ObservableEntry.renal_metric` (Task 4); `Threshold.states_metric` (Task 4); `ACTIVE_MEDICATIONS` (Task 6); `load_rules`, `load_thresholds`, `load_profile`, `load_release_document`, `ReleaseDocument` (Task 7); `load_cases`, `check_boundary_coverage` (Task 8); `CatalogueRelease`, `Pins`, `EvaluationContext`, `ENGINE_VERSION` (existing).
- Produces:
  - `compile_release(content_dir: Path, release_id: str) -> EvaluationContext` — the only public entry point of this step. Raises `ValueError` at the first gate it trips; no partial-success mode.
  - `CONTENT_DIR: Path` — the repo's committed content root, so callers and tests name it once.

- [ ] **Step 1: Move gate 11 from denylist to nowhere**

Delete from `src/noor/engine/rules.py` — the constant at lines 115-119:

```python
# §8.1/§8.4 invariant 10: a rule cannot ask which visit produced a fact or which
# trigger invoked it. Enforced on Requirement.observable at load (gate 11).
FORBIDDEN_REQUIREMENT_OBSERVABLES: frozenset[str] = frozenset(
    {"visit_state", "encounter_state", "narrative"}
)
```

and the validator at lines 421-432:

```python
    @model_validator(mode="after")
    def _requirements_never_name_encounter_or_trigger_state(self) -> Self:
        for requirement in self.requires:
            if (
                requirement.observable in FORBIDDEN_REQUIREMENT_OBSERVABLES
                or "trigger" in requirement.observable
            ):
                raise ValueError(
                    f"requirement `{requirement.observable}` is encounter, narrative, or "
                    f"trigger state, which no rule may read (§8.1, §10.4 gate 11)"
                )
        return self
```

Delete from `tests/engine/test_rules.py` the parametrized test at lines 415-427 (`test_requirements_cannot_reference_encounter_narrative_or_trigger_state`) — it reappears in step 2 against the allowlist, case for case.

`tests/test_import_direction.py` is untouched by this: it reads *identifiers*, and `FORBIDDEN_STATE_NAMES_IN_ENGINE` lives in the test file, not in `rules.py`.

- [ ] **Step 2: Write the failing compiler test**

Create `tests/catalogue/test_compiler.py`:

```python
"""Release compilation and every gate that needs more than one file (§10.4).

One refusal test per gate, each injecting exactly one violation into an
otherwise-valid tree, so the assertion names the gate rather than an unrelated
failure. The single-rule gates are tested in `tests/engine/test_rules.py` where
their validators live; what is here is what the compiler alone can decide.
"""

import pytest

from noor.catalogue.compiler import compile_release
from tests.catalogue.conftest import (
    PROFILE_NAME,
    REGISTRY,
    RELEASE,
    RELEASE_ID,
    RULE,
    RULE_ID,
    THRESHOLD,
    THRESHOLD_REF,
    write_yaml,
)


def _write_rule(content_dir, **overrides):
    write_yaml(content_dir / "rules" / f"{RULE_ID}.yaml", {**RULE, **overrides})


def test_a_valid_content_tree_compiles_to_an_evaluation_context(valid_content_dir):
    # Arrange / Act
    context = compile_release(valid_content_dir, RELEASE_ID)

    # Assert — the release resolved its ids into objects, not strings
    assert context.release.release_id == RELEASE_ID
    assert [rule.id for rule in context.release.rules] == [RULE_ID]
    assert [threshold.ref for threshold in context.release.thresholds] == [THRESHOLD_REF]
    assert context.release.profile.name == PROFILE_NAME
    assert context.registry.entry("egfr").canonical_ucum == "mL/min/{1.73_m2}"


def test_the_compiled_pins_carry_the_release_profile_and_terminology_version(valid_content_dir):
    # Arrange / Act — §8.2's pins are stamped on every evaluation record, so
    # they are compiled once here and never assembled per evaluation
    context = compile_release(valid_content_dir, RELEASE_ID)

    # Assert
    assert context.pins.catalogue_release == RELEASE_ID
    assert context.pins.profile == f"{PROFILE_NAME}@1.0.0"
    assert context.pins.source_family == "test-family"
    assert context.pins.terminology_version == "term-test-1"
    assert context.pins.snapshot_id is None


def test_a_release_naming_a_rule_no_file_declares_is_refused(valid_content_dir):
    # Arrange — the manifest is the release's contents; an id resolving to
    # nothing means the release ships less than it says it does
    write_yaml(
        valid_content_dir / "releases" / f"{RELEASE_ID}.yaml",
        {**RELEASE, "rules": [RULE_ID, "no-such-rule"]},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="no-such-rule"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_release_naming_a_threshold_no_file_declares_is_refused(valid_content_dir):
    # Arrange
    write_yaml(
        valid_content_dir / "releases" / f"{RELEASE_ID}.yaml",
        {**RELEASE, "thresholds": [THRESHOLD_REF, "no.such_threshold"]},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="no.such_threshold"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_rule_naming_a_condition_concept_no_valueset_declares_is_refused(valid_content_dir):
    # Arrange — claim 20, site 3: `on_dialysys` is a typo that passes every
    # existing validator and silently never matches at evaluation
    _write_rule(
        valid_content_dir,
        scope={"include": [{"op": "condition", "concept": "on_dialysys"}], "exclude": []},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="on_dialysys"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_rule_naming_an_ingredient_no_valueset_declares_is_refused(valid_content_dir):
    # Arrange — claim 20, site 4
    _write_rule(
        valid_content_dir,
        when={
            "op": "all",
            "children": [
                {"op": "lt", "fact": "egfr", "threshold_ref": THRESHOLD_REF},
                {"op": "drug_active", "ingredient_id": "metfromin"},
            ],
        },
    )

    # Act / Assert
    with pytest.raises(ValueError, match="metfromin"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_an_allergy_leaf_naming_an_unknown_ingredient_is_refused(valid_content_dir):
    # Arrange — the allergy leaf names the same id space as the drug leaves
    # (§5.5's culprit is an ingredient id), so the closure covers it too
    _write_rule(
        valid_content_dir,
        when={
            "op": "all",
            "children": [
                {"op": "lt", "fact": "egfr", "threshold_ref": THRESHOLD_REF},
                {"op": "drug_active", "ingredient_id": "metformin"},
                {
                    "op": "allergy",
                    "ingredient_id": "amoxycillin",
                    "verification_status": "confirmed",
                    "severity": "severe",
                },
            ],
        },
    )

    # Act / Assert
    with pytest.raises(ValueError, match="amoxycillin"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_monitor_naming_an_observable_the_registry_does_not_govern_is_refused(valid_content_dir):
    # Arrange — claim 20, site 7. This was unguarded: no engine code reads
    # `monitors` today, so a typo lies dormant until §11 schedules from it, and
    # surfaces as a renal recheck that is never scheduled
    _write_rule(
        valid_content_dir,
        monitors=[{"observable": "creatinin", "due_in_days": 90, "reason": "renal function"}],
    )

    # Act / Assert
    with pytest.raises(ValueError, match="creatinin"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_block_naming_an_ingredient_no_valueset_declares_is_refused(valid_content_dir):
    # Arrange — claim 20, site 8. Also unguarded, and worse: a hard stop whose
    # `order_of` is a typo blocks nothing, which is the highest severity in the
    # system failing silently
    _write_rule(
        valid_content_dir,
        then={**RULE["then"], "blocks": {"order_of": "metfromin"}},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="metfromin"):
        compile_release(valid_content_dir, RELEASE_ID)


@pytest.mark.parametrize(
    "observable",
    ["visit_state", "encounter_state", "narrative", "admission_trigger", "encounter.state"],
)
def test_a_requirement_naming_encounter_narrative_or_trigger_state_is_refused(
    valid_content_dir, observable
):
    # Arrange — gate 11, now by allowlist. §12.6 claim 18 for the visit and
    # trigger names, claim 42 for `narrative`. `encounter.state` is the spelling
    # §4.2 point 2 says a name-matching check would be defeated by; an allowlist
    # refuses it for the same reason it refuses every other unknown name
    _write_rule(
        valid_content_dir,
        requires=[
            {"observable": observable, "on_unusable": "indeterminate", "max_age_days": 90},
            {"observable": "active_medications", "on_unusable": "indeterminate"},
        ],
        when={"op": "drug_active", "ingredient_id": "metformin"},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="gate 11"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_active_medications_is_the_one_requirement_observable_outside_the_registry(
    valid_content_dir,
):
    # Arrange / Act — the allowlist admits it by name (section 9): it is a
    # list-level fact, not a measured observable, and it has no registry row
    context = compile_release(valid_content_dir, RELEASE_ID)

    # Assert
    observables = {
        requirement.observable
        for rule in context.release.rules
        for requirement in rule.requires
    }
    assert "active_medications" in observables


def test_a_renal_rule_omitting_its_renal_metric_is_refused(valid_content_dir):
    # Arrange — gate 15a, claim 49 first half: `egfr` is registry-marked as a
    # renal metric, so a rule requiring it must say which metric it means
    _write_rule(
        valid_content_dir,
        requires=[
            {"observable": "egfr", "on_unusable": "indeterminate", "max_age_days": 90},
            {"observable": "active_medications", "on_unusable": "indeterminate"},
        ],
    )

    # Act / Assert
    with pytest.raises(ValueError, match="gate 15"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_rule_declaring_a_metric_its_threshold_does_not_state_is_refused(valid_content_dir):
    # Arrange — gate 15b, claim 49 second half: the rule reasons in eGFR, the
    # cited label stated creatinine clearance. They diverge by weight (claim 36),
    # and the gate refuses rather than warns
    write_yaml(
        valid_content_dir / "thresholds" / "test-family.yaml",
        {"thresholds": [{**THRESHOLD, "states_metric": "crcl"}]},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="gate 15"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_threshold_stating_no_metric_pairs_with_any_renal_rule(valid_content_dir):
    # Arrange — a non-renal threshold states no metric, and gate 15b compares
    # only where both halves speak: `states_metric: null` is silence, not a
    # contradiction
    write_yaml(
        valid_content_dir / "thresholds" / "test-family.yaml",
        {"thresholds": [{**THRESHOLD, "states_metric": None}]},
    )

    # Act / Assert — compiles
    assert compile_release(valid_content_dir, RELEASE_ID).release.release_id == RELEASE_ID


def test_a_rule_citing_a_code_system_the_charter_does_not_name_is_refused(valid_content_dir):
    # Arrange — gate 17. The registry's code_unit_map keys are the repo's live
    # code-system citations, and the charter is joined to them by URI
    entry = {
        **REGISTRY["observables"][0],
        "code_unit_map": {"http://snomed.info/sct|445518008": "mL/min/{1.73_m2}"},
    }
    write_yaml(valid_content_dir / "observables" / "registry.yaml", {"observables": [entry]})

    # Act / Assert
    with pytest.raises(ValueError, match="gate 17"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_rule_with_no_boundary_cases_is_refused(valid_content_dir):
    # Arrange — gate 8, reached through the compiler rather than called directly
    (valid_content_dir / "rules" / f"{RULE_ID}.cases.yaml").unlink()

    # Act / Assert
    with pytest.raises(ValueError, match="gate 8"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_profile_omitting_a_required_field_is_refused_not_defaulted(valid_content_dir):
    # Arrange — claim 29's refusal pattern, on the fields `Profile` carries
    # today. Its operational-policy half belongs to the §11 app packages that
    # own those schemas (steps 8-12, amendment 6)
    write_yaml(
        valid_content_dir / "profiles" / f"{PROFILE_NAME}.yaml",
        {"name": PROFILE_NAME, "version": "1.0.0", "disablements": []},
    )

    # Act / Assert — no default source family is invented
    with pytest.raises(ValueError, match="source_family"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_rule_whose_threshold_resolves_outside_the_pinned_family_is_refused(valid_content_dir):
    # Arrange — gate 7, enforced by EvaluationContext and reached here: the
    # compiler's last step is constructing it, so its refusals are the
    # compiler's refusals (§7.3, "source families are never blended")
    write_yaml(
        valid_content_dir / "thresholds" / "test-family.yaml",
        {"thresholds": [{**THRESHOLD, "source_family": "other-family"}]},
    )

    # Act / Assert
    with pytest.raises(ValueError, match="never blended"):
        compile_release(valid_content_dir, RELEASE_ID)


def test_a_rule_comparing_against_a_threshold_in_a_foreign_unit_is_refused(valid_content_dir):
    # Arrange — also EvaluationContext's: mL/min is not mL/min/{1.73_m2}, and
    # a target is never silently rescaled (§6.1)
    write_yaml(
        valid_content_dir / "thresholds" / "test-family.yaml",
        {"thresholds": [{**THRESHOLD, "unit": "mL/min"}]},
    )

    # Act / Assert
    with pytest.raises(ValueError):
        compile_release(valid_content_dir, RELEASE_ID)


def test_an_empty_release_compiles(valid_content_dir):
    # Arrange — §14 step 5 precedes step 6, so the release this step commits
    # holds no rules and no thresholds. That must be a compiling state, or the
    # step cannot land before its content does
    write_yaml(
        valid_content_dir / "releases" / f"{RELEASE_ID}.yaml",
        {**RELEASE, "rules": [], "thresholds": []},
    )

    # Act
    context = compile_release(valid_content_dir, RELEASE_ID)

    # Assert
    assert context.release.rules == ()
    assert context.release.thresholds == ()
```

- [ ] **Step 3: Run it and watch it fail**

```bash
uv run pytest tests/catalogue/test_compiler.py -q
```

Expected: `ModuleNotFoundError: No module named 'noor.catalogue.compiler'`. `tests/engine/test_rules.py` still passes — step 1 deleted a validator and its test together.

- [ ] **Step 4: Write the compiler**

Create `src/noor/catalogue/compiler.py`:

```python
"""Release compilation: content files in, a pinned `EvaluationContext` out (§7.4).

The one public entry point of `catalogue`, and the one place that reads more
than one kind of content file at a time. Everything here is a gate that needs
that breadth: a rule and the registry, a rule and the valuesets, a rule and its
thresholds, a rule and its golden cases. Single-rule gates live on the `engine`
models where a rule alone can decide them (§10.4).

`catalogue` is the filesystem boundary above the device boundary (§4.2): this
module reads files, and nothing below it does. It acquires no clock, no HTTP
client, and no database session — `compile_release` takes an explicit
`release_id` rather than "the newest", because there is no ordering authority
here to make that choice.

Bad content raises at the first gate it trips. There is no partial-success
mode: a content tree either compiles whole or is refused.
"""

from pathlib import Path

from noor.canon.registry import ObservableRegistry, UnknownObservableError
from noor.catalogue.cases import check_boundary_coverage, load_cases
from noor.catalogue.loader import (
    load_profile,
    load_release_document,
    load_rules,
    load_thresholds,
)
from noor.catalogue.registry_loader import load_registry
from noor.catalogue.terminology import check_code_systems_are_chartered, load_charter
from noor.catalogue.valuesets import (
    ConditionValueset,
    IngredientValueset,
    load_conditions,
    load_ingredients,
)
from noor.engine.content import (
    ENGINE_VERSION,
    CatalogueRelease,
    EvaluationContext,
    Pins,
    Threshold,
)
from noor.engine.rules import ACTIVE_MEDICATIONS, Operator, Rule, walk_expression

CONTENT_DIR = Path(__file__).resolve().parents[3] / "content"

# The operators whose `ingredient_id` names the ingredient valueset. All three
# read the same id space: `evaluate.py` compares an allergy's culprit
# ingredient and a medication's ingredient against the same authored string.
_INGREDIENT_OPERATORS = frozenset(
    {Operator.drug_active, Operator.drug_requested, Operator.allergy}
)


def compile_release(content_dir: Path, release_id: str) -> EvaluationContext:
    """Compile one release into the pinned world `evaluate` runs against.

    Raises `ValueError` at the first gate the content trips.
    """
    registry = load_registry(content_dir / "observables" / "registry.yaml")
    conditions = load_conditions(content_dir / "valuesets" / "conditions.yaml")
    ingredients = load_ingredients(content_dir / "valuesets" / "ingredients.yaml")
    charter = load_charter(content_dir / "terminology" / "charter.yaml")
    check_code_systems_are_chartered(charter, registry)

    rules = load_rules(content_dir)
    thresholds = load_thresholds(content_dir)
    document = load_release_document(content_dir, release_id)
    profile = load_profile(content_dir, document.profile)

    released_rules = tuple(_resolve(rules, document.rules, "rule", release_id))
    released_thresholds = tuple(
        _resolve(thresholds, document.thresholds, "threshold", release_id)
    )
    threshold_by_ref = {threshold.ref: threshold for threshold in released_thresholds}

    for rule in released_rules:
        _check_authored_names_exist(rule, registry, conditions, ingredients)
        _check_renal_metric(rule, registry, threshold_by_ref)
        check_boundary_coverage(rule, load_cases(content_dir, rule.id), threshold_by_ref)

    release = CatalogueRelease(
        release_id=document.release_id,
        rules=released_rules,
        thresholds=released_thresholds,
        profile=profile,
    )
    pins = Pins(
        catalogue_release=release.release_id,
        profile=f"{profile.name}@{profile.version}",
        source_family=profile.source_family,
        engine_version=ENGINE_VERSION,
        terminology_version=document.terminology_version,
    )
    return EvaluationContext(release=release, registry=registry, pins=pins)


def _resolve[ItemT](
    available: dict[str, ItemT], named: tuple[str, ...], noun: str, release_id: str
) -> list[ItemT]:
    """Turn a manifest's ids into the objects they name."""
    missing = sorted(set(named) - set(available))
    if missing:
        raise ValueError(
            f"release {release_id!r} names {noun}s no file declares: {missing} — a "
            f"release ships exactly what its manifest lists (§7.4)"
        )
    return [available[name] for name in named]


def _check_authored_names_exist(
    rule: Rule,
    registry: ObservableRegistry,
    conditions: ConditionValueset,
    ingredients: IngredientValueset,
) -> None:
    """Close every authored name-reference against the registry that owns it.

    §10.4 gate 12. `Expression.fact` and `Expression.threshold_ref` are closed by
    `EvaluationContext` at the end of compilation; the rest are closed here. A
    name that exists nowhere does not fail loudly at evaluation — the rule
    silently never matches, or silently schedules nothing, which is the worst
    failure mode this engine has.
    """
    for node in (*walk_expression(rule.when), *_scope_nodes(rule)):
        if node.concept is not None and node.concept not in conditions.ids:
            raise ValueError(
                f"rule {rule.id!r} names condition concept {node.concept!r}, which "
                f"`valuesets/conditions.yaml` does not declare (§10.4 gate 12)"
            )
        if node.op in _INGREDIENT_OPERATORS and node.ingredient_id not in ingredients.ids:
            raise ValueError(
                f"rule {rule.id!r} names ingredient {node.ingredient_id!r}, which "
                f"`valuesets/ingredients.yaml` does not declare (§10.4 gate 12)"
            )

    for requirement in rule.requires:
        if requirement.observable == ACTIVE_MEDICATIONS:
            continue  # a list-level fact, not a measured observable (§7.1)
        try:
            registry.entry(requirement.observable)
        except UnknownObservableError as error:
            raise ValueError(
                f"rule {rule.id!r} requires {requirement.observable!r}, which the "
                f"observable registry does not govern. A rule reads measured "
                f"observables and the medication list; encounter, narrative, and "
                f"trigger state are not readable at all (§8.1, §10.4 gates 11, 12)"
            ) from error

    for monitor in rule.monitors:
        try:
            registry.entry(monitor.observable)
        except UnknownObservableError as error:
            raise ValueError(
                f"rule {rule.id!r} monitors {monitor.observable!r}, which the observable "
                f"registry does not govern — a recheck nobody can schedule (§10.4 gate 12)"
            ) from error

    if rule.then.blocks is not None and rule.then.blocks.order_of not in ingredients.ids:
        raise ValueError(
            f"rule {rule.id!r} blocks orders of {rule.then.blocks.order_of!r}, which "
            f"`valuesets/ingredients.yaml` does not declare — a hard stop that blocks "
            f"nothing (§10.4 gate 12)"
        )


def _scope_nodes(rule: Rule) -> list[object]:
    """Every expression node in either half of a rule's scope (§7.1)."""
    return [
        node
        for side in (rule.scope.include, rule.scope.exclude)
        for root in side
        for node in walk_expression(root)
    ]


def _check_renal_metric(
    rule: Rule, registry: ObservableRegistry, thresholds: dict[str, Threshold]
) -> None:
    """Refuse a renal rule that does not say which renal metric it means.

    §10.4 gate 15. eGFR and creatinine clearance diverge by weight (§12.6 claim
    36), so a rule reasoning in one against a bound stated in the other is
    wrong by an amount nobody sees. Which observables are renal metrics is the
    registry's declaration, and which metric a bound states is the threshold's;
    no substring of a citation is read to decide either.
    """
    for requirement in rule.requires:
        if requirement.observable == ACTIVE_MEDICATIONS:
            continue
        if registry.entry(requirement.observable).renal_metric is None:
            continue
        if requirement.renal_metric is None:
            raise ValueError(
                f"rule {rule.id!r} requires {requirement.observable!r}, a renal metric, "
                f"without declaring `renal_metric` — eGFR and creatinine clearance are "
                f"not interchangeable numbers (§10.4 gate 15)"
            )
        for node in walk_expression(rule.when):
            if node.threshold_ref is None:
                continue
            stated = thresholds[node.threshold_ref].states_metric
            if stated is not None and stated != requirement.renal_metric:
                raise ValueError(
                    f"rule {rule.id!r} declares `renal_metric: {requirement.renal_metric}` "
                    f"but threshold {node.threshold_ref!r} states its bound in {stated} — "
                    f"the two diverge by weight and are refused, never warned "
                    f"(§10.4 gate 15, §12.6 claim 49)"
                )
```

Four notes on the shape:

- **`_scope_nodes` returns `list[object]`** only because `Expression` is not imported here for anything else; if mypy `--strict` objects to the iteration, import `Expression` from `noor.engine.rules` and annotate `list[Expression]`. The scope halves are walked because §7.1's scope holds `condition` leaves, and a typo there silently admits or excludes the wrong patients — the same failure as a typo in `when`.
- **`node.ingredient_id` needs no `is None` guard.** The three ingredient operators each require it at load (`test_ingredient_predicates_name_their_ingredient`), so inside the `_INGREDIENT_OPERATORS` branch it is always a string. A guard here would be an unreachable branch and `--cov-fail-under=100` would fail on it.
- **`thresholds[node.threshold_ref]` is a bare subscript**, as in `cases.py`: `_resolve` has already refused a release naming a threshold no file declares, and `EvaluationContext` refuses a rule referencing one outside the release. Both run against the same dict.
- **`def _resolve[ItemT]`** is PEP 695 generic syntax again, matching `loader._validate`.

- [ ] **Step 5: Run it and watch it pass**

```bash
uv run pytest tests/catalogue/test_compiler.py -q
```

Expected: 22 passed.

- [ ] **Step 6: Run the whole suite**

```bash
uv run ruff check . && uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Gate 11's coverage moved from `rules.py` to `compiler.py` in one commit; if coverage reports an uncovered branch in either, the move is incomplete.

- [ ] **Step 7: Commit**

```bash
git add src/noor/catalogue/compiler.py tests/catalogue/test_compiler.py \
        src/noor/engine/rules.py tests/engine/test_rules.py
git commit -m "feat(catalogue): release compilation and the cross-file gates

compile_release is the step's only public entry point: content files in, a
pinned EvaluationContext out, raising at the first gate bad content trips.

Closes the six gate-12 reference sites a single rule cannot decide — condition
concepts, ingredient ids, requirement observables, monitor observables, and
order blocks — plus gates 15a, 15b, 17, and 8. Monitor.observable and
OrderBlock.order_of were previously unguarded: no engine code reads either, so
a typo lay dormant until an app consumed it and surfaced as a recheck never
scheduled or a hard stop that blocked nothing.

Gate 11 moves from a three-name denylist on Requirement to the compiler's
allowlist, which refuses \`encounter.state\` for the same reason it refuses every
other unknown name — the defeat SSOT §4.2 point 2 warned a name-matching check
would suffer."
```

---

### Task 10: The real `content/` tree, the widened seam, and the stale project docs

Three things that only make sense once `compile_release` exists: the two content files that make the committed tree compilable, the import-direction test extended to cover `catalogue`, and `CLAUDE.md` / `AGENTS.md` brought back in line with what the repository actually holds (**cleanup 3**).

**The committed content stays clinically clean.** `content/profiles/riyadh-hh.yaml` names one source family and disables nothing; `content/releases/rel-2026-09-01.yaml` names that profile and empty rule and threshold lists. Neither carries a clinical claim — no rule, no number, no citation, no approver — so spec decision 4 holds and §14 step 6 still authors the first real rule (deviation 5).

**The profile is `version: "1"`, not `"3"`.** `tests/conftest.py:419`'s `make_pins` fixture says `"profile": "riyadh-hh@3"`, and it stays as it is: it is synthetic engine-test scaffolding for a package that has never heard of `content/`, and nothing checks the two against each other. A file committed for the first time claiming version 3 would be the only false statement in the tree. The test below asserts `riyadh-hh@1` accordingly — do not "fix" either side to match the other.

**Files:**
- Create: `content/profiles/riyadh-hh.yaml`, `content/releases/rel-2026-09-01.yaml`, `tests/catalogue/test_content_tree.py`
- Modify: `tests/test_import_direction.py:1-19` (docstring), `:40-76` (constants), `:231-243` (the wall-clock test)
- Modify: `CLAUDE.md:8-10`, `:34-41`, `:42-44`, `:165-167` — and `AGENTS.md`, byte-identically

**Interfaces:**
- Consumes: `compile_release`, `CONTENT_DIR` (Task 9); `Profile` (existing, `src/noor/engine/content.py:101`); `ObservableRegistry.entry` (existing, `src/noor/canon/registry.py:189`).
- Produces: nothing later tasks import — Task 11 edits documents only.

- [ ] **Step 1: Write the failing test**

Create `tests/catalogue/test_content_tree.py`:

```python
"""The committed `content/` tree compiles (spec section 11).

Every other catalogue test builds a synthetic tree under `tmp_path`, because
`content/` carries no clinical content yet — §14 step 6 authors the first rule.
This file is the one test that reads the real directory: it proves the committed
infrastructure files agree with each other, with the observable registry, and
with the terminology charter, and that a release produces the pins §8.2 requires.
"""

from noor.catalogue.compiler import CONTENT_DIR, compile_release

RELEASE_ID = "rel-2026-09-01"


def test_the_committed_content_tree_compiles_into_a_pinned_context():
    # Arrange / Act — the real directory, not a fixture tree
    context = compile_release(CONTENT_DIR, RELEASE_ID)

    # Assert — §8.2's pins are release-level facts, read off release-level files
    assert context.pins.catalogue_release == RELEASE_ID
    assert context.pins.profile == "riyadh-hh@1"
    assert context.pins.source_family == "ada-kdigo"
    assert context.pins.terminology_version == "term-2026-06-01"
    assert context.pins.snapshot_id is None


def test_the_committed_release_carries_no_clinical_content_yet():
    # Arrange / Act
    context = compile_release(CONTENT_DIR, RELEASE_ID)

    # Assert — spec decision 4: a tenant profile and an empty release carry no
    # clinical claim. §14 step 6 is what makes these tuples non-empty.
    assert context.release.rules == ()
    assert context.release.thresholds == ()


def test_the_committed_registry_is_loaded_and_chartered():
    # Arrange / Act
    context = compile_release(CONTENT_DIR, RELEASE_ID)

    # Assert — the registry and gate 17's charter check run whether or not the
    # release has rules in it, so an unchartered code system fails here today
    assert len(context.registry.entries) == 10
    assert context.registry.entry("egfr").renal_metric == "egfr"


def test_the_content_tree_carries_no_golden_cases_yet():
    # Arrange / Act — §7.4: "a single pytest parametrize discovers every
    # *.cases.yaml in the tree". It discovers none today.
    discovered = sorted((CONTENT_DIR / "rules").glob("*.cases.yaml"))

    # Assert — an asserted zero, not an oversight. When step 6 lands the first
    # rule and its cases file together, this test fails and is rewritten in the
    # same pull request as the rule that broke it.
    assert discovered == []
```

`CONTENT_DIR / "rules"` does not exist yet. `Path.glob` on a missing directory yields nothing rather than raising, which is why the last test needs no guard.

- [ ] **Step 2: Run the tests and watch three of them fail**

```bash
uv run pytest tests/catalogue/test_content_tree.py -q
```

Expected: 3 failed, 1 passed. The three failures are `FileNotFoundError: .../content/releases/rel-2026-09-01.yaml: no release declares 'rel-2026-09-01'`. The fourth passes already — there are no cases files, which is exactly what it asserts.

- [ ] **Step 3: Write the two content files**

`content/profiles/riyadh-hh.yaml`:

```yaml
# The pilot tenant profile (SSOT §10.5).
#
# `source_family` pins which evidence base this tenant's numbers come from. It is
# never blended: the compiler refuses a release whose thresholds resolve across
# two families (§7.3), so this one line decides the answer for every threshold the
# tenant ever sees.
#
# `version` is bumped by pull request whenever any field below changes. It is
# copied into every evaluation record's pins as `riyadh-hh@1` (§8.2), which is how
# a card rendered last month is traced back to the profile that produced it.
#
# `disablements: []` is a positive statement, not a placeholder: no rule is
# switched off for this tenant. A disablement carries a reason, a requester, and
# an approver (§10.5) — switching a rule off is a governed act, not a config edit.
name: riyadh-hh
version: "1"
source_family: ada-kdigo
disablements: []
```

`content/releases/rel-2026-09-01.yaml`:

```yaml
# A release manifest (SSOT §7.4). A release is immutable: it names ids, and the
# objects those ids resolve to are fixed by the commit this file was tagged in.
# Correcting content means a new release, never an edit here.
#
# `rules` and `thresholds` are empty because no clinical content is authored yet —
# §14 step 6 is the first rule. The file exists so the compiler has a release to
# compile and the committed tree is exercised from the first commit, exactly as
# §14 step 1's seam test runs before there is anything to import.
#
# `terminology_version` is a release-level fact because §8.2's pins are
# release-level facts. A pin the compiler invented would be a pin that lies.
release_id: rel-2026-09-01
profile: riyadh-hh
terminology_version: term-2026-06-01
rules: []
thresholds: []
```

`release_id` must equal the filename stem — `load_release_document` refuses the mismatch, because the filename is how a release is found.

- [ ] **Step 4: Run the tests and watch them pass**

```bash
uv run pytest tests/catalogue/test_content_tree.py -q
```

Expected: 4 passed.

- [ ] **Step 5: Extend the seam test to `catalogue`**

`catalogue` reads files, so the filesystem ban cannot apply to it — but the clock, HTTP, and database bans must, and today nothing checks. A compiler that reads the wall clock cannot be replayed against a past release; one that reaches the network compiles content nobody reviewed.

In `tests/test_import_direction.py`, replace the docstring's second paragraph (`:7-13`):

```python
`app` imports from `canon`, `engine`, and `catalogue` — never the reverse.
`canon` and `engine` are pure: no database, no HTTP, no filesystem, no clock
(§8.4 invariant 8 applied to the whole boundary). `catalogue` is the filesystem
boundary above them, so it reads files — and acquires nothing else: no clock, no
HTTP client, no database session (§4.2). `canon` additionally never names a
treatment threshold: §6.4's three boundary types are separate, and
`docs/testing-standards.md` requires a test that proves they are not read from
one another. This test exists from the first commit, before there is anything
to import (§14 step 1).
```

Add after `FORBIDDEN_IMPORT_ROOTS_IN_PURE` (`:68`):

```python
# The subset of the above that binds every boundary package, `catalogue` included.
# `os`, `pathlib`, and `io` are absent by design — reading content files is
# `catalogue`'s whole job. A clock, a socket, or a session is not: `compile_release`
# takes an explicit `release_id` because there is no ordering authority here, and
# content that was not reviewed in a pull request must not be reachable at all.
FORBIDDEN_INFRASTRUCTURE_ROOTS = frozenset(
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
        "urllib",
        "http",
        "smtplib",
        "subprocess",
        "time",
    }
)
```

Add the new test immediately after `test_pure_packages_import_no_io_or_clock_modules`:

```python
@pytest.mark.parametrize("package", BOUNDARY_PACKAGES)
def test_boundary_packages_acquire_no_clock_http_client_or_database(package: str):
    # Arrange / Act
    offenders = [
        (path, module)
        for path in _python_files(package)
        for module in _imported_modules(path)
        if module.split(".")[0] in FORBIDDEN_INFRASTRUCTURE_ROOTS
    ]

    # Assert
    assert not offenders, (
        f"{package} must acquire no clock, HTTP client, or database session "
        f"(SSOT §4.2, §8.4.8): {offenders}"
    )
```

For `canon` and `engine` this overlaps the pure test, deliberately: the constant is a strict subset of `FORBIDDEN_IMPORT_ROOTS_IN_PURE`, so it cannot fail there without the pure test failing too, and parametrizing over all three means the infrastructure ban survives any future change to `PURE_PACKAGES`.

Then widen the wall-clock test (`:231-243`) — three edits, one test:

```python
@pytest.mark.parametrize("package", BOUNDARY_PACKAGES)
def test_boundary_packages_never_read_the_wall_clock(package: str):
    # Arrange / Act
    offenders = [
        (path, attribute)
        for path in _python_files(package)
        for attribute in set(_called_attributes(path)) & FORBIDDEN_CLOCK_CALLS_IN_PURE
    ]

    # Assert
    assert not offenders, (
        f"{package} reads the wall clock; time enters as data (SSOT §4.2): {offenders}"
    )
```

`FORBIDDEN_CLOCK_CALLS_IN_PURE` keeps its name — it is still the pure packages' list, now also applied one layer up.

- [ ] **Step 6: Run the seam test, then prove the new guards bite**

```bash
uv run pytest tests/test_import_direction.py -q
```

Expected: PASS. Both new guards pin properties `catalogue` already has, so neither can fail on first run — which means the run proves nothing on its own. Break them deliberately and watch them fail. Temporarily add to the top of `src/noor/catalogue/compiler.py`:

```python
import datetime

import httpx

_ = datetime.datetime.now()
```

```bash
uv run pytest tests/test_import_direction.py -q
```

Expected: 2 failed — `catalogue must acquire no clock, HTTP client, or database session` naming `compiler.py` and `httpx`, and `catalogue reads the wall clock` naming `compiler.py` and `now`. Then revert:

```bash
git checkout src/noor/catalogue/compiler.py
```

- [ ] **Step 7: Refresh `CLAUDE.md` and `AGENTS.md` (cleanup 3)**

Both files claim there is no `engine`, that `catalogue` is one registry loader, and that `docs/superpowers/specs/` holds a design note that no longer exists. An instruction file that lies about what exists causes exactly the failure its own closing warning names — "do not infer that any component exists because a document describes it." Make each edit in `CLAUDE.md`, then apply it identically to `AGENTS.md`; they are byte-identical today and their footer requires they stay so.

Replace `CLAUDE.md:8-10`:

```markdown
`canon`, `engine`, and `catalogue` are built and tested; nothing above them is.
There is no database and no HTTP layer — `src/noor/app/` holds a single
docstring. There is no clinical rule content: `content/` holds the observable
registry, the two valuesets, the terminology charter, one tenant profile, and one
empty release.
```

Replace `CLAUDE.md:34-41` (the "What exists in code" bullet):

```markdown
- **What exists in code.** `src/noor/canon/` implements SSOT §5, §6.1–§6.3, and
  §6.6: the observation model, the observable registry, unit resolution, the two
  mistype shapes, both plausibility envelopes, delta review, the `canonicalise`
  pipeline, and quality resolution. `src/noor/engine/` implements §4.3.1, §7.1–§7.3,
  and §8.1–§8.3: the closed expression tree, the rule and threshold models, the
  snapshot, requirement resolution, the three-outcome evaluator, and the
  evaluation record. `src/noor/catalogue/` implements §7.4, §7.5, and the §10.4
  content gates: the schema-only YAML door, the three closed id registries, the
  terminology charter, the per-kind loaders, the golden-case harness, and
  `compile_release`, which turns a content directory into a validated
  `EvaluationContext`. `tests/` covers all of it at 100% branch coverage, plus the
  seam test (§4.2) and hypothesis properties. The plans that built it are
  `docs/superpowers/plans/2026-08-18-foundation-and-canon.md` (Tasks 1–12),
  `2026-08-22-engine-evaluator.md`, and `2026-08-24-catalogue-loader-compiler.md`.
```

Replace `CLAUDE.md:42-44` (the specs bullet):

```markdown
- `docs/superpowers/specs/` holds one design note
  (`2026-08-24-catalogue-loader-compiler-design.md`); the SSOT remains the only
  architectural document.
```

Replace `CLAUDE.md:165-167` (the Testing section's second paragraph). The same staleness from the same cause, one paragraph outside "Current State" — left as it is, it tells the next agent that the engine tests it is about to edit do not exist:

```markdown
`canon`, `engine`, and `catalogue` have tests and fixtures (`tests/`,
`tests/conftest.py`, `tests/catalogue/conftest.py`). There is no test database
and no golden clinical case yet. The standards describe the whole suite, not the
part that runs today.
```

- [ ] **Step 8: Run CI's five commands**

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy src/noor/canon src/noor/engine src/noor/catalogue
uv run pytest --cov --cov-report=term-missing --cov-fail-under=100
```

Expected: all clean, 100% branch coverage. This is the first run where the whole suite reads the committed `content/` tree, so a coverage miss in `compiler.py` here means a branch only the synthetic fixture trees reach.

- [ ] **Step 9: Verify the two files stayed identical**

```bash
diff CLAUDE.md AGENTS.md && echo IDENTICAL
```

Expected: `IDENTICAL`.

- [ ] **Step 10: Commit**

```bash
git add content/profiles/riyadh-hh.yaml content/releases/rel-2026-09-01.yaml \
        tests/catalogue/test_content_tree.py tests/test_import_direction.py \
        CLAUDE.md AGENTS.md
git commit -m "feat(content): a compilable release, and the seam widened to catalogue

A tenant profile and an empty release manifest, which is what compile_release
needs to produce an EvaluationContext from the committed tree. Neither file
carries a clinical claim - no rule, no number, no citation, no approver - so
content/ stays clinically clean until step 6 authors the first rule.

The import-direction test now holds catalogue to the clock, HTTP, and database
bans while leaving the filesystem ban to the pure packages: reading content files
is catalogue's job, but a compiler that reads the wall clock cannot be replayed
and one that reaches the network compiles content nobody reviewed.

CLAUDE.md and AGENTS.md said there was no engine and pointed at a design note
that no longer exists."
```

---

### Task 11: The seven SSOT amendments

The code is done. This task edits `docs/cds-architecture.md` alone, so that the SSOT describes what the repository now holds — including where its previous instrument was replaced, and why. Spec section 10 lists all seven; each lands as a specific edit below.

**No code changes here.** If any step below needs a code change to be true, the amendment is wrong or the code is — stop and ask, do not edit the SSOT to match the code.

**Files:**
- Modify: `docs/cds-architecture.md:713-718` (amendment 4), `:1197-1201` (1), `:1396-1418` and `:1420-1422` (2), `:1330-1341` (5, 7), `:1439-1452` and `:1454-1455` (3), `:2803-2812` and `:2984-3002` (6)

**Interfaces:**
- Consumes: nothing. Documentation only.
- Produces: nothing. This is the last task.

- [ ] **Step 1: Amendment 1 — §6.6 declares the renal marker**

In the paragraph at `:1197`, replace `required method/context fields, and a named owner.` with:

```markdown
required method/context fields, whether the observable is a renal metric
(`renal_metric: egfr | crcl | null`), and a named owner.
```

Then add this paragraph immediately after that paragraph:

```markdown
**`renal_metric` is a marker, not a bound.** It states *which renal metric this
observable is*, so §10.4 gate 15 can ask whether a rule declared the metric it
means without matching free text. It carries no clinical decision boundary, so
§6.4's separation between data validity and treatment thresholds is untouched. It
is set on `egfr` today; `crcl` gets it when its registry row lands. Creatinine is
deliberately unmarked — it is CrCl's *input*, not a renal metric, and marking it
would force a creatinine-delta rule to declare a metric it does not use and would
bless the exact input-to-metric conflation gate 15 exists to catch.
```

- [ ] **Step 2: Amendment 2 — §7.3 records which metric a threshold states**

In the YAML block at `:1396`, insert after the `source_family: ada-kdigo` line:

```yaml
  states_metric: egfr           # egfr | crcl | null — which renal metric this number
                                # is expressed in, read off the source document, never
                                # inferred from the observable it is compared against
```

Then add this paragraph after the `**No rule loads referencing an `unpopulated` threshold.**` paragraph at `:1420-1422`:

```markdown
**`states_metric` records which renal metric the source stated.** With §6.6's
`renal_metric` marker it gives §10.4 gate 15 both halves: a rule requiring a
renal observable declares the metric it means, and every threshold it references
must state that same metric. `null` is silence, not a claim — a non-renal
threshold pairs with any rule.
```

- [ ] **Step 3: Amendments 5 and 7 — §7.1's declaration rule widens, and the medication list gets a stamp**

Both amendments land on the same paragraph, §7.1's closer at `:1330-1341`. Replace it whole:

```markdown
**Every observable a rule reads as patient state is declared in `requires`.** The
freshness and quality gate is not optional: a threshold compared against an
ungated value is a decision made on data of unknown age and unknown grade, which is
the failure §5.1 and §8.3 exist to prevent. A numeric leaf naming an observable
absent from the rule's `requires` manifest is a load failure (§10.4 gate 12), and
at evaluation the engine reads only the requirement-validated value: when that
requirement is unusable the rule is already `indeterminate` (§8.3) and the
comparison never runs.

**A `drug_active` leaf is covered by the same rule, and declares
`active_medications`.** The medication list is patient state read as of a moment,
not an always-present collection: an empty list from a patient nobody asked and an
empty list from a patient confirmed to be on nothing are opposite facts, and §5.5
rule 2 forbids inferring the second from the first. The list therefore carries a
list-level `medications_reconciled_at` stamp — the medication list's answer to
`allergy_status` — and a rule reading the list resolves that stamp through its own
`active_medications` requirement and window, exactly as it resolves an eGFR. No
stamp is `indeterminate`; a stamp older than the rule's `max_age_days` is
`indeterminate`; a stamp inside the window is usable whether the list is empty or
not. The stamp is *last reconciled*, never transmitted to a device (§4.2). §7.1's
own example above already declares this requirement.

`drug_requested` is not covered: a requested action arrives with the request, not
from the list. Allergy, condition, and age predicates read always-present snapshot
collections directly and need no declaration — an absent allergy or condition is a
usable *false*, not missing data, with the single exception that `allergy_status:
not_asked` is `indeterminate` (§5.5).
```

The `Snapshot` field this describes is the one §0 exception in this plan, approved 2026-08-24 (Task 5, spec section 9 amendment 5). The SSOT is being brought into line with an approved change, not granting one.

- [ ] **Step 4: Amendment 3 — §7.4's layout closes the authoring spaces**

In the tree at `:1439-1452`, replace the `valuesets/*.yaml` line with three lines:

```
  valuesets/conditions.yaml      # the closed condition-concept space
  valuesets/ingredients.yaml     # the closed ingredient-id space
  terminology/charter.yaml       # code-system licence status (§3.3, gate 17)
```

Then add these two paragraphs after `**Adding a rule is two YAML files and zero Python.** A single `pytest` parametrize discovers every `*.cases.yaml` in the tree.` at `:1454-1455`:

```markdown
**`valuesets/` closes the authoring spaces; it does not add an operator.** A
`concept` a rule tests and an `ingredient_id` it names must appear in the matching
valueset or the rule does not compile (§10.4 gate 12). This is a closed id space,
not an `in_valueset` predicate — the expression vocabulary stays exactly the
operators §4.3 declares, and closing a *space* needs no new way to ask a question.

`terminology/charter.yaml` is where §3.3's attribution obligations are recorded,
one entry per code system with its URI and its licence status. Gate 17 refuses
content citing a system the charter does not name, and refuses a charter entry
whose licence status is absent. The URI is the join key: the citation sites in
content are namespaced URIs, and matching them against a human-readable name
cannot work.
```

- [ ] **Step 5: Amendment 4 — §4.2 point 2 changes instrument**

Replace point 2 at `:713-718` whole. This is the one amendment that retires a mechanism the SSOT already specified, so it says so explicitly rather than quietly overwriting it:

```markdown
2. **The compiler closes every rule reference site against the registry that owns
   that name's space.** A rule may name only ids the content tree declares:
   observables and monitored observables against §6.6's registry, condition
   concepts and ingredient ids against `content/valuesets/`, threshold refs
   against the release. This is what makes §10.4 gates 11 and 12 enforceable:
   encounter state appears in none of those registries, so a rule referencing it
   fails to compile whatever it calls it — `encounter.state` is refused for
   exactly the same reason as any other unknown name, which is the defeat a
   name-matching check would suffer. **Validating against the snapshot's exported
   JSON Schema was the original instrument and is retired.** A schema cannot reach
   the *values* inside the snapshot's `frozenset[str]` and `tuple[...]`
   collections, which is where an ingredient id and a condition concept actually
   live, and two reference sites — a monitored observable and a blocked order
   action — are not snapshot fields at all. The concern is unchanged and is now
   more completely met: eight reference sites, eight owning registries.
```

- [ ] **Step 6: Amendment 6 — claim 29 and §14 step 5 stop over-promising**

Claim 29 asks for a tenant profile omitting "the escalation policy, an ageing threshold, or a per-kind obligation default" to be refused at load. `Profile` declares none of those three — they belong to §11's visit and obligation schemas, in packages that do not exist. Step 5 proves the *refusal pattern* on `Profile`'s existing required fields; the three named policies are proved where their schemas land.

Replace the claim-29 row at `:2807`:

```markdown
| 29 | A missing operational policy is refused, not defaulted | Load a tenant profile omitting a required field → refused at load, never defaulted (step 5, on `Profile`'s own fields). The escalation policy, ageing thresholds, and per-kind obligation defaults are proved the same way against the §11 schemas that declare them (steps 8–12) | §10.5 |
```

Then in §14 step 5 at `:2984-3002`, replace its final sentence — `§12.6 claim 29: a tenant profile omitting an operational policy is refused at load, never silently defaulted (§10.5).` — with:

```markdown
§12.6 claim 29, first half: a tenant profile omitting a required field is refused
at load, never silently defaulted (§10.5). The escalation policy, ageing
thresholds, and per-kind obligation defaults are not `Profile` fields and are
proved against their own schemas in steps 8–12.
```

- [ ] **Step 7: Read the amended sections back and check them against the code**

```bash
uv run pytest -q
```

Expected: PASS — no test reads the SSOT, so this is a regression check that step 7's document-only claim is true. Then read each amended section beside the code it describes:

| Amendment | Read | Against |
|---|---|---|
| 1 | §6.6 | `src/noor/canon/registry.py` `ObservableEntry.renal_metric` |
| 2 | §7.3 | `src/noor/engine/content.py` `Threshold.states_metric` |
| 3 | §7.4 | `content/valuesets/`, `content/terminology/charter.yaml` |
| 4 | §4.2 point 2 | `src/noor/catalogue/compiler.py` `_check_authored_names_exist` |
| 5 | §7.1 | `src/noor/engine/snapshot.py`, `evaluate.py` `_resolve_requirement` |
| 6 | §12.6 claim 29, §14 step 5 | `src/noor/engine/content.py` `Profile` |
| 7 | §7.1 | `src/noor/engine/rules.py` `_every_compared_observable_is_declared_in_requires` |

Any row where the document now claims more than the code does is a defect in this task, not a future step's problem.

- [ ] **Step 8: Refresh the knowledge graph**

```bash
graphify update .
```

- [ ] **Step 9: Commit**

```bash
git add docs/cds-architecture.md graphify-out/
git commit -m "docs: the seven SSOT amendments for catalogue

Six additions and one retirement. The registry marks which observables are renal
metrics and thresholds record which metric they state, which is what gives gate 15
both halves without matching free text. The valuesets and the terminology charter
join the content layout. A drug_active leaf now declares active_medications, which
resolves against a list-level reconciliation stamp - the medication list's answer
to allergy_status, and the one §0 change in this step, approved 2026-08-24.

Retired: §4.2 point 2's snapshot-JSON-Schema field-reference pass, replaced by one
closure per reference site against the registry owning that name's space. A schema
cannot reach the values inside a frozenset[str], which is where an ingredient id
lives, and two of the eight sites are not snapshot fields at all. Gate 12's
concern is unchanged and now more completely met.

Claim 29 and §14 step 5 stop promising that step 5 refuses policies whose schemas
do not exist yet; they move to steps 8-12, with the packages that declare them."
```

---

## Done when

All eleven tasks committed on `design/catalogue-loader-compiler`, CI's five commands clean, and one pull request opened against `main` under the existing `CODEOWNERS` and branch protection. The pull request *is* the §7.5 four-eyes approval — for the code, for the committed content, and for the seven SSOT amendments alike.

§14 step 5 is then complete, and step 6 — the first real rule — has a compiler to refuse it.
