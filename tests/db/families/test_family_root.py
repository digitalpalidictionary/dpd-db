"""Characterization tests for db/families/family_root.py.

Fixtures frozen from real DB output before any refactor. Tests assert the
refactored code produces byte-identical results on a representative sample
of three root families (√kaṅkh 1, √kaṅkh 2, √kath).
"""

import json
from pathlib import Path

import pytest
from sqlalchemy.orm import joinedload

from db.db_helpers import get_db_session
from db.families.family_root import (
    compile_rf_html,
    make_anki_data,
    make_root_header,
    make_roots_family_dict_and_bases_dict,
)
from db.models import DpdHeadword
from tools.pali_sort_key import pali_sort_key

FIXTURE_PATH = Path(__file__).parent / "test_family_root_fixtures.json"
DB_PATH = Path("dpd.db")


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sample_headwords(fixtures: dict) -> list[DpdHeadword]:
    db = get_db_session(DB_PATH)
    lemmas = set(fixtures["sample_lemmas"])
    hw_list = (
        db.query(DpdHeadword)
        .options(joinedload(DpdHeadword.rt))
        .filter(DpdHeadword.lemma_1.in_(lemmas))
        .all()
    )
    hw_list = sorted(hw_list, key=lambda x: pali_sort_key(x.lemma_1))
    db.close()
    return hw_list


def _serialize_rf_dict(d: dict) -> dict:
    return {
        k: {
            "root_key": v["root_key"],
            "root_family": v["root_family"],
            "root_meaning": v["root_meaning"],
            "headwords": v["headwords"],
            "html": v["html"],
            "count": v["count"],
            "data": [list(row) for row in v["data"]],
            "anki": [list(row) for row in v["anki"]],
        }
        for k, v in d.items()
    }


def test_make_roots_family_dict_and_bases_dict(
    sample_headwords: list[DpdHeadword], fixtures: dict
) -> None:
    expected_rf = fixtures["make_roots_family_dict_and_bases_dict"]["rf_dict"]
    expected_bases = fixtures["make_roots_family_dict_and_bases_dict"]["bases_dict"]

    rf_dict, bases_dict = make_roots_family_dict_and_bases_dict(sample_headwords)

    assert _serialize_rf_dict(rf_dict) == expected_rf
    assert {k: sorted(v) for k, v in bases_dict.items()} == expected_bases


def test_compile_rf_html(sample_headwords: list[DpdHeadword], fixtures: dict) -> None:
    expected = fixtures["compile_rf_html"]

    rf_dict, _ = make_roots_family_dict_and_bases_dict(sample_headwords)
    result = compile_rf_html(sample_headwords, rf_dict)

    assert _serialize_rf_dict(result) == expected


def test_make_root_header(sample_headwords: list[DpdHeadword], fixtures: dict) -> None:
    expected = fixtures["make_root_header"]

    rf_dict, _ = make_roots_family_dict_and_bases_dict(sample_headwords)
    rf_dict = compile_rf_html(sample_headwords, rf_dict)

    for rf_key in rf_dict:
        assert make_root_header(rf_dict, rf_key) == expected[rf_key]


def test_make_anki_data(sample_headwords: list[DpdHeadword], fixtures: dict) -> None:
    expected = fixtures["make_anki_data"]

    rf_dict, _ = make_roots_family_dict_and_bases_dict(sample_headwords)
    rf_dict = compile_rf_html(sample_headwords, rf_dict)
    result = make_anki_data(rf_dict)

    assert [list(row) for row in result] == expected
