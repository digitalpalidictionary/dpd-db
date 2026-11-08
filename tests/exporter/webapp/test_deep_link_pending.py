"""Phone panes wait for a deep link's results instead of being pushed off screen."""

import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape

STATIC = Path("exporter/webapp/static")


def rendered_home(query: dict[str, str], results: str) -> str:
    env = Environment(
        loader=FileSystemLoader("exporter/webapp/templates"),
        autoescape=select_autoescape(),
    )
    return env.get_template("home.html").render(
        request=SimpleNamespace(query_params=query),
        dpd_results=results,
        bd_count=0,
        book_options=[],
        dpd_release_version="test",
    )


def rendered_html_tag(query: dict[str, str], results: str) -> str:
    tag = re.search(r"<html[^>]*>", rendered_home(query, results))
    assert tag is not None
    return tag.group(0)


@pytest.mark.parametrize(
    ("query", "results", "pending"),
    [
        ({}, "", False),
        ({"q": ""}, "", False),
        ({"q": "  "}, "", False),
        ({"q": "dhamma"}, "", True),
        ({"q": "12345"}, "", True),
        ({"tab": "dpd", "q": "dhamma"}, "", True),
        ({"tab": "tt", "q": "dhamma"}, "", False),
        ({"tab": "bd", "q1": "dhamma"}, "", False),
        ({"q1": "dhamma"}, "", False),
        ({"q": "dhamma"}, "<p>Result</p>", False),
    ],
)
def test_panes_only_wait_when_a_dpd_search_will_run(
    query: dict[str, str], results: str, pending: bool
) -> None:
    assert ('class="search-pending"' in rendered_html_tag(query, results)) is pending


def test_panes_return_if_app_js_fails_to_load() -> None:
    tag = re.search(
        r'<script src="static/app\.js[^>]*>', rendered_home({"q": "dhamma"}, "")
    )
    assert tag is not None
    assert (
        "onerror=\"document.documentElement.classList.remove('search-pending')\""
        in tag.group(0)
    )


def test_panes_only_wait_at_phone_width() -> None:
    css = (STATIC / "home.css").read_text(encoding="utf-8")
    assert css.index("@media (max-width: 750px)") < css.index("html.search-pending")
