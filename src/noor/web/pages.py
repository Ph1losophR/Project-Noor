"""Every Field Team handler, and the two things every render needs: the template
environment, and the mode the page is stamped with.

Separate from `app.py` so the wiring can import the handlers without a cycle, and so
`app.py` stays a table a reader can check against web_plan §2.
"""
from datetime import date, datetime, time, timedelta
from pathlib import Path
from sqlite3 import Connection
from urllib.parse import urlsplit

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.templating import Jinja2Templates

from noor import content, emr, prefetch, store
from noor.domain import examination, plans, reconciliation, selfcare, vitals
from noor.domain.brief import brief as read_brief
from noor.domain.plans import (Axis, BetweenVisitPlan, Comparison, MeasurementSchedule,
                               Threshold)
from noor.domain.records import (CarePlanTooEarly, Resolution, ResolutionError,
                                 check_care_plan_ready, reason_for)
from noor.domain.states import Datum, IllegalTransition, Section, VisitKind, VisitState
from noor.domain.visit import Visit, kind_for
from noor.web import views

templates = Jinja2Templates(directory=Path(__file__).with_name("templates"))

CATALOGUE = examination.items(
    content.load("surveillance-intervals").data["intervals"]["rows"])
MEASURES = vitals.measurements(
    content.load("vitals-by-condition").data["measurements"]["rows"])
"""The two catalogues `brief()` takes. Read at import, like `views.CANCELLED_ROWS`: a
malformed content file should stop the process starting rather than surface as a half-built
Brief on the one screen that needed it (ADR 0007). Held here rather than in `views.py`
because they are arguments to the domain, not copy."""

ELEMENTS = examination.elements(
    content.load("physical-examination-elements").data["elements"]["rows"])
INTERVALS = examination.months_by_item(
    content.load("surveillance-intervals").data["intervals"]["rows"])
SELF_CARE = selfcare.self_care_items(
    content.load("self-care-items").data["items"]["rows"])
PRODUCTS = {product.id: product for product in emr.catalogue()}
"""The shipped drug list by id (§6): a demonstration subset, not a formulary. Held here so
the search and the decode of a stored house read the same rows."""

THEMES = frozenset({"light", "dark"})
FLIP = {"dark": "light"}
"""One entry, because one direction is all the mapping has to state: from dark go light,
from anywhere else — light, or the OS preference nobody has overridden — go dark. A
two-armed `if` would be two branches for one fact."""
A_YEAR = 60 * 60 * 24 * 365


def theme_of(request: Request) -> str:
    """The mode this render is stamped with (§9). `system` is a value the stylesheet has
    no rule for, which is how `prefers-color-scheme` gets to decide."""
    return _known(request.cookies.get("theme"))


def _known(value: str | None) -> str:
    """A cookie is something a person can type. Anything that is not one of the two
    words is `system`, which is also the answer when there is no cookie at all."""
    return value if value in THEMES else "system"


def here(request: Request) -> str:
    """Where the toggle comes back to, query and all, so flipping the mode on
    `/visits?day=2026-08-28` does not silently drop the day."""
    return "?".join(filter(None, (request.url.path, request.url.query)))


def _back(value: str) -> str:
    """A `Location` built out of a form field is an open redirect until the scheme and
    the host are dropped. `urlsplit` drops them, so `https://elsewhere/x` becomes `/x`
    and this header can only ever point back into Noor."""
    parts = urlsplit(value)
    return "?".join(filter(None, (parts.path, parts.query))) or "/"


def page(request: Request, name: str, status: int = 200, **context) -> Response:
    """One render, so no handler can forget the two things the header needs."""
    return templates.TemplateResponse(
        request, name,
        {"theme": theme_of(request), "back": here(request), **context},
        status_code=status)


async def doors(request: Request) -> Response:
    """web_plan §3: it picks a surface, not a person."""
    return page(request, "doors.html")


async def toggle(request: Request) -> Response:
    """The one POST on every page (§9). A route rather than a listener: the stamp is
    written before the document is sent, so there is no flash of the wrong mode, and a
    route is testable in Python where a listener is not."""
    form = await request.form()
    answer = RedirectResponse(_back(str(form.get("back", ""))), status_code=303)
    answer.set_cookie("theme", FLIP.get(theme_of(request), "dark"),
                      max_age=A_YEAR, httponly=True, samesite="lax")
    return answer


async def not_found(request: Request, exc: Exception) -> Response:
    """An address Noor does not have, answered in words with the header still on it."""
    return page(request, "refusal.html", status=404,
                heading="No such page",
                sentence="Noor has no page at this address. The wordmark above goes "
                         "back to the two doors.")


class Refusal(Exception):
    """A request Noor can read the shape of and cannot answer: a day nobody could have
    written, a Visit the store does not have.

    Carries its own words, because the handler that raises it knows what went wrong and the
    one that renders it does not. §4.1's first rule for a screen is that it never looks
    broken — a 500 says Noor is broken, and this says what happened.
    """

    def __init__(self, heading: str, sentence: str) -> None:
        super().__init__(heading)
        self.heading = heading
        self.sentence = sentence


async def refused(request: Request, exc: Refusal) -> Response:
    """400, in words, with the header still on it and the wordmark still a way back."""
    return page(request, "refusal.html", status=400,
                heading=exc.heading, sentence=exc.sentence)


async def visits(request: Request) -> Response:
    """web_plan §4.1: the day's roster. Today unless the address says otherwise."""
    day = _day(request)
    conn = store.connect(request.app.state.db)
    entries = store.roster(conn, day)
    lines = [_line(conn, entry) for entry in entries]
    conn.close()
    return page(request, "visits.html",
                day=views.day_words(day),
                summary=views.summary(entries),
                lines=lines,
                earlier=(day - timedelta(days=1)).isoformat(),
                later=(day + timedelta(days=1)).isoformat())


def _day(request: Request) -> date:
    """`?day=` where it is given, today where it is not.

    A day that is not a day is refused rather than swallowed. Falling back to today would
    answer a question nobody asked, and on a screen whose entire subject is *which day*
    that is the quiet failure §4.10 forbids wearing a different hat.
    """
    asked = request.query_params.get("day")
    if asked is None:
        return request.app.state.now().date()
    try:
        return date.fromisoformat(asked)
    except ValueError:
        raise Refusal(
            "Not a day",
            f"Noor cannot read {asked!r} as a day. A day is written 2026-08-28, and the "
            f"two links at the foot of the Visit List move one day at a time.") from None


def _line(conn: Connection, entry: store.RosterEntry) -> views.Line:
    """Three reads per row: the Visit for its settled kind, the history for the planning
    indicator, the cache for readiness.

    Fifteen reads of a local file for a five-Visit day. One clinician against one SQLite
    file (ADR 0006) is what makes that a loop and not a problem; if a day ever holds a
    hundred Visits, the join belongs in the store instead.
    """
    return views.line(entry,
                      visit=store.load(conn, entry.visit_id),
                      planned=kind_for(store.history(conn, entry.patient_id)),
                      prepared=prefetch.readiness(conn, entry.patient_id))


class Suspended(Exception):
    """§5.7: while a Visit is in Emergency the Visit Protocol stops. §4.2 says what that
    means for navigation — every address under /visits/{id} goes to the Emergency Protocol
    instead. Raised from `_visit`, so every page that loads a Visit inherits the rule
    instead of each one remembering it."""

    def __init__(self, visit_id: str) -> None:
        super().__init__(visit_id)
        self.visit_id = visit_id


async def suspended(request: Request, exc: Suspended) -> Response:
    """303 for every redirect in Noor, whether it follows a GET or a POST: one number is
    one thing to hold in the head, and 'see other' is true of all of them."""
    return RedirectResponse(f"/visits/{exc.visit_id}/emergency", status_code=303)


async def unknown_visit(request: Request, exc: store.UnknownVisit) -> Response:
    """404 in words. The address was well-formed and named nothing, which is a different
    thing from Noor being broken — and §4.1 says a screen never looks broken."""
    return page(request, "refusal.html", status=404,
                heading="No Visit at that address",
                sentence="Noor has no Visit with that identifier. It may have been opened "
                         "from a page that is out of date — the day's Visits are one link "
                         "up.")


async def visit(request: Request) -> Response:
    """web_plan §4.2: one address, and what it shows is what the Visit is."""
    conn = store.connect(request.app.state.db)
    record = _visit(conn, request.path_params["visit_id"])
    template, build = PAGES[record.state]
    context = _common(conn, record) | build(conn, record)
    conn.close()
    return page(request, template, **context)


def _visit(conn: Connection, visit_id: str) -> Visit:
    """The Visit behind any address under /visits/{id}, or the suspension (§4.2).

    Task 8's Brief, Task 7's two POSTs and Web Pass 2's eight section pages load through
    here for that second reason. §4.2 excepts the Handover, which is Web Pass 2 and reads
    its Visit with `store.load` directly rather than through this. An unknown id raises
    `store.UnknownVisit` from the load, which nothing here catches: it is answered once, for
    every route, by `unknown_visit`.
    """
    record = store.load(conn, visit_id)
    if record.state is VisitState.EMERGENCY:
        raise Suspended(visit_id)
    return record


def _open_visit(conn: Connection, visit_id: str) -> Visit:
    """The Visit behind a section address, which exists only while it is In Progress.

    CONTEXT.md makes In Progress the only state the Visit Protocol is worked through in.
    One arm rather than two, because the sentence is true of all four other states and a
    second arm would be a second branch for the same fact. web_plan §6.2 wants the closed
    case on the Addendum screen — that is Web Pass 3, and it replaces this refusal rather
    than adding to it.
    """
    record = _visit(conn, visit_id)
    if record.state is not VisitState.IN_PROGRESS:
        raise Refusal(
            "This Visit is not open",
            f"The Visit Protocol is worked through while a Visit is In Progress. It is "
            f"{views.STATE_WORDS[record.state]}. The Visit itself is one link up.")
    return record


def _section_of(slug: str) -> Section:
    """One of web_plan §4.3's eight, or the same 404 any other unknown address gets."""
    try:
        return views.SLUGS[slug]
    except KeyError:
        raise HTTPException(404) from None


def _frame(conn: Connection, record: Visit, section: Section) -> dict[str, object]:
    """What every section template carries, whatever its form asks for."""
    return {"visit_id": record.id,
            "patient": store.patient_name(conn, record.patient_id),
            "section": views.SECTION_WORDS[section],
            "slug": views.SLUG_OF[section],
            "steps": views.strip(record, section),
            "recorded": views.recorded_sentence(record, section),
            "reasons": views.SECTION_REASONS[section]}


async def section(request: Request) -> Response:
    """web_plan §4.3: one page per section, dispatched on which of the eight it is."""
    conn = store.connect(request.app.state.db)
    section_of = _section_of(request.path_params["slug"])
    record = _open_visit(conn, request.path_params["visit_id"])
    template, build, _ = SECTIONS[section_of]
    context = _frame(conn, record, section_of) | build(request, conn, record)
    conn.close()
    return page(request, template, **context)


async def resolve(request: Request) -> Response:
    """One POST per section, and both of §5.8's two ways to resolve one.

    A posted reason is the whole answer, because §5.10's list sits behind its own guard
    rather than beside the form — so content and a reason cannot arrive together, and
    `Resolution`'s exclusive-or never has to be guessed at. `reason_for` checks the row
    against the list that was rendered, so a list that changed under an open page is
    refused rather than stored.
    """
    conn = store.connect(request.app.state.db)
    section_of = _section_of(request.path_params["slug"])
    visit_id = request.path_params["visit_id"]
    record = _open_visit(conn, visit_id)
    form = await request.form()
    _, _, parse = SECTIONS[section_of]
    record.resolutions[section_of] = _resolution(section_of, form, conn, record, parse)
    store.save(conn, record)
    conn.close()
    return RedirectResponse(
        _after(str(form.get("act", DONE)), visit_id, views.SLUG_OF[section_of]),
        status_code=303)


def _resolution(section: Section, form, conn: Connection, record: Visit,
                parse) -> Resolution:
    """Which of §5.8's two shapes this post is. One branch, on one field."""
    row_id = str(form.get("reason", ""))
    if row_id:
        return Resolution(section, reason=reason_for(
            views.SECTION_REASONS[section], row_id, str(form.get("words", ""))))
    return Resolution(section, content=parse(form, conn, record))


STAY = frozenset({"add", "remove"})


def _after(act: str, visit_id: str, slug: str) -> str:
    """Where a save lands. Seven sections have one answer; Reconciliation is built a box
    at a time, so two of its three acts come back to the form. §12.1 already contemplates
    a post that stays — the autosave is one — so this is that shape and not a new one."""
    return {True: f"/visits/{visit_id}/sections/{slug}",
            False: f"/visits/{visit_id}"}[act in STAY]


def _visit_reason(request: Request, conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2's Visit Reason: why this Visit is happening, in prose."""
    return {"prompt": views.PROMPTS[Section.VISIT_REASON],
            "held": views.held_text(record, Section.VISIT_REASON)}


def _notes(request: Request, conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2's Notes: eighth in the record, and the Care Plan is assembled after it."""
    return {"prompt": views.PROMPTS[Section.NOTES],
            "held": views.held_text(record, Section.NOTES)}


def _free_text(form, conn: Connection, record: Visit) -> str:
    """The box, or the refusal that names both ways out. `Resolution` would refuse an
    empty string too, in words about content and reasons that are true and are not for
    somebody standing in a doorway."""
    words = str(form.get("words", "")).strip()
    if not words:
        raise Refusal(
            "Nothing was recorded",
            "This section has nothing recorded in it and no reason for having nothing. "
            "Record something, or use “Nothing to record here” and choose a reason.")
    return words


def _concerns(request: Request, conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2's two halves: the fixed list a rule reads, and the free text it cannot."""
    return {"ticks": views.event_ticks(record),
            "raisers": views.RAISERS,
            "held": views.concerns_held(record)}


def _interval(form, conn: Connection, record: Visit) -> dict[str, object]:
    """The ticks and the concerns, with the one combination that cannot be true refused."""
    events = [str(value) for value in form.getlist("events")]
    if not events:
        raise Refusal(
            "Nothing was recorded",
            "The list of events since the last Visit has nothing ticked. If nothing "
            "happened, tick “None of these” — it is an answer, and a blank list is not.")
    if views.NONE_OF_THESE in events and len(events) > 1:
        raise Refusal(
            "Two answers that cannot both be true",
            "“None of these” is ticked beside an event that happened. Untick whichever "
            "of the two is wrong — a rule reading this list has no way to choose.")
    return {"events": events, "concerns": _raised(form)}


def _raised(form) -> list[dict[str, str]]:
    """One item per non-blank line, in the box's order, attributed to that box's raiser."""
    return [{"raised_by": who, "words": line.strip()}
            for who in views.RAISERS
            for line in str(form.get(who, "")).splitlines()
            if line.strip()]


def _vitals(request: Request, conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2's Vitals: what the conditions and the kind ask for, and nothing else."""
    asked = vitals.asked_for(MEASURES,
                             conditions=store.conditions(conn, record.patient_id),
                             kind=record.kind)
    return {"fields": views.vitals_fields(record, asked)}


def _readings(form, conn: Connection, record: Visit) -> dict[str, str]:
    """Only the boxes with something in them. A blank box is not a reading of nought, and
    storing one would put a number where there was no measurement (N6)."""
    asked = vitals.asked_for(MEASURES,
                             conditions=store.conditions(conn, record.patient_id),
                             kind=record.kind)
    taken = {measure.id: str(form.get(measure.id, "")).strip() for measure in asked}
    recorded = {key: value for key, value in taken.items() if value}
    if not recorded:
        raise Refusal(
            "Nothing was recorded",
            "Every box in Vitals is empty. Record at least one reading, or use "
            "“Nothing to record here” and choose a reason.")
    return recorded


def _examination(request: Request, conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2: Noor composes the required list. `compose` reads the cache, so an unfilled
    one comes back as Composition.UNREACHABLE rather than as a shorter list (§4.10)."""
    composed = examination.compose(
        ELEMENTS,
        kind=record.kind,
        conditions=store.conditions(conn, record.patient_id),
        surveillance=prefetch.surveillance(conn, record.patient_id),
        intervals=INTERVALS,
        as_of=store.visit_day(conn, record.id))
    basis, basis_css = views.composition_block(composed)
    held = views.element_rows(record, composed.required)
    return {"basis": basis, "basis_css": basis_css, "rows": held,
            "added": views.added_text(record)}


def _findings(form, conn: Connection, record: Visit) -> dict[str, object]:
    """A finding against each element examined, plus whatever else was."""
    written = {element.id: str(form.get(element.id, "")).strip()
               for element in ELEMENTS}
    elements = {key: value for key, value in written.items() if value}
    added = str(form.get("added", "")).strip()
    if not elements and not added:
        raise Refusal(
            "Nothing was recorded",
            "Nothing is written against any element of the examination. Record what was "
            "found, or use “Nothing to record here” and choose a reason.")
    return {"elements": elements, "added": added}


def _self_care(request: Request, conn: Connection, record: Visit) -> dict[str, object]:
    """§4.5's items, filtered to this Patient's conditions. `selfcare` carries no filter
    of its own, so `examination.applies` reads the shared no-condition-means-everybody
    convention here too (ADR 0007)."""
    return {"rows": views.self_care_rows(record, _applicable(conn, record))}


def _applicable(conn: Connection, record: Visit) -> list[selfcare.SelfCareItem]:
    held = set(store.conditions(conn, record.patient_id))
    return [item for item in SELF_CARE if examination.applies(item.conditions, held)]


VALID_OUTCOMES = frozenset(value for value, _ in views.OUTCOMES)


def _observations(form, conn: Connection, record: Visit) -> dict[str, str]:
    """One of the three against each item that was watched, and nothing invented for the
    ones that were not."""
    watched = {item.id: str(form.get(item.id, ""))
               for item in _applicable(conn, record)}
    recorded = {key: value for key, value in watched.items() if value}
    if not recorded:
        raise Refusal(
            "Nothing was recorded",
            "Nothing is recorded against any self-care item. Record what was watched, or "
            "use “Nothing to record here” and choose a reason.")
    if not set(recorded.values()) <= VALID_OUTCOMES:
        raise Refusal(
            "That is not one of the three outcomes",
            "An outcome arrived that is not one of the three this section offers. The "
            "page it was sent from is out of date — open the section again.")
    return recorded


def _medication(request: Request, conn: Connection,
                record: Visit) -> dict[str, object]:
    """§4.2's Reconciliation: the house so far, the search, and what the comparison found.

    The discrepancies are recomputed on every render rather than read back from the stored
    content, so the Nurse sees an omission appear the moment the box that answers it goes
    into the house.
    """
    query = request.query_params.get("q", "")
    hits = views.search_results(
        reconciliation.search(tuple(PRODUCTS.values()), query))
    result = _reconciled(conn, record, _house(conn, record))
    comparison, comparison_css = views.comparison_block(result)
    return {"query": query,
            "results": hits,
            "found_heading": views.search_heading(query, hits),
            "boxes": views.house_boxes(result.house),
            "found_so_far": views.discrepancy_heading(result.discrepancies),
            "discrepancies": views.discrepancy_lines(result.discrepancies),
            "comparison": comparison,
            "comparison_css": comparison_css}


def _house(conn: Connection, record: Visit) -> list[reconciliation.Medication]:
    """The house as it stands, decoded from the stored section. `read_entry` resolves each
    product against the shipped list on the way in, so a correction to that list reaches a
    house already recorded."""
    held = record.resolutions.get(Section.MEDICATION_RECONCILIATION)
    if held is None or held.reason is not None:
        return []
    return [reconciliation.read_entry(row, PRODUCTS)
            for row in held.content["in_house"]]


def _reconciled(conn: Connection, record: Visit,
                house: list[reconciliation.Medication]) -> reconciliation.Reconciliation:
    return reconciliation.reconcile(
        house,
        prefetch.prescribed(conn, record.patient_id, products=PRODUCTS),
        store.visit_day(conn, record.id))


def _cupboard(form, conn: Connection, record: Visit) -> dict[str, object]:
    """Add a box, take one back out, or claim the cupboard is empty and save.

    Three acts and one route, because all three change the same house and the section is
    resolved by the house as it stands after each. `as_content` shapes it, so the store and
    the Write-Back get the same dict and the discrepancies are computed once, in the module
    that owns the comparison.
    """
    house = ACTS[str(form.get("act", DONE))](form, _house(conn, record))
    if not house and not str(form.get("empty", "")):
        raise Refusal(
            "Nothing was recorded",
            "Nothing has been added to the house. Add what is in the cupboard, tick “The "
            "cupboard was empty” if that is the finding, or use “Nothing to record here” "
            "and choose a reason.")
    return reconciliation.as_content(
        _reconciled(conn, record, house),
        datetime.combine(store.visit_day(conn, record.id), time()))


def _added(form, house: list[reconciliation.Medication]
           ) -> list[reconciliation.Medication]:
    """One box, named by the list where the list has it and as written where it does not."""
    product = PRODUCTS.get(str(form.get("product", "")))
    label = str(form.get("label", "")).strip()
    if product is not None and label:
        raise Refusal(
            "Two names for one box",
            "A product from the drug list and words as written on the box arrived "
            "together. Choose one: the list where it holds the item, or the box "
            "where it does not — Noor keeps an item the list does not hold, but "
            "not two names for one box.")
    if product is None and not label:
        raise Refusal(
            "A box with no name on it",
            "Choose a product from the drug list, or record the item as written on the "
            "box. Noor keeps an item the list does not hold; it cannot keep one with no "
            "name at all.")
    return house + [reconciliation.Medication(
        product.generic if product is not None else label,
        product,
        _count(str(form.get("quantity", ""))),
        _expiry(str(form.get("expiry", ""))))]


def _removed(form, house: list[reconciliation.Medication]
             ) -> list[reconciliation.Medication]:
    row = int(str(form.get("row", "")))
    if row >= len(house):
        raise Refusal(
            "That box is no longer in the house",
            "The row this was sent from is out of date — it may already have been taken "
            "out. Open the section again to see the house as it stands.")
    return house[:row] + house[row + 1:]


def _kept(form, house: list[reconciliation.Medication]
          ) -> list[reconciliation.Medication]:
    """Save and return changes nothing about the house; it is the act of finishing."""
    return house


DONE = "done"
ACTS = {"add": _added, "remove": _removed, DONE: _kept}
"""The section's three acts. An act Noor does not have raises KeyError rather than being
treated as one of the three (ADR 0007) — `_after` is the one place that reads a missing
`act` as *done*, because that is a browser without the hidden field and not a wrong act."""


def _count(typed: str) -> int | None:
    """§4.2's only objective adherence signal, and the one number this section takes."""
    if not typed.strip():
        return None
    try:
        return int(typed)
    except ValueError:
        raise Refusal(
            "That is not a count of tablets",
            f"Noor cannot read {typed!r} as a number of tablets. Count them, or leave the "
            f"box empty — an uncounted box is recorded as uncounted.") from None


def _expiry(typed: str) -> date | None:
    if not typed.strip():
        return None
    return date.fromisoformat(typed)


def _care_plan(request: Request, conn: Connection,
               record: Visit) -> dict[str, object]:
    """§4.2: assembled after the other seven, Notes included. The guard runs before the
    form is built, so the page never offers a plan it would then refuse to accept."""
    check_care_plan_ready(record.resolutions)
    return {"withheld": views.TITRATION_WITHHELD,
            "rows": views.plan_rows(record),
            "action": views.plan_action(record)}


def _between_visit(form, conn: Connection, record: Visit) -> dict[str, object]:
    """§4.8: the plan the Visit emits, and the section's own content, from one build.

    Every guard is `plans`' own — an empty plan, a schedule under once a week, a threshold
    with no action. Re-checking any of them here would be a second copy of a rule that
    already has one, and the two would drift.
    """
    check_care_plan_ready(record.resolutions)
    action = str(form.get("action", "")).strip()
    plan = BetweenVisitPlan(
        schedule=tuple(MeasurementSchedule(axis, times)
                       for axis, times in _weekly(form)),
        stop_rules=tuple(Threshold(axis, comparison, value, action)
                         for axis, comparison, value in _stops(form)))
    record.plan = plan
    return {"titration": [],
            "schedule": [{"axis": line.axis.value,
                          "times_per_week": line.times_per_week}
                         for line in plan.schedule],
            "stop_rules": [{"axis": rule.axis.value,
                            "comparison": rule.comparison.value,
                            "value": rule.value, "action": rule.action}
                           for rule in plan.stop_rules]}


def _weekly(form) -> list[tuple[Axis, int]]:
    return [(axis, _times(str(form.get(f"times-{axis.value}", ""))))
            for axis in views.HOME_AXES
            if str(form.get(f"times-{axis.value}", "")).strip()]


DIRECTIONS = (("below", Comparison.BELOW), ("above", Comparison.ABOVE))


def _stops(form) -> list[tuple[Axis, Comparison, float]]:
    return [(axis, comparison, _value(str(form.get(f"{prefix}-{axis.value}", ""))))
            for axis in views.HOME_AXES
            for prefix, comparison in DIRECTIONS
            if str(form.get(f"{prefix}-{axis.value}", "")).strip()]


def _times(typed: str) -> int:
    try:
        return int(typed)
    except ValueError:
        raise Refusal(
            "That is not a number of measurements",
            f"Noor cannot read {typed!r} as how many times a week. Write a whole number, "
            f"or leave the box empty if this is not measured at home.") from None


def _value(typed: str) -> float:
    try:
        return float(typed)
    except ValueError:
        raise Refusal(
            "That is not a threshold",
            f"Noor cannot read {typed!r} as a number. A stop rule is a number the "
            f"household can compare a reading against.") from None


SECTIONS = {
    Section.VISIT_REASON: ("section_free_text.html", _visit_reason, _free_text),
    Section.CONCERNS_AND_INTERVAL_HISTORY: ("section_concerns.html", _concerns,
                                            _interval),
    Section.MEDICATION_RECONCILIATION: ("section_medication.html", _medication,
                                        _cupboard),
    Section.VITALS: ("section_vitals.html", _vitals, _readings),
    Section.PHYSICAL_EXAMINATION: ("section_examination.html", _examination, _findings),
    Section.SELF_CARE_CHECK: ("section_self_care.html", _self_care, _observations),
    Section.CARE_PLAN: ("section_care_plan.html", _care_plan, _between_visit),
    Section.NOTES: ("section_free_text.html", _notes, _free_text),
}
"""web_plan §4.3's eight, as the dispatch itself: the template, the builder that fills
its form, and the parser that reads the form back. Three arms rather than two because a
section's GET and its POST are different shapes over the same address. A ninth key raises
KeyError rather than rendering one of these and being wrong quietly (ADR 0007)."""


def _common(conn: Connection, record: Visit) -> dict[str, object]:
    """What all four templates carry: whose Visit, what state, and the way back to the day
    it was scheduled on — that day and not today, so the one link up (§7) never lands on
    somebody else's roster."""
    return {"visit_id": record.id,
            "patient": store.patient_name(conn, record.patient_id),
            "state": views.STATE_WORDS[record.state],
            "day": store.visit_day(conn, record.id).isoformat()}


def _scheduled(conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2: readiness, the planning indicator, the way to the Brief — and Task 7's two
    acts, whose guard carries §5.10's list and the pair to attribute a Cancel to."""
    team = store.field_team(conn, record.patient_id)
    return {"kind": views.KIND_WORDS[kind_for(store.history(conn, record.patient_id))],
            "readiness": views.readiness_sentence(
                prefetch.readiness(conn, record.patient_id)),
            "reasons": views.CANCELLED_ROWS,
            "team": team}


def _open(conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2: the eight with their marks, the Home Readings, and any Emergency the Visit
    passed through. The last two are counts because their own screens — /home-readings and
    /handover — are Web Pass 2, and a count is honest at nought as well as at three."""
    return {"kind": views.settled_kind(record),
            "attendance": views.attendance(record),
            "sections": views.marks(record),
            "home_readings": views.home_readings_sentence(record.home_readings),
            "emergencies":
                f"Emergencies during this Visit: {len(record.emergencies)}."}


def _closed(conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2: the record read-only, and what the Write-Back is doing (§6.1). One read of the
    queue answers both the count §7.3 asks for and this Visit's own line."""
    queued = {row.visit_id: row for row in store.pending(conn)}
    return {"kind": views.settled_kind(record),
            "attendance": views.attendance(record),
            "sections": views.marks(record),
            "closed": views.closed_sentence(record),
            "reason": views.reason_sentence(record),
            "queue": views.queue_count(queued),
            "writeback": views.writeback_sentence(record, queued.get(record.id))}


def _cancelled(conn: Connection, record: Visit) -> dict[str, object]:
    """§4.2: the reason and who set it. `conn` goes unused — a Cancelled Visit needs no
    read beyond the one that loaded it, and every builder takes the same two arguments so
    the dispatch below stays a lookup."""
    return {"closed": views.closed_sentence(record),
            "reason": views.reason_sentence(record),
            "writeback": views.writeback_sentence(record, None)}


PAGES = {
    VisitState.SCHEDULED: ("visit_scheduled.html", _scheduled),
    VisitState.IN_PROGRESS: ("visit_open.html", _open),
    VisitState.COMPLETED: ("visit_closed.html", _closed),
    VisitState.ENDED_EARLY: ("visit_closed.html", _closed),
    VisitState.CANCELLED: ("visit_cancelled.html", _cancelled),
}
"""§4.2's table, as the dispatch itself. Emergency is deliberately absent: it has no page,
and `_visit` has already redirected before this is read. A seventh state raises KeyError
rather than rendering one of these five and being wrong quietly (ADR 0007)."""


async def start(request: Request) -> Response:
    """§5.5's Start: the kind is settled here and never scheduled (§4.9).

    Three facts are frozen onto the record in one write. The pair, so §5.13's later
    reassignment cannot restate a closed Visit's attendance. And the standing plan, because
    `Visit.previous_plan` may not be left at its default for a Routine Visit — Task 8's
    Brief reads that field, and N6 calls an unset one a silent degrade. Absent comes back
    for a Baseline's first Visit, which is the truth there.
    """
    conn = store.connect(request.app.state.db)
    visit_id = request.path_params["visit_id"]
    record = _visit(conn, visit_id)
    team = store.field_team(conn, record.patient_id)
    record.start(request.app.state.now(),
                 kind_for(store.history(conn, record.patient_id)),
                 junior_physician=team.junior_physician, nurse=team.nurse)
    record.previous_plan = store.standing_plan(conn, record.patient_id)
    store.save(conn, record)
    conn.close()
    return RedirectResponse(f"/visits/{visit_id}", status_code=303)


async def cancel(request: Request) -> Response:
    """§5.4: what became of an attendance nobody made, on §5.10's terms.

    `reason_for` is the parser — it checks the posted row against the list that was
    rendered, so a list that changed under an open page is refused rather than stored. Who
    cancelled is asked, never proved (§10): a Scheduled Visit carries no pair yet, so the
    two names offered are the Patient's standing pair.
    """
    conn = store.connect(request.app.state.db)
    visit_id = request.path_params["visit_id"]
    record = _visit(conn, visit_id)
    form = await request.form()
    reason = reason_for(views.CANCELLED_ROWS,
                        str(form.get("reason", "")), str(form.get("words", "")))
    if not str(form.get("by", "")): raise Refusal("No name on this Cancel", "Noor needs the name of whoever is recording this Cancel. Choose a name and record it again.")
    record.cancel(reason, str(form.get("by", "")), request.app.state.now())
    store.save(conn, record)
    conn.close()
    return RedirectResponse(f"/visits/{visit_id}", status_code=303)


async def illegal(request: Request, exc: IllegalTransition) -> Response:
    """409: the act is real and the state it needed is gone (§5.1).

    The exception's own message names both states, and it stays in the log rather than on
    the page: `a scheduled Visit cannot become in_progress` is true and is not what somebody
    holding a tablet in a doorway needs to read.
    """
    return page(request, "refusal.html", status=409,
                heading="This Visit has moved on",
                sentence="That action needed the Visit to be in a state it has already "
                         "left. The page it was sent from is out of date — open the Visit "
                         "again to see where it is now.")


async def not_on_the_list(request: Request, exc: ResolutionError) -> Response:
    """400: the posted reason was not one of §5.10's rows, or the Other row arrived without
    its words. `reason_for` writes both sentences, and both are for the person reading."""
    return page(request, "refusal.html", status=400,
                heading="That reason cannot be recorded", sentence=str(exc))


async def bad_box(request: Request, exc: reconciliation.ReconError) -> Response:
    """400: `Medication` refused the box (§4.2). Its message names the item and the
    problem, and both are for the person reading."""
    return page(request, "refusal.html", status=400,
                heading="That box cannot be recorded", sentence=str(exc))


async def too_early(request: Request, exc: CarePlanTooEarly) -> Response:
    """409: the act is real and the Visit is not there yet (§4.2). Same number as
    `illegal`, because both are *this cannot happen in the state the Visit is in*.

    `check_care_plan_ready` already names every outstanding section in its message, and
    `SECTION_WORDS` is the Field Team's wording for the same eight — so the sentence is
    rebuilt from the enum names the message carries rather than re-reading the Visit.
    """
    outstanding = views.outstanding_in(str(exc))
    visit_id = request.path_params["visit_id"]
    conn = store.connect(request.app.state.db)
    patient = store.patient_name(conn, store.load(conn, visit_id).patient_id)
    conn.close()
    links = [{"href": f"/visits/{visit_id}/sections/{views.SLUG_OF[s]}",
              "name": views.SECTION_WORDS[s]} for s in outstanding]
    return page(request, "too_early.html", status=409,
                heading="The Care Plan is not ready to assemble",
                sentence=views.too_early_sentence(outstanding),
                visit_id=visit_id, patient=patient, links=links)


async def not_a_plan(request: Request, exc: plans.PlanError) -> Response:
    """400: §4.8's machine-testable bar, refused in the domain's own words — a threshold
    with no action, a schedule under once a week, a plan with no line in it."""
    return page(request, "refusal.html", status=400,
                heading="That is not a line a machine can test", sentence=str(exc))


async def brief(request: Request) -> Response:
    """§5.3's Brief. Computed on open and never stored — a stored Brief is a second,
    ageing copy of the truth. Reading it starts nothing: §5.5's timestamp is the attendance
    record, and there is no write anywhere in here."""
    conn = store.connect(request.app.state.db)
    visit_id = request.path_params["visit_id"]
    record = _visit(conn, visit_id)
    record.previous_plan = _standing(conn, record)
    computed = read_brief(
        record,
        history=store.history(conn, record.patient_id),
        conditions=store.conditions(conn, record.patient_id),
        catalogue=CATALOGUE,
        measures=MEASURES,
        surveillance=prefetch.surveillance(conn, record.patient_id),
        as_of=request.app.state.now().date())
    patient = store.patient_name(conn, record.patient_id)
    conn.close()
    return page(request, "brief.html", visit_id=visit_id, patient=patient,
                findings_only=views.FINDINGS_ONLY,
                last_visit=views.last_visit_sentence(computed.last_visit),
                plan=views.plan_sentence(computed.previous_plan),
                trends=views.trend_summary(computed.trends),
                trend_tiles=views.trend_tiles(computed.trends),
                home_readings=views.NO_HOME_READINGS,
                due=views.due_summary(computed.due),
                due_tiles=views.due_tiles(computed.due),
                spots=views.spot_summary(computed.blind_spots),
                spot_lines=computed.blind_spots)


def _standing(conn: Connection, record: Visit) -> Datum:
    """Which Between-Visit Plan this Brief declares.

    Two arms, and each is a different rule in §5.3's own two consequences. While the Visit is
    Scheduled nothing has been frozen, so it is read now — the Brief is computed on open, and
    must reflect the cache as it stands when it is read. Once the Visit is In Progress it is
    whatever the Start froze, because §5.5 freezes the engine's inputs for the Visit's
    duration and a Brief re-read in the house may not quietly show a newer answer than the
    one the team has been working from.
    """
    if record.state is VisitState.SCHEDULED:
        return store.standing_plan(conn, record.patient_id)
    return record.previous_plan


async def home_readings(request: Request) -> Response:
    """§4.8's between-Visit series, on web_plan §4.4's own page.

    Read on arrival, so the page exists only while the Visit is In Progress — before the
    Start nobody has arrived, and after the close the record is read on the review screen
    (Pass 3). `_open_visit` is Task 1's guard, shared with the eight sections.
    """
    conn = store.connect(request.app.state.db)
    record = _open_visit(conn, request.path_params["visit_id"])
    asked = _asked(conn, record)
    context = {"visit_id": record.id,
               "patient": store.patient_name(conn, record.patient_id),
               "options": views.reading_options(asked),
               "sources": views.SOURCE_ROWS,
               "summary": views.home_readings_sentence(record.home_readings),
               "readings": views.reading_lines(record.home_readings, asked)}
    conn.close()
    return page(request, "home_readings.html", **context)


async def add_reading(request: Request) -> Response:
    """One reading, appended. `home_readings` is a plain list on the Visit with no method
    guarding it, because §4.8 puts no rule on the series beyond what a single reading
    carries — and `HomeReading.__post_init__` is where that one rule lives."""
    conn = store.connect(request.app.state.db)
    visit_id = request.path_params["visit_id"]
    record = _open_visit(conn, visit_id)
    form = await request.form()
    record.home_readings.append(vitals.HomeReading(
        _measurement(form, _asked(conn, record)),
        str(form.get("value", "")).strip(),
        _taken_at(str(form.get("taken_at", ""))),
        _source(str(form.get("source", "")))))
    store.save(conn, record)
    conn.close()
    return RedirectResponse(f"/visits/{visit_id}/home-readings", status_code=303)


def _asked(conn: Connection, record: Visit) -> tuple[vitals.Measurement, ...]:
    """Which measurements this page offers.

    `kind=VisitKind.ROUTINE` on every Visit, whatever the Visit's own kind. The argument
    decides whether the `baseline_only` measurements are included, and those are the ones
    taken once at enrolment — a between-Visit series of a height is not a thing a device
    memory holds. So the honest answer here is the recurring set, on a Baseline Visit too.
    """
    return vitals.asked_for(MEASURES,
                            conditions=store.conditions(conn, record.patient_id),
                            kind=VisitKind.ROUTINE)


def _measurement(form, asked: tuple[vitals.Measurement, ...]) -> str:
    """The posted id, checked against the list that was rendered — the same rule
    `reason_for` applies to §5.10's rows, for the same reason: a page that has gone stale
    is refused rather than stored."""
    posted = str(form.get("measurement", ""))
    if posted not in {measure.id for measure in asked}:
        raise Refusal(
            "That is not a measurement on this page",
            f"{posted!r} is not one of the measurements this Patient's conditions ask "
            f"for. Open the page again to see the ones that are offered.")
    return posted


def _taken_at(typed: str) -> datetime:
    try:
        return datetime.fromisoformat(typed)
    except ValueError:
        raise Refusal(
            "Noor cannot read when it was taken",
            f"A Home Reading carries the time it was taken, and {typed!r} is not one. The "
            f"device's memory shows a date and a time against every reading.") from None


def _source(posted: str) -> vitals.Source:
    try:
        return vitals.Source(posted)
    except ValueError:
        raise Refusal(
            "No source on this reading",
            "Noor needs to know where this reading came from — the device's own memory, "
            "or a Caregiver's paper log. §4.8 requires it of every reading, because the "
            "two are not equally direct.") from None


async def not_a_reading(request: Request, exc: vitals.VitalsError) -> Response:
    """400: `HomeReading` refused it (§4.8). Its message names the measurement and what
    was wrong, and both are for the person reading."""
    return page(request, "refusal.html", status=400,
                heading="That is not a reading", sentence=str(exc))
