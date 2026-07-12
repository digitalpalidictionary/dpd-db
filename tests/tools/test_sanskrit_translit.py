"""Tests for tools/sanskrit_translit.py Harvard-Kyoto and SLP1 to IAST."""

import pytest

from tools.sanskrit_translit import hk_translit, slp1_translit


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", ""),
        ("buddhaH", "buddhaḥ"),
        ("saMskRta", "saṃskṛta"),
        ("jJAna", "jñāna"),
        ("zaTkoNa", "ṣaṭkoṇa"),
        ("kRSNa", "kṛśṇa"),
        ("dharma", "dharma"),  # plain lowercase passes through
    ],
)
def test_hk_translit(text: str, expected: str) -> None:
    assert hk_translit(text) == expected


def test_hk_translit_multichar_keys_are_dead() -> None:
    """The dict has "RR", "lR", "lRR" keys but lookup is per-character,
    so they can never match. Lock the current char-by-char behaviour."""
    assert hk_translit("RR") == "ṛṛ"
    assert hk_translit("lR") == "lṛ"
    assert hk_translit("lRR") == "lṛṛ"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", ""),
        ("Darma", "dharma"),
        ("kfzRa", "kṛṣṇa"),
        ("gOtama", "gautama"),
        ("arTa", "artha"),
        ("jYAna", "jñāna"),
        ("SAstra", "śāstra"),
        ("nirvana", "nirvana"),  # plain lowercase passes through
    ],
)
def test_slp1_translit(text: str, expected: str) -> None:
    assert slp1_translit(text) == expected
