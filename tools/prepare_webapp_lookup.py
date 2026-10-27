"""Offline preparation for existing source databases (not the mobile database).

Stop writers, back up dpd.db, then run:
    uv run tools/prepare_webapp_lookup.py dpd.db
SQLAlchemy create_all only adds this index for newly created tables.
"""

import argparse
import sqlite3
from pathlib import Path

INDEX_NAME = "ix_lookup_key_nocase"


def prepare_lookup_index(path: Path) -> None:
    """Idempotently prepare the non-unique index, rejecting incompatible data/DDL."""
    with sqlite3.connect(f"{path.resolve().as_uri()}?mode=rw", uri=True) as connection:
        # Obtain the write lock before checking data, so no writer can insert a
        # NUL key between validation and index creation.
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute(
            "SELECT 1 FROM lookup WHERE instr(lookup_key, char(0)) > 0 LIMIT 1"
        ).fetchone():
            raise ValueError("lookup contains NUL keys; retain the legacy lookup")
        existing = connection.execute(
            "SELECT tbl_name FROM sqlite_master WHERE name = ?", (INDEX_NAME,)
        ).fetchone()
        if existing:
            indexes = connection.execute("PRAGMA index_list(lookup)").fetchall()
            match = [row for row in indexes if row[1] == INDEX_NAME]
            columns = connection.execute(
                "PRAGMA index_xinfo(ix_lookup_key_nocase)"
            ).fetchall()
            key_columns = [(row[2], row[3], row[4]) for row in columns if row[5]]
            if (
                existing[0] != "lookup"
                or len(match) != 1
                or match[0][2] != 0
                or match[0][4] != 0
                or key_columns != [("lookup_key", 0, "NOCASE")]
            ):
                raise ValueError(f"{INDEX_NAME} has an incompatible definition")
        else:
            connection.execute(
                "CREATE INDEX ix_lookup_key_nocase ON lookup(lookup_key COLLATE NOCASE)"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path)
    prepare_lookup_index(parser.parse_args().database)


if __name__ == "__main__":
    main()
