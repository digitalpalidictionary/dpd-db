#!/usr/bin/env python3.11

from rich import print
# from sqlalchemy import inspect
import csv

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot
from tools.timeis import tic, toc


def backup_db_to_tsvs():
    print("[bright_yellow]backing up db to tsv")
    print("[green]getting db session")
    db_session = get_db_session("dpd.db")

    print("[green]writing PaliWord")
    db = db_session.query(PaliWord).all()

    with open("backups/PaliWord.tsv", 'w', newline='') as tsvfile:
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        csvwriter.writerow([column.name for column in PaliWord.__mapper__.columns])
        [csvwriter.writerow([getattr(curr, column.name)
                            for column in PaliWord.__mapper__.columns]) for curr in db]

    print("[green]writing PaliRoot")
    db = db_session.query(PaliRoot).all()

    with open("backups/PaliRoot.tsv", 'w', newline='') as tsvfile:
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        csvwriter.writerow(
            [column.name for column in PaliRoot.__mapper__.columns])
        [csvwriter.writerow([getattr(curr, column.name)
                            for column in PaliRoot.__mapper__.columns]) for curr in db]


def main():
    tic()
    backup_db_to_tsvs()
    toc()


if __name__ == "__main__":
    main()
