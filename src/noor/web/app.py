"""The one application (ADR 0006): one process, server-rendered, no build step.

A factory as well as a module-level instance, so a test can point Noor at its own
database file. Wiring only — the routes table, the static mount, the exception handlers,
and where the database is. Every decision is in `pages.py` or `views.py`.
"""
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from noor import store
from noor.domain import plans, reconciliation, vitals
from noor.domain.records import CarePlanTooEarly, ResolutionError
from noor.domain.states import IllegalTransition
from noor.web import pages

STATIC = Path(__file__).with_name("static")
DEFAULT_DB = Path(__file__).resolve().parents[3] / "noor.db"
"""Beside `run.py` at the repository root, because it is the operator's file rather than
the package's: `seed.py` writes it and `.gitignore`'s `*.db` keeps it out of the repo."""


def create_app(db: Path | str,
               now: Callable[[], datetime] = datetime.now) -> Starlette:
    """Wiring only: web_plan §2's address table, and nothing that decides anything.

    `now` is a callable rather than a datetime so the default can be the real clock: a
    datetime default would freeze the application at import time, which is a bug that only
    shows up the day after it is deployed.
    """
    application = Starlette(
        routes=[
            Route("/", pages.doors),
            Route("/theme", pages.toggle, methods=["POST"]),
            Route("/visits", pages.visits),
            Route("/visits/{visit_id}", pages.visit),
            Route("/visits/{visit_id}/start", pages.start, methods=["POST"]),
            Route("/visits/{visit_id}/cancel", pages.cancel, methods=["POST"]),
            Route("/visits/{visit_id}/brief", pages.brief),
            Route("/visits/{visit_id}/sections/{slug}", pages.section),
            Route("/visits/{visit_id}/sections/{slug}", pages.resolve,
                  methods=["POST"]),
            Route("/visits/{visit_id}/home-readings", pages.home_readings),
            Route("/visits/{visit_id}/home-readings", pages.add_reading,
                  methods=["POST"]),
            Mount("/static", StaticFiles(directory=STATIC), name="static"),
        ],
        exception_handlers={404: pages.not_found,
                            pages.Refusal: pages.refused,
                            pages.Suspended: pages.suspended,
                            store.UnknownVisit: pages.unknown_visit,
                            IllegalTransition: pages.illegal,
                             ResolutionError: pages.not_on_the_list,
                             reconciliation.ReconError: pages.bad_box,
                             CarePlanTooEarly: pages.too_early,
                             plans.PlanError: pages.not_a_plan,
                             vitals.VitalsError: pages.not_a_reading},
    )
    application.state.db = db
    application.state.now = now
    return application


# `run.py` names this. Building it opens no connection, so importing this module is safe
# before `seed.py` has been run and the database file exists.
app = create_app(DEFAULT_DB)
