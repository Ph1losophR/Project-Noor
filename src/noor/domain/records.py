"""What a section holds, and what it takes for one to be Resolved (§5.8)."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from noor.domain.states import Section

OTHER = "other"  # §5.10 ends every reason list with this row. No content file has it.


class ResolutionError(ValueError):
    """A section resolved in neither of the two shapes §5.8 allows."""


class CarePlanTooEarly(Exception):
    """The Care Plan is assembled after all seven others, Notes included (§4.2)."""


@dataclass(frozen=True)
class Reason:
    """A row from a §5.10 list. `free_text` is required only for the Other row."""

    row_id: str
    free_text: str | None = None


@dataclass(frozen=True)
class Resolution:
    """Content, or a structured reason for having none. Never both, never neither."""

    section: Section
    content: object | None = None
    reason: Reason | None = None

    def __post_init__(self) -> None:
        if (self.content is None) == (self.reason is None):
            raise ResolutionError(
                f"{self.section.name} is resolved by content or by a reason for "
                "having none — not by both, and not by neither"
            )
        if self.content in ({}, [], ""):
            raise ResolutionError(f"{self.section.name}: empty content is not content")
        if self.reason is not None and self.reason.row_id == OTHER and not self.reason.free_text:
            raise ResolutionError(f"{self.section.name}: the Other row needs its free text")


def unresolved(resolutions: Mapping[Section, Resolution]) -> tuple[Section, ...]:
    """Sections with no Resolution at all, in the record's order (§4.2)."""
    return tuple(s for s in Section if s not in resolutions)


def outstanding_before_care_plan(
    resolutions: Mapping[Section, Resolution]
) -> tuple[Section, ...]:
    """The sections the Care Plan waits on (§4.2) — Notes among them, itself excluded.

    §4.2's rule as a question rather than as a refusal, because a page has to ask before it
    renders a form. `check_care_plan_ready` reads this too, so the two cannot disagree.
    """
    return tuple(s for s in unresolved(resolutions) if s is not Section.CARE_PLAN)


def check_care_plan_ready(resolutions: Mapping[Section, Resolution]) -> None:
    """Guard: the Care Plan is assembled last, after Notes (§4.2)."""
    outstanding = outstanding_before_care_plan(resolutions)
    if outstanding:
        raise CarePlanTooEarly(
            "the Care Plan is assembled after the other seven; still unresolved: "
            + ", ".join(s.name for s in outstanding)
        )


OTHER_ROW = {"id": OTHER, "label": "Other — write what happened"}


def reason_rows(*lists: Sequence[Mapping[str, str]]) -> tuple[Mapping[str, str], ...]:
    """§5.10's rows for one context, ending in the structural Other row.

    Every list in the product is built here, so no list can lose `Other +`: no content
    file holds that row, and `reason-lists.md` says a loader that finds one is reading a
    wrong file. A section's list is two lists — the shared core and its own rows — which
    is why this takes as many as it is given.
    """
    return tuple(row for rows in lists for row in rows) + (OTHER_ROW,)


def reason_for(rows: Sequence[Mapping[str, str]], row_id: str, free_text: str) -> Reason:
    """A posted row, back as a `Reason`, refusing what §5.10 does not allow.

    The row id is the one value that arrives from outside, so it is checked against the
    list that was rendered. Other without its words is refused here rather than at the
    `Resolution`, because a Cancel carries a `Reason` and never builds one.
    """
    if row_id not in {row["id"] for row in rows}:
        raise ResolutionError(
            "That is not a reason on this list. It may have changed since this page was "
            "opened — choose one from the list as it is now.")
    if row_id == OTHER and not free_text.strip():
        raise ResolutionError(
            "Other is the row that needs its own words. Write what happened.")
    # Words typed beside a named row are kept: §5.10 asks for them on Other and never
    # asks for them to be thrown away anywhere else.
    return Reason(row_id, free_text.strip() or None)
