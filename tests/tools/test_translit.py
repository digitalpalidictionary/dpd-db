"""Tests for tools/translit.py auto-detection and transliteration to Roman.

Locks current behaviour: Roman/English/ALL-CAPS input passes through
unchanged, other scripts are transliterated to IAST Pāḷi via aksharamukha.
"""

import pytest

from tools.translit import auto_translit_to_roman


def test_empty_string_returns_empty() -> None:
    assert auto_translit_to_roman("") == ""


@pytest.mark.parametrize(
    "text",
    [
        "DN1",  # first two chars uppercase
        "DHPa",
        "dhamma",  # pure roman Pāḷi
        "Buddha",  # uppercase first letter, still roman
        "māḷā",  # Pāḷi diacritics
        "hello",  # plain English
    ],
)
def test_roman_and_english_pass_through_unchanged(text: str) -> None:
    assert auto_translit_to_roman(text) == text


@pytest.mark.parametrize(
    "text,expected",
    [
        ("धम्म", "dhamma"),  # Devanagari
        ("मेत्ता", "mettā"),
        ("ධම්ම", "dhamma"),  # Sinhala
        ("බුද්ධ", "buddha"),
        ("පඤ්ඤා", "paññā"),
        ("ဓမ္မ", "dhamma"),  # Burmese
        ("ธมฺม", "dhamma"),  # Thai
    ],
)
def test_other_scripts_transliterate_to_roman(text: str, expected: str) -> None:
    assert auto_translit_to_roman(text) == expected


def test_anusvara_converted_to_nasal() -> None:
    # the AnusvaratoNasalASTISO post-option: ං before ඝ becomes ṅ
    assert auto_translit_to_roman("සංඝ") == "saṅgha"
