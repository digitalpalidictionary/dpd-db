#!/usr/bin/env python3.11
import csv
import sys

import datetime
from pathlib import Path
from rich import print

from db.get_db_session import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import PaliWord, PaliRoot
from tools.timeis import tic, toc


def restore_db_from_tsvs():
    tic()
    print("[bright_yellow]restoring db from tsv")

    dpd_db_path = Path("dpd.db")
    pali_word_path = Path("backups/PaliWord.tsv")
    pali_root_path = Path("backups/PaliRoot.tsv")

    if dpd_db_path.exists():
        dpd_db_path.unlink()

    create_db_if_not_exists(dpd_db_path)

    for p in [pali_root_path, pali_word_path]:
        if not p.exists():
            print(f"[bright_red]File does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session(dpd_db_path)
    datetime_format = "%Y-%m-%d %H:%M:%S"

    print("[green]loading PaliWord rows")
    with open(pali_word_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("created_at", "updated_at"):
                    data[col_name] = value
                # else:
                #     if value != "":
                #         value = datetime.datetime.strptime(value, datetime_format)
                #         data[col_name] = value
                #     else:
                #         data[col_name] = value

            db_session.add(PaliWord(**data))

    db_session.commit()

    print("[green]loading PaliRoot rows")
    with open(pali_root_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("created_at", "updated_at"):
                    data[col_name] = value
                # else:
                #     if value != "":
                #         value = datetime.strptime(value, datetime_format)
                #         data[col_name] = value
                #     else:
                #         data[col_name] = value

            db_session.add(PaliRoot(**data))

    db_session.commit()
    print("[bright_green]database restored successfully")
    toc()


restore_db_from_tsvs()
