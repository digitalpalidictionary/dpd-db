"""Golden-master tests for scripts/build/api_ca_eva_iti_iva_hi.py.

Fixtures were captured from the current (pre-refactor) code against real dpd.db
data. The functions are run on transient, session-less ORM objects with a dummy
commit, so no database write occurs. The refactor must reproduce byte-identical
per-headword output.
"""

import json
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

from db.models import DpdHeadword, Lookup
from scripts.build.api_ca_eva_iti_iva_hi import (
    GlobalVars,
    add_apicaevaitihi_to_inflections,
    make_apicaevaitihi_dict,
)

FIXTURE_PATH = Path(__file__).parent / "test_api_ca_eva_iti_iva_hi_fixtures.json"
FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _make_dict() -> dict[str, list[str]]:
    g = object.__new__(GlobalVars)
    g.lookup_db = [
        Lookup(lookup_key=item["lookup_key"], deconstructor=item["deconstructor"])
        for item in FIXTURES["make"]["inputs"]
    ]
    g.lookup_db_len = len(g.lookup_db)
    g.apicaevaitihi_dict = defaultdict(list)
    make_apicaevaitihi_dict(g)
    return {k: sorted(v) for k, v in g.apicaevaitihi_dict.items()}


def test_make_apicaevaitihi_dict_matches_fixture() -> None:
    assert _make_dict() == FIXTURES["make"]["output"]


def test_make_skips_non_matching_deconstructions() -> None:
    result = _make_dict()
    flat_values = {v for vals in result.values() for v in vals}
    assert "twoplus" not in flat_values
    assert "notparticle" not in flat_values


def test_add_apicaevaitihi_to_inflections_matches_fixture() -> None:
    sandhi_dict: defaultdict[str, list[str]] = defaultdict(list)
    for key, values in FIXTURES["add"]["dict"].items():
        sandhi_dict[key].extend(values)

    g = object.__new__(GlobalVars)
    g.headwords_db = [
        DpdHeadword(
            lemma_1=item["lemma_1"],
            inflections=item["inflections"],
            inflections_api_ca_eva_iti=item["inflections_api_ca_eva_iti"],
        )
        for item in FIXTURES["add"]["headwords"]
    ]
    g.headwords_db_len = len(g.headwords_db)
    g.apicaevaitihi_dict = sandhi_dict
    g.db_session = SimpleNamespace(commit=lambda: None)
    add_apicaevaitihi_to_inflections(g)

    output = {hw.lemma_1: hw.inflections_api_ca_eva_iti for hw in g.headwords_db}
    assert output == FIXTURES["add"]["output"]
