"""The words the Field Team's screens are made of.

Pure functions over what the store and the domain already settled, returning strings. Two
reasons, and neither is tidiness. The coverage gate is branch coverage at 100% with no
exclusions (ADR 0006) and coverage cannot see inside a Jinja `{% if %}`, so a decision in a
template is a decision nothing tests. And a sentence tested here is tested once, where the
five words of it that matter are visible, rather than through an assertion about HTML.

Nothing here takes a connection. A view model that can query is a view model that can
disagree with the page around it.
"""
from collections.abc import Mapping, Sequence
from datetime import date
from typing import NamedTuple

from noor import content
from noor.domain.brief import Due, LastVisit, Point, Trend
from noor.domain.examination import Composed, Composition, Element
from noor.domain.plans import Axis, BetweenVisitPlan, Comparison
from noor.domain.records import OTHER, Reason, reason_rows
from noor.domain.reconciliation import (Discrepancy, Medication, Product,
                                        Reconciliation)
from noor.domain.selfcare import SelfCareItem
from noor.domain.states import DataState, Datum, Section, VisitKind, VisitState
from noor.domain.visit import Visit
from noor.domain.vitals import HomeReading, Measurement, Source
from noor.prefetch import Readiness
from noor.store import Pending, RosterEntry

STATE_WORDS = {
    VisitState.SCHEDULED: "Scheduled",
    VisitState.IN_PROGRESS: "In Progress",
    VisitState.EMERGENCY: "Emergency",
    VisitState.COMPLETED: "Completed",
    VisitState.ENDED_EARLY: "Ended Early",
    VisitState.CANCELLED: "Cancelled",
}
"""§5.1's six states as words, and no status colour on any of them: the design system §4.4
reserves the three hues for Escalation Tiers and for an item Noor examined and found normal,
and forbids colour as the carrier of a data state. A seventh state would raise KeyError on
the page rather than leave a row half-written, which is ADR 0007's loud failure."""

KIND_WORDS = {VisitKind.BASELINE: "Baseline Visit", VisitKind.ROUTINE: "Routine Visit"}
"""ADR 0008's two words. The same two whether they are the read-time planning indicator on
a Scheduled row or the kind the Start settled — what separates those is the state word
beside them, not a second vocabulary."""

NEVER_STARTED = "Never started, so no Visit type was settled."
"""ADR 0008's last line as a sentence rather than a gap. The design system §7.2 prohibits
the empty cell, the em dash and 'N/A' in every table Noor renders, and a Cancelled Visit's
missing kind is exactly the hole one of those three would fill."""

READS = {"prescribed": "the prescribed list",
         "allergies": "the allergy list",
         "surveillance": "the surveillance dates"}
"""§5.2's three pre-departure reads. `prefetch.readiness` collapses seven failed
surveillance items into the one name, so this maps the read and never the item: seven
failures of one read are one thing to report."""

NOTHING_PREPARED = (
    "The office prepared nothing for this Visit. Readiness never holds a Visit up: it "
    "starts, and it runs with every EMR read Unreachable.")
"""§5.2's fourth rule, said where the Field Team is deciding whether to leave. N4: software
that refuses to let a team travel is software preventing care, so this line reports and
never warns."""


class Line(NamedTuple):
    """One row of the Visit List (web_plan §4.1). Every field is already a string, so the
    template chooses nothing."""

    visit_id: str
    patient_name: str
    reason: str
    state: str
    kind: str
    readiness: str


def line(entry: RosterEntry, *, visit: Visit, planned: VisitKind,
         prepared: Readiness) -> Line:
    """`planned` is the read-time indicator and `visit.kind` the settled one. Both arrive
    because choosing between them is this function's job and not the caller's (ADR 0008)."""
    return Line(entry.visit_id, entry.patient_name, entry.reason,
                STATE_WORDS[entry.state], _kind(entry, visit, planned),
                readiness_sentence(prepared))


def _kind(entry: RosterEntry, visit: Visit, planned: VisitKind) -> str:
    """Two cases, in ADR 0008's order: before the Start, the indicator derived from the
    history that exists now; after it, whatever the Start settled."""
    if entry.state is VisitState.SCHEDULED:
        return KIND_WORDS[planned]
    return settled_kind(visit)


def readiness_sentence(prepared: Readiness) -> str:
    """§5.2's readiness as one sentence: when the office read, and what came back.

    A time and not an age. §5.2's first rule is that every cached value carries an as-of
    time, and the design system §7.2 renders a stale Present value as the value with a
    timestamp beside it — 'two hours ago' is that timestamp with the arithmetic already
    done and the reference point thrown away.
    """
    if prepared.prepared_at is None:
        return NOTHING_PREPARED
    when = f"Prepared {prepared.prepared_at:%H:%M, %d %B}."
    if not prepared.unreadable:
        return f"{when} Every read came back."
    return f"{when} Could not be read: {', '.join(READS[r] for r in prepared.unreadable)}."


def summary(entries: Sequence[RosterEntry]) -> str:
    """The one sentence above the list. An empty roster is a finding — the office scheduled
    nobody — and the sentence says which of §7.2's two absences it is, because a roster
    nobody could read and a roster with nobody on it are different days' work."""
    if not entries:
        return ("The office scheduled no Visits for this day. That is what an empty "
                "roster says; it is not a roster Noor could not read.")
    return f"Visits on this day's roster: {len(entries)}."


def day_words(day: date) -> str:
    """Written out in full, weekday included: `?day=` reaches any day in either direction,
    and the wrong day is only obvious if the page says which one it is."""
    return f"{day:%A %d %B %Y}"


SECTION_WORDS = {
    Section.VISIT_REASON: "Visit Reason",
    Section.CONCERNS_AND_INTERVAL_HISTORY: "Concerns & Interval History",
    Section.MEDICATION_RECONCILIATION: "Medication Reconciliation",
    Section.VITALS: "Vitals",
    Section.PHYSICAL_EXAMINATION: "Physical Examination",
    Section.SELF_CARE_CHECK: "Self-Care Check",
    Section.CARE_PLAN: "Care Plan",
    Section.NOTES: "Notes",
}
"""§4.2's eight, as words. `Section`'s integer is the position, so iterating the enum is
already the record's order and no page sorts."""

SLUGS = {
    "visit-reason": Section.VISIT_REASON,
    "concerns-and-interval-history": Section.CONCERNS_AND_INTERVAL_HISTORY,
    "medication-reconciliation": Section.MEDICATION_RECONCILIATION,
    "vitals": Section.VITALS,
    "physical-examination": Section.PHYSICAL_EXAMINATION,
    "self-care-check": Section.SELF_CARE_CHECK,
    "care-plan": Section.CARE_PLAN,
    "notes": Section.NOTES,
}
"""web_plan §4.3's eight addresses. The slug is the section's own name, so no address
invents a synonym CONTEXT.md forbids."""

SLUG_OF = {section: slug for slug, section in SLUGS.items()}

CANCELLED_ROWS = reason_rows(content.load("reason-lists").data["cancelled"]["rows"])
ENDED_EARLY_ROWS = reason_rows(content.load("reason-lists").data["ended_early"]["rows"])
"""§5.10's two closing lists, each ending in the structural Other row `reason_rows` adds.
Read at import: a malformed content file should stop the process starting, not surface as a
half-written popover on the one screen that needed it (ADR 0007). Content is versioned
clinical text rather than request state, which is why it may live here — the rule this
module keeps is that nothing in it touches a connection."""

CLOSING_LABELS = {row["id"]: row["label"] for row in CANCELLED_ROWS + ENDED_EARLY_ROWS}
"""Row id to the words the Field Team actually chose. The two lists share no ids, and a
closing reason from either one resolves here without the page having to know which."""

NO_CONTENT = content.load("reason-lists").data["no_content"]
SECTION_REASONS = {
    section: reason_rows(NO_CONTENT["shared"],
                         NO_CONTENT["per_section"][section.name.lower()])
    for section in Section
}
"""§5.10's list for each of the eight: the five shared rows, the section's own, and the
Other row `reason_rows` appends. All eight keys exist in the file and two hold no rows of
their own, so every section offers at least six and none has to be special-cased."""

SECTION_LABELS = {row["id"]: row["label"]
                  for rows in SECTION_REASONS.values() for row in rows}

NO_CLOSING_REASON = ("This Visit finished the Visit Protocol, so it carries no closing "
                     "reason.")
"""§7.2 again: the Completed page's reason line is a written finding, not a blank."""

NOTHING_TO_SEND = ("A Visit that never started writes nothing back to the EMR, so there is "
                   "nothing queued for this one.")
"""§5.4. Said out loud on the Cancelled page rather than left off it — a missing Write-Back
line would make the reader guess between 'nothing to send' and 'nobody looked'."""

ACCEPTED = "The EMR accepted this Visit's Write-Back."
NOT_ATTEMPTED = ("This Visit's Write-Back is queued. Noor has not attempted it yet, and "
                 "nothing retries by itself.")
"""§6.1's last line as copy: no background loop, no timer, no polling. A queue that looked
like it was working on itself would be the thing §4.10 forbids, dressed as reassurance."""


class SectionMark(NamedTuple):
    """One of the eight, as a tile draws it. The word and the class travel together
    because §4.3 says a status colour never appears without its word."""

    name: str
    word: str
    mark: str
    slug: str


def marks(visit: Visit) -> tuple[SectionMark, ...]:
    """The eight, in the record's order, each with its resolved mark (web_plan §4.2)."""
    return tuple(_mark(section, section in visit.resolutions) for section in Section)


def _mark(section: Section, resolved: bool) -> SectionMark:
    """Resolved by content and resolved by a reason are one mark here (§5.8 makes both a
    passing Visit). Which of the two it was is `recorded_sentence`, on the section's own
    page — a tile that tried to say it would be a tile saying two things."""
    word, mark = RESOLVED[resolved]
    return SectionMark(SECTION_WORDS[section], word, mark, SLUG_OF[section])


RESOLVED = {True: ("Resolved", "mark-clear"), False: ("Nothing recorded", "mark-open")}


def settled_kind(visit: Visit) -> str:
    """What the Start settled, for a Visit that has one. ADR 0008: the record's own kind
    stands even where the history has moved on since."""
    if visit.kind is None:
        return NEVER_STARTED
    return KIND_WORDS[visit.kind]


def attendance(visit: Visit) -> str:
    """§5.13: who was in the house. Copied off the Patient at the Start, so a later
    reassignment never restates a closed Visit's pair — which is why this reads the Visit
    and never the Patient."""
    return f"Attended by {visit.junior_physician}, with {visit.nurse}."


def closed_sentence(visit: Visit) -> str:
    """Which close, by whom, and when — one sentence for all three terminal states, because
    the state word is already the first thing in it."""
    return (f"{STATE_WORDS[visit.state]} by {visit.closed_by} at "
            f"{visit.closed_at:%H:%M, %d %B}.")


def reason_sentence(visit: Visit) -> str:
    """The closing reason on a Visit page. `reason_words` is the same sentence for the
    Brief, which has a `Reason` and no Visit around it."""
    return reason_words(visit.closing_reason, CLOSING_LABELS)


def reason_words(reason: Reason | None, labels: Mapping[str, str]) -> str:
    """§5.10's structured reason, as the words the Field Team chose.

    The Other row is answered by its free text alone. Its label is an instruction to whoever
    is filling the form in — printing 'Other, write what happened' back onto a closed record
    would be the form's prompt leaking into the record it produced.
    """
    if reason is None:
        return NO_CLOSING_REASON
    if reason.row_id == OTHER:
        return f"Reason, in their own words: {reason.free_text}"
    if reason.free_text is None:
        return f"Reason: {labels[reason.row_id]}."
    return (f"Reason: {labels[reason.row_id]}. In their own words: "
            f"{reason.free_text}")


STRIP_CLASSES = {True: "strip-link strip-here", False: "strip-link"}
CURRENT = {True: "page", False: "false"}
"""`aria-current` is how the strip names the page you are on without a template deciding
anything. `false` is a real ARIA value and means exactly not-this-one, so both arms are a
lookup rather than an attribute that has to be absent."""


class Step(NamedTuple):
    """One of the eight in the strip: its mark, where it goes, and whether it is here."""

    name: str
    word: str
    mark: str
    href: str
    css: str
    current: str


def strip(visit: Visit, here: Section) -> tuple[Step, ...]:
    """The eight in the record's order, each a link, with this page marked (web_plan
    §4.3). It carries the eight and nothing else: the Brief and Home Readings are §4.4's,
    and a ninth entry would say Home Readings was one of the eight."""
    return tuple(
        _step(visit.id, _mark(section, section in visit.resolutions), section is here)
        for section in Section)


def _step(visit_id: str, mark: SectionMark, here: bool) -> Step:
    return Step(mark.name, mark.word, mark.mark,
                f"/visits/{visit_id}/sections/{mark.slug}",
                STRIP_CLASSES[here], CURRENT[here])


NOTHING_YET = "Nothing recorded in this section yet."
BY_CONTENT = "Recorded in this Visit."


def recorded_sentence(visit: Visit, section: Section) -> str:
    """Which of the two resolutions this section has, or neither — the distinction the
    Visit page's tiles defer to the section's own page (web_plan §4.3, §5.8)."""
    held = visit.resolutions.get(section)
    if held is None:
        return NOTHING_YET
    if held.reason is None:
        return BY_CONTENT
    if held.reason.row_id == OTHER:
        return f"Resolved without content: {held.reason.free_text}"
    words = SECTION_LABELS[held.reason.row_id]
    if held.reason.free_text is None:
        return f"Resolved without content: {words}."
    return (f"Resolved without content: {words}. In their own words: "
            f"{held.reason.free_text}")


def queue_count(queued: Mapping[str, Pending]) -> str:
    """§7.3: 'a count and a word' — never a glyph with a number on it. The colon form takes
    0, 1 and 5 without a plural, and a plural is a branch that would need testing twice to
    say nothing new."""
    return f"Write-Backs pending: {len(queued)}."


def writeback_sentence(visit: Visit, row: Pending | None) -> str:
    """What the Write-Back is doing (web_plan §4.2, §6.1). Only ever asked of a Visit that
    closed, which is why being off the queue means accepted rather than not yet due.

    `row.said` needs no case of its own: `store.mark_refused` writes the time and the words
    in one statement, so a refusal without words is not a row the store can produce.
    """
    if visit.state is VisitState.CANCELLED:
        return NOTHING_TO_SEND
    if row is None:
        return ACCEPTED
    if row.refused_at is None:
        return NOT_ATTEMPTED
    return (f"The EMR refused this Visit's Write-Back at "
            f"{row.refused_at:%H:%M, %d %B} and said: {row.said}")


NO_TRENDS = ("No previous Visit recorded any Vitals for this Patient, so there is no series "
             "to read yet.")
NOTHING_OVERDUE = "Every surveillance item this Patient's conditions call for is current."
NOTHING_HIDDEN = ("Noor read everything it asked the EMR for, so nothing on this page is "
                  "missing because of a failed read.")
"""§7.2 in three sentences. An empty region is not an answer, and N6 cuts both ways: a Brief
that saw everything has to say so, or a clean page and a broken one look alike."""

FIRST_VISIT = "This is the first Visit Noor holds for this Patient."
NEVER_RECORDED = "The record holds none."
"""§7.2's Absent shape — a written finding in the value's place, not an emptiness."""

NO_PLAN_YET = ("No Visit has emitted a Between-Visit Plan for this Patient yet, so there is "
               "none standing.")
PLAN_UNREACHABLE = ("The Between-Visit Plan in force could not be read. Noor cannot say "
                    "whether one is standing.")
"""Absent and Unreachable, kept apart (N6). This one states the failed read and stops there,
because `_blind_spots` already writes the consequence — *'...so this Visit's Home Readings
have nothing to be scored against'* — and on an open Visit both land on this page. The
declaration names the input; the `.note` below names the cost. Saying it twice would read
like two separate problems."""

FINDINGS_ONLY = ("This Brief states findings. It makes no recommendation, and nothing on it "
                 "has been decided for the Field Team.")
NO_HOME_READINGS = ("Home Readings are not in the Brief. They are read off the devices' own "
                    "memory when the Nurse arrives, so the between-Visit series becomes "
                    "visible in the house and not before.")
"""§5.3's own two limits, said on the page. The second is a consequence of the zero-cost
constraint rather than an oversight, and a reader who is not told that assumes an oversight."""


class Tile(NamedTuple):
    """A name and one line about it — what `.tile` is shaped for. Used for the Vitals series
    and for the overdue items, which are the same shape and never the same list."""

    name: str
    detail: str


def trend_tiles(trends: Sequence[Trend]) -> tuple[Tile, ...]:
    """§5.3's Vitals trend, as text. No chart: §7.3 removes the icon channel and §12.1
    admits one script that does the autosave and nothing else — and a series of dates and
    values read left to right is a trend a clinician can read out loud."""
    return tuple(Tile(f"{trend.label} ({trend.unit})", _series(trend.points))
                 for trend in trends)


def _series(points: Sequence[Point]) -> str:
    """Oldest first, as `brief()` builds them, because that is the direction a trend runs."""
    return " · ".join(f"{point.on:%d %B %Y}: {point.value}" for point in points)


def due_tiles(due: Sequence[Due]) -> tuple[Tile, ...]:
    return tuple(Tile(item.label, _last_done(item.last_done)) for item in due)


def _last_done(last: Datum) -> str:
    """Two states only. `brief()` drops an Unreachable item from the overdue list rather
    than making a clinical claim out of a failed request, so it cannot arrive here."""
    if last.is_present:
        return f"Last done {last.value:%d %B %Y}."
    return NEVER_RECORDED


def trend_summary(trends: Sequence[Trend]) -> str:
    return _counted(trends, some="Vitals series Noor holds for this Patient",
                    none=NO_TRENDS)


def due_summary(due: Sequence[Due]) -> str:
    return _counted(due, some="Surveillance items overdue", none=NOTHING_OVERDUE)


def spot_summary(spots: Sequence[str]) -> str:
    return _counted(spots, some="Reads Noor could not make", none=NOTHING_HIDDEN)


def _counted(items: Sequence[object], *, some: str, none: str) -> str:
    """§7.2's rule as one function: a count and a word where there is something, a written
    finding where there is not, and an empty region in neither case. Written once because
    three collections on one page obey it, and three copies would drift."""
    if items:
        return f"{some}: {len(items)}."
    return none


def last_visit_sentence(last: LastVisit | None) -> str:
    """§5.3: what the last Visit concluded. The state and the date are the conclusion; the
    reason is only ever set on a Visit that did not finish, and it is worth reading before
    knocking on the same door again."""
    if last is None:
        return FIRST_VISIT
    return (f"The last Visit was {STATE_WORDS[last.state]} on {last.on:%d %B %Y}. "
            f"{reason_words(last.reason, CLOSING_LABELS)}")


def plan_sentence(plan: Datum) -> str:
    """§5.3's declaration, in three shapes because there are three states (N6).

    The plan's own lines are not here: §5.3 asks whether one is in force and since when, and
    the titration steps, the schedule and the stop rules belong to the Care Plan section.
    """
    if plan.state is DataState.UNREACHABLE:
        return PLAN_UNREACHABLE
    if plan.state is DataState.ABSENT:
        return NO_PLAN_YET
    return (f"A Between-Visit Plan has been standing since {plan.as_of:%d %B %Y}. Its "
            "titration steps, schedule and stop rules are on the Care Plan section.")


PROMPTS = {
    Section.VISIT_REASON: "Why this Visit is happening, in the words the household used.",
    Section.NOTES: "Anything the other seven sections have no place for.",
}
"""The one line above a free-text box. Two entries, because two of the eight are prose."""


def held_text(visit: Visit, section: Section) -> str:
    """What is already in the box.

    A section resolved without content hands back nothing to type over: its reason is
    already on the page in `recorded_sentence`, and putting a reason's label into a
    content box would turn a structured reason into prose the engine cannot read (§5.10).
    """
    held = visit.resolutions.get(section)
    if held is None or held.reason is not None:
        return ""
    return str(held.content)


EVENT_ROWS = tuple(content.load("interval-events").data["events"]["rows"])
NONE_OF_THESE = "none-of-these"
RAISERS = ("Patient", "Caregiver")
"""The two people a concern can be attributed to (§4.2). A concern with no name against it
is prose, and prose is what Notes is for."""

TICKED = {True: "checked", False: ""}
"""The attribute or nothing. `checked=""` is a *checked* box in HTML, so the whole
attribute has to come through the map rather than its value."""


class Tick(NamedTuple):
    id: str
    label: str
    checked: str


def event_ticks(visit: Visit) -> tuple[Tick, ...]:
    """The eight rows in the file's order, each remembering whether it is already
    ticked — so reopening the section shows what was recorded rather than a blank list."""
    held = _content(visit, Section.CONCERNS_AND_INTERVAL_HISTORY, {"events": []})
    ticked = set(held["events"])
    return tuple(Tick(row["id"], row["label"], TICKED[row["id"] in ticked])
                 for row in EVENT_ROWS)


def concerns_held(visit: Visit) -> dict[str, str]:
    """Each raiser's concerns, one to a line, back in that raiser's own box."""
    held = _content(visit, Section.CONCERNS_AND_INTERVAL_HISTORY, {"concerns": []})
    lines: dict[str, list[str]] = {who: [] for who in RAISERS}
    for item in held["concerns"]:
        lines[item["raised_by"]].append(item["words"])
    return {who: "\n".join(said) for who, said in lines.items()}


def _content(visit: Visit, section: Section, empty: Mapping[str, object]) -> Mapping:
    """A section's recorded content, or an empty shape of the same form.

    A section resolved by a reason answers `empty` too: its reason is on the page in
    `recorded_sentence`, and there is nothing in it to put back in a box (§5.10).
    """
    held = visit.resolutions.get(section)
    if held is None or held.reason is not None:
        return empty
    return held.content


class Field(NamedTuple):
    """One numeric box: what it asks for, in what unit, and what is already in it."""

    id: str
    label: str
    unit: str
    held: str


def vitals_fields(visit: Visit, asked: Sequence[Measurement]) -> tuple[Field, ...]:
    """A box per measurement this Visit asks for, in the content file's order — which
    `asked_for` documents as the form's order, so the form does not reorder it."""
    held = _content(visit, Section.VITALS, {})
    return tuple(Field(measure.id, measure.label, measure.unit,
                       str(held.get(measure.id, "")))
                 for measure in asked)


BASIS_WORDS = {
    Composition.COMPOSED:
        "This list was composed from the Patient's conditions and the surveillance that "
        "is overdue.",
    Composition.BASELINE:
        "This is a Baseline Visit, so the whole examination is required — there is no "
        "surveillance history to compose from.",
    Composition.UNREACHABLE:
        "The surveillance dates could not be read. The whole examination is required, "
        "and no element is marked overdue.",
}
"""One sentence per basis. The Unreachable one names the input *and* the consequence,
because §7.2 says an Unreachable that only names the input leaves the reader to guess what
it cost them. Noor does not distinguish no signal from a cache that was never filled
(§4.10), so the sentence says *could not be read* and claims nothing about why."""

UNREACHABLE = frozenset({Composition.UNREACHABLE})
BASIS_CLASSES = {True: "unreachable", False: "note"}
"""§7.2: Absent and Unreachable differ by shape, not by colour. The hairline-bounded block
is the shape, and neither carries a status colour or a badge."""


def composition_block(composed: Composed) -> tuple[str, str]:
    """What the top of the Physical Examination says about its own list, and how it is
    drawn — a sentence in the flow, or a bounded block when an input was unreachable."""
    return (BASIS_WORDS[composed.basis],
            BASIS_CLASSES[composed.basis in UNREACHABLE])


EVERY_PATIENT = "Required for every Patient."


class Row(NamedTuple):
    """One required element: what it is, why it is required, and what was found."""

    id: str
    label: str
    note: str
    held: str


def element_rows(visit: Visit, required: Sequence[Element]) -> tuple[Row, ...]:
    """The composed list, each row saying why it is on the list. A row that is there
    because surveillance is overdue says so, because that is the difference between a list
    the Field Team trusts and a list it works around."""
    held = _content(visit, Section.PHYSICAL_EXAMINATION, {"elements": {}})
    return tuple(Row(element.id, element.label, _why(element),
                     str(held["elements"].get(element.id, "")))
                 for element in required)


def _why(element: Element) -> str:
    if element.overdue is None:
        return EVERY_PATIENT
    return f"Required because {element.overdue} surveillance is overdue."


def added_text(visit: Visit) -> str:
    """The elements the Field Team added, back in the box they were typed in."""
    return str(_content(visit, Section.PHYSICAL_EXAMINATION, {"added": ""})["added"])


OUTCOMES = (("correct", "Done correctly"),
            ("incorrect", "Done, and not correctly"),
            ("nothing-to-use", "Nothing in the house to do it with"))
"""§4.5: observed, never asked — so the three outcomes are three things somebody watched,
not three things somebody was told. The third is a Finding in its own right: an item that
needed a meter, in a house with no meter, is a fact about the house
(`self-care-items.md`)."""


class Choice(NamedTuple):
    value: str
    label: str
    checked: str


class Watched(NamedTuple):
    id: str
    label: str
    mode: str
    choices: tuple[Choice, ...]


def self_care_rows(visit: Visit,
                   items: Sequence[SelfCareItem]) -> tuple[Watched, ...]:
    """One row per applicable item, in the catalogue's order, each remembering which of
    the three outcomes is already recorded against it."""
    held = _content(visit, Section.SELF_CARE_CHECK, {})
    return tuple(Watched(item.id, item.label, item.mode,
                         tuple(Choice(value, label,
                                      TICKED[held.get(item.id) == value])
                               for value, label in OUTCOMES))
                  for item in items)


class Found(NamedTuple):
    """One search hit, labelled with everything the list decides so nothing is typed."""

    id: str
    label: str


class Box(NamedTuple):
    """One item in the house, as it reads back."""

    index: int
    label: str
    detail: str
    quantity: str
    expiry: str


UNMATCHED = "Not on the drug list — Noor cannot reconcile this item"
NO_COUNT = "no count recorded"
NO_EXPIRY = "no expiry recorded"
"""§7.2: Absent is a written finding. A box nobody counted says so in words, because an
empty cell and a count of nought are different facts and the second is prohibited."""


def product_label(product: Product) -> str:
    return f"{product.generic} {product.strength} {product.form}"


def search_results(products: Sequence[Product]) -> tuple[Found, ...]:
    return tuple(Found(product.id, product_label(product)) for product in products)


def house_boxes(house: Sequence[Medication]) -> tuple[Box, ...]:
    """The house as it reads back. The index is how a row is removed — a label is not
    unique, because two boxes of the same drug is a discrepancy Noor has to be able to
    hold long enough to report."""
    return tuple(Box(index, *_box(item)) for index, item in enumerate(house))


def _box(item: Medication) -> tuple[str, str, str, str]:
    label, detail = _named(item)
    return (label, detail, _count(item.quantity_remaining), _expiry(item.expiry))


def _named(item: Medication) -> tuple[str, str]:
    if item.product is None:
        return (item.label, UNMATCHED)
    return (product_label(item.product), item.product.drug_class)


def _count(remaining: int | None) -> str:
    if remaining is None:
        return NO_COUNT
    return f"{remaining} remaining"


def _expiry(expiry: date | None) -> str:
    if expiry is None:
        return NO_EXPIRY
    return f"expires {expiry.isoformat()}"


def discrepancy_lines(found: Sequence[Discrepancy]) -> tuple[str, ...]:
    """One sentence each, the kind's own words after the subject. `DiscrepancyKind`'s
    values are already sentences, so nothing is restated here."""
    return tuple(f"{item.subject} — {item.kind.value}" for item in found)


COMPARISON_WORDS = {
    DataState.PRESENT:
        "The house was compared against the prescribed list Noor read before the van "
        "left.",
    DataState.UNREACHABLE:
        "The prescribed list could not be read. What is in the house is recorded in "
        "full, and nothing is compared against the list — no omission and no "
        "unprescribed item can be found here.",
}
"""`reconcile` answers with these two states and no third: an Absent prescribed list is
compared as an empty list, which is a real comparison. So there are two rows here, and a
third state would raise KeyError rather than be drawn as one of the two (ADR 0007)."""


def comparison_block(result: Reconciliation) -> tuple[str, str]:
    """What the section says about its own comparison, and how it is drawn (§7.2)."""
    return (COMPARISON_WORDS[result.comparison],
            BASIS_CLASSES[not result.is_complete])


NOTHING_MATCHED = ("No product on the drug list matches. Record the item as written on "
                   "the box instead — Noor keeps it, marked unmatched.")
SEARCH_PROMPT = "Search the drug list above to add a box."
NOTHING_FOUND_YET = "Nothing found against the house yet"
FOUND_SO_FAR = "What the comparison found"


def search_heading(query: str, hits: Sequence[Found]) -> str:
    """Three things the search can be, as three sentences. A search nobody has run and a
    search that matched nothing are different, and the second is where §4.2's unmatched
    outcome has to be offered."""
    if not query.strip():
        return SEARCH_PROMPT
    if not hits:
        return NOTHING_MATCHED
    return f"Products matching “{query}”"


def discrepancy_heading(found: Sequence[Discrepancy]) -> str:
    return FOUND_SO_FAR if found else NOTHING_FOUND_YET


HOME_AXES = (Axis.SYSTOLIC, Axis.DIASTOLIC,
             Axis.GLUCOSE_PRE_PRANDIAL, Axis.GLUCOSE_POST_PRANDIAL)
"""The four of `Axis`'s five a household can measure. HbA1c is drawn in a laboratory, and
§4.8 requires every line of a Between-Visit Plan to be one somebody can carry out."""

AXIS_WORDS = {
    Axis.SYSTOLIC: "Systolic blood pressure",
    Axis.DIASTOLIC: "Diastolic blood pressure",
    Axis.GLUCOSE_PRE_PRANDIAL: "Glucose before a meal",
    Axis.GLUCOSE_POST_PRANDIAL: "Glucose two hours after a meal",
}

TITRATION_WITHHELD = (
    "No titration step can be set on this Visit. Titration needs a ratified Goal of "
    "Care, and this Patient has none — the home measurement schedule and the stop rules "
    "do not, and both are set below.")
"""§4.11's withholding, in §4.8's own terms. The Goal of Care is proposed and ratified in
Web Pass 5; until then this is a limit Noor states, not a field it offers and refuses."""


class PlanRow(NamedTuple):
    """One axis: how often it is measured at home, and the two thresholds that stop."""

    axis: Axis
    label: str
    times: str
    floor: str
    ceiling: str


def plan_rows(visit: Visit) -> tuple[PlanRow, ...]:
    """The four axes with whatever the Visit has already emitted against each."""
    plan = visit.plan
    weekly = _weekly(plan)
    below, above = _stops(plan)
    return tuple(PlanRow(axis, AXIS_WORDS[axis],
                         weekly.get(axis, ""), below.get(axis, ""), above.get(axis, ""))
                 for axis in HOME_AXES)


def _weekly(plan: BetweenVisitPlan | None) -> dict[Axis, str]:
    if plan is None:
        return {}
    return {line.axis: str(line.times_per_week) for line in plan.schedule}


def _stops(plan: BetweenVisitPlan | None) -> tuple[dict[Axis, str], dict[Axis, str]]:
    """The stop rules split by direction, because a floor and a ceiling are two boxes."""
    if plan is None:
        return ({}, {})
    return ({rule.axis: str(rule.value) for rule in plan.stop_rules
             if rule.comparison is Comparison.BELOW},
            {rule.axis: str(rule.value) for rule in plan.stop_rules
             if rule.comparison is Comparison.ABOVE})


def too_early_sentence(outstanding: Sequence[Section]) -> str:
    """§4.2's rule as the page's own words. The list is named, because *finish the others*
    with no list is an instruction the Field Team has to go hunting to follow."""
    return ("The Care Plan is assembled after the other seven. Still unresolved: "
            + ", ".join(SECTION_WORDS[section] for section in outstanding) + ".")


def plan_action(visit: Visit) -> str:
    """The action already set against the stop rules. One action for all of them, so the
    first is the answer and an empty plan is an empty box."""
    plan = visit.plan
    if plan is None or not plan.stop_rules:
        return ""
    return plan.stop_rules[0].action


def outstanding_in(message: str) -> tuple[Section, ...]:
    """The sections `check_care_plan_ready` named, back as sections. The message ends in
    the enum names, comma-separated; parsing them here keeps the domain's guard the only
    place that decides which sections are outstanding."""
    named = message.rsplit(": ", 1)[-1].split(", ")
    return tuple(Section[name] for name in named)


SOURCE_WORDS = {Source.DEVICE_MEMORY: "Read off the device's own memory",
                Source.PAPER_LOG: "Copied from a Caregiver's paper log"}
"""§4.8's two sources as the words on the radio. The values stored are the enum's own, so
this map is the label and never the record."""

SOURCE_ROWS = tuple((source.value, SOURCE_WORDS[source]) for source in Source)
"""Value and label, in `Source`'s own declaration order, so a third source added to the
enum reaches the form without this file being edited."""


class Reading(NamedTuple):
    """One Home Reading as it reads back. Every field a string: §4.8's series is read, not
    computed on, so the page needs no numbers."""

    label: str
    value: str
    when: str
    source: str


def reading_lines(readings: Sequence[HomeReading],
                  asked: Sequence[Measurement]) -> tuple[Reading, ...]:
    """The series, grouped by measurement and in time order within each.

    Sorted on the label so the grouping is the same one the reader sees, and a measurement
    the Patient is no longer asked for sorts by its id — which is also what it is labelled
    with, because a reading already collected must not lose its name to a condition that
    changed.
    """
    labels = {measure.id: measure.label for measure in asked}
    units = {measure.id: measure.unit for measure in asked}
    return tuple(Reading(labels.get(reading.measurement, reading.measurement),
                         _with_unit(reading.value, units.get(reading.measurement)),
                         f"{reading.taken_at:%H:%M, %d %B}",
                         reading.source.value)
                 for reading in sorted(readings, key=lambda r: (
                     labels.get(r.measurement, r.measurement), r.taken_at)))


def _with_unit(value: str, unit: str | None) -> str:
    """A reading with no unit is one whose measurement is off this Patient's list. The
    value stands alone rather than acquiring a unit Noor is guessing at."""
    if unit is None:
        return value
    return f"{value} {unit}"


def reading_options(asked: Sequence[Measurement]) -> tuple[Found, ...]:
    """The measurements this Patient's conditions ask for, with the unit on the label so
    the Nurse knows which one the box wants before typing into it."""
    return tuple(Found(measure.id, f"{measure.label} ({measure.unit})")
                 for measure in asked)


NO_READINGS_YET = ("No Home Readings have been collected on this Visit. That is not a "
                   "series Noor could not read — nothing has been entered yet.")
"""§7.2's two absences, distinguished. An empty series and an unreadable one are different
facts, and this page can only ever be the first."""


def home_readings_sentence(readings: Sequence[HomeReading]) -> str:
    """The Visit page's line, and the heading on this one. A count, honest at nought."""
    if not readings:
        return NO_READINGS_YET
    return f"Home Readings collected on this Visit: {len(readings)}."
