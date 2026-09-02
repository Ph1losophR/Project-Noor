"""Medication Reconciliation (§4.2), and the comparison that degrades (§4.10)."""
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from noor.domain.states import DataState, Datum


class ReconError(ValueError):
    """An item in the house that could not have been recorded from a real box."""


@dataclass(frozen=True)
class Product:
    """One row of the bundled drug list — a demonstration subset, not a formulary (§6)."""

    id: str
    generic: str
    strength: str
    form: str
    drug_class: str


@dataclass(frozen=True)
class Medication:
    """A named item, on either side of the comparison.

    `product` is None for an item the drug list does not contain: the free text stands,
    marked unmatched, and the comparison leaves it alone (§4.2, N6). `quantity_remaining`
    and `expiry` are the only two fields the Field Team types, and only in the house.
    """

    label: str
    product: Product | None = None
    quantity_remaining: int | None = None
    expiry: date | None = None

    def __post_init__(self) -> None:
        if not self.label:
            raise ReconError("an item in the house is recorded by name, matched or not")
        if self.quantity_remaining is not None and self.quantity_remaining < 0:
            raise ReconError(f"{self.label}: a count of tablets cannot be negative")

    @property
    def is_matched(self) -> bool:
        return self.product is not None


class DiscrepancyKind(Enum):
    """§4.2's list, plus the item Noor cannot reconcile at all."""

    OMISSION = "prescribed, not in the house"
    UNPRESCRIBED = "in the house, not on the prescribed list"
    STRENGTH_MISMATCH = "the right drug, a different strength"
    DUPLICATE = "two boxes of the same drug in the house"
    EXPIRED = "in the house, past its expiry"
    UNMATCHED = "not on the drug list — Noor cannot reconcile this item"


@dataclass(frozen=True)
class Discrepancy:
    kind: DiscrepancyKind
    subject: str


@dataclass(frozen=True)
class Reconciliation:
    """The section's content. Never empty just because the EMR was out of reach."""

    house: tuple[Medication, ...]
    discrepancies: tuple[Discrepancy, ...]
    comparison: DataState

    @property
    def is_complete(self) -> bool:
        """False means the discrepancies are what the cupboard showed, and no more."""
        return self.comparison is DataState.PRESENT


def products(rows: Sequence[dict]) -> tuple[Product, ...]:
    """Build the catalogue from `drug-list.md`'s rows. The only place its columns bind."""
    return tuple(Product(**row) for row in rows)


def search(catalogue: Sequence[Product], query: str) -> list[Product]:
    """Phase 1 searches `generic` only; brands belong in a later synonym field (§4.2)."""
    text = query.strip().lower()
    if not text:
        return []
    return [product for product in catalogue if text in product.generic.lower()]


def reconcile(house: Sequence[Medication], prescribed: Datum,
              as_of: date) -> Reconciliation:
    """The house against the prescribed list, or the house alone when that is all there is.

    `as_of` is the day the expiry is judged against, passed in rather than read from a
    clock, so the whole module is a function of its arguments (testing standards, N7).
    """
    house = tuple(house)
    found = _from_the_cupboard(house, as_of)
    if prescribed.state is DataState.UNREACHABLE:
        return Reconciliation(house, tuple(found), DataState.UNREACHABLE)
    lines = prescribed.value if prescribed.is_present else ()
    return Reconciliation(house, tuple(found + _against(house, lines)),
                          DataState.PRESENT)


def as_content(result: Reconciliation, at: datetime) -> dict[str, object]:
    """The section's content, JSON-safe, for the store and the Write-Back both.

    A `Datum` cannot be stored or sent, so the state becomes a word here — once,
    in the module that owns the comparison, rather than in each consumer.
    """
    return {"in_house": [house_entry(item) for item in result.house],
            "discrepancies": [{"kind": item.kind.value, "subject": item.subject}
                              for item in result.discrepancies],
            "detection": _declared(result.comparison, at)}


def house_entry(item: Medication) -> dict[str, object]:
    """§4.2's only objective adherence signal and the matched product survive
    with the name — a label alone would lose them."""
    return {"label": item.label,
            "product_id": item.product.id if item.is_matched else None,
            "quantity_remaining": item.quantity_remaining,
            "expiry": item.expiry.isoformat() if item.expiry is not None else None}


def read_entry(row: Mapping[str, object], products: Mapping[str, Product]) -> Medication:
    """The inverse of `house_entry`, for a cached list and a stored section both.

    The product is resolved against the shipped drug list on the way in rather than
    stored, so a correction to that list reaches a Visit already recorded. A `product_id`
    the list no longer holds comes back unmatched, which is the same degradation §4.2
    already specifies for an item it never held.
    """
    return Medication(
        row["label"],
        products.get(row["product_id"]) if row["product_id"] else None,
        row["quantity_remaining"],
        date.fromisoformat(row["expiry"]) if row["expiry"] else None)


def _declared(comparison: DataState, at: datetime) -> dict[str, object]:
    """§4.10: 'no discrepancies' and 'the list could not be read' are different
    facts, so the state is a word the EMR receives (N6)."""
    if comparison is DataState.PRESENT:
        return {"state": comparison.value, "as_of": at.isoformat()}
    return {"state": comparison.value}


def _from_the_cupboard(house: Sequence[Medication],
                       as_of: date) -> list[Discrepancy]:
    """The three checks that need no prescribed list, so §4.10 never loses them."""
    counted = Counter(item.product.generic for item in house if item.is_matched)
    return (
        [Discrepancy(DiscrepancyKind.UNMATCHED, item.label)
         for item in house if not item.is_matched]
        + [Discrepancy(DiscrepancyKind.EXPIRED, item.label)
           for item in house if item.expiry is not None and item.expiry < as_of]
        + [Discrepancy(DiscrepancyKind.DUPLICATE, generic)
           for generic, seen in counted.items() if seen > 1]
    )


def _against(house: Sequence[Medication],
             lines: Sequence[Medication]) -> list[Discrepancy]:
    in_house = _by_generic(house)
    on_list = _by_generic(lines)
    return (
        [Discrepancy(DiscrepancyKind.UNMATCHED, item.label)
         for item in lines if not item.is_matched]
        + [Discrepancy(DiscrepancyKind.OMISSION, generic)
           for generic in on_list if generic not in in_house]
        + [Discrepancy(DiscrepancyKind.UNPRESCRIBED, generic)
           for generic in in_house if generic not in on_list]
        + [Discrepancy(DiscrepancyKind.STRENGTH_MISMATCH, generic)
           for generic, ids in on_list.items()
           if generic in in_house and not (ids & in_house[generic])]
    )


def _by_generic(items: Sequence[Medication]) -> dict[str, set[str]]:
    """generic → the product ids under it. Unmatched items are absent by construction:
    an item Noor cannot name is one it cannot compare, and UNMATCHED already said so."""
    grouped: dict[str, set[str]] = {}
    for item in items:
        if item.is_matched:
            grouped.setdefault(item.product.generic, set()).add(item.product.id)
    return grouped
