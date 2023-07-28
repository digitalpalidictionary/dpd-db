#!/usr/bin/env python3

"""Rebuild the databse from scratch from files in backup_tsv folder."""

import csv
import sys

from rich import print

from db.get_db_session import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import PaliWord, PaliRoot, Russian, SBS
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths as PTH


def main():
    tic()
    print("[bright_yellow]rebuilding db from tsvs")

    if PTH.dpd_db_path.exists():
        PTH.dpd_db_path.unlink()

    create_db_if_not_exists(PTH.dpd_db_path)

    for p in [
        PTH.pali_root_path,
        PTH.pali_word_path,
        PTH.russian_path,
        PTH.sbs_path
    ]:
        if not p.exists():
            print(f"[bright_red]TSV backup file does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session(PTH.dpd_db_path)

    make_pali_word_table_data(db_session)
    make_pali_root_table_data(db_session)
    make_russian_table_data(db_session)
    make_sbs_table_data(db_session)

    db_session.commit()
    db_session.close()
    print("[bright_green]database restored successfully")
    toc()


def make_pali_word_table_data(db_session):
    """Read TSV and return PaliWord table data."""
    print("[green]creating PaliWord table data")
    with open(PTH.pali_word_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("created_at", "updated_at"):
                    data[col_name] = value
            db_session.add(PaliWord(**data))


def make_pali_root_table_data(db_session):
    """Read TSV and return PaliRoot table data."""
    print("[green]creating PaliRoot table data")
    with open(PTH.pali_root_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in (
                    "created_at", "updated_at",
                        "root_info", "root_matrix"):
                    data[col_name] = value
            db_session.add(PaliRoot(**data))


def make_russian_table_data(db_session):
    """Read TSV and return Russian table data."""
    print("[green]creating Russian table data")
    with open(PTH.russian_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(Russian(**data))


def make_sbs_table_data(db_session):
    """Read TSV and return SBS table data."""
    print("[green]creating SBS table data")
    with open(PTH.sbs_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(SBS(**data))


if __name__ == "__main__":
    main()
