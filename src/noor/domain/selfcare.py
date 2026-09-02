"""§4.5's Self-Care Check items: what the Field Team observes, and who performs it."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class SelfCareItem:
    """One row of `self-care-items.md`."""

    id: str
    label: str
    mode: str
    conditions: tuple[str, ...]
    requires: str | None = None


def self_care_items(rows: Sequence[Mapping[str, object]]) -> tuple[SelfCareItem, ...]:
    """The catalogue in the file's order."""
    return tuple(
        SelfCareItem(row["id"], row["label"], row["mode"],
                     tuple(row["conditions"]), row.get("requires"))
        for row in rows
    )
