#!/usr/bin/env python3.11

from git import Repo
# from git import Actor
from datetime import datetime
from rich import print
# from sqlalchemy import inspect
import csv

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot
from tools.timeis import tic, toc


def backup_paliwords(db_session):
    print("[bright_yellow]backing up db to tsv")
    print("[green]getting db session")

    print("[green]writing PaliWord")
    db = db_session.query(PaliWord).all()

    with open("backups/PaliWord.tsv", 'w', newline='') as tsvfile:
        exclude_columns = [
            "created_at", "updated_at"]

        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)

        column_names = [
            column.name for column in PaliWord.__mapper__.columns
            if column.name not in exclude_columns]

        csvwriter.writerow(column_names)

        for curr in db:
            row = [
                getattr(curr, column.name)
                for column in PaliWord.__mapper__.columns
                if column.name not in exclude_columns]
            csvwriter.writerow(row)


def backup_paliroots(db_session):
    print("[green]writing PaliRoot")
    db = db_session.query(PaliRoot).all()

    with open("backups/PaliRoot.tsv", 'w', newline='') as tsvfile:

        exclude_columns = [
            "created_at", "updated_at",
            "root_info", "root_matrix"]

        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)

        column_names = [
            column.name for column in PaliRoot.__mapper__.columns
            if column.name not in exclude_columns]

        csvwriter.writerow(column_names)

        for curr in db:
            row = [
                getattr(curr, column.name)
                for column in PaliRoot.__mapper__.columns
                if column.name not in exclude_columns]
            csvwriter.writerow(row)


def git_commit():
    today = datetime.today()
    date = datetime.date(today)
    repo = Repo("backups/")
    index = repo.index
    index.add(["PaliRoot.tsv", "PaliWord.tsv"])
    index.commit(f"update {date}")


def db_to_tsv():
    tic()
    db_session = get_db_session("dpd.db")
    backup_paliwords(db_session)
    backup_paliroots(db_session)
    git_commit()
    db_session.close()
    toc()


if __name__ == "__main__":
    db_to_tsv()
