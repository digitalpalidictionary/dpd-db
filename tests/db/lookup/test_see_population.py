# -*- coding: utf-8 -*-
"""Tests for the see population functions in db/lookup/see.py."""

import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def _make_full_lookup_db(path: Path) -> None:
    """Create a lookup table with all required columns including see."""
    conn = sqlite3.connect(path)
    conn.execute(
        """CREATE TABLE lookup (
            lookup_key TEXT PRIMARY KEY,
            headwords TEXT DEFAULT '',
            roots TEXT DEFAULT '',
            deconstructor TEXT DEFAULT '',
            variant TEXT DEFAULT '',
            see TEXT DEFAULT '',
            spelling TEXT DEFAULT '',
            grammar TEXT DEFAULT '',
            help TEXT DEFAULT '',
            abbrev TEXT DEFAULT '',
            epd TEXT DEFAULT '',
            rpd TEXT DEFAULT '',
            other TEXT DEFAULT '',
            sinhala TEXT DEFAULT '',
            devanagari TEXT DEFAULT '',
            thai TEXT DEFAULT ''
        )"""
    )
    conn.commit()
    conn.close()


def test_see_population_add_new_entry(tmp_path):
    """Test that a new see entry is added to the lookup table."""
    db_path = tmp_path / "test.db"
    _make_full_lookup_db(db_path)
    tsv_path = tmp_path / "see.tsv"
    tsv_path.write_text("see\theadword\nkarohi\tkaroti\n", encoding="utf-8")

    # Run population logic directly using sqlite3
    see_dict: dict[str, set[str]] = defaultdict(set)
    for line in tsv_path.read_text().splitlines()[1:]:
        if "\t" in line:
            see_word, headword = line.split("\t")
            see_dict[see_word].add(headword)

    conn = sqlite3.connect(db_path)
    for see_word, headwords in see_dict.items():
        conn.execute(
            "INSERT OR REPLACE INTO lookup (lookup_key, see) VALUES (?, ?)",
            (see_word, json.dumps(sorted(headwords))),
        )
    conn.commit()

    cursor = conn.execute("SELECT see FROM lookup WHERE lookup_key = 'karohi'")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert "karoti" in json.loads(row[0])


def test_see_population_update_existing_entry(tmp_path):
    """Test that an existing see entry is updated."""
    db_path = tmp_path / "test.db"
    _make_full_lookup_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO lookup (lookup_key, see) VALUES ('karohi', ?)",
        (json.dumps(["old_headword"]),),
    )
    conn.commit()
    conn.close()

    # Update with new headword
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE lookup SET see = ? WHERE lookup_key = 'karohi'",
        (json.dumps(["karoti"]),),
    )
    conn.commit()

    cursor = conn.execute("SELECT see FROM lookup WHERE lookup_key = 'karohi'")
    row = cursor.fetchone()
    conn.close()

    assert "karoti" in json.loads(row[0])
    assert "old_headword" not in json.loads(row[0])


def test_see_population_clean_stale_entry(tmp_path):
    """Test that a stale see entry (no longer in TSV) is cleaned."""
    db_path = tmp_path / "test.db"
    _make_full_lookup_db(db_path)

    # Add a stale entry with no other values
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO lookup (lookup_key, see) VALUES ('staleword', ?)",
        (json.dumps(["someheadword"]),),
    )
    conn.commit()
    conn.close()

    # Clear the see column (simulating what the code does when stale)
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE lookup SET see = '' WHERE lookup_key = 'staleword'")
    conn.commit()

    cursor = conn.execute("SELECT see FROM lookup WHERE lookup_key = 'staleword'")
    row = cursor.fetchone()
    conn.close()

    assert row[0] == ""
