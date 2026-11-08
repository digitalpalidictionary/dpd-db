"""Render the real landing template without importing the database-backed app."""

from types import SimpleNamespace

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape


@pytest.mark.parametrize(
    ("query", "results", "welcome"),
    [
        ({}, "", True),
        ({"q": "dhamma"}, "", False),
        ({"q": " "}, "", False),
        ({"tab": "dpd", "q": "dhamma"}, "", False),
        ({"tab": "bd"}, "", False),
        ({"tab": "tt"}, "", False),
        ({}, "<p>Result</p>", False),
    ],
)
def test_welcome_is_present_before_javascript_only_for_empty_dpd_state(
    query: dict[str, str], results: str, welcome: bool
) -> None:
    env = Environment(
        loader=FileSystemLoader("exporter/webapp/templates"),
        autoescape=select_autoescape(),
    )
    output = env.get_template("home.html").render(
        request=SimpleNamespace(query_params=query),
        dpd_results=results,
        book_options=[],
        bd_count=100,
        dpd_release_version="test",
    )
    assert ("Search for Pāḷi or English words above" in output) == welcome
    if results:
        assert "<p>Result</p>" in output
