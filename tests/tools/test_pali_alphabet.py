"""Tests for tools/pali_alphabet.py alphabet data."""

from tools.pali_alphabet import (
    alphabet,
    aspirated,
    consonants,
    dentals,
    double_consonants,
    english_alphabet,
    english_capitals,
    gutterals,
    labials,
    nasals,
    niggahita,
    pali_alphabet,
    palatals,
    retroflexes,
    sanskrit_alphabet,
    semi_vowels,
    unaspirated,
    vowels,
)


def test_pali_alphabet_length_and_ends() -> None:
    assert len(pali_alphabet) == 41
    assert pali_alphabet[0] == "a"
    assert pali_alphabet[-1] == "ṃ"


def test_vowels() -> None:
    assert vowels == ["a", "ā", "i", "ī", "u", "ū", "e", "o"]


def test_consonants_length_and_ends() -> None:
    assert len(consonants) == 33
    assert consonants[0] == "k"
    assert consonants[-1] == "ṃ"


def test_pali_alphabet_is_vowels_then_consonants() -> None:
    assert pali_alphabet == vowels + consonants


def test_double_consonants() -> None:
    assert len(double_consonants) == 20
    assert "kkh" in double_consonants
    assert "bbh" in double_consonants


def test_aspirated_and_unaspirated_pair_up() -> None:
    assert unaspirated == ["k", "g", "c", "j", "ṭ", "ḍ", "t", "d", "p", "b"]
    assert aspirated == [f"{c}h" for c in unaspirated]


def test_articulation_groups() -> None:
    assert gutterals == ["k", "kh", "g", "gh", "ṅ"]
    assert palatals == ["c", "ch", "j", "jh", "ñ"]
    assert retroflexes == ["ṭ", "ṭh", "ḍ", "ḍh", "ṇ"]
    assert dentals == ["t", "th", "d", "dh", "n"]
    assert labials == ["p", "ph", "b", "bh", "m"]
    assert nasals == ["ṅ", "ñ", "ṇ", "n", "m", "ṃ"]
    assert semi_vowels == ["y", "r", "l", "s", "v", "h", "ḷ"]
    assert niggahita == ["ṃ"]


def test_alphabet_composed_from_groups_equals_pali_alphabet() -> None:
    assert alphabet == pali_alphabet


def test_english_alphabets() -> None:
    assert len(english_alphabet) == 26
    assert english_alphabet[0] == "a"
    assert english_alphabet[-1] == "z"
    assert english_capitals == [c.upper() for c in english_alphabet]


def test_sanskrit_alphabet_length_and_extras() -> None:
    assert len(sanskrit_alphabet) == 49
    assert sanskrit_alphabet[0] == "a"
    assert sanskrit_alphabet[-1] == "h"
    assert "ṛ" in sanskrit_alphabet
    assert "ś" in sanskrit_alphabet
    assert "ṣ" in sanskrit_alphabet
