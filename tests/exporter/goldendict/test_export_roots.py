"""Golden-master tests for exporter/goldendict/export_roots.py.

Freezes generate_root_html's output (per-root definition html, synonyms and
rendered sizes) against an in-memory db seeded with real DpdRoot/FamilyRoot rows
copied from dpd.db. Covers the multi-family, few-family and niggahita-synonym
(ṃ in root and in family) render branches.
"""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, DpdRoot, FamilyRoot
from tools.paths import ProjectPaths
from exporter.goldendict.export_roots import generate_root_html

FIXTURE_PATH = Path(__file__).parent / "test_export_roots_fixtures.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add_all(DpdRoot(**row) for row in FIXTURE["root_rows"])
    session.add_all(FamilyRoot(**row) for row in FIXTURE["fr_rows"])
    session.commit()
    return session


def _run() -> tuple[list, dict]:
    session = _build_session()
    entries, size_dict = generate_root_html(
        session, ProjectPaths(), FIXTURE["roots_count_dict"]
    )
    return entries, size_dict


def test_generate_root_html_matches_frozen_entries() -> None:
    entries, _ = _run()
    produced = [
        {
            "word": e.word,
            "definition_html": e.definition_html,
            "synonyms": sorted(e.synonyms),
        }
        for e in entries
    ]
    assert produced == FIXTURE["expected"]


def test_generate_root_html_matches_frozen_sizes() -> None:
    _, size_dict = _run()
    assert size_dict["root_definition"] == FIXTURE["size_dict"]["root_definition"]
    assert size_dict["root_synonyms"] == FIXTURE["size_dict"]["root_synonyms"]


def test_generate_root_html_dict_entry_shape() -> None:
    entries, _ = _run()
    assert len(entries) == len(FIXTURE["root_rows"])
    for entry in entries:
        assert entry.definition_plain == ""
        assert entry.definition_html
        assert entry.synonyms


@pytest.mark.parametrize("word", ["√ḍaṃs", "√khip 1"])
def test_generate_root_html_niggahita_synonyms(word: str) -> None:
    entries, _ = _run()
    entry = next(e for e in entries if e.word == word)
    assert any("ṁ" in s or "ŋ" in s for s in entry.synonyms)


def test_generate_root_html_strips_root_marker_from_synonyms() -> None:
    entries, _ = _run()
    entry = next(e for e in entries if e.word == "√har 1")
    assert any("√" not in s for s in entry.synonyms)
    assert "har" in entry.synonyms
