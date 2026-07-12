"""Tests for tools/clean_machine.py text cleaning."""

from tools.clean_machine import clean_machine


def test_lowercases_and_strips_punctuation() -> None:
    assert clean_machine("Kammaṁ, karoti.", show_errors=False) == "kammaṃ karoti"


def test_default_niggahita_converts_dotted_m_above() -> None:
    assert clean_machine("kammaṁ", show_errors=False) == "kammaṃ"


def test_alternative_niggahita_keeps_dotted_m_above() -> None:
    assert clean_machine("kammaṁ", niggahita="ṁ", show_errors=False) == "kammaṁ"


def test_digits_removed() -> None:
    assert clean_machine("abc123", show_errors=False) == "abc"


def test_hyphen_removed_by_default() -> None:
    assert clean_machine("a-b", show_errors=False) == "ab"


def test_hyphen_kept_when_requested() -> None:
    assert clean_machine("a-b", remove_hyphen=False, show_errors=False) == "a-b"


def test_newline_gets_leading_space() -> None:
    assert clean_machine("line1\nline2", show_errors=False) == "line \nline"


def test_empty_string() -> None:
    assert clean_machine("", show_errors=False) == ""


def test_quotes_and_exclamation_removed_without_spacing() -> None:
    assert clean_machine("“sādhu!”", show_errors=False) == "sādhu"


def test_bold_tags_removed() -> None:
    assert clean_machine("<b>bold</b>", show_errors=False) == "bold"


def test_en_dash_replaced_after_space_collapse_leaves_double_space() -> None:
    # "–" becomes " " after the "  " -> " " pass has already run,
    # so a spaced en dash leaves a double space in the output.
    assert clean_machine("one two – three", show_errors=False) == "one two  three"


def test_t_underscore_becomes_v() -> None:
    assert clean_machine("at_a", show_errors=False) == "ava"
