"""Shared add / update / clear / delete logic for single-column writes to the
Lookup table.

Replaces the per-script copy-paste of ``update_test_add`` + ``is_another_value``
loops. Copies the scoped pattern from ``db/variants/add_to_db.py``: it never loads
the whole 1.29M-row table, only the rows that hold a value in the target column
plus the rows matching the incoming data keys.

Usage::

    from tools.lookup_sync import sync_lookup_column

    data = {key: pali_list_sorter(values) for key, values in source.items()}
    sync_lookup_column(db_session, "see", data)

Pass ``use_raw_sql=True`` to dispatch to a set-based raw SQL upsert instead of
the row-by-row ORM path — ~100x faster for large ``data`` (e.g. 449K entries),
with identical semantics and result counts. See ``_raw_sql_sync``.
"""

from dataclasses import dataclass
from itertools import batched
from typing import Any, cast

from sqlalchemy.orm import Session

from db.models import Lookup
from tools.lookup_is_another_value import is_another_value

LOOKUP_COLUMNS = [c.name for c in Lookup.__table__.columns]


@dataclass
class LookupSyncResult:
    updated: int = 0
    inserted: int = 0
    cleared: int = 0
    deleted: int = 0


def sync_lookup_column(
    db_session: Session,
    column: str,
    data: dict[str, Any],
    *,
    pack_attr: str | None = None,
    clear_stale: bool = True,
    chunk_size: int = 900,
    use_raw_sql: bool = False,
) -> LookupSyncResult:
    """Sync one Lookup column to ``data`` ({lookup_key: value}).

    - ``clear_stale``: clear/delete rows that currently hold a value in ``column``
      but are no longer in ``data``. A stale row is cleared (column set to "") when
      another column still holds a value, otherwise the whole row is deleted.
    - keys in ``data`` are updated if the row exists, inserted otherwise.
    - ``pack_attr`` defaults to ``f"{column}_pack"``; pass it explicitly when the
      column's pack method uses a non-standard name.
      raise on empty input, so clearing always assigns "" directly.
    - ``use_raw_sql``: dispatch to ``_raw_sql_sync``, a set-based raw SQL upsert
      on the session's own connection, instead of the row-by-row ORM path below.
      Same semantics and result counts, much faster for large ``data``.

    Commits internally: once after the stale pass and once per chunk of the
    update/insert loop. Callers do not need to commit afterwards.

    Returns counts of rows updated / inserted / cleared / deleted.
    """

    pack_attr = pack_attr or f"{column}_pack"

    if use_raw_sql:
        return _raw_sql_sync(db_session, column, data, pack_attr, clear_stale)

    col = getattr(Lookup, column)
    result = LookupSyncResult()

    if clear_stale:
        stale_candidates: list[Lookup] = (
            db_session.query(Lookup).filter(col != "").all()
        )
        for row in stale_candidates:
            if row.lookup_key in data:
                continue
            if is_another_value(row, column):
                setattr(row, column, "")
                result.cleared += 1
            else:
                db_session.delete(row)
                result.deleted += 1
        db_session.commit()

    for chunk in batched(data, chunk_size):
        existing = db_session.query(Lookup).filter(Lookup.lookup_key.in_(chunk)).all()
        found: set[str] = set()
        for row in existing:
            getattr(row, pack_attr)(data[row.lookup_key])
            found.add(row.lookup_key)
            result.updated += 1

        new_rows: list[Lookup] = []
        for key in chunk:
            if key not in found:
                new_row = Lookup()
                new_row.lookup_key = key
                getattr(new_row, pack_attr)(data[key])
                new_rows.append(new_row)
        db_session.add_all(new_rows)
        result.inserted += len(new_rows)

        db_session.commit()

    return result


def _raw_sql_sync(
    db_session: Session,
    column: str,
    data: dict[str, Any],
    pack_attr: str,
    clear_stale: bool,
) -> LookupSyncResult:
    """Set-based SQL implementation of sync_lookup_column on the session's own
    connection: one transaction, one executemany upsert, no ORM overhead.
    ~100x faster for large ``data`` (403.8s -> ~4s for 449K entries)."""

    if column not in LOOKUP_COLUMNS:
        raise ValueError(f"unknown Lookup column: {column}")

    result = LookupSyncResult()

    packer = Lookup()
    rows: list[tuple[str, str]] = []
    for key, value in data.items():
        getattr(packer, pack_attr)(value)
        rows.append((key, getattr(packer, column)))

    conn = db_session.connection()
    conn.exec_driver_sql("CREATE TEMP TABLE _lookup_sync_keys (k TEXT PRIMARY KEY)")
    try:
        if data:
            conn.exec_driver_sql(
                "INSERT INTO _lookup_sync_keys (k) VALUES (?)",
                [(key,) for key in data],
            )

        if clear_stale:
            others_empty = " AND ".join(
                f"IFNULL({c}, '') = ''"
                for c in LOOKUP_COLUMNS
                if c not in ("lookup_key", column)
            )
            deleted = conn.exec_driver_sql(
                f"DELETE FROM lookup WHERE {column} != '' "
                "AND lookup_key NOT IN (SELECT k FROM _lookup_sync_keys) "
                f"AND {others_empty}"
            )
            result.deleted = deleted.rowcount
            cleared = conn.exec_driver_sql(
                f"UPDATE lookup SET {column} = '' WHERE {column} != '' "
                "AND lookup_key NOT IN (SELECT k FROM _lookup_sync_keys)"
            )
            result.cleared = cleared.rowcount

        existing = cast(
            int,
            conn.exec_driver_sql(
                "SELECT COUNT(*) FROM lookup "
                "WHERE lookup_key IN (SELECT k FROM _lookup_sync_keys)"
            ).scalar_one(),
        )
        result.updated = existing
        result.inserted = len(data) - existing

        if rows:
            other_columns = [
                c for c in LOOKUP_COLUMNS if c not in ("lookup_key", column)
            ]
            columns_sql = ", ".join(["lookup_key", column, *other_columns])
            placeholders = ", ".join(["?", "?", *["''"] * len(other_columns)])
            conn.exec_driver_sql(
                f"INSERT INTO lookup ({columns_sql}) VALUES ({placeholders}) "
                f"ON CONFLICT(lookup_key) DO UPDATE SET {column} = excluded.{column}",
                rows,
            )
    finally:
        conn.exec_driver_sql("DROP TABLE _lookup_sync_keys")

    db_session.commit()
    return result
