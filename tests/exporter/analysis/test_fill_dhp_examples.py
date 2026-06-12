"""Tests for fill_dhp_examples pure functions."""

import pytest
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from exporter.analysis.example_bolding import (
    bold_component_in_token,
    bold_word_in_verse,
    bold_word_toplevel,
    collect_all_ids,
    find_token_in_apos_verse,
    strip_bold_tags,
)
from tools.paths import ProjectPaths


@pytest.fixture
def db_session() -> Session:
    """Provide a database session for tests."""
    paths = ProjectPaths()
    session = get_db_session(paths.dpd_db_path)
    yield session
    session.close()


class TestStripBoldTags:
    def test_removes_bold_tags(self):
        assert strip_bold_tags("foo <b>bar</b> baz") == "foo bar baz"

    def test_no_tags_unchanged(self):
        assert strip_bold_tags("plain text") == "plain text"


class TestFindTokenInAposVerse:
    def test_token_without_apostrophe_found_as_is(self):
        verse = "viharantaṃ indriyesu"
        assert find_token_in_apos_verse("viharantaṃ", verse) == "viharantaṃ"

    def test_finds_apostrophe_form(self):
        verse = "subh'ānupassiṃ viharantaṃ"
        assert find_token_in_apos_verse("subhānupassiṃ", verse) == "subh'ānupassiṃ"

    def test_finds_sandhi_with_apostrophe(self):
        verse = "bhojanamhi c'āmattaññuṃ kusītaṃ"
        assert find_token_in_apos_verse("cāmattaññuṃ", verse) == "c'āmattaññuṃ"

    def test_rukkhaṃva_form(self):
        verse = "vāto rukkhaṃ'va dubbalaṃ"
        assert find_token_in_apos_verse("rukkhaṃva", verse) == "rukkhaṃ'va"

    def test_not_found_returns_token(self):
        verse = "manasā ce paduṭṭhena"
        assert find_token_in_apos_verse("nothere", verse) == "nothere"


class TestBoldComponentInToken:
    def test_direct_match(self, db_session: Session):
        assert (
            bold_component_in_token("viharantaṃ", "viharantaṃ", 999999, db_session)
            == "<b>viharantaṃ</b>"
        )

    def test_strip_m_match(self, db_session: Session):
        # mattaṃ → matta is first component of compound
        assert (
            bold_component_in_token(
                "c'āmattaññuṃ", "mattaṃ", 999999, db_session, is_first_component=True
            )
            == "c'ā<b>matta</b>ññuṃ"
        )

    def test_compound_prefix_no_apostrophe(self, db_session: Session):
        # hīna is first component of hīnavīriyaṃ
        assert (
            bold_component_in_token(
                "hīnavīriyaṃ", "hīna", 999999, db_session, is_first_component=True
            )
            == "<b>hīna</b>vīriyaṃ"
        )

    def test_apostrophe_split_left_subha(self, db_session: Session):
        # subhaṃ → consonant frame subh → matches left part 'subh'
        assert (
            bold_component_in_token("subh'ānupassiṃ", "subhaṃ", 999999, db_session)
            == "<b>subh</b>'ānupassiṃ"
        )

    def test_apostrophe_split_right_anupassi(self, db_session: Session):
        # anupassī → consonant frame anupass → doesn't match left 'subh' → bold right
        assert (
            bold_component_in_token("subh'ānupassiṃ", "anupassī", 999999, db_session)
            == "subh'<b>ānupassiṃ</b>"
        )

    def test_apostrophe_split_left_ca(self, db_session: Session):
        # ca → consonant frame c → matches left part 'c'
        assert (
            bold_component_in_token("c'āmattaññuṃ", "ca", 999999, db_session)
            == "<b>c</b>'āmattaññuṃ"
        )

    def test_apostrophe_split_right_amatta(self, db_session: Session):
        # amattaññuṃ → consonant frame amattañ → doesn't match left 'c' → bold right
        assert (
            bold_component_in_token("c'āmattaññuṃ", "amattaññuṃ", 999999, db_session)
            == "c'<b>āmattaññuṃ</b>"
        )

    def test_rukkham_direct_match(self, db_session: Session):
        # rukkhaṃ is first component of compound with apostrophe
        assert (
            bold_component_in_token(
                "rukkhaṃ'va", "rukkhaṃ", 999999, db_session, is_first_component=True
            )
            == "<b>rukkhaṃ</b>'va"
        )

    def test_iva_right_side(self, db_session: Session):
        # iva → consonant frame iv → doesn't match left 'rukkhaṃ' → bold right
        assert (
            bold_component_in_token("rukkhaṃ'va", "iva", 999999, db_session)
            == "rukkhaṃ'<b>va</b>"
        )

    def test_fallback_whole_token(self, db_session: Session):
        # No match possible, no apostrophe → bold whole token
        result = bold_component_in_token("sometoken", "xyzq", 999999, db_session)
        assert result == "<b>sometoken</b>"


class TestBoldWordInVerse:
    def test_simple_word(self, db_session: Session):
        verse = "manasā ce paduṭṭhena"
        assert (
            bold_word_in_verse(verse, "manasā", "manasā", 999999, db_session)
            == "<b>manasā</b> ce paduṭṭhena"
        )

    def test_multiple_occurrences(self, db_session: Session):
        verse = "akkocchi maṃ avadhi maṃ"
        assert (
            bold_word_in_verse(verse, "maṃ", "maṃ", 999999, db_session)
            == "akkocchi <b>maṃ</b> avadhi <b>maṃ</b>"
        )

    def test_apostrophe_token_left_bold(self, db_session: Session):
        verse = "subh'ānupassiṃ viharantaṃ"
        result = bold_word_in_verse(
            verse, "subh'ānupassiṃ", "subhaṃ", 999999, db_session
        )
        assert result == "<b>subh</b>'ānupassiṃ viharantaṃ"

    def test_apostrophe_token_right_bold(self, db_session: Session):
        verse = "subh'ānupassiṃ viharantaṃ"
        result = bold_word_in_verse(
            verse, "subh'ānupassiṃ", "anupassī", 999999, db_session
        )
        assert result == "subh'<b>ānupassiṃ</b> viharantaṃ"

    def test_matta_in_camattannhum(self, db_session: Session):
        verse = "bhojanamhi c'āmattaññuṃ"
        result = bold_word_in_verse(
            verse, "c'āmattaññuṃ", "mattaṃ", 999999, db_session, is_first_component=True
        )
        assert result == "bhojanamhi c'ā<b>matta</b>ññuṃ"

    def test_no_match_returns_original(self, db_session: Session):
        verse = "akkocchi maṃ avadhi maṃ"
        assert (
            bold_word_in_verse(verse, "notinverse", "notinverse", 999999, db_session)
            == verse
        )


class TestCollectAllIds:
    def test_simple_option_no_components(self):
        option = {
            "key": "123_0",
            "id": 123,
            "pali": "dhammā",
            "ai_score": 10,
            "components": [],
        }
        assert collect_all_ids(option, "dhammā") == [
            (123, "dhammā", "dhammā", False, True)
        ]

    def test_decon_key_skipped(self):
        option = {
            "key": "decon_foo_0",
            "id": "",
            "pali": "foo",
            "ai_score": 10,
            "components": [],
        }
        assert collect_all_ids(option, "foo") == []

    def test_recurses_into_compound_components(self):
        option = {
            "key": "71345_3",
            "id": 71345,
            "pali": "hīnavīriyaṃ",
            "ai_score": 10,
            "compound_type": "kammadhāraya",
            "components": [
                [
                    {
                        "key": "71324_0",
                        "id": 71324,
                        "pali": "hīna",
                        "ai_score": 0,
                        "compound_type": "",
                        "components": [],
                    }
                ],
                [
                    {
                        "key": "69911_0",
                        "id": 69911,
                        "pali": "vīriya",
                        "ai_score": 0,
                        "compound_type": "",
                        "components": [],
                    }
                ],
            ],
        }
        results = collect_all_ids(option, "hīnavīriyaṃ")
        assert [r[0] for r in results] == [71345, 71324, 69911]

    def test_decon_top_still_recurses_children(self):
        option = {
            "key": "decon_cāmattaññuṃ_1",
            "id": "",
            "pali": "cāmattaññuṃ",
            "ai_score": 10,
            "components": [
                [
                    {
                        "key": "25662_default",
                        "id": 25662,
                        "pali": "ca",
                        "ai_score": 10,
                        "components": [],
                    }
                ],
                [
                    {
                        "key": "8487_2",
                        "id": 8487,
                        "pali": "amattaññuṃ",
                        "ai_score": 10,
                        "components": [],
                    }
                ],
            ],
        }
        ids = [r[0] for r in collect_all_ids(option, "cāmattaññuṃ")]
        assert 25662 in ids and 8487 in ids

    def test_deeply_nested(self):
        option = {
            "key": "8487_2",
            "id": 8487,
            "pali": "amattaññuṃ",
            "ai_score": 10,
            "compound_type": "kammadhāraya",
            "components": [
                [
                    {
                        "key": "35345_0",
                        "id": 35345,
                        "pali": "na",
                        "ai_score": 0,
                        "compound_type": "",
                        "components": [],
                    }
                ],
                [
                    {
                        "key": "50951_0",
                        "id": 50951,
                        "pali": "mattaññū",
                        "ai_score": 0,
                        "compound_type": "kammadhāraya",
                        "components": [
                            [
                                {
                                    "key": "50938_0",
                                    "id": 50938,
                                    "pali": "mattaṃ",
                                    "ai_score": 0,
                                    "compound_type": "",
                                    "components": [],
                                }
                            ],
                            [
                                {
                                    "key": "28965_0",
                                    "id": 28965,
                                    "pali": "ñū",
                                    "ai_score": 0,
                                    "compound_type": "",
                                    "components": [],
                                }
                            ],
                        ],
                    }
                ],
            ],
        }
        assert [r[0] for r in collect_all_ids(option, "amattaññuṃ")] == [
            8487,
            35345,
            50951,
            50938,
            28965,
        ]

    def test_collect_all_ids_no_recurse_uttara_type(self):
        # uttara: adj, no compound_type — its sub-components (ud, tara) must NOT be collected
        option = {
            "key": "14659_0",
            "id": 14659,
            "pali": "uttara",
            "ai_score": 0,
            "compound_type": "",
            "pos": "adj",
            "components": [
                [
                    {
                        "key": "missing_ud",
                        "id": "",
                        "pali": "ud",
                        "compound_type": "",
                        "ai_score": 0,
                        "components": [],
                    }
                ],
                [
                    {
                        "key": "30078_0",
                        "id": 30078,
                        "pali": "tara",
                        "compound_type": "",
                        "ai_score": 0,
                        "components": [],
                    }
                ],
            ],
        }
        ids = [r[0] for r in collect_all_ids(option, "uttara")]
        assert ids == [14659]
        assert 30078 not in ids  # tara must not appear

    def test_collect_all_ids_anuttara_atomic_no_components(self):
        # Post-analyzer-fix: anuttara has components=[] → only anuttara ID returned
        option = {
            "key": "4524_0",
            "id": 4524,
            "pali": "anuttara",
            "ai_score": 10,
            "compound_type": "kammadhāraya",
            "components": [],
        }
        assert collect_all_ids(option, "anuttaraṃ") == [
            (4524, "anuttara", "anuttaraṃ", False, True)
        ]

    def test_collect_all_ids_akatapāpa_breaks(self):
        # akatapāpa: na + katapāpa where katapāpa has compound_type → breakdown kept
        akatapāpa_id = 99000
        katapāpa_id = 99001
        kata_id = 99002
        pāpa_id = 99003
        na_id = 35345
        option = {
            "key": f"{akatapāpa_id}_0",
            "id": akatapāpa_id,
            "pali": "akatapāpa",
            "ai_score": 10,
            "compound_type": "kammadhāraya",
            "components": [
                [
                    {
                        "key": f"{na_id}_0",
                        "id": na_id,
                        "pali": "na",
                        "compound_type": "",
                        "ai_score": 0,
                        "components": [],
                    }
                ],
                [
                    {
                        "key": f"{katapāpa_id}_0",
                        "id": katapāpa_id,
                        "pali": "katapāpa",
                        "compound_type": "kammadhāraya",
                        "ai_score": 0,
                        "components": [
                            [
                                {
                                    "key": f"{kata_id}_0",
                                    "id": kata_id,
                                    "pali": "kata",
                                    "compound_type": "",
                                    "ai_score": 0,
                                    "components": [],
                                }
                            ],
                            [
                                {
                                    "key": f"{pāpa_id}_0",
                                    "id": pāpa_id,
                                    "pali": "pāpa",
                                    "compound_type": "",
                                    "ai_score": 0,
                                    "components": [],
                                }
                            ],
                        ],
                    }
                ],
            ],
        }
        ids = [r[0] for r in collect_all_ids(option, "akatapāpo")]
        assert ids == [akatapāpa_id, na_id, katapāpa_id, kata_id, pāpa_id]


class TestBoldWordToplevel:
    def test_plain_token(self):
        assert bold_word_toplevel("manasā") == "<b>manasā</b>"

    def test_apostrophe_token(self):
        assert bold_word_toplevel("n'ābhikīrati") == "<b>n'ābhikīrati</b>"


class TestBoldWordInVerseTopLevel:
    def test_toplevel_bolds_whole_apostrophe_token(self, db_session: Session):
        verse = "n'ābhikīrati paṇḍito"
        result = bold_word_in_verse(
            verse, "n'ābhikīrati", "nābhikīrati", 36392, db_session, is_top_level=True
        )
        assert result == "<b>n'ābhikīrati</b> paṇḍito"

    def test_toplevel_plain_token(self, db_session: Session):
        verse = "manasā ce paduṭṭhena"
        result = bold_word_in_verse(
            verse, "manasā", "manasā", 999999, db_session, is_top_level=True
        )
        assert result == "<b>manasā</b> ce paduṭṭhena"


class TestBoldComponentStemMatch:
    def test_stem_match_compound_component(self, db_session: Session):
        # parakkama (lemma, short a) is component of daḷhaparakkamā (inflected, long ā)
        # direct match fails; stem 'parakkam' must match and bold the suffix portion
        assert (
            bold_component_in_token("daḷhaparakkamā", "parakkama", 999999, db_session)
            == "daḷha<b>parakkamā</b>"
        )
