"""Resource limits on webapp searches (issue #268)."""

from collections import defaultdict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from db.models import Lookup
from exporter.webapp.main import app
from exporter.webapp.toolkit import find_closest_matches, make_dpd_html
from tools.paths import ProjectPaths

# Aborts the load on the first row that is not an exact key, so a failing run
# cannot fill memory.


class WildcardMatch(Exception):
    pass


@pytest.mark.parametrize("q", ["%", "_", "d%", "%%", "dhamm_", "\\", "a\\", "%."])
def test_wildcard_characters_only_match_themselves(q: str) -> None:
    exact_keys = {q.lower(), q.lower() + "."}
    loaded = 0

    def check_load(target: Lookup, context: object) -> None:
        nonlocal loaded
        loaded += 1
        if target.lookup_key.lower() not in exact_keys:
            raise WildcardMatch(f"query {q!r} loaded key {target.lookup_key!r}")

    event.listen(Lookup, "load", check_load)
    try:
        dpd_html, _ = make_dpd_html(
            q, ProjectPaths(), None, {}, set(), defaultdict(list)
        )
    finally:
        event.remove(Lookup, "load", check_load)

    assert loaded == 0
    assert "No results found" in dpd_html


def test_failed_lookups_do_not_grow_the_ascii_map() -> None:
    ascii_map: defaultdict[str, list[str]] = defaultdict(list)
    ascii_map["kamma"] = ["kamma"]

    for i in range(1000):
        find_closest_matches(f"zzzmiss{i}", {"dhamma"}, ascii_map)

    assert list(ascii_map) == ["kamma"]


@pytest.fixture
def lenient_client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("digits", [19, 25, 4000, 5000])
def test_very_long_number_query_is_no_match_not_a_server_error(
    lenient_client: TestClient, digits: int
) -> None:
    response = lenient_client.get("/search_json", params={"q": "1" * digits})
    assert response.status_code == 200
    assert "No results found" in response.json()["dpd_html"]


def test_very_long_page_address_is_not_found(lenient_client: TestClient) -> None:
    assert lenient_client.get("/" + "1" * 5000).status_code == 404


def test_normal_page_address_still_redirects(lenient_client: TestClient) -> None:
    response = lenient_client.get("/24043", follow_redirects=False)
    assert response.status_code == 308
    assert response.headers["location"] == "/?q=24043"


def test_audio_range_with_a_huge_number_is_not_a_server_error(
    lenient_client: TestClient,
) -> None:
    plain = lenient_client.get("/audio/buddha")
    if plain.status_code != 200:
        pytest.skip("no audio for this headword in this database")
    huge = lenient_client.get(
        "/audio/buddha", headers={"Range": "bytes=" + "9" * 5000 + "-"}
    )
    assert huge.status_code == 200
    ranged = lenient_client.get("/audio/buddha", headers={"Range": "bytes=0-9"})
    assert ranged.status_code == 206
    assert len(ranged.content) == 10
