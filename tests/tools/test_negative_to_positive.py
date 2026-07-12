"""Tests for tools/negative_to_positive.py negative-to-positive lemma derivation."""

from db.models import DpdHeadword
from tools.negative_to_positive import make_positive


def test_na_prefix_with_doubled_letter_drops_three() -> None:
    i = DpdHeadword(lemma_1="nassa", construction="")
    assert make_positive(i) == "sa"


def test_na_prefix_plain_drops_two() -> None:
    i = DpdHeadword(lemma_1="nagacchati", construction="")
    assert make_positive(i) == "gacchati"


def test_an_prefix_na_a_construction() -> None:
    i = DpdHeadword(lemma_1="anisajjitva", construction="na > a + isajjitva")
    assert make_positive(i) == "nisajjitva"


def test_an_prefix_na_an_construction() -> None:
    i = DpdHeadword(lemma_1="anasava", construction="na > an + asava")
    assert make_positive(i) == "asava"


def test_an_prefix_default_construction() -> None:
    i = DpdHeadword(lemma_1="ankusa", construction="")
    assert make_positive(i) == "kusa"


def test_naa_macron_prefix() -> None:
    i = DpdHeadword(lemma_1="nāsava", construction="")
    assert make_positive(i) == "asava"


def test_ni_prefix() -> None:
    i = DpdHeadword(lemma_1="nikkha", construction="")
    assert make_positive(i) == "kha"


def test_nu_prefix() -> None:
    i = DpdHeadword(lemma_1="nuppajjati", construction="")
    assert make_positive(i) == "uppajjati"


def test_a_prefix_doubled_letter() -> None:
    i = DpdHeadword(lemma_1="aggi", construction="na + aggi")
    assert make_positive(i) == "gi"


def test_a_prefix_default() -> None:
    i = DpdHeadword(lemma_1="akusala", construction="na + kusala")
    assert make_positive(i) == "kusala"


def test_too_short_lemma_returns_empty() -> None:
    i = DpdHeadword(lemma_1="ab", construction="")
    assert make_positive(i) == ""
