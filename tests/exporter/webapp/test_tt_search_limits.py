"""Translation search limits (issue #268)."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

import exporter.webapp.main as webapp_main
from exporter.webapp.main import app
from tools.search_deadline import TIMEOUT_MESSAGE, regex_deadline

# `regex` gives up on this against long real text
SLOW_PATTERN = "^(.|.)+[Z!]"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    recorded: list[dict[str, Any]] = []

    def fake_search_books(books: list[str], q: str, **kwargs: Any) -> list[Any]:
        recorded.append({"books": books, "q": q, **kwargs})
        return []

    def fake_search_all(q: str, **kwargs: Any) -> list[Any]:
        recorded.append({"books": ["all"], "q": q, **kwargs})
        return []

    monkeypatch.setattr(webapp_main, "search_books", fake_search_books)
    monkeypatch.setattr(webapp_main, "search_all_cst_texts", fake_search_all)
    return recorded


@pytest.mark.parametrize("q", ["", "   "])
def test_empty_query_is_rejected_by_the_server(
    client: TestClient, calls: list[dict[str, Any]], q: str
) -> None:
    response = client.get("/tt_search", params={"q": q, "book": "dn1", "lang": "Pāḷi"})
    assert response.status_code == 200
    assert response.json() == {"total": 0, "results": []}
    assert calls == []


def test_repeated_books_are_searched_once(
    client: TestClient, calls: list[dict[str, Any]]
) -> None:
    client.get(
        "/tt_search", params={"q": "dhamma", "book": "dn1,mn1,dn1", "lang": "Pāḷi"}
    )
    assert calls[0]["books"] == ["dn1", "mn1"]


@pytest.mark.parametrize("book", ["dn1", "all"])
def test_search_asks_for_one_row_past_the_display_limit(
    client: TestClient, calls: list[dict[str, Any]], book: str
) -> None:
    client.get("/tt_search", params={"q": "dhamma", "book": book, "lang": "Pāḷi"})
    assert calls[0]["limit"] == 101


def test_more_than_a_page_reports_one_over_and_returns_a_page(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows = [(f"pali {i}", "eng", "t1", "dn1") for i in range(101)]
    monkeypatch.setattr(webapp_main, "search_books", lambda *a, **k: rows)
    data = client.get(
        "/tt_search", params={"q": "dhamma", "book": "dn1", "lang": "Pāḷi"}
    ).json()
    assert data["total"] == 101
    assert len(data["results"]) == 100


def test_slow_regex_returns_an_error_not_an_empty_result(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(webapp_main, "regex_deadline", lambda: regex_deadline(0.5))
    data = client.get(
        "/tt_search", params={"q": SLOW_PATTERN, "book": "all", "lang": "Pāḷi"}
    ).json()
    assert data["error"] == TIMEOUT_MESSAGE
    assert data["results"] == []


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
def test_bad_pattern_returns_an_error_not_an_empty_result(
    client: TestClient, pattern: str, message: str
) -> None:
    data = client.get(
        "/tt_search", params={"q": pattern, "book": "dn1", "lang": "Pāḷi"}
    ).json()
    assert data["error"] == message
    assert data["results"] == []
