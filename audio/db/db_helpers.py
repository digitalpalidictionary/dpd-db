"""Database helpers for DPD audio files."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, DpdAudio
from tools.printer import printer as pr
from tools.paths import ProjectPaths

pth = ProjectPaths()


def create_audio_database() -> Path:
    """
    Create the audio database if it doesn't exist.
    """
    db_path = pth.dpd_audio_db_path

    # Create the database engine
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)

    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)

    return db_path


def get_audio_session(db_path: Optional[Path] = None) -> Session:
    """
    Get a database session for audio operations.

    Args:
        db_path: Path to the database file. If None, uses default location.

    Returns:
        SQLAlchemy session object.
    """
    if db_path is None:
        db_path = pth.dpd_audio_db_path

    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
    SessionLocal = sessionmaker(bind=engine)

    return SessionLocal()


def get_audio_record(headword: str, gender: str) -> Optional[bytes]:
    """
    Get audio data for a specific headword and gender.

    Args:
        headword: The lemma_clean value to search for.
        gender: 'male' or 'female' to specify which audio to return.

    Returns:
        Audio data as bytes if found, None otherwise.
    """
    db_path = pth.dpd_audio_db_path
    session = get_audio_session(db_path)

    try:
        record = (
            session.query(DpdAudio).filter(DpdAudio.lemma_clean == headword).first()
        )
        if not record:
            return None

        gender = gender.lower()
        if gender == "male":
            return record.male1
        elif gender == "female":
            return record.female1
        else:
            raise ValueError("Gender must be 'male' or 'female'")
    finally:
        session.close()


def clear_audio_database(db_path: Optional[Path] = None) -> None:
    """
    Clear all records from the audio database.

    Args:
        db_path: Path to the database file. If None, uses default location.
    """
    session = get_audio_session(db_path)

    try:
        session.query(DpdAudio).delete()
        session.commit()
        pr.yes("Audio database cleared")
    except Exception as e:
        session.rollback()
        pr.red(f"Error clearing audio database: {e}")
        raise
    finally:
        session.close()


def make_version() -> str:
    """Create version using same system as tools/version.py"""
    major = 0
    minor = 1
    patch = datetime.now().strftime("%y%m%d")  # YYMMDD format

    version = f"v{major}.{minor}.{patch}"
    return version
