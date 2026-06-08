"""Golden-master tests for db/grammar/grammar_to_lookup.py.

Freezes the current output of modify_pos() and generate_grammar_data() against real
DB data so a behaviour-preserving refactor can be proven byte-identical. Uses a real
db session only for the InflectionTemplates lookup; no mocks.
"""

import json
from pathlib import Path

from db.db_helpers import get_db_session
from db.grammar.grammar_to_lookup import (
    GlobalVars,
    generate_grammar_data,
    modify_pos,
)
from db.models import DpdHeadword

FIXTURE_PATH = Path(__file__).parent / "test_grammar_to_lookup_fixtures.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _make_headword(data: dict) -> DpdHeadword:
    # lemma_clean is a cached_property derived from lemma_1, so it is not passed.
    return DpdHeadword(
        id=data["id"],
        lemma_1=data["lemma_1"],
        stem=data["stem"],
        pattern=data["pattern"],
        pos=data["pos"],
        grammar=data["grammar"],
    )


def _build_globalvars() -> GlobalVars:
    g = object.__new__(GlobalVars)
    g.db_session = get_db_session(Path("dpd.db"))
    g.nouns = FIXTURE["nouns"]
    g.verbs = FIXTURE["verbs"]
    g.all_words_set = set(FIXTURE["all_words_set"])
    g.db = [_make_headword(d) for d in FIXTURE["inputs"]]
    return g


def test_modify_pos_does_not_mutate_headwords() -> None:
    """Neither modify_pos nor generate_grammar_data must write back to ORM objects."""
    g = _build_globalvars()
    original_pos = [hw.pos for hw in g.db]
    original_stem = [hw.stem for hw in g.db]
    pos_override = modify_pos(g.db, g.nouns, g.verbs)
    generate_grammar_data(g, pos_override)
    assert [hw.pos for hw in g.db] == original_pos
    assert [hw.stem for hw in g.db] == original_stem


def test_modify_pos_matches_fixture() -> None:
    g = _build_globalvars()
    pos_override = modify_pos(g.db, g.nouns, g.verbs)
    effective_pos = [pos_override.get(hw.id, hw.pos) for hw in g.db]
    assert effective_pos == FIXTURE["expected_pos"]


def test_generate_grammar_data_matches_fixture() -> None:
    g = _build_globalvars()
    pos_override = modify_pos(g.db, g.nouns, g.verbs)
    generate_grammar_data(g, pos_override)
    produced = json.loads(json.dumps(g.grammar_data, ensure_ascii=False))
    assert produced == FIXTURE["expected_grammar_data"]


def test_bang_and_indeclinable_stems_produce_no_entries() -> None:
    """! stems and '-' stems must never contribute a source lemma."""
    g = _build_globalvars()
    pos_override = modify_pos(g.db, g.nouns, g.verbs)
    generate_grammar_data(g, pos_override)
    sources = {entry[0] for entries in g.grammar_data.values() for entry in entries}
    bang_or_dash = {
        d["lemma_clean"]
        for d in FIXTURE["inputs"]
        if "!" in d["stem"] or d["stem"] == "-"
    }
    assert sources.isdisjoint(bang_or_dash)


def test_pattern_without_template_yields_no_entries() -> None:
    """A real stem whose pattern has no InflectionTemplate adds nothing (None branch)."""
    g = object.__new__(GlobalVars)
    g.db_session = get_db_session(Path("dpd.db"))
    g.nouns = FIXTURE["nouns"]
    g.verbs = FIXTURE["verbs"]
    g.all_words_set = {"xyzabc", "xyzabci"}
    hw = _make_headword(
        {
            "id": -1,
            "lemma_1": "xyzabc 1",
            "lemma_clean": "xyzabc",
            "stem": "xyzab",
            "pattern": "no such pattern",
            "pos": "masc",
            "grammar": "masc",
        }
    )
    g.db = [hw]
    generate_grammar_data(g, {})
    assert g.grammar_data == {}
