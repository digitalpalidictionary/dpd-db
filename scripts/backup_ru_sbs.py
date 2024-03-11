#!/usr/bin/env python3

"""Save latest Russian and SBS tables to backup_tsv folder."""


from git import Repo
from rich import print
import csv

from sqlalchemy.orm.session import Session

from db.get_db_session import get_db_session
from db.models import Russian, SBS
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths


def backup_ru_sbs():
    tic()
    print("[bright_yellow]backing russian and sbs tables to tsv")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    backup_russian(db_session, pth)
    backup_sbs(db_session, pth)
    db_session.close()
    toc()


def backup_russian(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup Russian table to TSV."""
    print("[green]writing Russian table")
    db = db_session.query(Russian).all()

    # Use the custom path if provided, otherwise use the default path
    russian_path = custom_path if custom_path else pth.russian_path

    with open(russian_path, 'w', newline='') as tsvfile:
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


def backup_sbs(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup SBS tables to TSV."""
    print("[green]writing SBS table")
    db = db_session.query(SBS).all()

    # Use the custom path if provided, otherwise use the default path
    sbs_path = custom_path if custom_path else pth.sbs_path

    with open(sbs_path, 'w', newline='') as tsvfile:

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


def git_commit():
    repo = Repo("./")
    index = repo.index
    index.add(["db/backup_tsv/russian.tsv", "db/backup_tsv/sbs.tsv"])
    index.commit("backup russian & sbs")


if __name__ == "__main__":
    backup_ru_sbs()
