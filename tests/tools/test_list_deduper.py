"""Tests for tools/list_deduper.py order-preserving dedupe."""

from tools.list_deduper import dedupe_list


def test_removes_duplicates_preserving_order() -> None:
    assert dedupe_list(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]


def test_no_duplicates_unchanged() -> None:
    assert dedupe_list(["x", "y", "z"]) == ["x", "y", "z"]


def test_empty_list() -> None:
    assert dedupe_list([]) == []


def test_all_duplicates_collapse_to_one() -> None:
    assert dedupe_list(["a", "a", "a"]) == ["a"]


def test_works_with_integers() -> None:
    assert dedupe_list([3, 1, 3, 2, 1]) == [3, 1, 2]
