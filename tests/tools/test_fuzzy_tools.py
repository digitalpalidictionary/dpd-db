"""Tests for tools/fuzzy_tools.py fuzzy string matching."""

from tools.fuzzy_tools import find_closest_matches


def test_finds_closest_matches_limited() -> None:
    result = find_closest_matches(
        "dhama", ["dhamma", "kamma", "dharma", "sangha"], limit=2
    )
    assert result == ["dhamma", "dharma"]


def test_empty_term_returns_empty_list() -> None:
    assert find_closest_matches("", ["dhamma"]) == []


def test_empty_allowed_list_returns_empty_list() -> None:
    assert find_closest_matches("x", []) == []


def test_default_limit_is_three() -> None:
    result = find_closest_matches(
        "kamma", ["kamma", "kammam", "kamman", "dhamma", "sangha"]
    )
    assert len(result) <= 3
    assert "kamma" in result


def test_exact_match_is_first_result() -> None:
    result = find_closest_matches("kamma", ["dhamma", "kamma", "sangha"])
    assert result[0] == "kamma"
