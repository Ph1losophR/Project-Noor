"""Content loads through a schema-only YAML loader (SSOT §7.5)."""

import pytest
from yaml.constructor import ConstructorError

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
    side_effect = tmp_path / "owned.txt"
    hostile.write_text(
        f"observables: !!python/object/apply:builtins.open ['{side_effect.as_posix()}', 'w']\n",
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(ConstructorError):
        load_registry(hostile)
    assert not side_effect.exists()


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
        "observables:\n  - {observable: glucose, owner: a}\n  - {observable: glucose, owner: b}\n",
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(ValueError, match="duplicate"):
        load_registry(bad)


def test_a_content_file_with_a_repeated_key_is_refused(tmp_path):
    # Arrange — stock PyYAML keeps the LAST of two identical keys silently, so this
    # file would load a physiologic ceiling of 99 while the approver read 10 (§7.5)
    bad = tmp_path / "registry.yaml"
    bad.write_text(
        "observables:\n"
        "  - observable: glucose\n"
        '    physiologic: {low: "2", high: "10", version: v1}\n'
        '    physiologic: {low: "2", high: "99", version: v1}\n',
        encoding="utf-8",
    )

    # Act / Assert
    with pytest.raises(ConstructorError, match="duplicate keys: physiologic"):
        load_registry(bad)


@pytest.mark.parametrize(
    "observables_block",
    ["observables:\n  - {owner: a}\n", "observables:\n  - glucose\n"],
    ids=["mapping-without-an-id", "not-a-mapping"],
)
def test_an_entry_that_is_not_an_identified_mapping_names_the_offending_file(
    tmp_path, observables_block
):
    # Arrange — a content author's error must say which file to open
    bad = tmp_path / "registry.yaml"
    bad.write_text(observables_block, encoding="utf-8")

    # Act / Assert
    with pytest.raises(ValueError, match=r"registry\.yaml: every observable"):
        load_registry(bad)
