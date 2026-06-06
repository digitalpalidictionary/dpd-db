"""Tests for db/variants/extract_variants_from_sya.py.

Scenarios covered:
  get_page_number: page found, page not found
  get_variants_in_page: single word, two-word context, multiple markers, no markers
  clean_variant: long-dash removal, trailing dashes, no-op, all-dashes, short-dash preserved
  get_variants_in_footnotes: normal (two footnotes), double-range, triple-range (bug fix),
                             no footnote section
  extract_sya_variants: normal extraction, empty-word-clean guard, missing footnote, stats
"""

from db.variants.extract_variants_from_sya import (
    _SyaStats,
    clean_variant,
    extract_sya_variants,
    get_page_number,
    get_variants_in_footnotes,
    get_variants_in_page,
)

# Sample text (newlines already removed, matching post-get_sya_text state)
_PAGE_NORMAL = (
    "[page 002] jiṇṇe vuḍḍhe 1- mahallake āsanena 2- nimantetīti"
    "   *  *  *  *  *  *   Footnote:1 Ma. vuddhe. 2 gatātipi pāṭho."
    " -------------------------------------------------"
)
_PAGE_DOUBLE_RANGE = (
    "[page 003] foo 1- bar 2- baz 3-"
    "   Footnote:1-3 Yu. Ma. arahattaṁ. -------------------------------------------------"
)
_PAGE_TRIPLE_RANGE = (
    "[page 004] foo 3- bar 4- baz 5-"
    "   Footnote:3-4-5 yamidha sañjotibhūtā. -------------------------------------------------"
)
_PAGE_NO_FOOTNOTE = "[page 005] some text without footnote section"


# ---------------------------------------------------------------------------
# get_variants_in_page
# ---------------------------------------------------------------------------


def test_get_variants_in_page_single_word() -> None:
    result = get_variants_in_page("vuḍḍhe 1- mahallake")
    assert result == {"1": "vuḍḍhe"}


def test_get_variants_in_page_two_words() -> None:
    result = get_variants_in_page("jiṇṇe vuḍḍhe 1- mahallake")
    assert result == {"1": "jiṇṇe vuḍḍhe"}


def test_get_variants_in_page_multiple_markers() -> None:
    result = get_variants_in_page("jiṇṇe 1- foo āsanena 2- bar")
    assert result == {"1": "jiṇṇe", "2": "foo āsanena"}


def test_get_variants_in_page_no_markers() -> None:
    result = get_variants_in_page("text without any variant markers")
    assert result == {}


# ---------------------------------------------------------------------------
# clean_variant
# ---------------------------------------------------------------------------


def test_clean_variant_removes_long_dashes() -> None:
    assert clean_variant("text---more") == "textmore"


def test_clean_variant_removes_trailing_separator() -> None:
    assert clean_variant("foo ---------") == "foo"


def test_clean_variant_strips_whitespace() -> None:
    assert clean_variant("  foo  ") == "foo"


def test_clean_variant_all_dashes() -> None:
    assert clean_variant("---------") == ""


def test_clean_variant_short_dash_preserved() -> None:
    assert clean_variant("foo-bar") == "foo-bar"


def test_clean_variant_two_dashes_preserved() -> None:
    assert clean_variant("foo--bar") == "foo--bar"


# ---------------------------------------------------------------------------
# get_variants_in_footnotes
# ---------------------------------------------------------------------------


def test_get_variants_in_footnotes_normal() -> None:
    result = get_variants_in_footnotes(_PAGE_NORMAL)
    assert result.get("1") == "Ma. vuddhe."
    assert result.get("2") == "gatātipi pāṭho."


def test_get_variants_in_footnotes_double_range() -> None:
    result = get_variants_in_footnotes(_PAGE_DOUBLE_RANGE)
    assert set(result.keys()) >= {"1", "2", "3"}
    assert result["1"] == result["2"] == result["3"]


def test_get_variants_in_footnotes_no_footnote_section() -> None:
    result = get_variants_in_footnotes(_PAGE_NO_FOOTNOTE)
    assert result == {}


def test_get_variants_in_footnotes_triple_range_all_keys_present() -> None:
    """Triple-range footnote must produce entries for all three keys.

    Old behaviour (bug): double-range branch also fired (if/if instead of if/elif),
    overwriting keys 3 and 4 with an incorrect variant string ("-5 yamidha...").
    New behaviour (fix): only the triple-range branch fires; all three keys get the
    correct stripped variant.
    This test FAILS against the unedited source and PASSES after the if/elif fix.
    """
    result = get_variants_in_footnotes(_PAGE_TRIPLE_RANGE)
    assert set(result.keys()) >= {"3", "4", "5"}
    assert result["3"] == result["4"] == result["5"]
    assert not result["3"].startswith("-")


# ---------------------------------------------------------------------------
# get_page_number (refactored: removed dead i: int param)
# ---------------------------------------------------------------------------


def test_get_page_number_found() -> None:
    assert get_page_number("[page 042] text here") == 42


def test_get_page_number_not_found() -> None:
    assert get_page_number("no page marker here") == 0


def test_get_page_number_leading_zeros() -> None:
    assert get_page_number("[page 001] text") == 1


# ---------------------------------------------------------------------------
# extract_sya_variants (refactored: stats param, empty-key guard, setdefault)
# ---------------------------------------------------------------------------

_TEXT_NORMAL = (
    "[page 002] jiṇṇe vuḍḍhe 1- mahallake āsanena 2- nimantetīti"
    "   *  *  *  *  *  *   Footnote:1 Ma. vuddhe. 2 gatātipi pāṭho."
    " -------------------------------------------------"
)
_TEXT_EMPTY_WORD = (
    "[page 010] 12345 1- mahallake"
    "   Footnote:1 vā empty. -------------------------------------------------"
)
_TEXT_NO_MATCHING_FOOTNOTE = (
    "[page 011] vuḍḍhe 1- mahallake"
    "   Footnote:99 unrelated. -------------------------------------------------"
)


def test_extract_sya_variants_normal() -> None:
    stats = _SyaStats()
    result = extract_sya_variants("VIN1", _TEXT_NORMAL, {}, stats)
    assert "vuḍḍhe" in result
    assert "SYA" in result["vuḍḍhe"]
    entries = result["vuḍḍhe"]["SYA"]["VIN1"]
    assert len(entries) == 1
    assert entries[0][1] == "ma. vuddhe."


def test_extract_sya_variants_accumulates() -> None:
    stats = _SyaStats()
    seed: dict = {"existing": {"SYA": {"VIN1": [("ctx", "defn")]}}}
    result = extract_sya_variants("VIN1", _TEXT_NORMAL, seed, stats)
    assert "existing" in result
    assert "vuḍḍhe" in result


def test_extract_sya_variants_empty_word_clean_skipped() -> None:
    """Word whose cleaned form is '' (all digits) must not produce a '' key."""
    stats = _SyaStats()
    result = extract_sya_variants("VIN1", _TEXT_EMPTY_WORD, {}, stats)
    assert "" not in result


def test_extract_sya_variants_missing_footnote_no_crash() -> None:
    """Marker with no matching footnote is silently skipped — no KeyError."""
    stats = _SyaStats()
    result = extract_sya_variants("VIN1", _TEXT_NO_MATCHING_FOOTNOTE, {}, stats)
    assert result == {}


def test_extract_sya_variants_stats_reset_between_calls() -> None:
    """Stats must not accumulate across independent _SyaStats instances."""
    stats1 = _SyaStats()
    extract_sya_variants("VIN1", _TEXT_NORMAL, {}, stats1)
    first_successes = stats1.successes

    stats2 = _SyaStats()
    extract_sya_variants("VIN1", _TEXT_NORMAL, {}, stats2)
    assert stats2.successes == first_successes
