"""Tests for tools/superscripter.py numeral superscripting."""

from tools.superscripter import superscripter_uni


def test_uni_replaces_space_with_hair_space_and_digit() -> None:
    assert superscripter_uni("kata 1") == "kata ¹"


def test_uni_dotted_number_uses_middle_dot() -> None:
    assert superscripter_uni("kata 2.3") == "kata ²·³"


def test_uni_no_number_unchanged() -> None:
    assert superscripter_uni("kata") == "kata"


def test_uni_replaces_any_full_stop() -> None:
    assert superscripter_uni("a.b") == "a·b"


def test_uni_empty_string() -> None:
    assert superscripter_uni("") == ""
