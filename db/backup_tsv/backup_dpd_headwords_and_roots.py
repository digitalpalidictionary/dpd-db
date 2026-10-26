#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Save latest DpdHeadword and DpdRoot tables to backup_tsv folder."""

import csv
import subprocess
import sys
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def backup_dpd_headwords_and_roots(pth: ProjectPaths):
    pr.tic()
    pr.yellow_title("backing headword and roots tables to tsv")
    db_session = get_db_session(pth.dpd_db_path)
    check_no_duplicate_lemma_1(db_session)
    backup_dpd_headwords(db_session, pth)
    backup_dpd_roots(db_session, pth)
    db_session.close()
    git_commit(pth)
    pr.toc()


def find_duplicate_lemma_1(db_session: Session) -> dict[str, list[int]]:
    """Map each lemma_1 held by more than one headword to those ids."""
    duplicate_names = (
        db_session.query(DpdHeadword.lemma_1)
        .group_by(DpdHeadword.lemma_1)
        .having(func.count() > 1)
    )
    rows = (
        db_session.query(DpdHeadword.lemma_1, DpdHeadword.id)
        .filter(DpdHeadword.lemma_1.in_(duplicate_names))
        .order_by(DpdHeadword.lemma_1, DpdHeadword.id)
        .all()
    )
    duplicates: dict[str, list[int]] = {}
    for lemma_1, headword_id in rows:
        duplicates.setdefault(lemma_1, []).append(headword_id)
    return duplicates


def check_no_duplicate_lemma_1(db_session: Session) -> None:
    """Stop before any file is written: the database build rejects a duplicate."""
    duplicates = find_duplicate_lemma_1(db_session)
    if not duplicates:
        return
    pr.red("duplicate lemma_1, backup stopped, nothing written or committed")
    for lemma_1, ids in duplicates.items():
        pr.red(f"{lemma_1}: ids {', '.join(str(i) for i in ids)}")
    sys.exit(1)


def split_tsv_file(file_path: Path, prefix: str, chunk_size: int = 30000):
    """Split a TSV file into chunks of specified size."""
    pr.green_tmr(f"splitting into chunks of {chunk_size}")

    with open(file_path, "r", newline="", encoding="utf-8") as tsvfile:
        lines = list(csv.reader(tsvfile, delimiter="\t"))

        header = lines[0]
        data = lines[1:]

        num_chunks = (len(data) + chunk_size - 1) // chunk_size

        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(data))
            chunk_data = data[start_idx:end_idx]

            part_num = f"{i + 1:03d}"
            chunk_filename = file_path.parent / f"{prefix}_part_{part_num}.tsv"

            with open(chunk_filename, "w", newline="", encoding="utf-8") as chunk_file:
                writer = csv.writer(
                    chunk_file, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
                )
                writer.writerow(header)
                writer.writerows(chunk_data)

        if num_chunks > 0:
            file_path.unlink()

    pr.yes(num_chunks)


def backup_dpd_headwords(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup DpdHeadword table to TSV."""
    pr.green_tmr("writing DpdHeadword table")
    db = db_session.query(DpdHeadword).all()

    # Use the custom path if provided, otherwise use the default path
    pali_word_path = custom_path if custom_path else pth.pali_word_path

    with open(pali_word_path, "w", newline="", encoding="utf-8") as tsvfile:
        exclude_columns = [
            "created_at",
            "updated_at",
            "inflections",
            "inflections_sinhala",
            "inflections_devanagari",
            "inflections_thai",
            "inflections_html",
            "freq_html",
            "ebt_count",
        ]

        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
        )
        column_names = [
            column.name
            for column in DpdHeadword.__mapper__.columns
            if column.name not in exclude_columns
        ]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in DpdHeadword.__mapper__.columns
                if column.name not in exclude_columns
            ]
            csvwriter.writerow(row)

    pr.yes(len(db))

    # Split the TSV file into chunks
    split_tsv_file(Path(pali_word_path), "dpd_headwords")


def backup_dpd_roots(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup DpdRoot table to TSV."""
    pr.green_tmr("writing DpdRoot table")
    db = db_session.query(DpdRoot).all()

    # Use the custom path if provided, otherwise use the default path
    pali_root_path = custom_path if custom_path else pth.pali_root_path

    with open(pali_root_path, "w", newline="", encoding="utf-8") as tsvfile:
        exclude_columns = [
            "created_at",
            "updated_at",
            "root_info",
            "root_matrix",
            "root_ru_meaning",
            "sanskrit_root_ru_meaning",
        ]
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
        )
        column_names = [
            column.name
            for column in DpdRoot.__mapper__.columns
            if column.name not in exclude_columns
        ]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in DpdRoot.__mapper__.columns
                if column.name not in exclude_columns
            ]
            csvwriter.writerow(row)

    pr.yes(len(db))

    # Split the TSV file into chunks
    split_tsv_file(Path(pali_root_path), "dpd_roots")


def git_commit(pth: ProjectPaths):
    pr.green_tmr("committing changes to GitHub")

    # Add all split files for headwords and roots
    backup_dir = pth.pali_word_path.parent
    headword_files = list(backup_dir.glob("dpd_headwords_part_*.tsv"))
    root_files = list(backup_dir.glob("dpd_roots_part_*.tsv"))

    files_to_add = [str(f) for f in headword_files + root_files]
    if not files_to_add:
        pr.no("no files to commit")
        return

    try:
        # Path-limited commit, not `index.add` + `index.commit`. The latter
        # stages these files and then commits the *whole index*, so in a working
        # tree shared with other sessions it would sweep up whatever they had
        # staged and commit it as "pali update". Passing the paths after `--`
        # commits exactly these files from the working tree and ignores the rest
        # of the index entirely.
        #
        # It also leaves nothing staged when it fails — a busy index.lock or a
        # rejected pre-commit hook used to abort between the add and the commit
        # and leave these files sitting staged for someone else's next commit.
        subprocess.run(
            ["git", "commit", "-m", "pali update", "--", *files_to_add],
            check=True,
            capture_output=True,
            text=True,
        )
        pr.yes("ok")
    except subprocess.CalledProcessError as e:
        pr.no(e.stderr.strip())
    except FileNotFoundError as e:
        pr.no(f"{e}")


if __name__ == "__main__":
    pth = ProjectPaths()
    backup_dpd_headwords_and_roots(pth)
