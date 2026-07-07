"""Behavioural tests for db/inflections/transliterate_inflections._write_translit_to_db.

Runs against an in-memory SQLite db with the real DpdHeadword model (no mocks),
following the tests/tools/test_lookup_sync.py pattern.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.inflections.transliterate_inflections import (
    WordInflections,
    _write_translit_to_db,
)
from db.models import Base, DpdHeadword


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def _make_headword(db_session: Session, id_: int, lemma_1: str) -> DpdHeadword:
    hw = DpdHeadword()
    hw.id = id_
    hw.lemma_1 = lemma_1
    db_session.add(hw)
    return hw


def test_covered_rows_get_joined_values(db_session: Session) -> None:
    hw1 = _make_headword(db_session, 1, "buddha")
    hw2 = _make_headword(db_session, 2, "dhamma")
    db_session.commit()

    translit_dict: dict[str, WordInflections] = {
        "buddha": WordInflections(
            sinhala={"a", "b"}, devanagari={"c"}, thai={"d", "e"}
        ),
    }

    count = _write_translit_to_db(db_session, [hw1, hw2], translit_dict)

    db_session.expire_all()
    refreshed = db_session.get(DpdHeadword, 1)
    assert refreshed is not None
    assert set(refreshed.inflections_sinhala.split(",")) == {"a", "b"}
    assert refreshed.inflections_devanagari == "c"
    assert set(refreshed.inflections_thai.split(",")) == {"d", "e"}
    assert count == 1


def test_uncovered_rows_untouched(db_session: Session) -> None:
    hw1 = _make_headword(db_session, 1, "buddha")
    hw2 = _make_headword(db_session, 2, "dhamma")
    db_session.commit()

    translit_dict: dict[str, WordInflections] = {
        "buddha": WordInflections(sinhala={"a"}, devanagari={"b"}, thai={"c"}),
    }

    _write_translit_to_db(db_session, [hw1, hw2], translit_dict)

    db_session.expire_all()
    untouched = db_session.get(DpdHeadword, 2)
    assert untouched is not None
    assert untouched.inflections_sinhala == ""
    assert untouched.inflections_devanagari == ""
    assert untouched.inflections_thai == ""


def test_return_value_counts_covered_rows(db_session: Session) -> None:
    hw1 = _make_headword(db_session, 1, "buddha")
    hw2 = _make_headword(db_session, 2, "dhamma")
    hw3 = _make_headword(db_session, 3, "sangha")
    db_session.commit()

    translit_dict: dict[str, WordInflections] = {
        "buddha": WordInflections(sinhala={"a"}, devanagari={"b"}, thai={"c"}),
        "sangha": WordInflections(sinhala={"x"}, devanagari={"y"}, thai={"z"}),
    }

    count = _write_translit_to_db(db_session, [hw1, hw2, hw3], translit_dict)
    assert count == 2


def test_empty_translit_dict_is_a_noop(db_session: Session) -> None:
    hw1 = _make_headword(db_session, 1, "buddha")
    db_session.commit()

    count = _write_translit_to_db(db_session, [hw1], {})
    assert count == 0
