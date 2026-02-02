"""Tests for get_db_data function in proofreader."""

import pytest
from sqlalchemy.orm import Session
from db.models import Base, DpdHeadword
from tools.proofreader import get_db_data


@pytest.fixture
def db_session(monkeypatch):
    """Create an in-memory database for testing."""
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


def test_get_db_data(db_session: Session):
    """Test that data is extracted correctly."""
    # Add sample data
    entry1 = DpdHeadword(id=1, lemma_1="test1", meaning_1="meaning one")
    entry2 = DpdHeadword(id=2, lemma_1="test2", meaning_1="")  # Should be filtered
    entry3 = DpdHeadword(id=3, lemma_1="test3", meaning_1="meaning three")

    db_session.add_all([entry1, entry2, entry3])
    db_session.commit()

    data = get_db_data(db_session)

    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["lemma_1"] == "test1"
    assert data[0]["meaning_1"] == "meaning one"
    assert data[1]["id"] == 3
    assert data[1]["meaning_1"] == "meaning three"
