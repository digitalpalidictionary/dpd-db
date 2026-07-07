"""Behavioural tests for db/lookup/transliterate_lookup_table._write_translit_to_db.

Runs against an in-memory SQLite db with the real Lookup model (no mocks),
following the tests/tools/test_lookup_sync.py pattern.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.lookup.transliterate_lookup_table import WordInflections, _write_translit_to_db
from db.models import Base, Lookup


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def _get(db_session: Session, key: str) -> Lookup | None:
    return db_session.query(Lookup).filter(Lookup.lookup_key == key).first()


def test_written_values_match_pack_methods_byte_for_byte(db_session: Session) -> None:
    row = Lookup()
    row.lookup_key = "buddho"
    row.grammar_pack([["buddha", "masc", "nom sg"]])
    db_session.add(row)
    db_session.commit()

    translit_dict: dict[str, WordInflections] = {
        "buddho": WordInflections(sinhala={"a"}, devanagari={"b"}, thai={"c"}),
    }
    _write_translit_to_db(db_session, translit_dict)

    db_session.expire_all()
    refreshed = _get(db_session, "buddho")
    assert refreshed is not None

    expected = Lookup()
    expected.sinhala_pack(["a"])
    expected.devanagari_pack(["b"])
    expected.thai_pack(["c"])

    assert refreshed.sinhala == expected.sinhala
    assert refreshed.devanagari == expected.devanagari
    assert refreshed.thai == expected.thai
    # untouched column survives
    assert refreshed.grammar_unpack == [["buddha", "masc", "nom sg"]]


def test_rows_not_in_translit_dict_keep_old_values(db_session: Session) -> None:
    covered = Lookup()
    covered.lookup_key = "buddho"
    db_session.add(covered)

    uncovered = Lookup()
    uncovered.lookup_key = "dhammo"
    uncovered.sinhala_pack(["old"])
    uncovered.grammar_pack([["dhamma", "masc", "nom sg"]])
    db_session.add(uncovered)
    db_session.commit()

    translit_dict: dict[str, WordInflections] = {
        "buddho": WordInflections(sinhala={"a"}, devanagari={"b"}, thai={"c"}),
    }
    count = _write_translit_to_db(db_session, translit_dict)

    db_session.expire_all()
    untouched = _get(db_session, "dhammo")
    assert untouched is not None
    assert untouched.sinhala_unpack == ["old"]
    assert untouched.grammar_unpack == [["dhamma", "masc", "nom sg"]]
    assert count == 1


def test_empty_translit_dict_is_a_noop(db_session: Session) -> None:
    row = Lookup()
    row.lookup_key = "buddho"
    row.sinhala_pack(["old"])
    db_session.add(row)
    db_session.commit()

    count = _write_translit_to_db(db_session, {})

    db_session.expire_all()
    refreshed = _get(db_session, "buddho")
    assert refreshed is not None
    assert refreshed.sinhala_unpack == ["old"]
    assert count == 0
