"""Tests for db/variants/extract_variants_from_cst.py.

Fixture JSON: tests/db/variants/test_extract_variants_from_cst_fixtures.json

Scenarios:
  valid_variant: two-word context, single note → correct key/context/variant
  empty_key_bug: last word is punctuation-only → '' not in result (fixed by guard)
  multi_variant: note splits on 'x (y) z (w)' pattern → two entries
  single_word_context: only one preceding word → context == word
  empty_variant: note text is '( )' → no entry added (existing guard)
  accumulation: pre-populated dict is merged, not overwritten
  sort_order: get_cst_file_list returns files in cst_files_to_books order
"""

import json
from pathlib import Path

from bs4 import BeautifulSoup

from db.variants.extract_variants_from_cst import extract_variants, get_cst_file_list
from tools.paths import ProjectPaths

FIXTURE_PATH = Path("tests/db/variants/test_extract_variants_from_cst_fixtures.json")
_FIXTURES: dict = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _soup(xml: str) -> BeautifulSoup:
    return BeautifulSoup(xml, "xml")


def test_valid_variant_extracted() -> None:
    """Two-word context + single-variant note produces the correct dict entry."""
    xml = "<root><p>saraṇagamanaṃ saraṇattayaṃ<note>vā saraṇattayaṃ (vip)</note></p></root>"
    result = extract_variants(_soup(xml), {}, "VIN1")
    assert "saraṇattayaṃ" in result
    context, variant = result["saraṇattayaṃ"]["CST"]["VIN1"][0]
    assert context == "saraṇagamanaṃ saraṇattayaṃ"
    assert variant == "vā saraṇattayaṃ (vip)"


def test_empty_key_not_produced() -> None:
    """Word whose key_cleaner result is '' is skipped — no '' key in variants_dict.

    Old behaviour (bug): produced variants_dict[''] entry.
    New behaviour (fix): guarded by `if not word_clean: continue`.
    This test FAILS against the unedited source and PASSES after the fix.
    """
    xml = "<root><p>some text {3}<note>some variant</note></p></root>"
    result = extract_variants(_soup(xml), {}, "VIN1")
    assert "" not in result


def test_multi_variant_note_splits() -> None:
    """Note text 'x (y) z (w)' splits into two separate variant entries."""
    xml = "<root><p>some aṭṭha<note>aṭṭha (alt1) sāmi (alt2)</note></p></root>"
    result = extract_variants(_soup(xml), {}, "DN1")
    entries = result["aṭṭha"]["CST"]["DN1"]
    assert len(entries) == 2
    assert entries[0][1] == "aṭṭha (alt1)"
    assert entries[1][1] == "sāmi (alt2)"
    assert entries[0][0] == entries[1][0] == "some aṭṭha"


def test_single_word_context() -> None:
    """When only one word precedes the note, context equals that word."""
    xml = "<root><p>saraṇaṃ<note>varianttext</note></p></root>"
    result = extract_variants(_soup(xml), {}, "MN1")
    assert "saraṇaṃ" in result
    context, variant = result["saraṇaṃ"]["CST"]["MN1"][0]
    assert context == "saraṇaṃ"
    assert variant == "varianttext"


def test_empty_variant_paren_skipped() -> None:
    """Note text '( )' is skipped — no entry added."""
    xml = "<root><p>saraṇaṃ<note>( )</note></p></root>"
    result = extract_variants(_soup(xml), {}, "VIN1")
    assert result == {}


def test_variants_dict_accumulates() -> None:
    """Calling with a pre-populated dict merges entries rather than overwriting."""
    xml = "<root><p>gacchati<note>gacchāmi</note></p></root>"
    seed: dict = {"existing": {"CST": {"VIN1": [("ctx", "defn")]}}}
    result = extract_variants(_soup(xml), seed, "VIN1")
    assert "existing" in result
    assert "gacchati" in result
    context, variant = result["gacchati"]["CST"]["VIN1"][0]
    assert context == "gacchati"
    assert variant == "gacchāmi"


def test_sort_order_matches_books_map() -> None:
    """get_cst_file_list returns files in cst_files_to_books key order."""
    pth = ProjectPaths()
    files = get_cst_file_list(pth)
    names = [f.name for f in files]
    expected = _FIXTURES["sort_order"]
    assert len(names) == expected["file_count"]
    assert names[:5] == expected["first_5"]
    assert names[-5:] == expected["last_5"]
