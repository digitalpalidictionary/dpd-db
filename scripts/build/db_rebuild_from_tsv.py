#!/usr/bin/env python3

"""Rebuild the database from scratch from files in backup_tsv folder."""

import csv
import sys

from rich import print

from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.db_helpers import create_db_if_not_exists
from db.models import DpdHeadword, DpdRoot, Russian, SBS
from tools.printer import p_green, p_green_title, p_red, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from tools.configger import config_update, config_test


def main():
    tic()
    p_title("rebuilding db from tsvs")
    
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

    for p in [
        pth.pali_root_path,
        pth.pali_word_path,
        pth.russian_path,
        pth.sbs_path
    ]:
        if not p.exists():
            p_red(f"TSV backup file does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session(pth.dpd_db_path)

    make_pali_word_table_data(pth, db_session)
    make_pali_root_table_data(pth, db_session)
    make_russian_table_data(pth, db_session)
    make_sbs_table_data(pth, db_session)
    make_ru_root_table_data(pth, db_session)
    
    p_green("committing to db")
    db_session.commit()
    db_session.close()
    p_yes("ok")
    p_green_title("database restored successfully")
    toc()


def make_pali_word_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return DpdHeadword table data."""

    p_green("creating DpdHeadword table data")
    counter=0
    with open(pth.pali_word_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in ("user_id", "created_at", "updated_at"):
                    data[col_name] = value
            db_session.add(DpdHeadword(**data))
            counter+=1
    p_yes(counter)


def make_pali_root_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return DpdRoot table data."""
    p_green("creating DpdRoot table data")
    counter=0
    with open(pth.pali_root_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                if col_name not in (
                    "created_at", "updated_at",
                        "root_info", "root_matrix",
                        "root_ru_meaning", "sanskrit_root_ru_meaning"):
                    data[col_name] = value
            db_session.add(DpdRoot(**data))
            counter+=1
    p_yes(counter)


def make_russian_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return Russian table data."""
    p_green("creating Russian table data")
    counter=0
    with open(pth.russian_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(Russian(**data))
            counter+=1
    p_yes(counter)


def make_sbs_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return SBS table data."""
    p_green("creating SBS table data")
    counter = 0
    with open(pth.sbs_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                data[col_name] = value
            db_session.add(SBS(**data))
            counter+=1
    p_yes(counter)


def make_ru_root_table_data(pth: ProjectPaths, db_session: Session):
    """Read TSV and return ru columns from DpdRoot."""
    p_green("filling ru in DpdRoot table")
    counter=0
    with open(pth.ru_root_path, 'r', newline='') as tsvfile:
        csvreader = csv.reader(tsvfile, delimiter="\t", quotechar='"')
        columns = next(csvreader)
        for row in csvreader:
            data = {}
            for col_name, value in zip(columns, row):
                # Include 'root' in the data dictionary
                data[col_name] = value
            existing_record = db_session.query(DpdRoot).filter_by(root=data['root']).first()
            if existing_record:
                for key, value in data.items():
                    setattr(existing_record, key, value)
            else:
                db_session.add(DpdRoot(**data))
            counter+=1
    p_yes(counter)


if __name__ == "__main__":
    main()
