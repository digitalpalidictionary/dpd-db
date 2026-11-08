"""Hidden panels are sent empty, with their contents separately."""

import re

from fastapi.testclient import TestClient

from exporter.webapp.lazy_panels import split_hidden_panels
from exporter.webapp.main import app


def refill(shell: str, panels: dict[str, str]) -> str:
    """Put each panel's contents back, as the browser does when it's opened."""
    for panel_id, contents in panels.items():
        opening = re.search(rf'<div\b[^>]*\bid="{panel_id}"[^>]*>', shell)
        assert opening, panel_id
        assert shell[opening.end() :].startswith("</div>")
        shell = shell[: opening.end()] + contents + shell[opening.end() :]
    return shell


HEADWORD = (
    '<h3 class="dpd" id="dhamma_1">dhamma 1</h3>'
    '<div class="dpd"><a class="dpd-button" data-target="grammar_dhamma_1">grammar</a>'
    '<div id="grammar_dhamma_1" class="dpd content hidden" name="grammar-div">'
    "<table><tr><td>masc</td></tr></table>"
    '<div class="nested"><div id="inner" class="hidden">x</div></div>'
    "</div>"
    '<div id="family_compound_dhamma_1" class="dpd content hidden"><p>c</p></div>'
    '<div id="visible_dhamma_1" class="dpd content"><p>shown</p></div>'
    "</div>"
)


def test_panels_are_emptied_and_come_back_unchanged() -> None:
    shell, panels = split_hidden_panels(HEADWORD)
    assert list(panels) == ["grammar_dhamma_1", "family_compound_dhamma_1"]
    assert "masc" not in shell
    assert "<p>shown</p>" in shell
    assert refill(shell, panels) == HEADWORD


def test_a_hidden_panel_inside_another_stays_with_its_parent() -> None:
    _, panels = split_hidden_panels(HEADWORD)
    assert "inner" not in panels
    assert 'id="inner"' in panels["grammar_dhamma_1"]


def test_html_without_hidden_panels_is_unchanged() -> None:
    html = '<div class="dpd"><p>No results found.</p></div>'
    assert split_hidden_panels(html) == (html, {})


def test_stray_tags_outside_panels_still_split() -> None:
    html = '<div><div id="a" class="hidden"><p>x</p></div></div></div><div>open'
    shell, panels = split_hidden_panels(html)
    assert panels == {"a": "<p>x</p>"}
    assert refill(shell, panels) == html


def test_an_unclosed_panel_sends_everything() -> None:
    html = '<div id="a" class="hidden"><div>never closed</div>'
    assert split_hidden_panels(html) == (html, {})


def test_a_repeated_id_sends_everything() -> None:
    html = '<div id="a" class="hidden">1</div><div id="a" class="hidden">2</div>'
    assert split_hidden_panels(html) == (html, {})


def test_lazy_search_returns_the_same_results_once_refilled() -> None:
    client = TestClient(app)
    eager = client.get("/search_json", params={"q": "dhamma"}).json()
    lazy = client.get("/search_json", params={"q": "dhamma", "lazy": "1"}).json()
    assert "panels" not in eager
    assert len(lazy["panels"]) > 100
    assert len(lazy["dpd_html"]) < len(eager["dpd_html"]) / 10
    assert refill(lazy["dpd_html"], lazy["panels"]) == eager["dpd_html"]
    assert {k: v for k, v in lazy.items() if k not in ("dpd_html", "panels")} == {
        k: v for k, v in eager.items() if k != "dpd_html"
    }
