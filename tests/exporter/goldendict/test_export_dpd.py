"""Tests for export_dpd.py."""

from multiprocessing import get_context

import pytest

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyRoot, FamilyWord
from exporter.goldendict.export_dpd import render_pali_word_dpd_html
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


def test_crashing_worker_has_nonzero_exit_code():
    ctx = get_context("spawn")
    p = ctx.Process(target=_crashing_worker)
    p.start()
    p.join()
    assert p.exitcode != 0


def _crashing_worker():
    raise RuntimeError("simulated worker crash")
