"""Tests for tools/meaning_construction.py summary and cleaning helpers."""

from db.models import DpdHeadword
from tools.meaning_construction import (
    clean_construction,
    make_grammar_line,
    make_meaning_combo,
    make_meaning_combo_html,
    summarize_construction,
)


def test_make_meaning_combo_with_literal() -> None:
    i = DpdHeadword(meaning_1="happiness", meaning_lit="joy")
    assert make_meaning_combo(i) == "happiness; lit. joy"


def test_make_meaning_combo_falls_back_to_meaning_2() -> None:
    i = DpdHeadword(meaning_2="bliss")
    assert make_meaning_combo(i) == "bliss"


def test_make_meaning_combo_empty_when_nothing_set() -> None:
    i = DpdHeadword()
    assert make_meaning_combo(i) == ""


def test_make_meaning_combo_html_bolds_meaning_1() -> None:
    i = DpdHeadword(meaning_1="happiness", meaning_lit="joy")
    assert make_meaning_combo_html(i) == "<b>happiness</b>; lit. joy"


def test_make_meaning_combo_html_meaning_2_already_has_lit() -> None:
    i = DpdHeadword(meaning_2="bliss; lit. joy2")
    assert make_meaning_combo_html(i) == "bliss; lit. joy2"


def test_make_meaning_combo_html_meaning_2_appends_lit() -> None:
    i = DpdHeadword(meaning_2="bliss", meaning_lit="joy3")
    assert make_meaning_combo_html(i) == "bliss; lit. joy3"


def test_make_grammar_line_appends_all_optional_parts() -> None:
    i = DpdHeadword(
        grammar="pr 3rd sg",
        neg="neg",
        verb="trans",
        trans="trans2",
        plus_case="acc",
    )
    assert make_grammar_line(i) == "pr 3rd sg, neg, trans, trans2 (acc)"


def test_make_grammar_line_plain_grammar_only() -> None:
    i = DpdHeadword(grammar="masc nom sg")
    assert make_grammar_line(i) == "masc nom sg"


def test_summarize_construction_no_meaning_uses_family_root() -> None:
    i = DpdHeadword(
        meaning_1="",
        origin="dict",
        root_key="kar 1",
        family_root="√ kar",
        construction="",
    )
    assert summarize_construction(i) == "√ + kar"


def test_summarize_construction_no_meaning_no_root_uses_family_word() -> None:
    i = DpdHeadword(
        meaning_1="", origin="dict", root_key="", family_word="kamma", construction=""
    )
    assert summarize_construction(i) == "kamma"


def test_summarize_construction_no_meaning_no_root_no_family_is_empty() -> None:
    i = DpdHeadword(
        meaning_1="", origin="dict", root_key="", family_word="", construction=""
    )
    assert summarize_construction(i) == ""


def test_summarize_construction_with_meaning_no_construction_is_empty() -> None:
    i = DpdHeadword(meaning_1="x", construction="", root_base="")
    assert summarize_construction(i) == ""


def test_summarize_construction_with_meaning_no_root_base_returns_cleaned() -> None:
    i = DpdHeadword(meaning_1="x", construction="kusala + a", root_base="")
    assert summarize_construction(i) == "kusala + a"


def test_summarize_construction_with_root_base_substitutes_root_sign() -> None:
    i = DpdHeadword(
        meaning_1="x",
        construction="<b>karoti</b> + ti",
        root_base="kar + oti",
        root_sign="oti",
        root_key="kar 1",
        pos="pr",
    )
    assert summarize_construction(i) == "karkar + oti + ti"


def test_summarize_construction_fut_uses_base_construction() -> None:
    i = DpdHeadword(
        meaning_1="x",
        construction="<b>karissati</b> + ti",
        root_base="kar + issati > karissa",
        root_sign="issati",
        root_key="kar 1",
        pos="fut",
    )
    assert summarize_construction(i) == "kar + issatiti + ti"


def test_clean_construction_strips_line2() -> None:
    assert clean_construction("line1\nline2 extra") == "line1"


def test_clean_construction_strips_phonetic_change() -> None:
    assert clean_construction("kusala > kusal + a") == "kusala + a"


def test_clean_construction_strips_leading_insertion() -> None:
    assert clean_construction("[na] + kusala + a") == "kusala + a"


def test_clean_construction_strips_trailing_insertion() -> None:
    assert clean_construction("kusala + a + [insert]") == "kusala + a"


def test_clean_construction_strips_double_question_marks() -> None:
    assert clean_construction("kusala ?? + a") == "kusala + a"
