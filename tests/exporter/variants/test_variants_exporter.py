"""Golden-master tests for exporter/variants/variants_exporter.py.

The fixture freezes the synonym sets produced by the UNEDITED accumulation logic
(``add_niggahitas`` called inside the inner per-variant loop). The refactor hoists
that call to a single post-loop call; ``new_synonyms`` below mirrors the edited
order using the real imported functions and must produce an identical set for
every real-data case.
"""

import json
from pathlib import Path

import pytest

from exporter.variants.variants_exporter import make_synonyms, make_synonyms_bjt
from tools.niggahitas import add_niggahitas

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
