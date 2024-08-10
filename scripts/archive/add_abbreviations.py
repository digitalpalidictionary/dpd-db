#!/usr/bin/env python3

"""ADd abbreviations to db."""
from rich import print

from db.db_helpers import get_db_session
from db.models import Abbreviations
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Dict, List
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dict


def main():
    tic()
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    csv_path = pth.abbreviations_tsv_path
    add_abbreviations(db_session, csv_path)
    toc()


def add_abbreviations(db_session: Session, csv_path: Path):
    print("[yellow]adding abbreviations to db")

    print("[green]processing abbreviations csv", end=" ")

    file_path = csv_path
    rows = read_tsv_dict(file_path)

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
