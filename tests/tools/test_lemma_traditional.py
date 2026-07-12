"""Tests for tools/lemma_traditional.py traditional lemma ending derivation."""

from db.models import DpdHeadword
from tools.lemma_traditional import (
    find_space_digits,
    make_lemma_trad,
    make_lemma_trad_clean,
)


def test_find_space_digits_extracts_trailing_number() -> None:
    i = DpdHeadword(lemma_1="satthar 1.02")
    assert find_space_digits(i) == " 1.02"


def test_find_space_digits_none_when_no_number() -> None:
    i = DpdHeadword(lemma_1="satthar")
    assert find_space_digits(i) == ""


def test_make_lemma_trad_clean_applies_dict_ending() -> None:
    i = DpdHeadword(lemma_1="satthar 1.02", stem="satth*", pattern="ar masc")
    assert make_lemma_trad_clean(i) == "satthu"


def test_make_lemma_trad_keeps_trailing_number() -> None:
    i = DpdHeadword(lemma_1="satthar 1.02", stem="satth*", pattern="ar masc")
    assert make_lemma_trad(i) == "satthu 1.02"


def test_inflected_stem_is_skipped() -> None:
    # stem containing "!" marks an inflected form, not a lemma -> pass through unchanged.
    i = DpdHeadword(lemma_1="katvā", stem="!", pattern="ar masc")
    assert make_lemma_trad_clean(i) == "katvā"
    assert make_lemma_trad(i) == "katvā"


def test_pattern_not_in_dict_falls_back_to_lemma() -> None:
    i = DpdHeadword(lemma_1="dhamma", stem="dhamm*a", pattern="a masc")
    assert make_lemma_trad_clean(i) == "dhamma"
    assert make_lemma_trad(i) == "dhamma"
