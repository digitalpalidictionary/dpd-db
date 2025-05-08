#!/usr/bin/env python3

"""Rebuild the database from scratch from files in backup_tsv folder."""

import csv
import sys

from rich import print

from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import DpdHeadword, DpdRoot
from tools.printer import printer as pr
from tools.paths import ProjectPaths
from tools.configger import config_update, config_test


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

    for p in [pth.pali_root_path, pth.pali_word_path]:
        if not p.exists():
            pr.red(f"TSV backup file does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session(pth.dpd_db_path)

    make_pali_word_table_data(pth, db_session)
    make_pali_root_table_data(pth, db_session)

    pr.green("committing to db")
    db_session.commit()
    db_session.close()
    pr.yes("ok")
    pr.green_title("database restored successfully")
    pr.toc()


def make_pali_word_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return DpdHeadword table data."""

    pr.green("creating DpdHeadword table data")
    counter = 0
    with open(pth.pali_word_path, "r", newline="") as tsv_file:
        csvreader = csv.reader(tsv_file, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
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
    with open(pth.pali_root_path, "r", newline="") as tsv_file:
        csvreader = csv.reader(tsv_file, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
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
