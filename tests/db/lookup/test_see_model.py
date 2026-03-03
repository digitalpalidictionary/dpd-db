# -*- coding: utf-8 -*-
"""Tests for the Lookup.see column pack/unpack and migration idempotency."""

import sqlite3
from pathlib import Path

from db.models import Lookup


def test_see_pack_stores_json():
    """Test that see_pack stores a JSON list."""
    row = Lookup()
    row.see_pack(["karoti", "kāreti"])
    assert row.see == '["karoti", "kāreti"]'


def test_see_unpack_returns_list():
    """Test that see_unpack returns a list from JSON."""
    row = Lookup()
    row.see_pack(["karoti"])
    result = row.see_unpack
    assert isinstance(result, list)
    assert "karoti" in result


def test_see_unpack_empty_returns_empty_list():
    """Test that see_unpack returns [] when column is empty."""
    row = Lookup()
    row.see = ""
    assert row.see_unpack == []


def test_see_pack_raises_on_empty_list():
    """Test that see_pack raises ValueError for empty list."""
    row = Lookup()
    try:
        row.see_pack([])
        assert False, "Expected ValueError"
    except ValueError:
        pass


def _make_lookup_db(path: Path) -> None:
    """Create a minimal lookup table without the see column."""
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE lookup (lookup_key TEXT PRIMARY KEY, headwords TEXT DEFAULT '')"
    )
    conn.commit()
    conn.close()


def test_migration_adds_see_column(tmp_path):
    """Test that the migration adds the see column when absent."""
    from db.lookup.see import migrate_add_see_column

    db_path = tmp_path / "test.db"
    _make_lookup_db(db_path)

    migrate_add_see_column(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(lookup)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    assert "see" in columns


def test_migration_idempotent(tmp_path):
    """Test that running migration twice does not raise an error."""
    from db.lookup.see import migrate_add_see_column

    db_path = tmp_path / "test.db"
    _make_lookup_db(db_path)

    migrate_add_see_column(db_path)
    migrate_add_see_column(db_path)  # second run should be a no-op

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(lookup)")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()
    assert columns.count("see") == 1
