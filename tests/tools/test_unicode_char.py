"""Tests for tools/unicode_char.py Unicode escape conversion."""

from tools.unicode_char import unicode_char


def test_single_ascii_character() -> None:
    assert unicode_char("a") == "\\u0061"


def test_diacritic_character() -> None:
    assert unicode_char("ṭ") == "\\u1e6d"


def test_multiple_characters() -> None:
    assert unicode_char("ab") == "\\u0061\\u0062"


def test_int_converted_to_string() -> None:
    assert unicode_char(5) == "\\u0035"


def test_empty_string() -> None:
    assert unicode_char("") == ""


def test_niggahita() -> None:
    assert unicode_char("ṃ") == "\\u1e43"
