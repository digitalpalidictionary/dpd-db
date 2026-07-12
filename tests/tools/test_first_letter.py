"""Tests for tools/first_letter.py first letter finder."""

import pytest

from tools.first_letter import find_first_letter


def test_single_consonant() -> None:
    assert find_first_letter("kata") == "k"


def test_aspirated_digraph() -> None:
    assert find_first_letter("kha") == "kh"


def test_aspirated_digraph_with_diacritic() -> None:
    assert find_first_letter("ṭhāna") == "ṭh"


def test_labial_digraph() -> None:
    assert find_first_letter("bhāvanā") == "bh"


def test_vowel() -> None:
    assert find_first_letter("ānanda") == "ā"


def test_single_character_word() -> None:
    assert find_first_letter("a") == "a"


def test_non_pali_letters_return_first_char() -> None:
    assert find_first_letter("xyz") == "x"


def test_empty_string_raises_index_error() -> None:
    with pytest.raises(IndexError):
        find_first_letter("")
