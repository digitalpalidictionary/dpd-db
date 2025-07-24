#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Rebuild the database from scratch from files in backup_tsv folder."""

import csv
import sys
from pathlib import Path
from typing import Iterator, List, Tuple

from rich import print
from sqlalchemy.orm.session import Session

from db.db_helpers import create_db_if_not_exists, get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.configger import config_test, config_update
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.title("rebuilding db from tsvs")

    if config_test("regenerate", "db_rebuild", "no"):
        config_update("regenerate", "db_rebuild", "yes")

    pth = ProjectPaths()

    if pth.dpd_db_path.exists():
        print("[red]this will destroy your current database!")
        # response = input("are you sure you would like to rebuild the db? [y/n] ")
        # if response != "y":
        #     return
        # else:
        pth.dpd_db_path.unlink()

    create_db_if_not_exists(pth.dpd_db_path)

    # Check for TSV files (both split and single file formats)
    check_tsv_files(pth)

    db_session = get_db_session(pth.dpd_db_path)

    make_pali_word_table_data(pth, db_session)
    make_pali_root_table_data(pth, db_session)

    pr.green("committing to db")
    db_session.commit()
    db_session.close()
    pr.yes("ok")
    pr.green_title("database restored successfully")
    pr.toc()


def check_tsv_files(pth: ProjectPaths) -> None:
    """Check if TSV files exist in either split or single file format."""

    # Check for dpd_headwords files
    headword_files = get_tsv_files(pth.pali_word_path, "dpd_headwords")
    if not headword_files:
        pr.red("No dpd_headwords TSV files found")
        sys.exit(1)

    # Check for dpd_roots files
    root_files = get_tsv_files(pth.pali_root_path, "dpd_roots")
    if not root_files:
        pr.red("No dpd_roots TSV files found")
        sys.exit(1)


def get_tsv_files(original_path: Path, base_filename: str) -> List[Path]:
    """Get list of TSV files to process, handling both split and single file formats."""

    backup_dir = original_path.parent

    # Check for split files (dpd_headwords_part_*.tsv or dpd_roots_part_*.tsv)
    split_pattern = f"{base_filename}_part_*.tsv"
    split_files = sorted(backup_dir.glob(split_pattern))

    if split_files:
        pr.green(f"Found {len(split_files)} split {base_filename} files")
        return split_files

    # Fall back to single file format
    single_file = backup_dir / f"{base_filename}.tsv"
    if single_file.exists():
        pr.green(f"Found single {base_filename} file")
        return [single_file]

    return []


def read_tsv_files(file_paths: List[Path]) -> Iterator[Tuple[List[str], List[str]]]:
    """Read TSV files and yield (columns, row) tuples.

    Handles split files where only the first file has headers.
    """
    if not file_paths:
        return

    columns = None

    for file_idx, file_path in enumerate(file_paths):
        pr.green(f"Reading {file_path.name}")

        with open(file_path, "r", newline="") as tsv_file:
            csvreader = csv.reader(tsv_file, delimiter="\t", quotechar='"')

            # Read headers from first file only
            if file_idx == 0:
                columns = next(csvreader)
            else:
                # Skip headers for subsequent files
                next(csvreader)

            # Yield all data rows
            for row in csvreader:
                if columns:
                    yield columns, row


def make_pali_word_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return DpdHeadword table data."""

    pr.green("creating DpdHeadword table data")
    counter = 0

    headword_files = get_tsv_files(pth.pali_word_path, "dpd_headwords")

    for columns, row in read_tsv_files(headword_files):
        data = {}
        for col_name, value in zip(columns, row):
            if col_name not in ("user_id", "created_at", "updated_at"):
                data[col_name] = value
        db_session.add(DpdHeadword(**data))
        counter += 1

    pr.yes(counter)


def make_pali_root_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return DpdRoot table data."""

    pr.green("creating DpdRoot table data")
    counter = 0

    root_files = get_tsv_files(pth.pali_root_path, "dpd_roots")

    for columns, row in read_tsv_files(root_files):
        data = {}
        for col_name, value in zip(columns, row):
            if col_name not in (
                "created_at",
                "updated_at",
                "root_info",
                "root_matrix",
                "root_ru_meaning",
                "sanskrit_root_ru_meaning",
            ):
                data[col_name] = value
        db_session.add(DpdRoot(**data))
        counter += 1

    pr.yes(counter)


if __name__ == "__main__":
    main()
