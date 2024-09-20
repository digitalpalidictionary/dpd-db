#!/usr/bin/env python3

"""Rebuild the databse from scratch from latest files in dps/backup folder. Modfied copy of https://github.com/digitalpalidictionary/dpd-db/blob/main/scripts/db_rebuild_from_tsv.py"""

import csv
import os

from rich.console import Console

from db.db_helpers import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import DpdHeadword, DpdRoot, Russian, SBS
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

console = Console()


def get_latest_backup(dpspth, prefix):
    """Get the latest backup file from a given directory with a specific prefix."""
    backup_files = [f for f in os.listdir(dpspth.dps_backup_dir) if f.startswith(prefix)]
    return os.path.join(dpspth.dps_backup_dir, sorted(backup_files, reverse=True)[0])



def main():
    tic()
    console.print("[bold bright_yellow]rebuilding db from dps/backup/*.tsvs")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    if pth.dpd_db_path.exists():
        pth.dpd_db_path.unlink()

    create_db_if_not_exists(pth.dpd_db_path)

    db_session = get_db_session(pth.dpd_db_path)

    pali_word_latest_tsv = get_latest_backup(dpspth, "paliword")
    pali_root_latest_tsv = get_latest_backup(dpspth, "paliroot")
    russian_latest_tsv = get_latest_backup(dpspth, "russian")
    sbs_latest_tsv = get_latest_backup(dpspth, "sbs")

    make_pali_word_table_data(db_session, pali_word_latest_tsv)
    make_pali_root_table_data(db_session, pali_root_latest_tsv)
    make_russian_table_data(db_session, russian_latest_tsv)
    make_sbs_table_data(db_session, sbs_latest_tsv)



    db_session.commit()
    db_session.close()
    console.print("[bold bright_green]database restored successfully")
    toc()


def make_pali_word_table_data(db_session, pali_word_latest_tsv):
    """Read TSV and return DpdHeadword table data."""
    console.print("[bold green]creating DpdHeadword table data")
    with open(pali_word_latest_tsv, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("created_at", "updated_at"):
                    data[col_name] = value
            db_session.add(DpdHeadword(**data))


def make_pali_root_table_data(db_session, pali_root_latest_tsv):
    """Read TSV and return DpdRoot table data."""
    console.print("[bold green]creating DpdRoot table data")
    with open(pali_root_latest_tsv, 'r', newline='') as tsvfile:
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


def make_russian_table_data(db_session, russian_latest_tsv):
    """Read TSV and return Russian table data."""
    console.print("[bold green]creating Russian table data")
    with open(russian_latest_tsv, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(Russian(**data))


def make_sbs_table_data(db_session, sbs_latest_tsv):
    """Read TSV and return SBS table data."""
    console.print("[bold green]creating SBS table data")
    with open(sbs_latest_tsv, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(SBS(**data))


if __name__ == "__main__":
    main()
