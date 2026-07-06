"""Tests for DpdHeadword.lemma_ipa memoization (db/models.py).

The aksharamukha transliteration is memoized by lemma_clean text so that
homonyms sharing a clean lemma (e.g. "khandha 1"/"khandha 2") reuse one
transliteration call instead of repeating it per headword.
"""

from db.models import DpdHeadword, _lemma_ipa_transliterate


def _headword(lemma_1: str) -> DpdHeadword:
    return DpdHeadword(lemma_1=lemma_1)


def test_lemma_ipa_returns_nonempty_string() -> None:
    hw = _headword("dhamma")
    assert isinstance(hw.lemma_ipa, str)
    assert hw.lemma_ipa


def test_lemma_ipa_is_shared_across_homonyms_with_same_lemma_clean() -> None:
    hw1 = _headword("khandha 1")
    hw2 = _headword("khandha 2")
    assert hw1.lemma_clean == hw2.lemma_clean == "khandha"
    assert hw1.lemma_ipa == hw2.lemma_ipa


def test_lemma_ipa_transliterate_cache_hits_on_repeat_calls() -> None:
    _lemma_ipa_transliterate.cache_clear()
    _lemma_ipa_transliterate("dhamma")
    _lemma_ipa_transliterate("dhamma")
    info = _lemma_ipa_transliterate.cache_info()
    assert info.hits >= 1
