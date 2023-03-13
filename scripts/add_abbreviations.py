#!/usr/bin/env python3.11

import csv
from rich import print

from db.get_db_session import get_db_session
from db.models import Abbreviations
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Dict, List
from tools.timeis import tic, toc, bip, bop


def main():
    tic()
    db_session = get_db_session("dpd.db")
    csv_path = "../exporter/assets/abbreviations.tsv"
    add_abbreviations(db_session, csv_path)
    toc()


def add_abbreviations(db_session: Session, csv_path: Path):
    print("[yellow]adding abbreviations to db")

    print("[green]processing abbreviations csv", end=" ")

    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)

    items: List[Abbreviations] = list(map(_csv_row_to_abbrev, rows))

    print("[green]adding to db", end=" ")
    try:
        for i in items:
            db_session.add(i)
        db_session.commit()

    except Exception as e:
        print(f"[bright_red]ERROR: Adding to db failed:\n{e}")


def _csv_row_to_abbrev(x: Dict[str, str]) -> Abbreviations:
    return Abbreviations(
        abbrev=x['abbrev'],
        meaning=x['meaning'],
        pali=x['pāli'],
        example=x['example'],
        explanation=x['explanation'],
    )


if __name__ == "__main__":
    main()
