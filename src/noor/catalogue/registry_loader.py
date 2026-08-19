"""Loads registry content into validated models (SSOT §7.4).

Schema-only YAML (§7.5): anything `_ContentLoader` refuses is a build failure.
Decimal scalars in content files are quoted strings, so they load exactly —
a YAML float would carry binary error into clinical bounds.
"""

from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from noor.canon.registry import ObservableRegistry


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


def load_registry(path: Path) -> ObservableRegistry:
    """Load and validate an observable registry file (content/observables/registry.yaml)."""
    with path.open(encoding="utf-8") as content:
        registry_document = yaml.load(content, _ContentLoader)
    if not isinstance(registry_document, dict) or not isinstance(
        registry_document.get("observables"), list
    ):
        raise ValueError(f"{path}: expected a top-level 'observables' list")
    entries: dict[str, dict[str, object]] = {}
    for observable_document in registry_document["observables"]:
        if not isinstance(observable_document, dict) or "observable" not in observable_document:
            raise ValueError(f"{path}: every observable must be a mapping with an 'observable' id")
        observable_id = observable_document["observable"]
        if observable_id in entries:
            raise ValueError(f"{path}: duplicate observable id {observable_id!r}")
        entries[observable_id] = observable_document
    return ObservableRegistry.model_validate({"entries": entries})
