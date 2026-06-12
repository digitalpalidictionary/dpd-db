"""Test Pāli analyzer lookup filtering for particle sandhi candidates."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from exporter.analysis.analyzer import analyze_sentence
from exporter.analysis.types import AnalysisOption


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Provide a database session for analyzer integration tests."""
    db = get_db_session(Path("dpd.db"))
    try:
        yield db
    finally:
        db.close()


def _first_token_options(sentence: str, db_session: Session) -> list[AnalysisOption]:
    result = analyze_sentence(sentence, db_session)
    assert len(result) == 1
    assert result[0]["status"] == "found"
    return result[0]["data"]


def _top_level_ids(options: list[AnalysisOption]) -> set[int]:
    return {option["id"] for option in options if isinstance(option.get("id"), int)}


def _is_deconstruction_key(key: str) -> bool:
    return key.startswith("decon_") or "_decon_" in key


def test_particle_sandhi_keeps_real_sandhi_and_drops_base_noise(
    db_session: Session,
) -> None:
    options = _first_token_options("yañ'ca", db_session)

    ids = _top_level_ids(options)

    assert 53493 in ids
    assert 53444 not in ids
    assert all(
        option["pos"] == "sandhi" or _is_deconstruction_key(option["key"])
        for option in options
    )


def test_particle_sandhi_without_headword_uses_deconstructor(
    db_session: Session,
) -> None:
    options = _first_token_options("yañcidaṃ", db_session)

    assert [option["key"] for option in options] == ["w0_decon_yañcidaṃ_0"]
    assert options[0]["construction"] == "yaṃ + ca + idaṃ"


def test_particle_sandhi_with_component_headword_uses_deconstructor(
    db_session: Session,
) -> None:
    options = _first_token_options("soḷasinti", db_session)

    assert [option["key"] for option in options] == ["w0_decon_soḷasinti_0"]
    assert options[0]["construction"] == "soḷasiṃ + iti"
    component_ids = {
        part["id"]
        for component_options in options[0]["components"]
        for part in component_options
    }
    assert 65453 in component_ids


def test_direct_grammar_match_survives_particle_deconstructor(
    db_session: Session,
) -> None:
    options = _first_token_options("jānāti", db_session)

    ids = _top_level_ids(options)

    assert 28313 in ids
    assert 28314 in ids


def test_direct_grammar_and_real_sandhi_both_survive_particle_deconstructor(
    db_session: Session,
) -> None:
    options = _first_token_options("bhavissanti", db_session)

    ids = _top_level_ids(options)

    assert 49625 in ids
    assert 49628 not in ids
    assert any(option["grammar"] == "fut 3rd pl of bhavati" for option in options)
    assert any(option["grammar"] == "fut 3rd pl of bhavissati" for option in options)


def test_analyzer_emits_raw_meaning_1_for_fallback_quality(
    db_session: Session,
) -> None:
    options = _first_token_options("sammā", db_session)

    samma_option = next(option for option in options if option["id"] == 60789)

    assert samma_option["meaning_1"] == "perfectly; rightly; correctly; properly"
