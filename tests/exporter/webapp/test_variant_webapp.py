"""Tests for VariantData and the webapp variants template (issue #99)."""

import re

from jinja2 import Environment, FileSystemLoader

from db.models import Lookup
from exporter.webapp.data_classes import VariantData

SHOWN = VariantData.rows_shown


def _make_variant_data(rows_per_corpus: dict[str, int]) -> VariantData:
    variants = {
        corpus: {"book": [[f"{corpus} context {i}", f"variant {i}"] for i in range(n)]}
        for corpus, n in rows_per_corpus.items()
    }
    row = Lookup()
    row.lookup_key = "dhamma"
    row.variant_pack(variants)
    return VariantData(row)


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


def test_separators_after_the_shown_rows_are_hidden_too() -> None:
    d = _make_variant_data({"CST": SHOWN + 5, "BJT": 10, "SYA": 10})
    html = _render(d)
    separators = re.findall(r"<tr[^>]*>(?=\s*<td colspan)", html)
    # every corpus starts with a separator; only the first comes before the fold
    assert len(separators) == 3
    assert "hidden" not in separators[0]
    assert all("hidden" in tag for tag in separators[1:])
