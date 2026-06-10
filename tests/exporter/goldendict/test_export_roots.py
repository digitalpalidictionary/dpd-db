"""Tests for exporter/goldendict/export_roots.py.

Runs generate_root_html against an in-memory db seeded with real
DpdRoot/FamilyRoot rows copied from dpd.db. Covers the multi-family,
few-family and niggahita-synonym (ṃ in root and in family) render branches.
"""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, DpdRoot, FamilyRoot
from tools.date_and_time import year_month_day_dash
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


def test_generate_root_html_renders_each_root() -> None:
    entries, _ = _run()
    assert {e.word for e in entries} == {r["root"] for r in FIXTURE["root_rows"]}

    today = year_month_day_dash()
    root_meanings = {r["root"]: r["root_meaning"] for r in FIXTURE["root_rows"]}
    for entry in entries:
        assert entry.definition_html.startswith("<!DOCTYPE html>")
        assert today in entry.definition_html
        assert root_meanings[entry.word] in entry.definition_html


def test_generate_root_html_sizes() -> None:
    _, size_dict = _run()
    assert size_dict["root_definition"] > 0
    assert size_dict["root_synonyms"] > 0


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
