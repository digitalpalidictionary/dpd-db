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
"""

from dataclasses import dataclass
from itertools import batched
from typing import Any

from sqlalchemy.orm import Session

from db.models import Lookup
from tools.lookup_is_another_value import is_another_value


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
) -> LookupSyncResult:
    """Sync one Lookup column to ``data`` ({lookup_key: value}).

    - ``clear_stale``: clear/delete rows that currently hold a value in ``column``
      but are no longer in ``data``. A stale row is cleared (column set to "") when
      another column still holds a value, otherwise the whole row is deleted.
    - keys in ``data`` are updated if the row exists, inserted otherwise.
    - ``pack_attr`` defaults to ``f"{column}_pack"``; pass it explicitly for the one
      irregular column (``variant`` -> ``variants_pack``). The ``*_pack`` methods
      raise on empty input, so clearing always assigns "" directly.

    Commits internally: once after the stale pass and once per chunk of the
    update/insert loop. Callers do not need to commit afterwards.

    Returns counts of rows updated / inserted / cleared / deleted.
    """

    pack_attr = pack_attr or f"{column}_pack"
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
        db_session.expunge_all()

    return result
