#!/usr/bin/env python3

"""Save latest Russian,ru roots and SBS tables to backup_tsv folder."""


from git import Repo
from rich import print
import csv

from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import Russian, SBS, DpdRoot
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths


def backup_ru_sbs():
    tic()
    print("[bright_yellow]backing russian and sbs tables to tsv")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    backup_russian(db_session, pth)
    backup_sbs(db_session, pth)
    backup_ru_roots(db_session, pth)
    db_session.close()
    toc()


def backup_russian(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup Russian table to TSV."""
    print("[green]Checking Russian table")

    # Query the Russian table
    db = db_session.query(Russian).all()

    # Check if the table is empty
    if not db:
        print("[red]Error: The Russian table is empty. Backup aborted.")
        return

    # Proceed with backup if the table is not empty
    print("[green]Writing Russian table")

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
    print("[green]Checking SBS table")

    # Query the SBS table
    db = db_session.query(SBS).all()

    # Check if the table is empty
    if not db:
        print("[red]Error: The SBS table is empty. Backup aborted.")
        return

    # Proceed with backup if the table is not empty
    print("[green]writing SBS table")

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


def backup_ru_roots(db_session: Session, pth: ProjectPaths, custom_path: str = ""):
    """Backup Ru columns from the DpdRoot to TSV."""
    print("[green]Checking DpdRoot table")

    # Query DpdRoot table
    db = db_session.query(DpdRoot).all()

    # Check if the table is empty
    if not db:
        print("[red]Error: DpdRoot table is empty. Backup aborted.")
        return

    # Proceed with backup if the table is not empty
    print("[green]writing Ru columns from the DpdRoot table")

    # Check for rows where root.sanskrit_root is not "-" and root_sanskrit_root_ru_meaning is empty
    for record in db:
        if record.sanskrit_root != "-" and not record.sanskrit_root_ru_meaning:
            print(f"[red]No root_sanskrit_root_ru_meaning: {record}")
        if not record.root_ru_meaning:
            print(f"[red]No root_ru_meaning: {record}")


    # Use the custom path if provided, otherwise use the default path
    ru_root_path = custom_path if custom_path else pth.ru_root_path

    with open(ru_root_path, 'w', newline='') as tsvfile:
        used_columns = [
            "root",
            "root_ru_meaning", "sanskrit_root_ru_meaning"
            ]
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in DpdRoot.__mapper__.columns
            if column.name in used_columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in DpdRoot.__mapper__.columns
                if column.name in used_columns]
            csvwriter.writerow(row)



def git_commit():
    repo = Repo("./")
    index = repo.index
    index.add(["db/backup_tsv/russian.tsv", "db/backup_tsv/sbs.tsv", "db/backup_tsv/ru_roots.tsv"])
    index.commit("backup russian & sbs")


if __name__ == "__main__":
    backup_ru_sbs()
