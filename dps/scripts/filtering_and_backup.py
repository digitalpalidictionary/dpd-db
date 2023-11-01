#!/usr/bin/env python3

"""filtering words by some condition and make tsv of all tables PaliWord, PaliRoot, Russian and SBS into the PTH.temp_dir"""

from rich.console import Console

from sqlalchemy.orm.session import Session

import csv
import os

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot, Russian, SBS
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths

console = Console()


def saving():
    tic()
    console.print("[bold bright_yellow]saving all tables to tsv")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Fetch the ids and roots for PaliWord table
    word_records = db_session.query(PaliWord.id, PaliWord.root_key).filter(PaliWord.source_1 == "MN 107").all()
    ids_to_saving = [record[0] for record in word_records]
    roots_to_saving = [record[1] for record in word_records]

    saving_paliwords(pth, db_session, ids_to_saving)
    saving_paliroots(pth, db_session, roots_to_saving)
    saving_russian(pth, db_session, ids_to_saving)
    saving_sbs(pth, db_session, ids_to_saving)
    db_session.close()
    toc()


def saving_paliwords(pth: ProjectPaths, db_session: Session, ids_to_saving):
    """saving PaliWord table to TSV."""
    console.print("[bold green]writing PaliWord table")
    db = db_session.query(PaliWord).filter(PaliWord.id.in_(ids_to_saving)).all()


    file_path = os.path.join(pth.temp_dir, 'paliword.tsv')
    with open(file_path, 'w', newline='') as tsvfile:
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


def saving_paliroots(pth: ProjectPaths, db_session: Session, roots_to_saving):
    """saving PaliRoot table to TSV."""
    console.print("[bold green]writing PaliRoot table")
    db = db_session.query(PaliRoot).filter(PaliRoot.root.in_(roots_to_saving)).all()


    file_path = os.path.join(pth.temp_dir, 'paliroot.tsv')
    with open(file_path, 'w', newline='') as tsvfile:
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


def saving_russian(pth: ProjectPaths, db_session: Session, ids_to_saving):
    """saving Russian table to TSV."""
    console.print("[bold green]writing Russian table")
    db = db_session.query(Russian).filter(Russian.id.in_(ids_to_saving)).all()


    file_path = os.path.join(pth.temp_dir, 'russian.tsv')
    with open(file_path, 'w', newline='') as tsvfile:
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


def saving_sbs(pth: ProjectPaths, db_session: Session, ids_to_saving):
    """saving SBS tables to TSV."""
    console.print("[bold green]writing SBS table")
    db = db_session.query(SBS).filter(SBS.id.in_(ids_to_saving)).all()


    file_path = os.path.join(pth.temp_dir, 'sbs.tsv')
    with open(file_path, 'w', newline='') as tsvfile:

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
    saving()
