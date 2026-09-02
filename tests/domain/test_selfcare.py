"""Tests for domain selfcare items (§4.5)."""
from noor.domain.selfcare import SelfCareItem, self_care_items


def test_self_care_items_parses_catalogue_rows():
    rows = [
        {
            "id": "glucometer-technique",
            "label": "Glucometer technique check",
            "mode": "demonstration",
            "conditions": ["diabetes"],
            "requires": "glucometer",
        },
        {
            "id": "foot-inspection",
            "label": "Daily foot self-inspection",
            "mode": "inquiry",
            "conditions": ["diabetes", "hypertension"],
        },
    ]
    items = self_care_items(rows)
    assert len(items) == 2
    assert items[0] == SelfCareItem(
        id="glucometer-technique",
        label="Glucometer technique check",
        mode="demonstration",
        conditions=("diabetes",),
        requires="glucometer",
    )
    assert items[1] == SelfCareItem(
        id="foot-inspection",
        label="Daily foot self-inspection",
        mode="inquiry",
        conditions=("diabetes", "hypertension"),
        requires=None,
    )
