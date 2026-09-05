"""The CC BY-NC-SA licence notice must ride along with DPD dictionary data, and
must NOT appear on Tipiṭaka translations or audio, which are licensed separately.
"""

import pytest
from fastapi.testclient import TestClient

from exporter.webapp.main import app

client = TestClient(app)

DPD_ROUTES = [
    "/search_json?q=dhamma",
    "/search_html?q=dhamma",
    "/gd?search=dhamma",
]


def test_link_header_on_dpd_routes() -> None:
    for route in DPD_ROUTES:
        response = client.get(route)
        assert response.status_code == 200, route
        link = response.headers.get("link")
        assert link is not None, route
        assert 'rel="license"' in link, route
        assert "creativecommons.org/licenses/by-nc-sa/4.0/" in link, route
        assert "CC BY-NC-SA 4.0" in link, route


def test_search_json_keeps_its_pre_existing_header() -> None:
    """The licence header is merged into the route's own headers, not substituted
    for them. Note that `Accept-Encoding` is a request header and is inert in a
    response — this guards the pre-existing quirk, it does not endorse it.
    """
    response = client.get("/search_json?q=dhamma")
    assert response.headers.get("accept-encoding") == "gzip"


def test_license_header_is_readable_cross_origin() -> None:
    """`Link` is not CORS-safelisted, so browser clients on another origin can only
    read it if it is explicitly exposed.
    """
    response = client.get(
        "/search_json?q=dhamma", headers={"Origin": "https://example.com"}
    )
    exposed = response.headers.get("access-control-expose-headers", "")
    assert "Link" in exposed


def test_license_is_last_key_of_json_body() -> None:
    response = client.get("/search_json?q=dhamma")
    data = response.json()
    assert list(data)[-1] == "license"
    assert set(data["license"]) == {"name", "url", "attribution", "note"}
    assert data["license"]["name"] == "CC BY-NC-SA 4.0"
    assert data["license"]["url"] == (
        "https://creativecommons.org/licenses/by-nc-sa/4.0/"
    )


def test_visible_license_line_under_the_entries() -> None:
    """The header is machine-readable only. The visible notice lives at the end of
    the rendered entries, not in a page footer, so that it travels with the data
    into GoldenDict, the JSON body and any third-party embed of the fragment.
    """
    for route in ["/search_html?q=dhamma", "/gd?search=dhamma"]:
        text = client.get(route).text
        assert text.count('<div class="license-line">') == 1, route
        assert "Digital Pāḷi Dictionary by Bodhirasa Bhikkhu" in text, route
        assert "CC BY-NC-SA 4.0" in text, route
        assert "creativecommons.org/licenses/by-nc-sa/4.0/" in text, route


def test_license_line_carries_the_four_cc_marks_inline() -> None:
    """Inlined, not linked, so the marks survive offline in GoldenDict — and
    `currentColor` so they read in both light and dark mode.
    """
    text = client.get("/gd?search=dhamma").text
    start = text.index('<div class="license-line">')
    block = text[start : text.index("</div>", text.index("</a>", start)) + 6]
    assert block.count("<svg") == 4
    assert 'fill="currentColor"' in block
    assert "<img" not in block


def test_license_line_rides_inside_the_json_results_html() -> None:
    dpd_html = client.get("/search_json?q=dhamma").json()["dpd_html"]
    assert "license-line" in dpd_html
    # Last thing in the results, i.e. under the final entry.
    assert dpd_html.rstrip().endswith("</div>")
    assert dpd_html.rindex("license-line") > dpd_html.rindex("</h3>")


def test_no_license_line_without_results() -> None:
    """A "no results" page carries no dictionary data, so it carries no licence."""
    for query in ["zzzqqqxxx", "dhamm"]:
        dpd_html = client.get(f"/search_json?q={query}").json()["dpd_html"]
        assert "No results found" in dpd_html, query
        assert "license-line" not in dpd_html, query


def test_empty_page_has_no_license_line() -> None:
    """The home page renders no entries, so nothing to licence."""
    assert '<div class="license-line">' not in client.get("/").text


def test_no_license_header_on_non_dpd_data() -> None:
    non_dpd_routes = [
        "/tt_search?q=dhamma&book=all&lang=Pāḷi",
        "/bd_search?q1=dhamma&q2=&option=exact",
        "/",
        "/bd",
    ]
    for route in non_dpd_routes:
        response = client.get(route)
        assert response.status_code == 200, route
        assert "link" not in response.headers, route

    audio = client.get("/audio/dhamma")
    # A 404 would make the header check below pass for the wrong reason. The audio
    # db is gitignored, so skip rather than fail when it is simply not present.
    if audio.status_code == 404:
        pytest.skip("audio db not available in this environment")
    assert audio.status_code == 200
    assert "link" not in audio.headers
