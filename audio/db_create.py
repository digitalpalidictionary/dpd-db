#!/usr/bin/env python3
"""
Database creation and population for DPD audio files.
This file handles creating and populating the audio database.
"""

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from audio.db.db_helpers import make_version
from audio.db.models import Base, DpdAudio
from audio.error_check.delete_silent_files import (
    find_and_delete_silent_files,
)
from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tarballer import create_tarball

pth = ProjectPaths()


def cleanup_old_tarballs() -> None:
    """
    Delete all but the latest three tarballs to save disk space.
    """
    db_dir = pth.dpd_audio_db_path.parent

    # Find all tarball files in the db directory
    tarballs = list(db_dir.glob("dpd_audio_*.tar.gz"))

    # Sort by modification time (newest first)
    tarballs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Keep only the latest 3, delete the rest
    if len(tarballs) > 3:
        pr.green_title("cleaning up old tarballs")

        # Files to delete are all except the first 3
        files_to_delete = tarballs[3:]

        for tarball in files_to_delete:
            pr.info(f"deleting: {tarball.name}")
            tarball.unlink()

        pr.info(f"deleted {len(files_to_delete)} old tarball(s)")


def create_audio_database() -> Path:
    """
    Create the audio database if it doesn't exist.
    """
    db_path = pth.dpd_audio_db_path

    # Delete existing database file if it exists to ensure schema updates
    if db_path.exists():
        pr.green("deleting existing database file")
        db_path.unlink()
        pr.yes("ok")

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


def populate_audio_database() -> None:
    """
    Populate the audio database with files from the specified folders.
    """
    pr.green_title("populating db with latest mp3s")
    db_path = pth.dpd_audio_db_path

    # Use paths from ProjectPaths
    male_folder = pth.dpd_audio_male1_dir
    male2_folder = pth.dpd_audio_male2_dir
    female_folder = pth.dpd_audio_female1_dir

    if not male_folder.exists():
        raise FileNotFoundError(f"Male audio folder not found: {male_folder}")
    if not male2_folder.exists():
        raise FileNotFoundError(f"Male2 audio folder not found: {male2_folder}")
    if not female_folder.exists():
        raise FileNotFoundError(f"Female audio folder not found: {female_folder}")

    # Get session
    session = get_audio_session(db_path)

    try:
        # Get all audio files from all three folders, excluding files starting with "!"
        male_files: dict[str, Path] = {
            f.stem: f for f in male_folder.glob("*.mp3") if not f.stem.startswith("!")
        }
        male2_files: dict[str, Path] = {
            f.stem: f for f in male2_folder.glob("*.mp3") if not f.stem.startswith("!")
        }
        female_files: dict[str, Path] = {
            f.stem: f for f in female_folder.glob("*.mp3") if not f.stem.startswith("!")
        }

        # Get all unique headwords (lemma_clean values)
        all_headwords = set(male_files.keys()) | set(female_files.keys())

        # Process each headword
        for counter, headword in enumerate(sorted(all_headwords)):
            if counter % 10000 == 0:
                pr.counter(counter, len(all_headwords), headword)

            # Read the binary data for male, male2, and female audio files
            male_blob: bytes | None = None
            male2_blob: bytes | None = None
            female_blob: bytes | None = None

            if headword in male_files:
                with open(male_files[headword], "rb") as f:
                    male_blob = f.read()

            if headword in male2_files:
                with open(male2_files[headword], "rb") as f:
                    male2_blob = f.read()

            if headword in female_files:
                with open(female_files[headword], "rb") as f:
                    female_blob = f.read()

            # Check if record already exists
            existing = (
                session.query(DpdAudio).filter(DpdAudio.lemma_clean == headword).first()
            )

            if existing:
                # Update existing record
                existing.male1 = male_blob  # type: ignore
                existing.male2 = male2_blob  # type: ignore
                existing.female1 = female_blob  # type: ignore
            else:
                # Create new record
                audio_record = DpdAudio(
                    lemma_clean=headword,
                    male1=male_blob,
                    male2=male2_blob,
                    female1=female_blob,
                )
                session.add(audio_record)

        pr.green("committing to db")
        session.commit()
        pr.yes(len(all_headwords))

    except Exception as e:
        session.rollback()
        pr.no("failed")
        pr.red(f"Error populating audio database: {e}")
        raise
    finally:
        session.close()


def create_archive() -> None:
    """Create tarball of database only."""

    version = make_version()
    db_file = pth.dpd_audio_db_path

    if not db_file.exists():
        pr.red("Database file not found!")
        return

    archive_name = f"dpd_audio_{version}.tar.gz"
    db_dir = pth.dpd_audio_db_path.parent

    # Use tarballer to create the archive
    create_tarball(archive_name, [db_file], db_dir, "gz")

    archive_path = db_dir / archive_name
    pr.info("archive created at:")
    pr.info(f"{archive_path}")


def main():
    """Main function to populate the audio database."""
    pr.tic()
    pr.title("populating audio database")

    if config_test("exporter", "make_audio_db", "no"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    find_and_delete_silent_files()
    create_audio_database()
    populate_audio_database()
    create_archive()
    cleanup_old_tarballs()
    pr.toc()


if __name__ == "__main__":
    main()
