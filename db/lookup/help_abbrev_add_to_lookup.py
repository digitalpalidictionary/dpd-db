#!/usr/bin/env python3

"""Add help and abbreviations to the Lookup table."""

from rich import print
from sqlalchemy import create_engine, inspect as sa_inspect, text

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_as_dict, read_tsv_dict


class GlobalVars:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)


def normalize_other_abbreviation_key(key: str) -> str:
    return key[:-1] if key.endswith(".") else key


def add_help(g: GlobalVars):
    print("[green]adding help")

    # first remove old abbreviations from the table
    results = g.db_session.query(Lookup).filter(Lookup.help != "").all()
    for r in results:
        if is_another_value(r, "help"):
            r.help = ""
        else:
            g.db_session.delete(r)

    help_data = read_tsv_as_dict(g.pth.help_tsv_path)

    # then update with new values
    for key, values in help_data.items():
        # query the key in Lookup table
        results = g.db_session.query(Lookup).filter_by(lookup_key=key).first()

        # if it exists, then update help column
        if results:
            results.help_pack(values["meaning"])

        # if not, add it
        else:
            lkp = Lookup()
            lkp.lookup_key = key
            lkp.help_pack(values["meaning"])
            g.db_session.add(lkp)

    g.db_session.commit()


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


def add_abbreviations(g: GlobalVars):
    """Add abbreviations to lookup"""
    print("[green]adding abbreviations")

    # first remove old abbreviations from the table
    results = g.db_session.query(Lookup).filter(Lookup.abbrev != "").all()
    for r in results:
        if is_another_value(r, "abbrev"):
            r.abbrev = ""
        else:
            g.db_session.delete(r)

    abbrevs = read_tsv_as_dict(g.pth.abbreviations_tsv_path)

    # then update with new values
    for key, values in abbrevs.items():
        # query the key in Lookup table
        results = g.db_session.query(Lookup).filter_by(lookup_key=key).first()

        # if it exists, then update abbrev column
        if results:
            results.abbrev_pack(values)

        # if not, add it
        else:
            lu = Lookup()
            lu.lookup_key = key
            lu.abbrev_pack(values)
            g.db_session.add(lu)

    g.db_session.commit()


def add_abbreviations_other(g: GlobalVars) -> None:
    """Add other-source abbreviations (PTS, CPD, Cone, CST, General) to lookup."""
    print("[green]adding abbreviations other")

    # first remove old abbrev_other entries from the table
    results = g.db_session.query(Lookup).filter(Lookup.abbrev_other != "").all()
    for r in results:
        if is_another_value(r, "abbrev_other"):
            r.abbrev_other = ""
        else:
            g.db_session.delete(r)

    rows = read_tsv_dict(g.pth.abbreviations_other_tsv_path)
    rows.sort(key=lambda row: normalize_other_abbreviation_key(row["abbreviation"]))

    # Group by abbreviation after dropping a final full stop so dotted and
    # undotted forms become one lookup entry. Sorting first by abbreviation
    # preserves a stable, easy-to-review row order inside each group.
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

    # upsert into Lookup
    for key, entries in grouped.items():
        result = g.db_session.query(Lookup).filter_by(lookup_key=key).first()
        if result:
            result.abbrev_other_pack(entries)
        else:
            lu = Lookup()
            lu.lookup_key = key
            lu.abbrev_other_pack(entries)
            g.db_session.add(lu)

    g.db_session.commit()


def main():
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
