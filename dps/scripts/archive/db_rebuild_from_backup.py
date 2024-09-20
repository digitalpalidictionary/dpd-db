#!/usr/bin/env python3

"""Rebuild the databse from scratch from files in backup_tsv folder."""

import csv
import sys
import os

from rich import print

from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import DpdHeadword, DpdRoot, Russian, SBS
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from tools.configger import config_update, config_test
from dps.tools.paths_dps import DPSPaths


def main():
    tic()
    print("[bright_yellow]rebuilding db from tsvs")
    
    if config_test("regenerate", "db_rebuild", "no"):
        config_update("regenerate", "db_rebuild", "yes")

    pth = ProjectPaths()
    dpspth = DPSPaths()

    if pth.dpd_db_path.exists():
        print("[red]this will destroy your current database!")
        response = input("are you sure you would like to rebuild the db? [y/n] ")
        if response != "y":
            return
        else:
            pth.dpd_db_path.unlink()

    create_db_if_not_exists(pth.dpd_db_path)

    for p in [
        pth.pali_root_path,
        pth.pali_word_path,
        pth.russian_path,
        pth.sbs_path
    ]:
        if not p.exists():
            print(f"[bright_red]TSV backup file does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session(pth.dpd_db_path)

    make_pali_word_table_data(dpspth, db_session)
    make_pali_root_table_data(dpspth, db_session)
    make_russian_table_data(dpspth, db_session)
    make_sbs_table_data(dpspth, db_session)

    db_session.commit()
    db_session.close()
    print("[bright_green]database restored successfully")
    toc()


def make_pali_word_table_data(dpspth, db_session: Session):
    """Read TSV and return DpdHeadword table data."""
    print("[green]creating DpdHeadword table data")
    pali_word_path = os.path.join(dpspth.dps_backup_dir, "dpd_headwords.tsv")
    with open(pali_word_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("user_id", "created_at", "updated_at"):
                    data[col_name] = value
            db_session.add(DpdHeadword(**data))


def make_pali_root_table_data(dpspth, db_session: Session):
    """Read TSV and return DpdRoot table data."""
    print("[green]creating DpdRoot table data")
    pali_root_path = os.path.join(dpspth.dps_backup_dir, "dpd_roots.tsv")
    with open(pali_root_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in (
                    "created_at", "updated_at",
                        "root_info", "root_matrix"):
                    data[col_name] = value
            db_session.add(DpdRoot(**data))


def make_russian_table_data(dpspth, db_session: Session):
    """Read TSV and return Russian table data."""
    print("[green]creating Russian table data")
    russian_path = os.path.join(dpspth.dps_backup_dir, "russian.tsv")
    with open(russian_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(Russian(**data))


def make_sbs_table_data(dpspth, db_session: Session):
    """Read TSV and return SBS table data."""
    print("[green]creating SBS table data")
    sbs_path = os.path.join(dpspth.dps_backup_dir, "sbs.tsv")
    with open(sbs_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(SBS(**data))


if __name__ == "__main__":
    main()
