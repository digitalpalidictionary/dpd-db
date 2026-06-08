#!/usr/bin/env python3

"""Add help and abbreviations to the Lookup table."""

from rich import print
from sqlalchemy import create_engine, inspect as sa_inspect, text

from db.db_helpers import get_db_session
from tools.lookup_sync import sync_lookup_column
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_as_dict, read_tsv_dict


class GlobalVars:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)


def normalize_other_abbreviation_key(key: str) -> str:
    return key[:-1] if key.endswith(".") else key


def add_help(g: GlobalVars) -> None:
    print("[green]adding help")
    help_data = read_tsv_as_dict(g.pth.help_tsv_path)
    data = {key: v["meaning"] for key, v in help_data.items()}
    sync_lookup_column(g.db_session, "help", data)


def ensure_abbrev_other_column(g: GlobalVars) -> None:
    """Add abbrev_other column to lookup table if it doesn't already exist."""
    engine = create_engine(f"sqlite+pysqlite:///{g.pth.dpd_db_path}", echo=False)
    insp = sa_inspect(engine)
    columns = [col["name"] for col in insp.get_columns("lookup")]
    if "abbrev_other" not in columns:
        with engine.connect() as con:
            con.execute(
                text("ALTER TABLE lookup ADD COLUMN abbrev_other TEXT DEFAULT ''")
            )
            con.commit()
        print("[green]added abbrev_other column to lookup")


def add_abbreviations(g: GlobalVars) -> None:
    """Add abbreviations to lookup"""
    print("[green]adding abbreviations")
    abbrevs = read_tsv_as_dict(g.pth.abbreviations_tsv_path)
    sync_lookup_column(g.db_session, "abbrev", abbrevs)


def add_abbreviations_other(g: GlobalVars) -> None:
    """Add other-source abbreviations (PTS, CPD, Cone, CST, General) to lookup."""
    print("[green]adding abbreviations other")

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
    print("[bright_yellow]adding help and abbreviations to lookup")
    g = GlobalVars()
    ensure_abbrev_other_column(g)
    add_help(g)
    add_abbreviations(g)
    add_abbreviations_other(g)
    pr.toc()


if __name__ == "__main__":
    main()
