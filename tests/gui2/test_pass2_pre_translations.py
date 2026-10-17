# -*- coding: utf-8 -*-
"""Tests for gui2.pass2_pre_translations: matching Pass2Pre's CST examples
to paragraphs of the tipitaka translations db. Paragraphs and examples are
copied from the real DNa data."""

import sqlite3
from pathlib import Path

import pytest

import gui2.pass2_pre_translations as translations_module
from gui2.pass2_pre_translations import Pass2PreTranslations

GATHA_PALI = (
    '<p rend="gatha1">Karuṇāsītalahadayaṃ<pb ed="P" n="1.0001" />'
    '<pb ed="V" n="1.0001" /><pb ed="M" n="1.0001" />, '
    "paññāpajjotavihatamohatamaṃ;</p>"
    '<p rend="gathalast">Sanarāmaralokagaruṃ, vande '
    '<hi rend="bold">sugataṃ</hi> gativimuttaṃ.</p>'
)
GATHA_ENGLISH = (
    "With a heart cooled by compassion, dispelling the thick darkness of "
    "delusion with the light of wisdom; Revered by humans and gods, I venerate "
    "the Sugata, freed from destiny."
)
GATHA_EXAMPLE = (
    "karuṇāsītalahadayaṃ,\npaññāpajjotavihatamohatamaṃ,\n"
    "sanarāmaralokagaruṃ,\nvande sugataṃ gativimuttaṃ."
)

BODY_PALI = (
    '<p rend="bodytext"><hi rend="bold">Paṭisaṅkhānabala</hi>nti '
    '<pb ed="M" n="3.0165" /> ‘‘tattha katamaṃ paṭisaṅkhānabalaṃ? Yā paññā '
    'pajānanā’’ti evaṃ vitthāritaṃ <pb ed="V" n="3.0150" /> appaṭisaṅkhāya '
    'akampanañāṇaṃ. <hi rend="bold">Bhāvanābala</hi>nti bhāventassa uppannaṃ '
    "balaṃ. Atthato vīriyasambojjhaṅgasīsena satta bojjhaṅgā honti.</p>"
)
BODY_ENGLISH = "The power of reflection: ..."
# a later paragraph whose text holds "bhāvanābalanti" only inside a longer word
PARTIAL_WORD_PALI = "<p>abhāvanābalanti bhāventassa uppannaṃ balaṃ.</p>"
PARTIAL_WORD_ENGLISH = "wrong paragraph"
# starts on the bold word, so no opening-words fallback can hide a split
BODY_EXAMPLE = (
    "bhāvanābalanti bhāventassa uppannaṃ balaṃ. atthato "
    "vīriyasambojjhaṅgasīsena satta bojjhaṅgā honti. "
)


@pytest.fixture
def translations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Pass2PreTranslations:
    db_path = tmp_path / "translations.db"
    conn = sqlite3.connect(db_path)
    for table in ("s0101a_att", "s0103a_att"):
        conn.execute(f"CREATE TABLE {table} (pali_text TEXT, english_translation TEXT)")
    for table, pali, english in [
        ("s0101a_att", GATHA_PALI, GATHA_ENGLISH),
        ("s0103a_att", BODY_PALI, BODY_ENGLISH),
        ("s0103a_att", PARTIAL_WORD_PALI, PARTIAL_WORD_ENGLISH),
    ]:
        conn.execute(f"INSERT INTO {table} VALUES (?, ?)", (pali, english))
    conn.commit()
    conn.close()

    # s0102a has no table in this db and is skipped
    monkeypatch.setattr(
        translations_module,
        "cst_texts",
        {"dna": ["s0101a.att.txt", "s0102a.att.txt", "s0103a.att.txt"]},
    )
    return Pass2PreTranslations(db_path, ["dna"])


def test_verse_finds_its_paragraph(translations: Pass2PreTranslations) -> None:
    assert translations.find_english(GATHA_EXAMPLE) == GATHA_ENGLISH


def test_bold_tag_inside_a_word_still_matches(
    translations: Pass2PreTranslations,
) -> None:
    # "<hi>Bhāvanābala</hi>nti" must read as one word, "bhāvanābalanti"
    assert translations.find_english(BODY_EXAMPLE) == BODY_ENGLISH


def test_rewritten_example_matches_on_its_opening_words(
    translations: Pass2PreTranslations,
) -> None:
    # the example search turns "…pe…" into "…", which breaks a full match
    example = "bhāvanābalanti bhāventassa uppannaṃ balaṃ … kiñci aññaṃ"
    assert translations.find_english(example) == BODY_ENGLISH


def test_unknown_example_returns_none(translations: Pass2PreTranslations) -> None:
    assert translations.find_english("na kiñci ettha atthi") is None


def test_match_ignores_part_of_a_longer_word(
    translations: Pass2PreTranslations,
) -> None:
    # only the opening four words can match, and the wrong paragraph holds
    # them inside "abhāvanābalanti"; it is read first here
    translations.paragraphs.reverse()
    example = "bhāvanābalanti bhāventassa uppannaṃ balaṃ … kiñci aññaṃ"
    assert translations.find_english(example) == BODY_ENGLISH
