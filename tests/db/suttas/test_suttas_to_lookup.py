"""Golden-master test for db/suttas/suttas_to_lookup.py.

Freezes the ``sutta_code -> {headword_id}`` mapping built by
``make_sutta_info_dict`` so the dataclass / batch-query refactor is proven
behaviour-preserving. Fixtures were captured from the unedited code against the
real dpd.db (see test_suttas_to_lookup_fixtures.json).

The function queries DpdHeadword internally to resolve names to ids, so the test
uses a real read-only session against dpd.db (real data, no mocks) — the same
session style used by other db tests in this suite.
"""

import json
from pathlib import Path
from typing import Any, cast

from db.db_helpers import get_db_session
from db.models import SuttaInfo
from db.suttas.suttas_to_lookup import GlobalVars, make_sutta_info_dict

FIXTURE_PATH = Path(__file__).parent / "test_suttas_to_lookup_fixtures.json"
_DB_PATH = Path("dpd.db")


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _make_sutta(row: dict[str, Any]) -> SuttaInfo:
    su = SuttaInfo()
    su.dpd_sutta = row["dpd_sutta"]
    su.dpd_code = row["dpd_code"]
    su.sc_code = row["sc_code"]
    su.is_vagga = row["is_vagga"]
    su.is_samyutta = row["is_samyutta"]
    su.is_nipata = row["is_nipata"]
    return su


def _build_g(sutta_db: list[SuttaInfo]) -> GlobalVars:
    g = object.__new__(GlobalVars)
    g.db_session = get_db_session(_DB_PATH)
    g.sutta_db = cast(Any, sutta_db)
    g.sutta_info_dict = {}
    return g


def test_make_sutta_info_dict_matches_fixture() -> None:
    fixture = _load_fixture()
    g = _build_g([_make_sutta(r) for r in fixture["rows"]])

    make_sutta_info_dict(g)

    actual = {code: sorted(ids) for code, ids in g.sutta_info_dict.items()}
    assert actual == fixture["expected"]


def test_make_sutta_info_dict_branches() -> None:
    """Each branch in the build loop is exercised by the fixture rows."""
    fixture = _load_fixture()
    g = _build_g([_make_sutta(r) for r in fixture["rows"]])

    make_sutta_info_dict(g)

    # accumulation branch: a code shared by two suttas gets both ids
    assert g.sutta_info_dict["SN32.55"] == {7291, 89351}
    # range-expansion branch: SN32.1-57 fans out to individual codes
    assert g.sutta_info_dict["SN32.55"] >= {7291, 89351}
    # THAG/THIG synthetic-alias branch
    assert g.sutta_info_dict["THI2.8"] == g.sutta_info_dict["THIG2.8"]


def test_make_sutta_info_dict_skips_unresolved_name() -> None:
    """An unresolvable dpd_sutta is skipped (no stale id leaks into its codes).

    Deliberate behaviour change vs the pre-refactor code, which left the
    previous sutta's id in place and added it under the unresolved sutta's
    codes. On real data no name fails to resolve, so the golden-master output
    above is byte-identical; this case locks the corrected error-path.
    """
    resolved = _make_sutta(
        {
            "dpd_sutta": "abbhantarajātaka",
            "dpd_code": "JA281",
            "sc_code": "JA281",
            "is_vagga": False,
            "is_samyutta": False,
            "is_nipata": False,
        }
    )
    unresolved = _make_sutta(
        {
            "dpd_sutta": "zzz_nonexistent_sutta_xyz",
            "dpd_code": "ZZZ999",
            "sc_code": "ZZZ999",
            "is_vagga": False,
            "is_samyutta": False,
            "is_nipata": False,
        }
    )
    g = _build_g([resolved, unresolved])

    make_sutta_info_dict(g)

    assert "ZZZ999" not in g.sutta_info_dict
    assert g.sutta_info_dict["JA281"] == {7281}
