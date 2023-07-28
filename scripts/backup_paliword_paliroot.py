#!/usr/bin/env python3

"""Save latest PaliWord and PaliRoot tables to backup_tsv folder."""

from git import Repo
from rich import print
import csv

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths as PTH


def backup_paliword_paliroot():
    tic()
    print("[bright_yellow]backing paliword and paliroot tables to tsv")
    db_session = get_db_session("dpd.db")
    backup_paliwords(db_session, PTH)
    backup_paliroots(db_session, PTH)
    db_session.close()
    git_commit()
    toc()


def backup_paliwords(db_session, PTH):
    """Backup PaliWord table to TSV."""
    print("[green]writing PaliWord table")
    db = db_session.query(PaliWord).all()

    with open(PTH.pali_word_path, 'w', newline='') as tsvfile:
        exclude_columns = [
            "created_at", "updated_at"]
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in PaliWord.__mapper__.columns
            if column.name not in exclude_columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in PaliWord.__mapper__.columns
                if column.name not in exclude_columns]
            csvwriter.writerow(row)


def backup_paliroots(db_session, PTH):
    """Backup PaliRoot table to TSV."""
    print("[green]writing PaliRoot table")
    db = db_session.query(PaliRoot).all()

    with open(PTH.pali_root_path, 'w', newline='') as tsvfile:
        exclude_columns = [
            "created_at", "updated_at",
            "root_info", "root_matrix"]
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in PaliRoot.__mapper__.columns
            if column.name not in exclude_columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in PaliRoot.__mapper__.columns
                if column.name not in exclude_columns]
            csvwriter.writerow(row)


def git_commit():
    repo = Repo("./")
    index = repo.index
    index.add(["backup_tsv/paliroot.tsv", "backup_tsv/paliword.tsv"])
    index.commit("backup paliword & paliroot")


if __name__ == "__main__":
    backup_paliword_paliroot()
