"""Golden-master tests for exporter/tbw/tbw_exporter.py.

Real-data characterization tests (no mocks). The fixture freezes the structures
produced by the pre-refactor pipeline run over a curated set of real dpd.db rows
with a controlled word_set. The refactor is behaviour-preserving, so every
structure (and its key order, which the emitted .js depends on) must reproduce
byte-for-byte.

Curated data exercises each branch: id=1 'a 1.1' carries '(gram)' (test2
exclusion); ids 2/3/4 share inflection 'a' (multi-headword append); the
'akakkasāti' split feeds 'akakkasa' (the deconstructed_splits_set test1 branch);
deconstructor/spelling rows cover matched, skipped, new, and append paths.
"""

import json
from pathlib import Path

import pytest

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths

import exporter.tbw.tbw_exporter as tbw

FIXTURE_PATH = Path(__file__).parent / "test_tbw_exporter_fixtures.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
INPUTS = FIXTURE["inputs"]


@pytest.fixture(scope="module")
def db():
    session = get_db_session(ProjectPaths().dpd_db_path)
    yield session
    session.close()


def _fresh_g(db, word_set: list[str]) -> tbw.GlobalVars:
    g = object.__new__(tbw.GlobalVars)
    hws = db.query(DpdHeadword).filter(DpdHeadword.id.in_(INPUTS["headword_ids"])).all()
    g.dpd_db = sorted(hws, key=lambda x: pali_sort_key(x.lemma_1))
    g.deconstructor_db = [
        db.query(Lookup).filter(Lookup.lookup_key == k).first()
        for k in INPUTS["dec_keys"]
    ]
    g.spelling_db = [
        db.query(Lookup).filter(Lookup.lookup_key == k).first()
        for k in INPUTS["spell_keys"]
    ]
    g.variants_db = []
    g.word_set = set(word_set)
    g.deconstructed_splits_set = set()
    g.matched_set = set()
    g.i2h_dict = {}
    g.unmatched_set = set()
    g.headwords_set = set()
    g.dpd_dict = {}
    g.deconstructor_dict = {}
    return g


def test_pipeline_chain_matches_frozen(db) -> None:
    g = _fresh_g(db, INPUTS["word_set"])
    tbw.generate_deconstructed_word_set(g)
    tbw.generate_i2h_dict(g)
    tbw.sort_i2h_dict(g)
    tbw.generate_unmatched_word_set(g)
    tbw.generate_ebt_headwords_set(g)
    tbw.generate_dpd_ebt_dict(g)
    tbw.generate_deconstructor_dict(g)
    tbw.deconstructor_dict_add_spelling_mistakes(g)
    tbw.sort_deconstructor_dict(g)

    chain = FIXTURE["chain"]
    assert sorted(g.deconstructed_splits_set) == chain["deconstructed_splits_set"]
    assert sorted(g.matched_set) == chain["matched_set"]
    assert sorted(g.unmatched_set) == chain["unmatched_set"]
    assert sorted(g.headwords_set) == chain["headwords_set"]
    # dicts: value equality AND key order (the emitted .js preserves insertion order)
    assert g.i2h_dict == chain["i2h_dict"]
    assert list(g.i2h_dict) == list(chain["i2h_dict"])
    assert g.dpd_dict == chain["dpd_dict"]
    assert list(g.dpd_dict) == list(chain["dpd_dict"])
    assert g.deconstructor_dict == chain["deconstructor_dict"]
    assert list(g.deconstructor_dict) == list(chain["deconstructor_dict"])


def test_spelling_append_branch(db) -> None:
    """spelling key already present in deconstructor_dict -> '<br>' append."""
    g = _fresh_g(db, ["aniruddho"])
    g.deconstructor_dict = {"aniruddho": "SEED"}
    tbw.deconstructor_dict_add_spelling_mistakes(g)
    assert g.deconstructor_dict == FIXTURE["spelling_append"]
