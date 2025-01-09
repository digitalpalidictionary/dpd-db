#!/usr/bin/env python3

"""filtering words by some condition and make tsv of all tables DpdHeadword, DpdRoot, Russian and SBS into the pth.temp_dir"""

from rich.console import Console

from sqlalchemy.orm.session import Session

import csv
import os

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, Russian, SBS
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths  

from sqlalchemy import and_, or_, null, not_

console = Console()


def saving():
    tic()
    console.print("[bold bright_yellow]saving all tables to tsv")
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Fetch the ids and roots for DpdHeadword table
    # word_records = db_session.query(DpdHeadword.id, DpdHeadword.root_key).filter(DpdHeadword.source_1 == "MN 107").all()
    word_records = db_session.query(DpdHeadword.id).outerjoin(
    SBS, DpdHeadword.id == SBS.id
        ).filter(
                or_(
                    SBS.sbs_example_1 != "",
                    SBS.sbs_example_2 != "",
                    SBS.sbs_example_3 != "",
                    SBS.sbs_example_4 != "",
                )
        ).all()

    #  Get the count of word_records
    word_count = len(word_records)
    console.print(f"Total word records: {word_count}")

    ids_to_saving = [record[0] for record in word_records]
    # roots_to_saving = [record[1] for record in word_records]

    # saving_paliwords(pth, db_session, ids_to_saving)
    # saving_paliroots(pth, db_session, roots_to_saving)
    # saving_russian(pth, db_session, ids_to_saving)
    saving_sbs(dpspth, db_session, ids_to_saving)
    db_session.close()
    toc()


def saving_paliwords(pth: ProjectPaths, db_session: Session, ids_to_saving):
    """saving DpdHeadword table to TSV."""
    console.print("[bold green]writing DpdHeadword table")
    db = db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(ids_to_saving)).all()


    file_path = os.path.join(pth.temp_dir, 'dpd_headwords.tsv')
    with open(file_path, 'w', newline='') as tsvfile:
        exclude_columns = [
            "created_at", "updated_at"]
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in DpdHeadword.__mapper__.columns
            if column.name not in exclude_columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in DpdHeadword.__mapper__.columns
                if column.name not in exclude_columns]
            csvwriter.writerow(row)


def saving_paliroots(pth: ProjectPaths, db_session: Session, roots_to_saving):
    """saving DpdRoot table to TSV."""
    console.print("[bold green]writing DpdRoot table")
    db = db_session.query(DpdRoot).filter(DpdRoot.root.in_(roots_to_saving)).all()


    file_path = os.path.join(pth.temp_dir, 'dpd_roots.tsv')
    with open(file_path, 'w', newline='') as tsvfile:
        exclude_columns = [
            "created_at", "updated_at",
            "root_info", "root_matrix"]
        csvwriter = csv.writer(
            tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        column_names = [
            column.name for column in DpdRoot.__mapper__.columns
            if column.name not in exclude_columns]
        csvwriter.writerow(column_names)

        for i in db:
            row = [
                getattr(i, column.name)
                for column in DpdRoot.__mapper__.columns
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


def saving_sbs(dpspth: DPSPaths, db_session: Session, ids_to_saving):
    """saving SBS tables to TSV."""
    console.print("[bold green]writing SBS table")
    db = db_session.query(SBS).filter(SBS.id.in_(ids_to_saving)).all()

    # file_path = os.path.join(pth.temp_dir, 'sbs.tsv')
    file_path = dpspth.sbs_archive
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
