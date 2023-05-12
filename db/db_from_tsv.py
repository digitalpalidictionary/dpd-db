#!/usr/bin/env python3.11
import csv
import sys

from rich import print

from db.get_db_session import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import PaliWord, PaliRoot
from tools.timeis import tic, toc
from tools.paths import ProjectPaths as PTH


def restore_db_from_tsvs():
    tic()
    print("[bright_yellow]restoring db from tsv")

    if PTH.dpd_db_path.exists():
        PTH.dpd_db_path.unlink()

    create_db_if_not_exists(PTH.dpd_db_path)

    for p in [PTH.pali_root_path, PTH.pali_word_path]:
        if not p.exists():
            print(f"[bright_red]File does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session(PTH.dpd_db_path)

    print("[green]loading PaliWord rows")
    with open(PTH.pali_word_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("created_at", "updated_at"):
                    data[col_name] = value

            db_session.add(PaliWord(**data))

    db_session.commit()

    print("[green]loading PaliRoot rows")
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

    db_session.commit()
    db_session.close()
    print("[bright_green]database restored successfully")
    toc()


restore_db_from_tsvs()
