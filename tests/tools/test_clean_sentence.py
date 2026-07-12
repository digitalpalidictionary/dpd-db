"""Tests for tools/clean_sentence.py Pāḷi sentence word splitting."""

from tools import pali_alphabet as pali_alphabet_module
from tools.clean_sentence import split_pali_sentence_into_words


def test_global_pali_alphabet_is_not_mutated() -> None:
    original = list(pali_alphabet_module.pali_alphabet)
    split_pali_sentence_into_words("cā'ti eka-puggalaṃ")
    assert pali_alphabet_module.pali_alphabet == original


def test_splits_sentence_dropping_non_pali_chars() -> None:
    sentence = (
        "(DNa) soceyyasīlālayuposathesu cā'ti ettha kāyasoceyy'ādi tividhaṃ soceyyaṃ."
    )
    assert split_pali_sentence_into_words(sentence) == [
        "a",
        "soceyyasīlālayuposathesu",
        "cā'ti",
        "ettha",
        "kāyasoceyy'ādi",
        "tividhaṃ",
        "soceyyaṃ",
    ]


def test_include_hyphen_false_still_splits_on_hyphen() -> None:
    # The hyphen is excluded from the word-finder character class,
    # so hyphenated words split apart.
    sentence = "eka-puggalaṃ āgamma, na tveva dhammaṃ."
    assert split_pali_sentence_into_words(sentence, include_hyphen=False) == [
        "eka",
        "puggalaṃ",
        "āgamma",
        "na",
        "tveva",
        "dhammaṃ",
    ]


def test_empty_string_returns_empty_list() -> None:
    assert split_pali_sentence_into_words("") == []


def test_bold_tags_are_stripped_before_splitting() -> None:
    assert split_pali_sentence_into_words("<b>kamma</b>") == ["kamma"]
