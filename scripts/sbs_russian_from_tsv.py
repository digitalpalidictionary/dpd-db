#!/usr/bin/env python3.11

import sys
import csv

from rich import print
from typing import Dict, List
from pathlib import Path
from sqlalchemy.orm import Session

from db.models import Russian, SBS, PaliWord
from db.get_db_session import get_db_session
from tools.timeis import tic, toc


def main():
    tic()
    print("[bright_yellow]add dps.tsv to db")
    dps_tsv_path = Path("csvs/dps.tsv")

    for p in [dps_tsv_path]:
        if not p.exists():
            print(f"[bright_red]File does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session("dpd.db")

    db_session.execute(Russian.__table__.delete())
    add_dps_russian(db_session, dps_tsv_path)
    add_dps_sbs(db_session, dps_tsv_path)

    db_session.close()
    toc()


def add_dps_russian(db_session: Session, csv_path: Path):
    print("[green]processing dps russian")

    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            for key, value in row.items():
                row[key] = value.replace("<br/>", "\n")
            rows.append(row)

    items: List[Russian] = []

    for r in rows:
        id_search = db_session.query(PaliWord.id).filter(
            PaliWord.user_id == r["ID"]).first()

        if id_search is not None:
            id = id_search[0]
            items += [_csv_row_to_russian(r, id)]

    print("[green]adding russian to db")
    try:
        for i in items:
            db_session.add(i)

        db_session.commit()

    except Exception as e:
        print(f"[bright_red]ERROR: Adding to db failed:\n{e}")


def _csv_row_to_russian(x: Dict[str, str], id) -> Russian:

    return Russian(
        id=id,
        ru_meaning=x['Meaning in native language'],
    )


def add_dps_sbs(db_session: Session, csv_path: Path):
    print("[green]processing dps sbs")

    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            for key, value in row.items():
                row[key] = value.replace("<br/>", "\n")
            rows.append(row)

    items: List[SBS] = []

    for r in rows:
        id_search = db_session.query(PaliWord.id).filter(
            PaliWord.user_id == r["ID"]).first()

        if id_search is not None:
            id = id_search[0]
            items += [_csv_row_to_sbs(r, id)]

    print("[green]adding sbs to db")
    try:
        for i in items:
            db_session.add(i)

        db_session.commit()

    except Exception as e:
        print(f"[bright_red]ERROR: Adding to db failed:\n{e}")


def _csv_row_to_sbs(x: Dict[str, str], id) -> SBS:

    return SBS(
        id=id,
        sbs_class_anki=x["ex"],
        sbs_class=x["class"],
        sbs_meaning=x["Meaning in SBS-PER"],
        # sbs_notes=x["Notes SBS"],
        sbs_chant_pali_1=x["Pali chant 1"],
        sbs_chant_eng_1=x["English chant 1"],
        sbs_chapter_1=x["Chapter 1"],
        sbs_chant_pali_2=x["Pali chant 2"],
        sbs_chant_eng_2=x["English chant 2"],
        sbs_chapter_2=x["Chapter 2"],
        sbs_source_3=x["Source3"],
        sbs_sutta_3=x["Sutta3"],
        sbs_example_3=x["Example3"],
        sbs_chant_pali_3=x["Pali chant 3"],
        sbs_chant_eng_3=x["English chant 3"],
        sbs_chapter_3=x["Chapter 3"],
        sbs_source_4=x["Source4"],
        sbs_sutta_4=x["Sutta4"],
        sbs_example_4=x["Example4"],
        sbs_chant_pali_4=x["Pali chant 4"],
        sbs_chant_eng_4=x["English chant 4"],
        sbs_chapter_4=x["Chapter 4"],
        sbs_index=x["Index"],
        sbs_category=x["Test"],
        sbs_audio=x["audio"],
    )


if __name__ == "__main__":
    main()
