"""Tests for export_dpd.py."""

import os
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool

import pytest

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyRoot, FamilyWord
from exporter.goldendict.export_dpd import (
    _dedupe_keys,
    _iter_dpd_row_pages,
    _lookup_family_compounds,
    _lookup_family_idioms,
    _lookup_family_set,
    render_pali_word_dpd_html,
)
from db.models import FamilyCompound, FamilyIdiom, FamilySet
from exporter.jinja2_env import get_jinja2_env
from tools.date_and_time import year_month_day_dash
from tools.exporter_functions import (
    get_family_compounds,
    get_family_idioms,
    get_family_set,
)
from tools.paths import ProjectPaths

TEST_LEMMAS = ["akaṅkhī", "namo", "mettasutta 1"]


@pytest.fixture(scope="module")
def render_data():
    pth = ProjectPaths()
    jinja_env = get_jinja2_env("exporter/goldendict/templates")
    return {
        "pth": pth,
        "jinja_env": jinja_env,
        "speech_marks": {},
        "cf_set": set(),
        "idioms_set": set(),
        "show_id": False,
    }


@pytest.fixture(scope="module")
def db_session():
    pth = ProjectPaths()
    return get_db_session(pth.dpd_db_path)


def _build_db_parts(db, lemma: str) -> dict:
    row = (
        db.query(DpdHeadword, FamilyRoot, FamilyWord)
        .outerjoin(
            FamilyRoot, DpdHeadword.root_family_key == FamilyRoot.root_family_key
        )
        .outerjoin(FamilyWord, DpdHeadword.family_word == FamilyWord.word_family)
        .filter(DpdHeadword.lemma_1 == lemma)
        .first()
    )
    assert row is not None, f"headword '{lemma}' not found in db"
    pw, fr, fw = row
    return {
        "pali_word": pw,
        "pali_root": pw.rt,
        "family_root": fr,
        "family_word": fw,
        "family_compounds": get_family_compounds(pw),
        "family_idioms": get_family_idioms(pw),
        "family_set": get_family_set(pw),
        "sutta_info": pw.su,
    }


@pytest.mark.parametrize("lemma", TEST_LEMMAS)
def test_render_pali_word_dpd_html(lemma, db_session, render_data):
    db_parts = _build_db_parts(db_session, lemma)
    pw: DpdHeadword = db_parts["pali_word"]
    entry, size_dict = render_pali_word_dpd_html(db_parts, render_data)

    assert entry.word == lemma
    html = entry.definition_html
    assert html.startswith("<!DOCTYPE html>")
    assert pw.pos in html
    assert year_month_day_dash() in html

    assert size_dict["dpd_header"] > 0
    assert size_dict["dpd_summary"] == len(pw.meaning_combo_html)
    assert size_dict["dpd_synonyms"] > 0

    synonyms = set(entry.synonyms)
    assert str(pw.id) in synonyms
    assert set(pw.inflections_list_all) <= synonyms
    assert set(pw.family_set_list) <= synonyms


def test_sutta_codes_in_synonyms(db_session, render_data):
    """Words with needs_sutta_info_button should include sutta codes in synonyms."""
    db_parts = _build_db_parts(db_session, "mettasutta 1")
    entry, _ = render_pali_word_dpd_html(db_parts, render_data)
    assert "AN7.62" in entry.synonyms


def test_dedupe_keys_preserves_first_occurrence_order():
    assert _dedupe_keys(["nicca", "nicca", "ucchādana", "bhedana"]) == [
        "nicca",
        "ucchādana",
        "bhedana",
    ]
    assert _dedupe_keys([]) == []
    assert _dedupe_keys(["a", "b", "a"]) == ["a", "b"]


def test_preloaded_family_lookups_match_reference(db_session):
    """New dict lookups reproduce the old get_family_* query results, including
    the duplicate-family-name edge case (id 4165 has 'nicca' twice)."""
    from tools.exporter_functions import (
        get_family_compounds,
        get_family_idioms,
        get_family_set,
    )

    fc_map = {x.compound_family: x for x in db_session.query(FamilyCompound).all()}
    fi_map = {x.idiom: x for x in db_session.query(FamilyIdiom).all()}
    fs_map = {x.set: x for x in db_session.query(FamilySet).all()}

    lemmas = ["aniccucchādanaparimaddanabhedana", "akaṅkhī", "namo", "mettasutta 1"]
    for lemma in lemmas:
        pw = db_session.query(DpdHeadword).filter(DpdHeadword.lemma_1 == lemma).one()
        assert [x.compound_family for x in _lookup_family_compounds(pw, fc_map)] == [
            x.compound_family for x in get_family_compounds(pw)
        ]
        assert [x.idiom for x in _lookup_family_idioms(pw, fi_map)] == [
            x.idiom for x in get_family_idioms(pw)
        ]
        assert [x.set for x in _lookup_family_set(pw, fs_map)] == [
            x.set for x in get_family_set(pw)
        ]


def test_default_page_is_single_lemma_ordered_page(db_session):
    """High-mem mode yields one page of all requested rows, ordered by lemma_1."""
    limit = 250
    pages = list(
        _iter_dpd_row_pages(db_session, data_limit=limit, low_mem=False, page_size=100)
    )
    assert len(pages) == 1
    got_ids = [pw.id for pw, _, _ in pages[0]]

    expected_ids = [
        row.id
        for row in db_session.query(DpdHeadword)
        .order_by(DpdHeadword.lemma_1)
        .limit(limit)
        .all()
    ]
    assert got_ids == expected_ids


def test_keyset_pages_match_ordered_by_id(db_session):
    """Low-mem keyset paging covers the same rows, in id order, no dupes/gaps."""
    limit = 250
    page_size = 100
    pages = list(
        _iter_dpd_row_pages(
            db_session, data_limit=limit, low_mem=True, page_size=page_size
        )
    )
    # 250 rows in pages of 100 -> 100, 100, 50
    assert [len(p) for p in pages] == [100, 100, 50]

    keyset_ids = [pw.id for page in pages for pw, _, _ in page]
    assert len(keyset_ids) == limit
    assert len(set(keyset_ids)) == limit

    expected_ids = [
        row.id
        for row in db_session.query(DpdHeadword)
        .order_by(DpdHeadword.id)
        .limit(limit)
        .all()
    ]
    assert keyset_ids == expected_ids


def _raising_worker(_batch):
    raise RuntimeError("simulated worker exception")


def _self_killing_worker(_batch):
    os._exit(1)  # abrupt death without an exception, mimics an OOM kill


def test_worker_exception_propagates_to_parent():
    """A worker exception surfaces when the result is consumed, failing loudly."""
    with ProcessPoolExecutor(max_workers=1) as pool:
        with pytest.raises(RuntimeError):
            list(pool.map(_raising_worker, [[]]))


def test_killed_worker_raises_broken_pool():
    """A worker killed outright (e.g. OOM) raises BrokenProcessPool rather than
    hanging — the same loud-failure guarantee the old exitcode check gave."""
    with ProcessPoolExecutor(max_workers=1) as pool:
        with pytest.raises(BrokenProcessPool):
            list(pool.map(_self_killing_worker, [[]]))
