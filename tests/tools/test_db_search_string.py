"""Tests for tools/db_search_string.py regex search string builder."""

from tools.db_search_string import db_search_string


def test_default_start_end_wraps_in_slashes() -> None:
    assert db_search_string(["a", "b"]) == "/^(a|b)$/"


def test_word_boundary_when_start_end_false() -> None:
    assert db_search_string(["a", "b"], start_end=False) == "/\\b(a|b)\\b/"


def test_gui_omits_slashes() -> None:
    assert db_search_string(["a", "b"], gui=True) == "^(a|b)$"


def test_empty_collection() -> None:
    assert db_search_string(set()) == "/^()$/"


def test_single_item_set() -> None:
    assert db_search_string({"x"}) == "/^(x)$/"
