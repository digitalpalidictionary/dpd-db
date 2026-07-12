"""Tests for tools/diacritics_cleaner.py diacritic removal."""

from tools.diacritics_cleaner import diacritics_cleaner


def test_removes_all_pali_diacritics() -> None:
    assert diacritics_cleaner("ṭhāṇa") == "thana"


def test_niggahita_becomes_m() -> None:
    assert diacritics_cleaner("saṃgha") == "samgha"


def test_all_vowel_diacritics() -> None:
    assert diacritics_cleaner("āīū") == "aiu"


def test_all_nasal_diacritics() -> None:
    assert diacritics_cleaner("ṅañaṇa") == "nanana"


def test_retroflex_and_l() -> None:
    assert diacritics_cleaner("ḍaḷa") == "dala"


def test_plain_text_unchanged() -> None:
    assert diacritics_cleaner("buddha") == "buddha"


def test_empty_string() -> None:
    assert diacritics_cleaner("") == ""


def test_dotted_m_above_not_handled() -> None:
    assert diacritics_cleaner("kammaṁ") == "kammaṁ"


def test_capital_diacritics_not_handled() -> None:
    assert diacritics_cleaner("Ānanda") == "Ānanda"
