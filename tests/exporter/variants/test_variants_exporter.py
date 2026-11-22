"""Golden-master tests for exporter/variants/variants_exporter.py.

The fixture freezes the synonym sets produced by the UNEDITED accumulation logic
(``add_niggahitas`` called inside the inner per-variant loop). The refactor hoists
that call to a single post-loop call; ``new_synonyms`` below mirrors the edited
order using the real imported functions and must produce an identical set for
every real-data case.
"""

import json
import re
from pathlib import Path

import pytest

from db.models import Lookup
from exporter.variants.variants_exporter import (
    make_entry_html,
    make_synonyms,
    make_synonyms_bjt,
)
from exporter.webapp.data_classes import VariantData
from tools.css_manager import CSSManager
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths

FIXTURE_PATH = Path(__file__).parent / "test_variants_exporter_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def new_synonyms(word: str, variant_data: dict) -> list[str]:
    """Mirror of the edited accumulation: add_niggahitas hoisted to one final call."""
    synonyms_list: list[str] = []
    if "ṃ" in word or "ṁ" in word:
        synonyms_list = add_niggahitas([word])
    for corpus, book_dict in variant_data.items():
        for book, entries in book_dict.items():
            for context, variant in entries:
                if corpus == "MST" or corpus == "CST":
                    synonyms_list = make_synonyms(synonyms_list, variant)
                if corpus == "BJT":
                    synonyms_list = make_synonyms_bjt(synonyms_list, variant)
    return add_niggahitas(synonyms_list)


@pytest.mark.parametrize("key", list(FIXTURES.keys()))
def test_hoisted_niggahita_set_identical(key: str) -> None:
    case = FIXTURES[key]
    result = new_synonyms(case["word"], case["variant_data"])
    assert sorted(result) == case["old_synonyms_sorted"]


def test_make_synonyms_single_word_appends() -> None:
    assert make_synonyms([], "akatānudhammena") == ["akatānudhammena"]


def test_make_synonyms_strips_parenthetical() -> None:
    assert make_synonyms([], "akata (foo bar)") == ["akata"]


def test_make_synonyms_multiword_skipped() -> None:
    assert make_synonyms([], "two words here") == []


def test_make_synonyms_dedup() -> None:
    assert make_synonyms(["akata"], "akata") == ["akata"]


def test_make_synonyms_bjt_strips_dash_remainder() -> None:
    assert make_synonyms_bjt([], "machasaṃ – PTS") == ["machasaṃ"]


def test_make_synonyms_bjt_multiword_skipped() -> None:
    assert make_synonyms_bjt([], "rūpādivaggo paṭhamo – machasaṃ, PTS") == []


# Entry HTML (issue #99): a long list folds behind a "show all" button.

SHOWN = VariantData.rows_shown
HIDDEN = "<tr class='variant-more hidden'>"


def _variant_data(rows_per_corpus: dict[str, int]) -> VariantData:
    variants = {
        corpus: {"book": [[f"{corpus} context {i}", f"variant {i}"] for i in range(n)]}
        for corpus, n in rows_per_corpus.items()
    }
    row = Lookup()
    row.lookup_key = "dhamma"
    row.variant_pack(variants)
    return VariantData(row, fold=True)


def _data_rows(html: str) -> list[str]:
    """The opening tag of every variant row, separators left out."""
    return re.findall(r"<tr[^>]*>(?=<td>)", html)


def _separators(html: str) -> list[str]:
    return re.findall(r"<tr[^>]*>(?=<td colspan)", html)


def test_entry_short_list_shows_every_row() -> None:
    html = make_entry_html("", _variant_data({"CST": 3, "BJT": 2}))
    assert len(_data_rows(html)) == 5
    assert "variant-more" not in html
    assert "variants-more" not in html
    assert _separators(html) == ["<tr>", "<tr>"]


def test_entry_folds_at_exactly_twice_the_shown_rows() -> None:
    html = make_entry_html("", _variant_data({"CST": 2 * SHOWN}))
    assert _data_rows(html).count(HIDDEN) == SHOWN
    assert f"show all {2 * SHOWN} variants" in html


def test_entry_long_list_hides_the_rows_after_the_first_few() -> None:
    html = make_entry_html("", _variant_data({"CST": 4, "BJT": 30}))
    rows = _data_rows(html)
    assert len(rows) == 34
    assert rows[:SHOWN] == ["<tr>"] * SHOWN
    assert rows[SHOWN:] == [HIDDEN] * (34 - SHOWN)


def test_entry_long_list_has_the_button_after_the_table() -> None:
    html = make_entry_html("", _variant_data({"CST": 4, "BJT": 30}))
    button = (
        "<button type='button' class='variants-more dpd-link' aria-expanded='false' "
        "data-more='show all 34 variants' data-less='show fewer'>"
        "show all 34 variants</button>"
    )
    assert html.count(button) == 1
    assert html.index("</table>") < html.index(button) < html.index("dpd-footer")


def test_entry_separators_after_the_fold_are_hidden() -> None:
    html = make_entry_html("", _variant_data({"CST": SHOWN + 5, "BJT": 10, "SYA": 10}))
    assert _separators(html) == ["<tr>", HIDDEN, HIDDEN]


def test_header_loads_the_shipped_variants_script() -> None:
    pth = ProjectPaths()
    header = pth.variants_header_path.read_text(encoding="utf-8")
    script = pth.variants_js_path
    assert script.exists()
    assert f'<link href="{script.name}" class="load_variants_js"' in header
    assert 'getElementsByClassName("load_variants_js")' in header
    assert 'typeof variants_js_already_loaded === "undefined"' in header


def test_header_defines_every_variable_the_button_styles_use() -> None:
    """The button is styled by its own reset and by the .dpd-link rules."""
    pth = ProjectPaths()
    header = CSSManager().update_style(
        pth.variants_header_path.read_text(encoding="utf-8"), "variants"
    )
    defined = set(re.findall(r"(--[\w-]+)\s*:", header))
    css = pth.dpd_css_and_fonts_path.read_text(encoding="utf-8")
    bodies = [
        body
        for selector, body in re.findall(r"([^{}]+)\{([^}]*)\}", css)
        if ".dpd-link" in selector or "button.variants-more" in selector
    ]
    used = set(re.findall(r"var\((--[\w-]+)\)", "".join(bodies)))
    assert used
    assert used <= defined, used - defined
