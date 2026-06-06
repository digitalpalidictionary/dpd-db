"""Tests for db/variants/extract_variants_from_bjt.py.

Fixture JSON: tests/db/variants/fixtures/vp-prj.json
Test scenarios (file name "vp-prj.json" → book "VIN1"):
  entry 1: saraṇagamanaṃ{1} + footnote "1. vā saraṇattayaṃ" → valid variant
  entry 2: "2. vatthu{2}" (valid word_clean) + no footnote 2 → entry-without-footnote error
  entry 3: "3. {5}" (word_clean="") + footnote "5. vā empty" → silently skipped (empty-key fix)
  footnote 3: no matching entry → footnote-without-entry error
  footnote 4: "__suppressed__" with no matching entry → suppressed (not logged)
"""

from pathlib import Path


from db.variants.extract_variants_from_bjt import extract_bjt_variants

FIXTURE_FILE = Path("tests/db/variants/fixtures/vp-prj.json")


def test_valid_variant_extracted() -> None:
    """Valid entry+footnote pair produces the correct variant entry."""
    variants_dict, _ = extract_bjt_variants(FIXTURE_FILE, {}, [])
    assert "saraṇagamanaṃ" in variants_dict
    entries = variants_dict["saraṇagamanaṃ"]["BJT"]["VIN1"]
    assert len(entries) == 1
    context, defn = entries[0]
    assert context == "saraṇagamanaṃ"
    assert defn == "vā saraṇattayaṃ"


def test_empty_key_not_produced() -> None:
    """Entry whose cleaned last word is empty is skipped — no '' key in variants_dict.

    Old behaviour (bug): produced variants_dict[""] entry.
    New behaviour (fix): guarded by `if not word_clean: continue`.
    This test FAILS against the unedited source and PASSES after the fix.
    """
    variants_dict, _ = extract_bjt_variants(FIXTURE_FILE, {}, [])
    assert "" not in variants_dict


def test_entry_without_footnote_logged() -> None:
    """Entry with valid word_clean but no matching footnote is added to errors_list."""
    _, errors_list = extract_bjt_variants(FIXTURE_FILE, {}, [])
    assert ("vp-prj", 1, "2") in errors_list


def test_empty_word_entry_silently_skipped() -> None:
    """Entry with empty word_clean is skipped entirely — no variant and no error logged."""
    variants_dict, errors_list = extract_bjt_variants(FIXTURE_FILE, {}, [])
    assert "" not in variants_dict
    error_keys = {e[2] for e in errors_list}
    assert "5" not in error_keys


def test_footnote_without_entry_logged() -> None:
    """Footnote with no matching entry marker is added to errors_list."""
    _, errors_list = extract_bjt_variants(FIXTURE_FILE, {}, [])
    assert ("vp-prj", 1, "3") in errors_list


def test_footnote_with_dunder_suppressed() -> None:
    """Footnote containing __ is not logged as an error."""
    _, errors_list = extract_bjt_variants(FIXTURE_FILE, {}, [])
    keys_in_errors = {e[2] for e in errors_list}
    assert "4" not in keys_in_errors


def test_variants_dict_accumulates() -> None:
    """Calling with a pre-populated dict merges, not overwrites."""
    seed: dict = {"existing": {"BJT": {"VIN1": [("ctx", "defn")]}}}
    variants_dict, _ = extract_bjt_variants(FIXTURE_FILE, seed, [])
    assert "existing" in variants_dict
    assert "saraṇagamanaṃ" in variants_dict
