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
    registry_document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(registry_document, dict) or not isinstance(
        registry_document.get("observables"), list
    ):
        raise ValueError(f"{path}: expected a top-level 'observables' list")
    entries: dict[str, dict[str, object]] = {}
    for observable_document in registry_document["observables"]:
        observable_id = observable_document["observable"]
        if observable_id in entries:
            raise ValueError(f"{path}: duplicate observable id {observable_id!r}")
        entries[observable_id] = observable_document
    return ObservableRegistry.model_validate({"entries": entries})
