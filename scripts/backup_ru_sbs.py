#!/usr/bin/env python3.11

from rich import print
import csv

from db.get_db_session import get_db_session
from db.models import Russian, SBS
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths as PTH


def backup_ru_sbs():
    tic()
    print("[bright_yellow]backing russian and sbs tables to tsv")
    db_session = get_db_session("dpd.db")
    backup_russian(db_session, PTH)
    backup_sbs(db_session, PTH)
    db_session.close()
    toc()


def backup_russian(db_session, PTH):
    """Backup Russian table to TSV."""
    print("[green]writing Russian table")
    db = db_session.query(Russian).all()

    with open(PTH.russian_path, 'w', newline='') as tsvfile:
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in Russian.__mapper__.columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in Russian.__mapper__.columns]
            csvwriter.writerow(row)


def backup_sbs(db_session, PTH):
    """Backup SBS tables to TSV."""
    print("[green]writing SBS table")
    db = db_session.query(SBS).all()

    with open(PTH.sbs_path, 'w', newline='') as tsvfile:

        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in SBS.__mapper__.columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in SBS.__mapper__.columns]
            csvwriter.writerow(row)


if __name__ == "__main__":
    backup_ru_sbs()
