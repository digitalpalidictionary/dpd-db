"""Tests for the citation permalink route, eg /24043."""

from fastapi.testclient import TestClient

from exporter.webapp.main import app

client = TestClient(app)


def test_a_bare_number_redirects_to_the_entry() -> None:
    response = client.get("/24043", follow_redirects=False)

    assert response.status_code == 308
    assert response.headers["location"] == "/?q=24043"


def test_a_word_is_not_a_permalink() -> None:
    response = client.get("/gacchati", follow_redirects=False)

    assert response.status_code == 404


def test_named_routes_still_win() -> None:
    """Digits only, so no named route can fall into the permalink route."""

    assert client.get("/status").status_code == 200
    assert client.get("/metrics").status_code == 200


def test_a_bare_number_resolves_to_a_headword_not_an_abbreviation() -> None:
    """3 is both a headword id and the abbreviation "declined in all three
    genders" — the permalink has to reach the headword."""

    response = client.get("/search_json?q=3")

    assert response.status_code == 200
    assert "declined in all three gender" not in response.json()["dpd_html"]


def test_the_goldendict_route_resolves_a_number_the_same_way() -> None:
    """The behaviour change reaches /gd too, so pin it there as well."""

    response = client.get("/gd?search=3")

    assert response.status_code == 200
    assert "declined in all three gender" not in response.text


def test_a_number_python_cannot_convert_is_not_a_permalink() -> None:
    """isnumeric() is true for "½" but int() rejects it."""

    assert client.get("/search_json?q=%C2%BD").status_code == 200
