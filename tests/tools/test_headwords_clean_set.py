"""Tests for tools/headwords_clean_set.py clean headword set builder."""

from db.models import DpdHeadword
from tools.headwords_clean_set import make_clean_headwords_set


def test_strips_trailing_numbers_and_dedupes() -> None:
    words = [
        DpdHeadword(lemma_1="dhamma 1.01"),
        DpdHeadword(lemma_1="dhamma 2.02"),
        DpdHeadword(lemma_1="kamma"),
    ]
    assert make_clean_headwords_set(words) == {"dhamma", "kamma"}


def test_empty_list_returns_empty_set() -> None:
    assert make_clean_headwords_set([]) == set()


def test_returns_a_set_not_a_list() -> None:
    words = [DpdHeadword(lemma_1="kamma")]
    result = make_clean_headwords_set(words)
    assert isinstance(result, set)
