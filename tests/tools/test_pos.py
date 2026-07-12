"""Tests for tools/pos.py part-of-speech category lists."""

from tools.pos import (
    CONJUGATIONS,
    DECLENSIONS,
    EXCLUDE_FROM_FREQ,
    INDECLINABLES,
    NOUNS,
    PARTICIPLES,
    POS,
    VERBS,
)


def test_pos_is_union_of_indeclinables_conjugations_declensions_except_var() -> None:
    # "var" is in INDECLINABLES but missing from POS (current data asymmetry).
    union = set(INDECLINABLES) | set(CONJUGATIONS) | set(DECLENSIONS)
    assert set(POS) == union - {"var"}


def test_nouns_are_declensions() -> None:
    assert set(NOUNS) <= set(DECLENSIONS)


def test_participles_are_verbs_and_declensions() -> None:
    assert set(PARTICIPLES) <= set(VERBS)
    assert set(PARTICIPLES) <= set(DECLENSIONS)


def test_no_duplicates_within_pos() -> None:
    assert len(POS) == len(set(POS))


def test_exclude_from_freq_is_subset_of_pos() -> None:
    assert EXCLUDE_FROM_FREQ <= set(POS)


def test_verbs_and_indeclinables_share_only_shared_tags() -> None:
    # abs, ger, inf are both verb forms and grouped under indeclinables.
    assert set(VERBS) & set(INDECLINABLES) == {"abs", "ger", "inf"}
