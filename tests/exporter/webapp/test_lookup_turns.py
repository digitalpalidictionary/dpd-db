"""Dictionary lookups take turns (issue #268).

Measured on the live app: 8 lookups took 6.7 s one at a time but 16.7 s all at
once, and 40 at once held the server for 115 s, because the page rendering
threads fight over Python's global lock.
"""

import threading
import time
from collections.abc import Generator
from typing import Any

import pytest
from anyio import CapacityLimiter
from fastapi.testclient import TestClient

import exporter.webapp.main as webapp_main
from exporter.webapp.main import app
from exporter.webapp.toolkit import LICENSE_LINK_HEADER

BUSY = "The server is busy. Try again in a moment."
LOOKUPS = [
    ("/search_json", {"q": "kamma"}),
    ("/search_html", {"q": "kamma"}),
    ("/gd", {"search": "kamma"}),
]


class Gate:
    """Makes the lookup block until released, so a test controls who is inside."""

    def __init__(self) -> None:
        self.inside = threading.Semaphore(0)
        self.release = threading.Event()
        self.fail_first = False
        self.calls = 0

    def __call__(self, *args: Any, **kwargs: Any) -> tuple[str, str]:
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise RuntimeError("render failed")
        self.inside.release()
        self.release.wait(10)
        return "<p>ok</p>", ""


@pytest.fixture
def client() -> Generator[TestClient]:
    """One client, used as a context manager, so every request runs on the same
    event loop as in the real server. Separate clients each get their own loop,
    and a waiting request is not woken from another loop."""
    with TestClient(app, raise_server_exceptions=False) as shared:
        yield shared


@pytest.fixture
def gate(monkeypatch: pytest.MonkeyPatch) -> Generator[Gate]:
    gate = Gate()
    monkeypatch.setattr(webapp_main, "make_dpd_html", gate)
    monkeypatch.setattr(webapp_main, "lookup_limiter", CapacityLimiter(1))
    monkeypatch.setattr(webapp_main, "LOOKUP_MAX_WAITING", 0)
    monkeypatch.setattr(webapp_main, "LOOKUP_WAIT_SECONDS", 5.0)
    yield gate
    gate.release.set()


def start_lookup(
    client: TestClient, results: list[int], path: str = "/search_json"
) -> threading.Thread:
    def run() -> None:
        results.append(client.get(path, params={"q": "kamma"}).status_code)

    thread = threading.Thread(target=run)
    thread.start()
    return thread


@pytest.mark.parametrize(("path", "params"), LOOKUPS)
def test_a_full_queue_is_told_the_server_is_busy_at_once(
    client: TestClient, gate: Gate, path: str, params: dict[str, str]
) -> None:
    first: list[int] = []
    thread = start_lookup(client, first)
    assert gate.inside.acquire(timeout=5)
    started = time.monotonic()
    response = client.get(path, params=params)
    assert response.status_code == 503
    assert BUSY in response.text
    assert response.headers["retry-after"]
    assert time.monotonic() - started < 1
    gate.release.set()
    thread.join()
    assert first == [200]


def test_busy_answer_keeps_the_json_shape_the_page_reads(
    client: TestClient, gate: Gate
) -> None:
    thread = start_lookup(client, [])
    assert gate.inside.acquire(timeout=5)
    data = client.get("/search_json", params={"q": "kamma"}).json()
    assert BUSY in data["dpd_html"]
    assert data["summary_html"] == ""
    gate.release.set()
    thread.join()


def test_a_waiting_lookup_gets_its_turn(
    client: TestClient, gate: Gate, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(webapp_main, "LOOKUP_MAX_WAITING", 5)
    first: list[int] = []
    second: list[int] = []
    thread_one = start_lookup(client, first)
    assert gate.inside.acquire(timeout=5)
    thread_two = start_lookup(client, second)
    time.sleep(0.4)
    assert second == []  # waiting, not rejected
    gate.release.set()
    thread_one.join()
    thread_two.join()
    assert first == [200]
    assert second == [200]


def test_a_lookup_that_waits_too_long_is_told_the_server_is_busy(
    client: TestClient, gate: Gate, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(webapp_main, "LOOKUP_MAX_WAITING", 5)
    monkeypatch.setattr(webapp_main, "LOOKUP_WAIT_SECONDS", 0.3)
    thread = start_lookup(client, [])
    assert gate.inside.acquire(timeout=5)
    started = time.monotonic()
    response = client.get("/search_json", params={"q": "kamma"})
    assert response.status_code == 503
    assert 0.2 < time.monotonic() - started < 2
    gate.release.set()
    thread.join()


def test_other_routes_are_not_held_up_by_lookups(
    client: TestClient, gate: Gate
) -> None:
    thread = start_lookup(client, [])
    assert gate.inside.acquire(timeout=5)
    started = time.monotonic()
    assert client.get("/status").status_code == 200
    assert (
        client.get(
            "/tt_search", params={"q": "", "book": "dn1", "lang": "Pāḷi"}
        ).status_code
        == 200
    )
    assert time.monotonic() - started < 2
    gate.release.set()
    thread.join()


def test_a_failed_lookup_gives_its_turn_back(client: TestClient, gate: Gate) -> None:
    gate.fail_first = True
    lenient = client
    assert lenient.get("/search_json", params={"q": "kamma"}).status_code == 500
    gate.release.set()
    assert lenient.get("/search_json", params={"q": "kamma"}).status_code == 200


def test_busy_answer_carries_the_cross_origin_and_licence_headers(
    client: TestClient, gate: Gate
) -> None:
    """The busy answer is sent before the CORS middleware runs, so without these
    a page on another site gets a CORS error and cannot read the message."""
    thread = start_lookup(client, [])
    assert gate.inside.acquire(timeout=5)
    response = client.get(
        "/search_json", params={"q": "kamma"}, headers={"Origin": "https://example.org"}
    )
    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == "*"
    assert response.headers["access-control-expose-headers"] == "Link"
    assert response.headers["link"] == LICENSE_LINK_HEADER["Link"]
    gate.release.set()
    thread.join()


def test_a_browser_preflight_is_not_held_by_the_queue(
    client: TestClient, gate: Gate, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(webapp_main, "LOOKUP_MAX_WAITING", 5)
    thread = start_lookup(client, [])
    assert gate.inside.acquire(timeout=5)
    started = time.monotonic()
    response = client.options(
        "/search_json",
        headers={
            "Origin": "https://example.org",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert time.monotonic() - started < 1
    gate.release.set()
    thread.join()
