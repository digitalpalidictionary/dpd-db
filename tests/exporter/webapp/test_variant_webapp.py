"""Tests for VariantData and the webapp variants template (issue #99)."""

import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from jinja2 import Environment, FileSystemLoader

from db.models import Lookup
from exporter.webapp.data_classes import VariantData

SHOWN = VariantData.rows_shown


def _make_variant_data(
    rows_per_corpus: dict[str, int], fold: bool = True
) -> VariantData:
    variants = {
        corpus: {"book": [[f"{corpus} context {i}", f"variant {i}"] for i in range(n)]}
        for corpus, n in rows_per_corpus.items()
    }
    row = Lookup()
    row.lookup_key = "dhamma"
    row.variant_pack(variants)
    return VariantData(row, fold=fold)


def _render(d: VariantData) -> str:
    env = Environment(
        loader=FileSystemLoader("exporter/webapp/templates"), autoescape=False
    )
    return env.get_template("variant.html").render(d=d)


def _variant_rows(html: str) -> list[str]:
    """The opening tag of every variant row, separators left out."""
    return re.findall(r"<tr[^>]*>(?=\s*<td>)", html)


def test_short_list_is_not_folded() -> None:
    d = _make_variant_data({"CST": 3, "BJT": 2})
    assert d.row_count == 5
    assert not d.folded
    html = _render(d)
    assert "variants-more" not in html
    assert "hidden" not in html
    assert len(_variant_rows(html)) == 5


def test_a_list_just_over_the_shown_rows_stays_whole() -> None:
    d = _make_variant_data({"CST": 2 * SHOWN - 1})
    assert not d.folded
    assert "hidden" not in _render(d)


def test_a_list_of_twice_the_shown_rows_folds() -> None:
    d = _make_variant_data({"CST": 2 * SHOWN})
    assert d.folded
    rows = _variant_rows(_render(d))
    assert sum("hidden" in tag for tag in rows) == SHOWN


def test_long_list_shows_its_first_rows_and_a_button() -> None:
    d = _make_variant_data({"CST": 4, "BJT": 30})
    assert d.row_count == 34
    assert d.folded
    html = _render(d)
    rows = _variant_rows(html)
    assert len(rows) == 34
    assert not any("hidden" in tag for tag in rows[:SHOWN])
    assert all('class="variant-more hidden"' in tag for tag in rows[SHOWN:])
    assert 'aria-expanded="false"' in html
    assert ">show all 34 variants</button>" in html


def test_long_list_without_fold_shows_every_row() -> None:
    d = _make_variant_data({"CST": 4, "BJT": 30}, fold=False)
    assert not d.folded
    html = _render(d)
    assert "variants-more" not in html
    assert "hidden" not in html
    assert len(_variant_rows(html)) == 34


def test_separators_after_the_shown_rows_are_hidden_too() -> None:
    d = _make_variant_data({"CST": SHOWN + 5, "BJT": 10, "SYA": 10})
    html = _render(d)
    separators = re.findall(r"<tr[^>]*>(?=\s*<td colspan)", html)
    # every corpus starts with a separator; only the first comes before the fold
    assert len(separators) == 3
    assert "hidden" not in separators[0]
    assert all("hidden" in tag for tag in separators[1:])


# The routes below run on the real dpd.db, where "ca" has the longest list.


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    from exporter.webapp.main import app

    with TestClient(app) as test_client:
        yield test_client


def _assert_folded(html: str) -> None:
    """The button names every row, and all rows past the first few are hidden."""
    match = re.search(r">show all (\d+) variants</button>", html)
    assert match
    hidden_rows = re.findall(r'<tr class="variant-more hidden">(?=\s*<td>)', html)
    assert len(hidden_rows) == int(match.group(1)) - SHOWN


def test_json_search_keeps_every_row_without_fold(client: TestClient) -> None:
    html = client.get("/search_json", params={"q": "ca"}).json()["dpd_html"]
    assert '<table class="variants">' in html
    assert "variants-more" not in html
    assert "variant-more" not in html


def test_json_search_folds_with_fold(client: TestClient) -> None:
    response = client.get("/search_json", params={"q": "ca", "fold": "1"})
    _assert_folded(response.json()["dpd_html"])


def test_html_search_folds(client: TestClient) -> None:
    _assert_folded(client.get("/search_html", params={"q": "ca"}).text)


def test_goldendict_page_folds(client: TestClient) -> None:
    _assert_folded(client.get("/gd", params={"search": "ca"}).text)
