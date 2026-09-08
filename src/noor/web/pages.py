"""Every Field Team handler, and the two things every render needs: the template
environment, and the mode the page is stamped with.

Separate from `app.py` so the wiring can import the handlers without a cycle, and so
`app.py` stays a table a reader can check against web_plan §2.
"""
from datetime import date, timedelta
from pathlib import Path
from sqlite3 import Connection
from urllib.parse import urlsplit

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.templating import Jinja2Templates

from noor import content, prefetch, store
from noor.domain import examination, vitals
from noor.domain.brief import brief as read_brief
from noor.domain.records import ResolutionError, reason_for
from noor.domain.states import Datum, IllegalTransition, VisitState
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
            "home_readings":
                f"Home Readings collected on arrival: {len(record.home_readings)}.",
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
