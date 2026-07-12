"""Tests for tools/niggahitas.py niggahita variants."""

from tools.niggahitas import add_niggahitas


def test_adds_both_variants_by_default() -> None:
    result = add_niggahitas(["kammaṃ"])
    assert sorted(result) == ["kammaŋ", "kammaṁ", "kammaṃ"]


def test_all_false_adds_only_dotted_m_above() -> None:
    result = add_niggahitas(["kammaṃ"], all=False)
    assert sorted(result) == ["kammaṁ", "kammaṃ"]


def test_word_without_niggahita_unchanged() -> None:
    assert add_niggahitas(["buddha"]) == ["buddha"]


def test_empty_list() -> None:
    assert add_niggahitas([]) == []


def test_multiple_words() -> None:
    result = add_niggahitas(["saṃgha", "dhamma"])
    assert sorted(result) == ["dhamma", "saŋgha", "saṁgha", "saṃgha"]


def test_mutates_input_list_in_place() -> None:
    words = ["saṃgha"]
    add_niggahitas(words)
    assert sorted(words) == ["saŋgha", "saṁgha", "saṃgha"]
