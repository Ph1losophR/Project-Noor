"""One database per test, the test's own connection over it, and a client."""
from datetime import datetime

import pytest
from starlette.testclient import TestClient

from noor import store
from noor.web.app import create_app

NOW = datetime(2026, 8, 28, 9, 30)
"""The demo day, at half past nine. `emr.ROSTER` schedules every fixture Visit for
2026-08-28; a test that reads the real clock is a test that fails next month."""


@pytest.fixture
def db(tmp_path):
    """A file, not `:memory:` — a handler opens its own connection per request (§6), and
    two connections to `:memory:` are two different databases."""
    return tmp_path / "noor.db"


@pytest.fixture
def conn(db):
    """The test's own connection, for arranging rows and reading them back. Deliberately
    not the handler's: a row this connection can see is a row that was committed."""
    connection = store.connect(db)
    yield connection
    connection.close()


@pytest.fixture
def client(db):
    """A fixed clock, so `/visits` with no `?day=` means the demo day and not the day the
    suite happens to run on."""
    with TestClient(create_app(db, now=lambda: NOW)) as test_client:
        yield test_client


@pytest.fixture
def day():
    """The day the client thinks it is. A test that arranges a Visit for *today* and then
    asks for it should not write the date down twice."""
    return NOW.date()
