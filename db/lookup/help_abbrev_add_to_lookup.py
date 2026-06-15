#!/usr/bin/env python3

"""Add help and abbreviations to the Lookup table."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from tools.lookup_sync import sync_lookup_column
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_as_dict, read_tsv_dict


@dataclass
class GlobalVars:
    pth: ProjectPaths
    db_session: Session


def normalize_other_abbreviation_key(key: str) -> str:
    return key.removesuffix(".")


def add_help(g: GlobalVars) -> None:
    pr.green("adding help")
    help_data = read_tsv_as_dict(g.pth.help_tsv_path)
    data = {key: v["meaning"] for key, v in help_data.items()}
    sync_lookup_column(g.db_session, "help", data)


def add_abbreviations(g: GlobalVars) -> None:
    """Add abbreviations to lookup"""
    pr.green("adding abbreviations")
    abbrevs = read_tsv_as_dict(g.pth.abbreviations_tsv_path)
    sync_lookup_column(g.db_session, "abbrev", abbrevs)


def add_abbreviations_other(g: GlobalVars) -> None:
    """Add other-source abbreviations (PTS, CPD, Cone, CST, General) to lookup."""
    pr.green("adding abbreviations other")

    rows = read_tsv_dict(g.pth.abbreviations_other_tsv_path)
    rows.sort(key=lambda row: normalize_other_abbreviation_key(row["abbreviation"]))

    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        key = normalize_other_abbreviation_key(row["abbreviation"])
        if not key:
            continue
        entry = {
            "source": row["source"],
            "meaning": row["meaning"],
            "notes": row["notes"],
        }
        grouped.setdefault(key, []).append(entry)

    sync_lookup_column(g.db_session, "abbrev_other", grouped)


def main() -> None:
    pr.tic()
    pr.yellow_title("adding help and abbreviations to lookup")
    pth = ProjectPaths()
    g = GlobalVars(pth=pth, db_session=get_db_session(pth.dpd_db_path))
    add_help(g)
    add_abbreviations(g)
    add_abbreviations_other(g)
    pr.toc()


if __name__ == "__main__":
    main()
