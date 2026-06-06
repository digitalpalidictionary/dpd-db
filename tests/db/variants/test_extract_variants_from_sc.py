"""Tests for db/variants/extract_variants_from_sc.py.

Scenarios:
  valid_variant: word→variant with arrow → correct dict entry
  ṁ_normalized: ṁ in data is normalized to ṃ before processing
  multiple_variants: word→var1;var2 → two entries for same key/book
  pipe_separator: data with '|' → each item processed separately
  empty_key_bug: word_clean=="" → '' not in result (fixed by empty-key guard)
  no_arrow_skipped: entry without '→' → skipped, no stale key reuse (fixed by continue)
  accumulation: pre-populated dict merges, not overwrites
  get_book_name_match: known prefix → returns book name
  get_book_name_no_match: unknown prefix → returns None
"""

from pathlib import Path

from db.variants.extract_variants_from_sc import extract_sc_variants, get_book_name


def test_valid_variant_extracted() -> None:
    """Single word→variant entry produces the correct dict entry."""
    json_data = {"dn-2:1.1": "saraṇagamanaṃ→vā saraṇattayaṃ"}
    result = extract_sc_variants(json_data, {}, "DN1")
    assert "saraṇagamanaṃ" in result
    entries = result["saraṇagamanaṃ"]["MST"]["DN1"]
    assert len(entries) == 1
    word, variant = entries[0]
    assert word == "saraṇagamanaṃ"
    assert variant == "vā saraṇattayaṃ"


def test_ṁ_normalized_to_ṃ() -> None:
    """ṁ in data is normalized to ṃ in both word key and variant text."""
    json_data = {"ref": "saraṇagamanaṁ→vā saraṇattayaṁ"}
    result = extract_sc_variants(json_data, {}, "DN1")
    assert "saraṇagamanaṃ" in result
    entries = result["saraṇagamanaṃ"]["MST"]["DN1"]
    assert entries[0][1] == "vā saraṇattayaṃ"


def test_multiple_variants_via_semicolon() -> None:
    """word→var1;var2 produces two separate entries under the same key/book."""
    json_data = {"ref": "dhammaṃ→dhammā;dhammī"}
    result = extract_sc_variants(json_data, {}, "MN1")
    entries = result["dhammaṃ"]["MST"]["MN1"]
    assert len(entries) == 2
    assert entries[0][1] == "dhammā"
    assert entries[1][1] == "dhammī"


def test_pipe_separator_processes_each_item() -> None:
    """'|'-separated data produces entries for each item independently."""
    json_data = {"ref": "dhammaṃ→dhammā|saraṇaṃ→vā saraṇattayaṃ"}
    result = extract_sc_variants(json_data, {}, "DN1")
    assert "dhammaṃ" in result
    assert "saraṇaṃ" in result


def test_empty_key_not_produced() -> None:
    """word whose key_cleaner result is '' is skipped — no '' key in variants_dict.

    Old behaviour (bug): produced variants_dict[''] entry.
    New behaviour (fix): guarded by `if not word_clean: continue`.
    This test FAILS against the unedited source and PASSES after the fix.
    """
    json_data = {"ref": "123→some variant"}
    result = extract_sc_variants(json_data, {}, "DN1")
    assert "" not in result


def test_no_arrow_entry_skipped() -> None:
    """Entry without '→' is skipped entirely — stale word_clean is not reused.

    Old behaviour (bug): used stale word_clean from previous iteration, duplicating
    the previous key's entry or raising NameError on the first iteration.
    New behaviour (fix): `continue` in the else branch skips the entry.
    This test FAILS against the unedited source and PASSES after the fix.
    """
    json_data = {"ref": "dhammaṃ→dhammā|noarrow_entry"}
    result = extract_sc_variants(json_data, {}, "DN1")
    assert "dhammaṃ" in result
    assert len(result["dhammaṃ"]["MST"]["DN1"]) == 1


def test_variants_dict_accumulates() -> None:
    """Calling with a pre-populated dict merges entries rather than overwriting."""
    seed: dict = {"existing": {"MST": {"DN1": [("ctx", "defn")]}}}
    json_data = {"ref": "dhammaṃ→dhammā"}
    result = extract_sc_variants(json_data, seed, "DN1")
    assert "existing" in result
    assert "dhammaṃ" in result


def test_get_book_name_matching_prefix() -> None:
    """Known file prefix returns the correct book name."""
    book = get_book_name(Path("pli-tv-bu-vb-pj1.json"))
    assert book == "VIN1"


def test_get_book_name_no_match() -> None:
    """Unknown file prefix returns None."""
    book = get_book_name(Path("unknown_file.json"))
    assert book is None
