"""Golden-master tests for exporter/tpr/tpr_exporter.py.

Freezes the data-transformation outputs (tpr_data_list, deconstructor_data_list,
spelling entries) against an in-memory db seeded with real rows copied from
dpd.db. Proves the behaviour-preserving refactor (type hints, pathlib, .append,
re.sub->str.replace, except IndexError) reproduces byte-identical output.

Covers: headword `•` branch (no meaning_1), meaning+root branch, the Compound
row rendered for any non-empty compound_type (digits cannot occur in the
column — enforced by db_tests/single/test_allowable_characters.py), root
homonym grouping (<br>-joined) plus the final-root `except IndexError` peek,
and the deconstructor skip-if-headword branch.
"""

import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, DpdHeadword, DpdRoot, Lookup
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
import exporter.tpr.tpr_exporter as tpr

FIXTURE_PATH = Path(__file__).parent / "test_tpr_exporter_fixtures.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _frozen_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tpr, "TODAY", date.fromisoformat(FIXTURE["today"]))


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add_all(DpdHeadword(**row) for row in FIXTURE["hw_dicts"])
    session.add_all(DpdRoot(**row) for row in FIXTURE["root_dicts"])
    session.add_all(Lookup(**row) for row in FIXTURE["decon_dicts"])
    session.add_all(Lookup(**row) for row in FIXTURE["spelling_dicts"])
    session.commit()
    return session


def _make_g(session: Session) -> tpr.GlobalVars:
    g = object.__new__(tpr.GlobalVars)
    g.pth = ProjectPaths()
    g.db_session = session
    g.dpd_db = sorted(
        session.query(DpdHeadword).all(), key=lambda x: pali_sort_key(x.lemma_1)
    )
    return g


def test_generate_tpr_data_matches_frozen() -> None:
    g = _make_g(_build_session())
    tpr.generate_tpr_data(g)
    assert g.tpr_data_list == FIXTURE["expected_tpr_data_list"]


def test_generate_deconstructor_data_matches_frozen() -> None:
    g = _make_g(_build_session())
    g.all_headwords_clean = {FIXTURE["skip_key"]}
    g.deconstructor_data_list = []
    tpr.generate_deconstructor_data(g)
    assert g.deconstructor_data_list == FIXTURE["expected_decon_list"]


def test_add_spelling_mistakes_matches_frozen() -> None:
    g = _make_g(_build_session())
    g.deconstructor_data_list = []
    tpr.add_spelling_mistakes(g)
    assert g.deconstructor_data_list == FIXTURE["expected_spelling_list"]


def test_deconstructor_skips_existing_headword() -> None:
    g = _make_g(_build_session())
    g.all_headwords_clean = {FIXTURE["skip_key"]}
    g.deconstructor_data_list = []
    tpr.generate_deconstructor_data(g)
    assert all(e["word"] != FIXTURE["skip_key"] for e in g.deconstructor_data_list)


def test_root_homonym_grouping_uses_br() -> None:
    g = _make_g(_build_session())
    tpr.generate_tpr_data(g)
    root_entries = [e for e in g.tpr_data_list if e["id"] == 0]
    definitions: list[str] = []
    for entry in root_entries:
        definition = entry["definition"]
        assert isinstance(definition, str)
        definitions.append(definition)
    # the homonym pair (same root_clean) collapses into one <br>-joined block
    assert any("<br>" in definition for definition in definitions)
    # every root block is wrapped and closed exactly once (final-element peek)
    for definition in definitions:
        assert definition.startswith("<div><p>")
        assert definition.endswith("</p></div>")


def test_compound_type_renders_compound_row() -> None:
    g = _make_g(_build_session())
    tpr.generate_tpr_data(g)
    compound_entry = next(
        e for e in g.tpr_data_list if e["word"] == "test_digit_compound 1"
    )
    definition = compound_entry["definition"]
    assert isinstance(definition, str)
    assert ">Compound</th>" in definition


def test_update_download_list_replaces_entry_found_by_url_suffix(
    tmp_path: Path,
) -> None:
    list_path = tmp_path / "download_list.json"
    list_path.write_text(
        json.dumps(
            [
                {"name": "Other Book", "url": "https://example.com/other.zip"},
                {
                    "name": "DPD old release",
                    "url": "https://github.com/bksubhuti/tpr_downloads/raw/master/release_zips/dpd.zip",
                },
            ]
        ),
        encoding="utf-8",
    )
    new_entry = {"name": "DPD new release", "url": "https://cdn.jsdelivr.net/x"}

    tpr._update_download_list(list_path, new_entry, "release_zips/dpd.zip")

    updated_list = json.loads(list_path.read_text(encoding="utf-8"))
    assert updated_list == [
        {"name": "Other Book", "url": "https://example.com/other.zip"},
        new_entry,
    ]


def test_update_download_list_skips_missing_file(tmp_path: Path) -> None:
    list_path = tmp_path / "does_not_exist.json"
    new_entry = {"name": "DPD new release", "url": "https://cdn.jsdelivr.net/x"}

    tpr._update_download_list(list_path, new_entry, "release_zips/dpd.zip")

    assert not list_path.exists()


def test_update_download_list_skips_when_no_entry_matches(tmp_path: Path) -> None:
    list_path = tmp_path / "download_list.json"
    original_list = [{"name": "Other Book", "url": "https://example.com/other.zip"}]
    list_path.write_text(json.dumps(original_list), encoding="utf-8")
    new_entry = {"name": "DPD new release", "url": "https://cdn.jsdelivr.net/x"}

    tpr._update_download_list(list_path, new_entry, "release_zips/dpd.zip")

    assert json.loads(list_path.read_text(encoding="utf-8")) == original_list
