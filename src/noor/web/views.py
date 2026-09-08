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
from noor.domain.records import OTHER, Reason, reason_rows
from noor.domain.states import DataState, Datum, Section, VisitKind, VisitState
from noor.domain.visit import Visit
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
    """One of the eight, with its mark. The word and the class travel together because §4.3
    says a status colour never appears without its word — as one tuple, a template cannot
    render the colour and forget the word."""

    name: str
    word: str
    mark: str


def marks(visit: Visit) -> tuple[SectionMark, ...]:
    """The eight, in the record's order, each with its resolved mark (web_plan §4.2)."""
    return tuple(_mark(section, section in visit.resolutions) for section in Section)


def _mark(section: Section, resolved: bool) -> SectionMark:
    """Resolved by content and resolved by a reason are one mark here (§5.8 makes both a
    passing Visit). Which of the two it was is on the section's own page, in Web Pass 2 —
    a tile that tried to say it would be a tile saying two things."""
    if resolved:
        return SectionMark(SECTION_WORDS[section], "Resolved", "mark-clear")
    return SectionMark(SECTION_WORDS[section], "Nothing recorded", "mark-open")


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
    return reason_words(visit.closing_reason)


def reason_words(reason: Reason | None) -> str:
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
        return f"Reason: {CLOSING_LABELS[reason.row_id]}."
    return (f"Reason: {CLOSING_LABELS[reason.row_id]}. In their own words: "
            f"{reason.free_text}")


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
            f"{reason_words(last.reason)}")


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
