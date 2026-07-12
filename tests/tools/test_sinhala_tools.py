"""Tests for tools/sinhala_tools.py POS lookups and roman ↔ Sinhala
transliteration via aksharamukha.

Note: roman → Sinhala output contains zero-width joiners (U+200D) inside
conjuncts — locked here exactly as produced.
"""

import pytest

from tools.sinhala_tools import (
    pos_si,
    pos_si_full,
    translit_ro_to_si,
    translit_si_to_ro,
)


def test_pos_si_known_values() -> None:
    assert pos_si("masc") == "පු"
    assert pos_si("fem") == "ඉ"
    assert pos_si("nt") == "න"


def test_pos_si_full_known_values() -> None:
    assert pos_si_full("masc") == "පුල්ලිංග"
    assert pos_si_full("root") == "ධාතුව"


def test_pos_si_unknown_raises_key_error() -> None:
    with pytest.raises(KeyError):
        pos_si("nonexistent")
    with pytest.raises(KeyError):
        pos_si_full("nonexistent")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", ""),
        ("dhamma", "ධම‍්ම"),
        ("buddha", "බුද්‍ධ"),
        ("saṅgha", "සඞ‍්ඝ"),
        ("paññā", "පඤ‍්ඤා"),
        ("mettā", "මෙත‍්තා"),
    ],
)
def test_translit_ro_to_si(text: str, expected: str) -> None:
    assert translit_ro_to_si(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", ""),
        ("ධම්ම", "dhamma"),
        ("බුද්ධ", "buddha"),
        ("පඤ්ඤා", "paññā"),
        ("සංඝ", "saṃgha"),  # anusvara stays ṃ in this direction
    ],
)
def test_translit_si_to_ro(text: str, expected: str) -> None:
    assert translit_si_to_ro(text) == expected
