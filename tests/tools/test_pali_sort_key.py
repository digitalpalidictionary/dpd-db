"""Tests for tools/pali_sort_key.py sorting helpers."""

from tools.pali_sort_key import pali_list_sorter, pali_sort_key, sanskrit_sort_key


def test_pali_sort_key_maps_letters_to_numbers() -> None:
    assert pali_sort_key("kata") == "09012401"


def test_pali_sort_key_empty_string() -> None:
    assert pali_sort_key("") == ""


def test_pali_sort_key_leaves_unknown_characters_untouched() -> None:
    assert pali_sort_key("a-b") == "01-31"


def test_pali_sort_key_passes_int_through() -> None:
    assert pali_sort_key(5) == 5  # type: ignore[arg-type]


def test_pali_sort_key_root_sign_sorts_first() -> None:
    assert pali_sort_key("√kar") == "00090135"


def test_pali_sort_key_aspirate_matches_single_letter_first() -> None:
    # "kh" is tokenised as "k" + "h" because "k" precedes "kh"
    # in the regex alternation, not as the digraph "kh" (= "10").
    assert pali_sort_key("kha") == "093901"


def test_sorted_with_pali_sort_key() -> None:
    words = ["dhamma", "dukkha", "deva"]
    assert sorted(words, key=pali_sort_key) == ["dukkha", "deva", "dhamma"]


def test_pali_list_sorter_orders_by_pali_alphabet() -> None:
    words = ["saṃgha", "buddha", "ānanda", "anicca"]
    assert pali_list_sorter(words) == ["anicca", "ānanda", "buddha", "saṃgha"]


def test_pali_list_sorter_accepts_set() -> None:
    assert pali_list_sorter({"ba"}) == ["ba"]


def test_pali_list_sorter_empty_list() -> None:
    assert pali_list_sorter([]) == []


def test_sanskrit_sort_key_maps_letters_to_numbers() -> None:
    assert sanskrit_sort_key("kṛta") == "17073201"


def test_sanskrit_sort_key_diphthong_matches_single_vowels_first() -> None:
    # "ai" is tokenised as "a" + "i", not as the diphthong "ai" (= "12"),
    # because "a" precedes "ai" in the regex alternation.
    assert sanskrit_sort_key("ai") == "0103"


def test_sorted_with_sanskrit_sort_key() -> None:
    words = ["ṛju", "ita", "ūna"]
    assert sorted(words, key=sanskrit_sort_key) == ["ita", "ūna", "ṛju"]
