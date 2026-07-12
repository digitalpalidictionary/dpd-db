"""Tests for tools/sort_naturally.py natural sorting helpers."""

from pathlib import Path

from tools.sort_naturally import (
    alpha_num_key,
    alpha_num_key_hyphenated,
    natural_sort,
    natural_sort_hyphenated,
)


def test_alpha_num_key_dotted_number() -> None:
    assert alpha_num_key("file-1.1.json") == (0, "file-", 1, 1, ".json")


def test_alpha_num_key_two_digit_number() -> None:
    assert alpha_num_key("file-10.2.json") == (0, "file-", 10, 2, ".json")


def test_alpha_num_key_no_second_number() -> None:
    assert alpha_num_key("an-3.json") == (0, "an-", 3, -1, ".json")


def test_alpha_num_key_accepts_path() -> None:
    assert alpha_num_key(Path("/x/an-3.json")) == (0, "an-", 3, -1, ".json")


def test_alpha_num_key_empty_string_falls_back() -> None:
    assert alpha_num_key("") == (1, "", 0, 0, "")


def test_alpha_num_key_no_digits_falls_back() -> None:
    assert alpha_num_key("nodigits") == (1, "nodigits", 0, 0, "")


def test_natural_sort_orders_numbers_numerically() -> None:
    files = ["file-10.1.json", "file-2.1.json", "file-1.2.json", "file-1.1.json"]
    assert natural_sort(files) == [
        "file-1.1.json",
        "file-1.2.json",
        "file-2.1.json",
        "file-10.1.json",
    ]


def test_natural_sort_non_list_returns_empty() -> None:
    assert natural_sort("notalist") == []  # type: ignore[arg-type]


def test_alpha_num_key_hyphenated_single_number() -> None:
    assert alpha_num_key_hyphenated("an-3.json") == (0, "an-", 3, -1, ".json")


def test_alpha_num_key_hyphenated_two_numbers() -> None:
    assert alpha_num_key_hyphenated("an-3-2.json") == (0, "an-", 3, 2, ".json")


def test_alpha_num_key_hyphenated_non_numeric_falls_back() -> None:
    assert alpha_num_key_hyphenated("an-x.json") == (1, "an-x.json", 0, 0, "")


def test_alpha_num_key_hyphenated_dotted_number_reads_as_one_int() -> None:
    # "1.2" becomes "1_2" and int("1_2") == 12 via Python's
    # underscore digit separator, so the key is 12 rather than (1, 2).
    assert alpha_num_key_hyphenated("file-1.2.json") == (0, "file-", 12, -1, ".json")


def test_natural_sort_hyphenated_base_file_sorts_first() -> None:
    files = ["an-3-3.json", "an-10.json", "an-3.json", "an-3-2.json"]
    assert natural_sort_hyphenated(files) == [
        "an-3.json",
        "an-3-2.json",
        "an-3-3.json",
        "an-10.json",
    ]


def test_natural_sort_hyphenated_non_list_returns_empty() -> None:
    assert natural_sort_hyphenated(None) == []  # type: ignore[arg-type]
