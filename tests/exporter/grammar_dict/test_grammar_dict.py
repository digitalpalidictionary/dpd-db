"""Golden-master tests for exporter/grammar_dict/grammar_dict.py::make_data_lists.

Freezes the DictEntry assembly (definition_html pass-through, empty
definition_plain, niggahita synonym expansion) so the `+=` → `.append`
refactor is proven byte-identical. Synonyms are compared order-insensitively
because add_niggahitas returns list(set(...)) and set ordering is subject to
hash randomization across processes.
"""

import json
from pathlib import Path

from exporter.grammar_dict.grammar_dict import GlobalVars, make_data_lists

FIXTURE_PATH = Path(__file__).parent / "test_grammar_dict_fixtures.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _run_make_data_lists(html_dict: dict[str, str]) -> GlobalVars:
    g = object.__new__(GlobalVars)
    g.html_dict = html_dict
    g.dict_data = []
    make_data_lists(g)
    return g


def test_make_data_lists_matches_fixture() -> None:
    g = _run_make_data_lists(FIXTURE["input_html_dict"])

    actual = [
        {
            "word": e.word,
            "definition_html": e.definition_html,
            "definition_plain": e.definition_plain,
            "synonyms_sorted": sorted(e.synonyms),
        }
        for e in g.dict_data
    ]
    assert actual == FIXTURE["output"]


def test_make_data_lists_preserves_order_and_count() -> None:
    html_dict = FIXTURE["input_html_dict"]
    g = _run_make_data_lists(html_dict)

    assert len(g.dict_data) == len(html_dict)
    assert [e.word for e in g.dict_data] == list(html_dict.keys())


def test_make_data_lists_empty() -> None:
    g = _run_make_data_lists({})
    assert g.dict_data == []


def test_make_data_lists_definition_plain_always_empty() -> None:
    g = _run_make_data_lists(FIXTURE["input_html_dict"])
    assert all(e.definition_plain == "" for e in g.dict_data)


def test_niggahita_word_expands_to_three_synonyms() -> None:
    g = _run_make_data_lists({"saṃ": "<x>"})
    entry = g.dict_data[0]
    assert set(entry.synonyms) == {"saṃ", "saṁ", "saŋ"}


def test_plain_word_has_single_synonym() -> None:
    g = _run_make_data_lists({"dhamma": "<x>"})
    entry = g.dict_data[0]
    assert entry.synonyms == ["dhamma"]
