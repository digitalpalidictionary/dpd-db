"""Golden-master tests for exporter/goldendict/export_epd.py.

Freezes generate_epd_html's output (per-entry definition html + rendered sizes)
against an in-memory db seeded with real Lookup epd rows copied from dpd.db.
Covers the single-entry and multi-entry (<br>-join) render branches.
"""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, Lookup
from tools.paths import ProjectPaths
from exporter.goldendict.export_epd import generate_epd_html

FIXTURE_PATH = Path(__file__).parent / "test_export_epd_fixtures.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add_all(
        Lookup(lookup_key=row["lookup_key"], epd=row["epd"]) for row in FIXTURE["rows"]
    )
    session.commit()
    return session


def test_generate_epd_html_matches_frozen_entries() -> None:
    session = _build_session()
    entries, _ = generate_epd_html(session, ProjectPaths())
    produced = [{"word": e.word, "definition_html": e.definition_html} for e in entries]
    assert produced == FIXTURE["expected"]


def test_generate_epd_html_matches_frozen_sizes() -> None:
    session = _build_session()
    _, size_dict = generate_epd_html(session, ProjectPaths())
    assert size_dict["epd"] == FIXTURE["size_dict"]["epd"]
    assert size_dict["epd_header"] == FIXTURE["size_dict"]["epd_header"]


def test_generate_epd_html_dict_entry_shape() -> None:
    session = _build_session()
    entries, _ = generate_epd_html(session, ProjectPaths())
    assert len(entries) == len(FIXTURE["rows"])
    for entry in entries:
        assert entry.definition_plain == ""
        assert entry.synonyms == []
        assert entry.definition_html


@pytest.mark.parametrize("word", ["a", "arahant"])
def test_generate_epd_html_multi_entry_joined(word: str) -> None:
    session = _build_session()
    entries, _ = generate_epd_html(session, ProjectPaths())
    entry = next(e for e in entries if e.word == word)
    assert "<br>" in entry.definition_html
