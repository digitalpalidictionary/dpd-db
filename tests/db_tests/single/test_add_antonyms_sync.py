"""Two sources naming one twin must both end up in the twin's antonym."""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword
from db_tests.single.add_antonyms_sync import commit_to_db, make_dest_antonyms


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def add(db: Session, lemma_1: str, antonym: str) -> DpdHeadword:
    i = DpdHeadword(
        lemma_1=lemma_1,
        pos="adj",
        meaning_1="x",
        meaning_lit="",
        antonym=antonym,
    )
    db.add(i)
    db.commit()
    return i


def test_second_source_keeps_the_first_lemma(db_session: Session) -> None:
    source_a = add(db_session, "alpha 1", "twin")
    source_b = add(db_session, "beta 1", "twin")
    twin = add(db_session, "twin 1", "")

    for source in (source_a, source_b):
        proposed = ", ".join(make_dest_antonyms(source, twin))
        commit_to_db(twin, proposed, db_session)

    assert twin.antonym == "alpha, beta"
