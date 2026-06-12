"""Verify example bolding helpers used by the analysis pipeline."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from exporter.analysis.example_bolding import (
    _verse_tokens,
    bold_component_in_token,
    bold_word_in_verse,
    bold_word_toplevel,
    collect_all_ids,
)


def _mock_session(headword: object | None = None) -> MagicMock:
    """Return a mock DB session with an optional headword lookup result."""
    mock = MagicMock()
    mock.query.return_value.filter_by.return_value.first.return_value = headword
    return mock


def test_bold_component_in_token_first_component() -> None:
    """First component is bolded precisely."""
    result = bold_component_in_token(
        "micchādiṭṭhisamādānā",
        "micchā",
        99998,
        _mock_session(),
        is_first_component=True,
    )
    assert result == "<b>micchā</b>diṭṭhisamādānā"


def test_bold_component_in_token_middle_component() -> None:
    """Component with a suffix in the token is bolded precisely, not to end.

    Covers the real DHP316 case: diṭṭhi is last in sub-compound micchādiṭṭhi
    but the verse token is micchādiṭṭhisamādānā — suffix exists, so bold only diṭṭhi.
    """
    result = bold_component_in_token(
        "micchādiṭṭhisamādānā",
        "diṭṭhi",
        32479,
        _mock_session(),
        is_first_component=False,
    )
    assert result == "micchā<b>diṭṭhi</b>samādānā"


def test_bold_component_in_token_last_component() -> None:
    """Component at end of token is bolded to end."""
    result = bold_component_in_token(
        "micchādiṭṭhisamādānā",
        "samādānā",
        99999,
        _mock_session(),
        is_first_component=False,
    )
    assert result == "micchādiṭṭhi<b>samādānā</b>"


def test_bold_component_strategy_0_db_inflections() -> None:
    """Database inflections are preferred before fallback component matching."""
    headword = SimpleNamespace(inflections_list=["yogaṃ", "yogā", "yoga"])
    result = bold_component_in_token(
        "yogācaraṇa",
        "yoga",
        54211,
        _mock_session(headword),
        is_first_component=True,
    )
    assert result == "<b>yogā</b>caraṇa"


def test_bold_component_apostrophe_fallback() -> None:
    """Sandhi apostrophe fallback bolds the right-hand side when needed."""
    result = bold_component_in_token(
        "ajj'uposatho",
        "uposatha",
        99999,
        _mock_session(),
        is_first_component=False,
    )
    assert result == "ajj'<b>uposatho</b>"


def test_bold_component_fallback_whole_token() -> None:
    """Unmatched components fall back to bolding the whole token."""
    result = bold_component_in_token(
        "vimokkhā",
        "dhamma",
        99999,
        _mock_session(),
        is_first_component=False,
    )
    assert result == "<b>vimokkhā</b>"


def test_bold_component_final_m_fallback() -> None:
    """Final-ṃ fallback strips niggahīta before matching a token component."""
    result = bold_component_in_token(
        "dhammacakkappavattana",
        "dhammaṃ",
        99999,
        _mock_session(),
        is_first_component=True,
    )
    assert result == "<b>dhamma</b>cakkappavattana"


def test_bold_component_stem_fallback() -> None:
    """Stem fallback strips a trailing vowel before matching."""
    result = bold_component_in_token(
        "kammiko",
        "kamma",
        99999,
        _mock_session(),
        is_first_component=True,
    )
    assert result == "<b>kammi</b>ko"


def test_verse_tokens_basic() -> None:
    """Verse tokenization returns word-like Pāḷi tokens."""
    assert _verse_tokens("namo tassa bhagavato") == ["namo", "tassa", "bhagavato"]


def test_verse_tokens_apostrophe() -> None:
    """Verse tokenization preserves apostrophes inside tokens."""
    assert _verse_tokens("ajj'uposatho aho") == ["ajj'uposatho", "aho"]


def test_bold_word_toplevel() -> None:
    """Top-level words are bolded as whole tokens."""
    assert bold_word_toplevel("dhamma") == "<b>dhamma</b>"


def test_bold_word_in_verse_top_level() -> None:
    """Top-level verse token replacement preserves the rest of the verse."""
    result = bold_word_in_verse(
        "namo tassa bhagavato",
        "tassa",
        "tassa",
        12345,
        _mock_session(),
        is_top_level=True,
    )
    assert result == "namo <b>tassa</b> bhagavato"


def test_collect_all_ids_flat_option() -> None:
    """A flat option contributes its own headword ID."""
    option = {"id": 12345, "key": "12345_0", "pali": "dhamma"}
    assert collect_all_ids(option, "dhammaṃ") == [
        (12345, "dhamma", "dhammaṃ", False, True)
    ]


def test_collect_all_ids_nested_components() -> None:
    """Nested component IDs are collected recursively."""
    option = {
        "id": 999,
        "key": "999_0",
        "pali": "micchādiṭṭhisamādānā",
        "compound_type": "kammadhāraya",
        "components": [
            [
                {
                    "id": 111,
                    "key": "111_0",
                    "pali": "micchā",
                    "compound_type": "kammadhāraya",
                    "ai_score": 2,
                    "components": [[{"id": 222, "key": "222_0", "pali": "diṭṭhi"}]],
                }
            ],
            [{"id": 333, "key": "333_0", "pali": "samādāna", "ai_score": 1}],
        ],
    }
    assert collect_all_ids(option, "micchādiṭṭhisamādānā") == [
        (999, "micchādiṭṭhisamādānā", "micchādiṭṭhisamādānā", False, True),
        (111, "micchā", "micchādiṭṭhisamādānā", True, False),
        (222, "diṭṭhi", "micchādiṭṭhisamādānā", True, False),
        (333, "samādāna", "micchādiṭṭhisamādānā", False, False),
    ]


def test_collect_all_ids_occurrence_prefixed_decon_key_skips_parent() -> None:
    """Occurrence-prefixed deconstruction keys recurse without bolding the parent ID."""
    option = {
        "id": 999,
        "key": "w0_decon_okassa_0",
        "pali": "okassa",
        "pos": "sandhi",
        "components": [[{"id": 111, "key": "w0_111_0", "pali": "oka"}]],
    }

    assert collect_all_ids(option, "okassa") == [(111, "oka", "okassa", True, False)]
