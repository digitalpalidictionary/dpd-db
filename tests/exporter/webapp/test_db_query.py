"""Database Query tab (issue #199). The route tests run against the real dpd.db."""

import re

import pytest
from fastapi.testclient import TestClient

import exporter.webapp.main as webapp_main
from exporter.webapp.db_query import (
    COLUMNS,
    DEFAULT_COLUMNS,
    MAX_LIMIT,
    QueryError,
    QueryFilter,
    check_columns,
    clamp_limit,
    group_filters,
    make_filters,
    to_pattern,
)
from exporter.webapp.main import app
from exporter.webapp.toolkit import LICENSE_LINK_HEADER
from tools.search_deadline import INVALID_MESSAGE, TIMEOUT_MESSAGE, regex_deadline

SLOW_PATTERN = "^(.|.)+[Z!]"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def short_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(webapp_main, "regex_deadline", lambda: regex_deadline(0.5))


def query(
    client: TestClient,
    filters: list[tuple[str, str, str, str]],
    columns: list[str],
    limit: int = MAX_LIMIT,
) -> dict:
    params: dict[str, list[str] | str | int] = {
        "field": [f[0] for f in filters],
        "search": [f[1] for f in filters],
        "value": [f[2] for f in filters],
        "logic": [f[3] for f in filters],
        "columns": ",".join(columns),
        "limit": limit,
    }
    response = client.get("/dq_search", params=params)
    return {
        "status": response.status_code,
        "headers": response.headers,
        **response.json(),
    }


def as_dicts(data: dict) -> list[dict]:
    return [dict(zip(data["columns"], row)) for row in data["rows"]]


# pure logic


def test_search_types_become_regex_patterns() -> None:
    assert to_pattern("contains", "a.b") == r"a\.b"
    assert to_pattern("starts_with", "dhamma") == "^dhamma"
    assert to_pattern("ends_with", "(gram)") == r"\(gram\)$"
    assert to_pattern("regex", "^a.b$") == "^a.b$"


def test_or_starts_a_new_group_and_empty_values_match_everything() -> None:
    a, b, c, d = (QueryFilter("lemma_1", "contains", v, "and") for v in "abcd")
    c_or = QueryFilter("lemma_1", "contains", "c", "or")
    empty = QueryFilter("lemma_1", "contains", "", "and")
    empty_or = QueryFilter("lemma_1", "contains", "", "or")
    assert group_filters([a, b, c_or, d]) == [[a, b], [c_or, d]]
    assert group_filters([a, empty, b]) == [[a, b]]
    assert group_filters([a, empty_or]) == [[a]]
    # the first filter's logic does not matter
    first_or = QueryFilter("lemma_1", "contains", "a", "or")
    assert group_filters([first_or, b]) == [[first_or, b]]
    assert group_filters([]) == []


def test_make_filters_checks_every_part() -> None:
    assert make_filters(["pos"], ["contains"], ["masc"], ["and"]) == [
        QueryFilter("pos", "contains", "masc", "and")
    ]
    with pytest.raises(QueryError, match="Unknown field"):
        make_filters(["password"], ["contains"], ["x"], ["and"])
    with pytest.raises(QueryError, match="Unknown search type"):
        make_filters(["pos"], ["sounds_like"], ["x"], ["and"])
    with pytest.raises(QueryError, match="Unknown logic"):
        make_filters(["pos"], ["contains"], ["x"], ["xor"])
    with pytest.raises(QueryError, match="Each filter needs"):
        make_filters(["pos", "lemma_1"], ["contains"], ["x"], ["and"])


def test_columns_default_and_unknown() -> None:
    assert check_columns([]) == DEFAULT_COLUMNS
    assert check_columns(["lemma_1", "id", "lemma_1"]) == ["lemma_1", "id"]
    with pytest.raises(QueryError, match="Unknown field"):
        check_columns(["id", "__class__"])
    assert set(DEFAULT_COLUMNS) <= set(COLUMNS)


def test_limit_stays_between_one_and_the_maximum() -> None:
    assert clamp_limit(500) == MAX_LIMIT
    assert clamp_limit(0) == 1
    assert clamp_limit(25) == 25


# the route


def test_starts_with_returns_the_chosen_columns(client: TestClient) -> None:
    data = query(
        client, [("lemma_1", "starts_with", "dhamma", "and")], ["id", "lemma_1", "pos"]
    )
    assert data["status"] == 200
    assert data["columns"] == ["id", "lemma_1", "pos"]
    rows = as_dicts(data)
    assert rows
    assert all(row["lemma_1"].startswith("dhamma") for row in rows)
    assert all(isinstance(row["id"], int) for row in rows)
    assert [row["id"] for row in rows] == sorted(row["id"] for row in rows)


def test_contains_ends_with_and_regex(client: TestClient) -> None:
    contains = as_dicts(
        query(client, [("meaning_1", "contains", "elephant", "and")], ["meaning_1"])
    )
    assert contains and all("elephant" in row["meaning_1"] for row in contains)

    ends = as_dicts(
        query(client, [("lemma_1", "ends_with", "ttana", "and")], ["lemma_1"])
    )
    assert ends and all(row["lemma_1"].endswith("ttana") for row in ends)

    regex = as_dicts(
        query(client, [("lemma_1", "regex", r"^k[aā]ma \d", "and")], ["lemma_1"])
    )
    assert regex and all(re.match(r"^k[aā]ma \d", row["lemma_1"]) for row in regex)


def test_pattern_characters_are_literal_outside_regex(client: TestClient) -> None:
    data = query(client, [("lemma_1", "contains", "(", "and")], ["lemma_1"])
    assert data["status"] == 200
    assert "error" not in data


def test_and_and_or_groups(client: TestClient) -> None:
    both = as_dicts(
        query(
            client,
            [
                ("lemma_1", "starts_with", "dhamma", "and"),
                ("pos", "regex", "^masc$", "and"),
            ],
            ["lemma_1", "pos"],
        )
    )
    assert both
    assert all(r["lemma_1"].startswith("dhamma") and r["pos"] == "masc" for r in both)

    either = as_dicts(
        query(
            client,
            [
                ("lemma_1", "regex", "^dhammacakka", "and"),
                ("pos", "regex", "^nt$", "and"),
                ("lemma_1", "regex", "^buddhānussati", "or"),
            ],
            ["lemma_1", "pos"],
        )
    )
    first = [r for r in either if r["lemma_1"].startswith("dhammacakka")]
    second = [r for r in either if r["lemma_1"].startswith("buddhānussati")]
    assert first and second
    assert len(first) + len(second) == len(either)
    assert all(r["pos"] == "nt" for r in first)


def test_numbers_are_matched_as_text(client: TestClient) -> None:
    rows = as_dicts(query(client, [("id", "regex", "^1$", "and")], ["id", "lemma_1"]))
    assert [row["id"] for row in rows] == [1]


def test_limit_and_more(client: TestClient) -> None:
    data = query(client, [("lemma_1", "contains", "a", "and")], ["id"], limit=5)
    assert len(data["rows"]) == 5
    assert data["more"] is True

    capped = query(client, [], ["id"], limit=1000)
    assert len(capped["rows"]) == MAX_LIMIT
    assert capped["more"] is True

    one = query(client, [("id", "regex", "^1$", "and")], ["id"])
    assert one["more"] is False


def test_results_carry_the_licence(client: TestClient) -> None:
    data = query(client, [("id", "regex", "^1$", "and")], ["id"])
    assert data["headers"]["link"] == LICENSE_LINK_HEADER["Link"]
    assert data["license"]


def test_bad_requests_say_what_is_wrong(client: TestClient) -> None:
    data = query(client, [("password", "contains", "x", "and")], ["id"])
    assert data["status"] == 400
    assert data["error"] == "Unknown field: password"

    data = query(client, [("lemma_1", "contains", "x", "and")], ["id", "rt"])
    assert data["status"] == 400
    assert data["error"] == "Unknown field: rt"


def test_invalid_regex_is_reported(client: TestClient) -> None:
    data = query(client, [("lemma_1", "regex", "(", "and")], ["id"])
    assert data["status"] == 200
    assert data["rows"] == []
    assert data["error"] == INVALID_MESSAGE


def test_slow_regex_stops_at_the_budget(client: TestClient, short_budget: None) -> None:
    data = query(client, [("meaning_1", "regex", SLOW_PATTERN, "and")], ["id"])
    assert data["status"] == 200
    assert data["rows"] == []
    assert data["error"] == TIMEOUT_MESSAGE
