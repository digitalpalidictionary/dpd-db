#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Save latest DpdHeadword and DpdRoot tables to backup_tsv folder."""

import csv
from pathlib import Path

from git import Repo
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def backup_dpd_headwords_and_roots(pth: ProjectPaths):
    pr.tic()
    pr.title("backing headword and roots tables to tsv")
    db_session = get_db_session(pth.dpd_db_path)
    backup_dpd_headwords(db_session, pth)
    backup_dpd_roots(db_session, pth)
    db_session.close()
    git_commit(pth)
    pr.toc()


def split_tsv_file(file_path: Path, prefix: str, chunk_size: int = 50000):
    """Split a TSV file into chunks of specified size."""
    pr.green(f"splitting into chunks of {chunk_size}")

    with open(file_path, "r", newline="", encoding="utf-8") as tsvfile:
        # Read all lines
        lines = list(csv.reader(tsvfile, delimiter="\t"))

        # Separate header from data
        header = lines[0]
        data = lines[1:]

        # Calculate number of chunks needed
        num_chunks = (len(data) + chunk_size - 1) // chunk_size

        # Create chunks
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(data))
            chunk_data = data[start_idx:end_idx]

            # Create filename with zero-padded part number
            part_num = f"{i + 1:03d}"
            chunk_filename = file_path.parent / f"{prefix}_part_{part_num}.tsv"

            # Write chunk to file
            with open(chunk_filename, "w", newline="", encoding="utf-8") as chunk_file:
                writer = csv.writer(
                    chunk_file, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL
                )

                # Write header only for the first part
                if i == 0:
                    writer.writerow(header)
                writer.writerows(chunk_data)

        # Remove original file if we created split files
        if num_chunks > 0:
            file_path.unlink()

    pr.yes(num_chunks)


def backup_dpd_headwords(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup DpdHeadword table to TSV."""
    pr.green("writing DpdHeadword table")
    db = db_session.query(DpdHeadword).all()

    # Use the custom path if provided, otherwise use the default path
    pali_word_path = custom_path if custom_path else pth.pali_word_path

    with open(pali_word_path, "w", newline="") as tsvfile:
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
    pr.green("writing DpdRoot table")
    db = db_session.query(DpdRoot).all()

    # Use the custom path if provided, otherwise use the default path
    pali_root_path = custom_path if custom_path else pth.pali_root_path

    with open(pali_root_path, "w", newline="") as tsvfile:
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
    pr.green("committing changes to GitHub")
    try:
        repo = Repo("./")
        index = repo.index

        # Add all split files for headwords and roots
        backup_dir = pth.pali_word_path.parent
        headword_files = list(backup_dir.glob("dpd_headwords_part_*.tsv"))
        root_files = list(backup_dir.glob("dpd_roots_part_*.tsv"))

        files_to_add = headword_files + root_files
        if files_to_add:
            index.add([str(f) for f in files_to_add])
            index.commit("pali update")
            pr.yes("ok")
        else:
            pr.no("no files to commit")
    except Exception as e:
        pr.no(f"{e}")


if __name__ == "__main__":
    pth = ProjectPaths()
    backup_dpd_headwords_and_roots(pth)
