#!/usr/bin/env python3

"""Save latest DpdHeadwords and DpdRoots tables to backup_tsv folder."""

from git import Repo
from rich import print
import csv

from sqlalchemy.orm.session import Session

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, DpdRoots
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths


def backup_dpd_headwords_and_roots(pth: ProjectPaths):
    tic()
    print("[bright_yellow]backing headword and roots tables to tsv")
    db_session = get_db_session(pth.dpd_db_path)
    backup_dpd_headwords(db_session, pth)
    backup_dpd_roots(db_session, pth)
    db_session.close()
    git_commit()
    toc()


def backup_dpd_headwords(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup DpdHeadwords table to TSV."""
    print("[green]writing DpdHeadwords table")
    db = db_session.query(DpdHeadwords).all()

    # Use the custom path if provided, otherwise use the default path
    pali_word_path = custom_path if custom_path else pth.pali_word_path

    with open(pali_word_path, 'w', newline='') as tsvfile:
        exclude_columns = [
            "created_at", "updated_at",
            "inflections", "inflections_sinhala", "inflections_devanagari", "inflections_thai", "inflections_html",
            "freq_html", "ebt_count"]
        
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in DpdHeadwords.__mapper__.columns
            if column.name not in exclude_columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in DpdHeadwords.__mapper__.columns
                if column.name not in exclude_columns]
            csvwriter.writerow(row)


def backup_dpd_roots(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup DpdRoots table to TSV."""
    print("[green]writing DpdRoots table")
    db = db_session.query(DpdRoots).all()

    # Use the custom path if provided, otherwise use the default path
    pali_root_path = custom_path if custom_path else pth.pali_root_path

    with open(pali_root_path, 'w', newline='') as tsvfile:
        exclude_columns = [
            "created_at", "updated_at",
            "root_info", "root_matrix"]
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in DpdRoots.__mapper__.columns
            if column.name not in exclude_columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in DpdRoots.__mapper__.columns
                if column.name not in exclude_columns]
            csvwriter.writerow(row)


def git_commit():
    repo = Repo("./")
    index = repo.index
    index.add(["db/backup_tsv/dpd_roots.tsv", "db/backup_tsv/dpd_headwords.tsv"])
    index.commit("pali update")


if __name__ == "__main__":
    pth = ProjectPaths()
    backup_dpd_headwords_and_roots(pth)
