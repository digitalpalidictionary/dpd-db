"""Tests for tools/ipa.py Pāḷi → IPA conversion.

convert_uni_to_ipa reads the real tools/ipa.tsv via a relative path, so
these tests (like the module itself) assume the project root as cwd.
"""

import pytest

from tools.ipa import a_at_the_end, clean_text, convert_uni_to_ipa, long_e_o


def test_clean_text_strips_punctuation_and_lowercases() -> None:
    assert clean_text("Sace, ‘so’ “bhikkhu” — evaṃ?") == "sace so bhikkhu evaṃ"


def test_clean_text_removes_full_stops_and_semicolons() -> None:
    assert clean_text("ahosi. udapādi; ahosi") == "ahosi udapādi ahosi"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("deva", "dēva"),  # open syllable: e lengthens
        ("loka", "lōka"),  # open syllable: o lengthens
        ("mettā", "mettā"),  # e before double consonant stays short
        ("okkamati", "okkamati"),  # o before double consonant stays short
        ("sace", "sacē"),  # word-final e lengthens
    ],
)
def test_long_e_o(text: str, expected: str) -> None:
    assert long_e_o(text) == expected


def test_a_at_the_end_replaces_with_schwa() -> None:
    # NB: the replacement is "ə " so a word-final match gains a trailing space
    assert a_at_the_end("dhamma") == "dhammə "
    assert a_at_the_end("a b") == "ə b"
    assert a_at_the_end("mettā") == "mettā"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("dhamma", "d̪ʰɐmmɐ"),
        ("mettā", "mɛ.t̪ɑː"),
        ("buddho", "bʊ.d̪ʰoː"),
        ("loka", "loːkɐ"),
        ("bhikkhu", "bʰi.kʰʊ"),
        ("khattiyo jātiyā", "kʰɐ.t̪ijoː ʤɑːt̪ijɑː"),
    ],
)
def test_convert_uni_to_ipa_academic(text: str, expected: str) -> None:
    assert convert_uni_to_ipa(text, "ipa") == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("dhamma", "d̪ʰɐmmɐ"),
        ("mettā", "mɛt̪t̪ɑː"),
        ("buddho", "bud̪d̪ʰoː"),
        ("bhikkhu", "bʰikkʰu"),
        ("khattiyo jātiyā", "kʰɐt̪t̪ijoː ʤɑːt̪ijɑː"),
    ],
)
def test_convert_uni_to_ipa_tts(text: str, expected: str) -> None:
    assert convert_uni_to_ipa(text, "tts") == expected


def test_convert_uni_to_ipa_invalid_mode_raises() -> None:
    """Anything other than "ipa" or "tts" leaves the lookup dict unbound."""
    with pytest.raises(UnboundLocalError):
        convert_uni_to_ipa("dhamma", "bogus")
