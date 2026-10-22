"""Bold-definition search limits (issue #268). Runs against the real dpd.db."""

import threading
import time
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

import exporter.webapp.main as webapp_main
import tools.bold_definitions_search as bold_search
from db.models import BoldDefinition
from exporter.webapp.main import app
from tools.search_deadline import TIMEOUT_MESSAGE, regex_deadline

# `regex` gives up on this one against the real row for the bold word " nibbuto"
SLOW_PATTERN = "^(.|.)+[Z!]"
ONE_ROW_BOLD = "^ nibbuto$"


class TooManyRows(Exception):
    pass


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def short_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(webapp_main, "regex_deadline", lambda: regex_deadline(0.5))


@pytest.fixture
def row_ceiling() -> Generator[None]:
    """Abort the load past 101 rows, so a failing run cannot fill memory."""
    loaded = 0

    def count(target: BoldDefinition, context: object) -> None:
        nonlocal loaded
        loaded += 1
        if loaded > 101:
            raise TooManyRows("loaded more than 101 BoldDefinition rows")

    event.listen(BoldDefinition, "load", count)
    yield
    event.remove(BoldDefinition, "load", count)


def test_broad_search_loads_one_page_and_says_so(
    client: TestClient, row_ceiling: None
) -> None:
    response = client.get("/bd_search", params={"q1": "", "q2": "a", "option": "plain"})
    assert response.status_code == 200
    assert "<b>100+</b> results found" in response.text
    assert "Only displaying the first <b>100</b> results" in response.text


def test_plain_search_with_pattern_characters_does_not_error(
    client: TestClient,
) -> None:
    response = client.get(
        "/bd_search", params={"q1": "dhamma", "q2": "(", "option": "plain"}
    )
    assert response.status_code == 200


def test_ordinary_regex_search_still_works(client: TestClient) -> None:
    response = client.get(
        "/bd_search", params={"q1": ONE_ROW_BOLD, "q2": "Z", "option": "regex"}
    )
    assert response.status_code == 200
    assert "results found" in response.text
    assert TIMEOUT_MESSAGE not in response.text


def test_real_database_error_is_not_reported_as_a_timeout(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_search(*args: object, **kwargs: object) -> None:
        raise OperationalError("select 1", {}, Exception("disk I/O error"))

    monkeypatch.setattr(
        bold_search.BoldDefinitionsSearchManager, "search", broken_search
    )
    with pytest.raises(OperationalError):
        client.get("/bd_search", params={"q1": "dhamma", "q2": "", "option": "plain"})


def test_slow_regex_ends_with_a_message(client: TestClient, short_budget: None) -> None:
    start = time.monotonic()
    response = client.get(
        "/bd_search",
        params={"q1": ONE_ROW_BOLD, "q2": SLOW_PATTERN, "option": "regex"},
    )
    assert response.status_code == 200
    assert TIMEOUT_MESSAGE in response.text
    assert time.monotonic() - start < 3


def test_slow_regex_does_not_block_other_requests(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(webapp_main, "regex_deadline", lambda: regex_deadline(1.5))
    slow = threading.Thread(
        target=client.get,
        args=("/bd_search",),
        kwargs={
            "params": {
                "q1": ONE_ROW_BOLD,
                "q2": SLOW_PATTERN,
                "option": "regex",
            }
        },
    )
    slow.start()
    time.sleep(0.1)
    start = time.monotonic()
    response = client.get("/status")
    elapsed = time.monotonic() - start
    # the slow search must still be running, or this test proves nothing
    still_running = slow.is_alive()
    slow.join()
    assert still_running
    assert response.status_code == 200
    assert elapsed < 0.8


@pytest.mark.parametrize(
    ("pattern", "message"),
    [
        ("(", "That search pattern is not valid."),
        (
            "(?:a{1500}){1500}",
            "That search pattern is too complex. Use a simpler pattern.",
        ),
    ],
)
def test_bad_pattern_ends_with_a_message_not_a_server_error(
    client: TestClient, pattern: str, message: str
) -> None:
    response = client.get(
        "/bd_search",
        params={"q1": ONE_ROW_BOLD, "q2": pattern, "option": "regex"},
    )
    assert response.status_code == 200
    assert message in response.text
