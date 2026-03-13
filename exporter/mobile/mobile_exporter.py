#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export a trimmed, mobile-optimised SQLite database for the DPD Flutter app.

Keep DB_SCHEMA_VERSION in sync with AppDatabase.requiredDbSchemaVersion in
lib/database/database.dart. Bump both when the Drift table definitions change.
"""

import re
import sqlite3
import unicodedata

from aksharamukha import transliterate

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.zip_up import zip_up_file


# Columns copied as-is from dpd_headwords.
# Dropped: inflections*, freq_html, derivative, non_root_in_comps, created_at, updated_at
HEADWORD_COLUMNS: list[str] = [
    "id",
    "lemma_1",
    "lemma_2",
    "pos",
    "grammar",
    "derived_from",
    "neg",
    "verb",
    "trans",
    "plus_case",
    "meaning_1",
    "meaning_lit",
    "meaning_2",
    "non_ia",
    "sanskrit",
    "root_key",
    "root_sign",
    "root_base",
    "family_root",
    "family_word",
    "family_compound",
    "family_idioms",
    "family_set",
    "construction",
    "suffix",
    "phonetic",
    "compound_type",
    "compound_construction",
    "source_1",
    "sutta_1",
    "example_1",
    "source_2",
    "sutta_2",
    "example_2",
    "antonym",
    "synonym",
    "variant",
    "var_phonetic",
    "var_text",
    "commentary",
    "notes",
    "cognate",
    "link",
    "origin",
    "stem",
    "pattern",
    "freq_data",
    "ebt_count",
]

# Columns copied as-is from dpd_roots.
# Dropped: html blobs (root_info, root_matrix), matrix_test, created_at, updated_at
ROOT_COLUMNS: list[str] = [
    "root",
    "root_in_comps",
    "root_has_verb",
    "root_group",
    "root_sign",
    "root_meaning",
    "sanskrit_root",
    "sanskrit_root_meaning",
    "sanskrit_root_class",
    "root_example",
    "dhatupatha_num",
    "dhatupatha_root",
    "dhatupatha_pali",
    "dhatupatha_english",
    "dhatumanjusa_num",
    "dhatumanjusa_root",
    "dhatumanjusa_pali",
    "dhatumanjusa_english",
    "dhatumala_root",
    "dhatumala_pali",
    "dhatumala_english",
    "panini_root",
    "panini_sanskrit",
    "panini_english",
    "note",
]

# family_root keeps html column because Flutter Drift schema defines it
# (even though it's not rendered — keeps schema compatibility)
FAMILY_ROOT_COLUMNS: list[str] = [
    "root_family_key",
    "root_key",
    "root_family",
    "root_meaning",
    "html",
    "data",
    "count",
]

# These family tables drop the html column — Flutter Drift schema doesn't include it
FAMILY_WORD_COLUMNS: list[str] = ["word_family", "data", "count"]
FAMILY_COMPOUND_COLUMNS: list[str] = ["compound_family", "data", "count"]
FAMILY_IDIOM_COLUMNS: list[str] = ["idiom", "data", "count"]
FAMILY_SET_COLUMNS: list[str] = ["set", "data", "count"]

# Must match AppDatabase.requiredDbSchemaVersion in the Flutter app.
# Bump when Drift table definitions change (added/removed columns).
DB_SCHEMA_VERSION: int = 2

# Tables copied verbatim from source db (no html columns in these)
PASSTHROUGH_TABLES: list[str] = [
    "sutta_info",
    "inflection_templates",
    "db_info",
]


def _strip_diacritics_mobile(text: str) -> str:
    text = text.replace("√", "").replace(" ", "")
    normalized = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    result = unicodedata.normalize("NFC", stripped).lower()
    return re.sub(r"([kgcjtdpb])h", r"\1", result)


class GlobalVars:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.src = sqlite3.connect(self.pth.dpd_db_path)
        self.src.row_factory = sqlite3.Row


def _copy_selected_columns(
    src: sqlite3.Connection,
    dest: sqlite3.Connection,
    table: str,
    columns: list[str],
    indexes: bool = True,
) -> None:
    src.row_factory = sqlite3.Row
    col_list = ", ".join(f'"{c}"' for c in columns)
    rows = src.execute(f'SELECT {col_list} FROM "{table}"').fetchall()

    placeholders = ", ".join(["?"] * len(columns))
    dest.execute(f'CREATE TABLE "{table}" ({col_list})')
    if rows:
        dest.executemany(
            f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})',
            [tuple(r) for r in rows],
        )

    if indexes:
        for idx in src.execute(
            f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table}' AND sql IS NOT NULL"
        ).fetchall():
            try:
                dest.execute(idx[0])
            except sqlite3.OperationalError:
                pass

    pr.yes(len(rows))


def _lemma_clean(lemma_1: str) -> str:
    return re.sub(r" \d.*$", "", lemma_1)


def export_headwords(g: GlobalVars, dest: sqlite3.Connection) -> None:
    pr.green_tmr("exporting dpd_headwords")

    src_col_list = ", ".join(f'"{c}"' for c in HEADWORD_COLUMNS)
    rows = g.src.execute(f"SELECT {src_col_list} FROM dpd_headwords").fetchall()

    # Batch-compute IPA for all unique lemma_clean values in one call
    lemmas_clean = [_lemma_clean(r["lemma_1"]) for r in rows]
    unique_lemmas = list(dict.fromkeys(lemmas_clean))
    joined = "\n".join(unique_lemmas)
    ipa_joined = transliterate.process("IASTPali", "IPA", joined) or ""
    ipa_list = ipa_joined.split("\n")
    ipa_map: dict[str, str] = dict(zip(unique_lemmas, ipa_list))

    dest_cols = HEADWORD_COLUMNS + ["lemma_ipa"]
    col_list = ", ".join(f'"{c}"' for c in dest_cols)
    placeholders = ", ".join(["?"] * len(dest_cols))

    dest.execute(f"CREATE TABLE dpd_headwords ({col_list})")
    batch = [
        tuple(r[c] for c in HEADWORD_COLUMNS) + (ipa_map.get(lemmas_clean[i], ""),)
        for i, r in enumerate(rows)
    ]
    dest.executemany(
        f"INSERT INTO dpd_headwords ({col_list}) VALUES ({placeholders})", batch
    )
    dest.execute("CREATE INDEX idx_headwords_id ON dpd_headwords (id)")
    dest.execute("CREATE INDEX idx_headwords_lemma_1 ON dpd_headwords (lemma_1)")
    dest.execute("CREATE INDEX idx_headwords_root_key ON dpd_headwords (root_key)")
    pr.yes(len(batch))


def export_roots(g: GlobalVars, dest: sqlite3.Connection) -> None:
    pr.green_tmr("exporting dpd_roots")

    src_col_list = ", ".join(f'"{c}"' for c in ROOT_COLUMNS)
    rows = g.src.execute(f"SELECT {src_col_list} FROM dpd_roots").fetchall()

    # Precompute root_count via single SQL query
    root_counts: dict[str, int] = {
        r["root_key"]: r["cnt"]
        for r in g.src.execute(
            "SELECT root_key, COUNT(*) AS cnt FROM dpd_headwords"
            " WHERE root_key != '' GROUP BY root_key"
        ).fetchall()
    }

    dest_cols = ROOT_COLUMNS + ["root_count"]
    col_list = ", ".join(f'"{c}"' for c in dest_cols)
    placeholders = ", ".join(["?"] * len(dest_cols))

    dest.execute(f"CREATE TABLE dpd_roots ({col_list})")
    batch = [
        tuple(r[c] for c in ROOT_COLUMNS) + (root_counts.get(r["root"], 0),)
        for r in rows
    ]
    dest.executemany(
        f"INSERT INTO dpd_roots ({col_list}) VALUES ({placeholders})", batch
    )
    dest.execute("CREATE INDEX idx_roots_root ON dpd_roots (root)")
    pr.yes(len(batch))


def export_lookup(g: GlobalVars, dest: sqlite3.Connection) -> None:
    pr.green_tmr("exporting lookup")

    rows = g.src.execute("SELECT * FROM lookup").fetchall()
    if not rows:
        pr.yes(0)
        return

    orig_cols = list(rows[0].keys())
    dest_cols = orig_cols + ["fuzzy_key"]
    col_list = ", ".join(f'"{c}"' for c in dest_cols)
    placeholders = ", ".join(["?"] * len(dest_cols))

    dest.execute(f"CREATE TABLE lookup ({col_list})")
    batch = [
        tuple(r[c] for c in orig_cols) + (_strip_diacritics_mobile(r["lookup_key"]),)
        for r in rows
    ]
    dest.executemany(f"INSERT INTO lookup ({col_list}) VALUES ({placeholders})", batch)

    for idx in g.src.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='lookup' AND sql IS NOT NULL"
    ).fetchall():
        try:
            dest.execute(idx[0])
        except sqlite3.OperationalError:
            pass

    dest.execute("CREATE INDEX idx_lookup_fuzzy_key ON lookup (fuzzy_key)")
    pr.yes(len(batch))


def copy_passthrough_tables(g: GlobalVars, dest: sqlite3.Connection) -> None:
    src = sqlite3.connect(g.pth.dpd_db_path)
    src.row_factory = sqlite3.Row

    for table in PASSTHROUGH_TABLES:
        pr.green_tmr(f"copying {table}")
        schema_row = src.execute(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'"
        ).fetchone()
        if not schema_row:
            pr.no("not found")
            continue

        dest.execute(schema_row[0])
        rows = src.execute(f'SELECT * FROM "{table}"').fetchall()
        if rows:
            cols = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_list = ", ".join(f'"{c}"' for c in cols)
            dest.executemany(
                f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})',
                [tuple(r) for r in rows],
            )

        for idx in src.execute(
            f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table}' AND sql IS NOT NULL"
        ).fetchall():
            try:
                dest.execute(idx[0])
            except sqlite3.OperationalError:
                pass

        pr.yes(len(rows))

    src.close()


def copy_family_tables(g: GlobalVars, dest: sqlite3.Connection) -> None:
    src = sqlite3.connect(g.pth.dpd_db_path)

    for table, columns in [
        ("family_root", FAMILY_ROOT_COLUMNS),
        ("family_word", FAMILY_WORD_COLUMNS),
        ("family_compound", FAMILY_COMPOUND_COLUMNS),
        ("family_idiom", FAMILY_IDIOM_COLUMNS),
        ("family_set", FAMILY_SET_COLUMNS),
    ]:
        pr.green_tmr(f"copying {table}")
        _copy_selected_columns(src, dest, table, columns)

    src.close()


def write_schema_version(dest: sqlite3.Connection) -> None:
    pr.green_tmr("writing db_schema_version")
    dest.execute(
        "INSERT OR REPLACE INTO db_info (key, value) VALUES (?, ?)",
        ("db_schema_version", str(DB_SCHEMA_VERSION)),
    )
    pr.yes(DB_SCHEMA_VERSION)


def zip_mobile_db(pth: ProjectPaths) -> None:
    zip_path = pth.dpd_mobile_db_zip_path
    pr.green_tmr("zipping mobile db")
    zip_up_file(input_file=pth.dpd_mobile_db_path, output_file=zip_path)
    pr.yes("ok")
    zip_size = zip_path.stat().st_size / 1_000_000
    pr.summary("zip size", f"{zip_size:.1f} MB")


def main() -> None:
    pr.tic()
    pr.yellow_title("export mobile db")

    if not config_test("exporter", "make_mobile", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g = GlobalVars()

    output_path = g.pth.dpd_mobile_db_path
    if output_path.exists():
        output_path.unlink()

    dest = sqlite3.connect(output_path)
    dest.execute("PRAGMA journal_mode=WAL")

    export_headwords(g, dest)
    export_roots(g, dest)
    export_lookup(g, dest)
    copy_passthrough_tables(g, dest)
    copy_family_tables(g, dest)
    write_schema_version(dest)

    dest.commit()
    dest.close()
    g.src.close()

    source_size = g.pth.dpd_db_path.stat().st_size / 1_000_000
    mobile_size = output_path.stat().st_size / 1_000_000
    pr.summary("source db", f"{source_size:.1f} MB")
    pr.summary("mobile db", f"{mobile_size:.1f} MB")
    pr.summary("size reduction", f"{(1 - mobile_size / source_size) * 100:.1f}%")

    zip_mobile_db(g.pth)

    pr.toc()


if __name__ == "__main__":
    main()
