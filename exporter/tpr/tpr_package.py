#!/usr/bin/env python3

"""Build dpd.pkg.db: DPD for Tipitaka Pali Reader as one extension package.

The package holds everything TPR's dictionary shows: the headword and root
entries, the inflection and word-split lookups, the grammar tables, and the
extras behind the Inflect, √ family, Samāsas and Frequency buttons. TPR
installs a package in one transaction and keeps it, so it is applied again
after an app update replaces the databases. The format is described in
tools/extension_packages/README.md of bksubhuti/tipitaka-pali-reader.

Everything comes from dpd.db alone, so the package can be built from a DPD
release: `uv run python exporter/tpr/tpr_package.py --db dpd.db`.
"""

import argparse
import json
import sqlite3
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound, FamilyRoot, Lookup
from exporter.tpr import tpr_exporter as tpr
from tools.headwords_clean_set import make_clean_headwords_set
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr

PACKAGE_ID = "dpd"
PACKAGE_FORMAT = 1

# The tables TPR has had since the .sql downloads, emptied and refilled.
BASE_TABLES = {
    "dpd": """("id" integer, "word" text, "definition" text, "book_id" integer,
        "has_inflections" INTEGER DEFAULT 0, "has_root_family" INTEGER DEFAULT 0,
        "has_compound_family" INTEGER DEFAULT 0,
        "has_word_family" INTEGER DEFAULT 0, "has_freq" INTEGER DEFAULT 0)""",
    "dpd_inflections_to_headwords": """("inflection" TEXT, "headwords" TEXT)""",
    "dpd_word_split": """("word" TEXT NOT NULL, "breakup" TEXT)""",
    "dpd_grammar": """("word" TEXT, "definition" TEXT)""",
}

BASE_INDEXES = [
    'CREATE INDEX IF NOT EXISTS main.dpd_index ON dpd ("word", "book_id")',
    "CREATE INDEX IF NOT EXISTS main.dpd_headwords_index "
    'ON dpd_inflections_to_headwords ("inflection" ASC)',
    'CREATE INDEX IF NOT EXISTS main.dpd_word_split_index ON dpd_word_split ("word")',
    'CREATE INDEX IF NOT EXISTS main.dpd_grammar_index ON dpd_grammar ("word")',
]

# The extras belong to DPD alone, so they are dropped and made again: a
# column added here then reaches devices that have the old table.
EXTRA_TABLES = {
    "dpd__inflections": """("id" INTEGER NOT NULL, "stem" VARCHAR NOT NULL,
        "pattern" VARCHAR NOT NULL, "inflections" VARCHAR NOT NULL,
        PRIMARY KEY ("id"))""",
    "dpd__family_root": """("root_family_key" VARCHAR NOT NULL,
        "root_key" VARCHAR NOT NULL, "root_family" VARCHAR NOT NULL,
        "root_meaning" VARCHAR NOT NULL, "data" VARCHAR NOT NULL,
        "count" INTEGER NOT NULL, PRIMARY KEY ("root_family_key", "root_key"))""",
    "dpd__word_family_root": """("id" INTEGER NOT NULL,
        "family_root" VARCHAR NOT NULL, "root_key" VARCHAR NOT NULL DEFAULT '',
        PRIMARY KEY ("id"))""",
    "dpd__family_compound": """("compound_family" VARCHAR NOT NULL,
        "data" VARCHAR NOT NULL, "count" INTEGER NOT NULL,
        PRIMARY KEY ("compound_family"))""",
    "dpd__word_family_compound": """("id" INTEGER NOT NULL,
        "family_compound" VARCHAR NOT NULL, PRIMARY KEY ("id"))""",
    "freq": """("headword" TEXT, "freq_data" TEXT, "id" INTEGER,
        PRIMARY KEY ("headword"))""",
}

EXTRA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS main.dpd__family_root_family "
    'ON dpd__family_root ("root_family")',
    'CREATE INDEX IF NOT EXISTS main.freq_id ON freq ("id")',
]


class GlobalVars:
    def __init__(self, db_path: Path) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(db_path)
        dpd_db = self.db_session.query(DpdHeadword).all()
        self.dpd_db: list[DpdHeadword] = sorted(
            dpd_db, key=lambda x: pali_sort_key(x.lemma_1)
        )
        self.all_headwords_clean: set[str] = make_clean_headwords_set(self.dpd_db)

        # filled by the functions in tpr_exporter
        self.tpr_data_list: list[dict[str, str | int]] = []
        self.deconstructor_data_list: list[dict[str, str]] = []

        self.i2h_rows: list[tuple[str, str]] = []
        self.grammar_rows: list[tuple[str, str]] = []
        self.extras: dict[str, list[tuple]] = {}


def make_i2h(g: GlobalVars) -> None:
    """Inflections to headwords, from the headwords column of the lookup table.

    The same as the i2h.tsv the db pipeline writes, which a release does not
    carry: the lookup holds headword ids where the tsv holds lemmas.
    """
    pr.green_tmr("compiling inflections to headwords")
    lemmas = {i.id: i.lemma_1 for i in g.dpd_db}
    i2h: dict[str, list[str]] = {}
    for i in g.db_session.query(Lookup).filter(Lookup.headwords != "").all():
        found = [lemmas[id] for id in i.headwords_unpack if id in lemmas]
        if found:
            i2h[i.lookup_key] = pali_list_sorter(found)

    # as tpr_exporter.add_roots_to_i2h
    for r in g.db_session.query(tpr.DpdRoot).all():
        if r.root_clean not in i2h:
            i2h[r.root_clean] = [r.root_clean]
        if r.root_no_sign not in i2h:
            i2h[r.root_no_sign] = [r.root_clean]

    g.i2h_rows = [(k, ",".join(v)) for k, v in i2h.items()]
    pr.yes(len(g.i2h_rows))


def grammar_row(headword: str, pos: str, grammar: str) -> str:
    if grammar in ("", "indeclinable", "indeclineable"):
        return f"<tr><td><b>{pos}</b></td><td colspan='3'>indeclineable</td></tr>"
    return (
        f"<tr><td><b>{pos}</b></td><td>{grammar}</td>"
        f"<td>of</td><td>{headword}</td></tr>"
    )


def make_grammar(g: GlobalVars) -> None:
    """Every grammatical possibility of each inflected form, as TPR shows it."""
    pr.green_tmr("compiling grammar")
    # The lookup leaves out words that do not inflect; TPR has shown them as
    # indeclineable, one row for each part of speech.
    indeclinable: dict[str, list[str]] = {}
    for i in g.dpd_db:
        if i.stem == "-" and i.pos not in indeclinable.get(i.lemma_clean, []):
            indeclinable.setdefault(i.lemma_clean, []).append(i.pos)

    cache: dict[str, str] = {}
    body_of: dict[str, str] = {}
    for i in g.db_session.query(Lookup).filter(Lookup.grammar != "").all():
        body = cache.get(i.grammar)
        if body is None:
            body = "".join(grammar_row(*t) for t in i.grammar_unpack)
            cache[i.grammar] = body
        body_of[i.lookup_key] = body
    for word, parts in indeclinable.items():
        body_of[word] = body_of.get(word, "") + "".join(
            grammar_row(word, pos, "") for pos in parts
        )

    g.grammar_rows = [
        (word, f"<div class='dpd_grammar'><table class='dpd_grammar'>{body}</table></div>")
        for word, body in body_of.items()
    ]
    rows = g.grammar_rows
    pr.yes(len(rows))


def make_extras(g: GlobalVars) -> None:
    """The tables behind the Inflect, √ family, Samāsas and Frequency buttons."""
    pr.green_tmr("compiling extras")
    inflections = []
    word_family_root = []
    word_family_compound = []
    freq = []
    for i in g.dpd_db:
        if i.stem and i.stem != "-" and i.pattern and i.inflections:
            inflections.append((i.id, i.stem, i.pattern, i.inflections))
        if i.family_root:
            word_family_root.append((i.id, i.family_root, i.root_key))
        if i.family_compound:
            word_family_compound.append((i.id, i.family_compound))
        if i.freq_data:
            freq.append((i.lemma_1, i.freq_data, i.id))

    family_root = [
        (r.root_family_key, r.root_key, r.root_family, r.root_meaning, r.data, r.count)
        for r in g.db_session.query(FamilyRoot).all()
    ]
    family_compound = [
        (f.compound_family, f.data, f.count)
        for f in g.db_session.query(FamilyCompound).all()
    ]

    g.extras = {
        "dpd__inflections": inflections,
        "dpd__family_root": family_root,
        "dpd__word_family_root": word_family_root,
        "dpd__family_compound": family_compound,
        "dpd__word_family_compound": word_family_compound,
        "freq": freq,
    }
    pr.yes(sum(len(v) for v in g.extras.values()))


def headword_rows(g: GlobalVars) -> list[tuple]:
    """The dpd table, with the flags that show each button."""
    inflected = {r[0] for r in g.extras["dpd__inflections"]}
    in_root_family = {r[0] for r in g.extras["dpd__word_family_root"]}
    in_compound_family = {r[0] for r in g.extras["dpd__word_family_compound"]}
    compound_families = {r[0] for r in g.extras["dpd__family_compound"]}
    with_freq = {r[2] for r in g.extras["freq"]}
    clean = {i.id: i.lemma_clean for i in g.dpd_db}

    rows = []
    for d in g.tpr_data_list:
        id = int(d["id"])
        is_headword = id != 0  # roots have id 0
        rows.append(
            (
                id,
                d["word"],
                d["definition"],
                d["book_id"],
                int(is_headword and id in inflected),
                int(is_headword and id in in_root_family),
                int(
                    is_headword
                    and (
                        id in in_compound_family
                        or clean.get(id, "") in compound_families
                    )
                ),
                0,
                int(is_headword and id in with_freq),
            )
        )
    return rows


def flat(sql: str) -> str:
    return " ".join(sql.split())


def commands() -> list[tuple[str, str, str | None, str | None]]:
    """The install steps: (phase, op, target, arg)."""
    steps: list[tuple[str, str, str | None, str | None]] = []
    for table, columns in BASE_TABLES.items():
        steps.append(
            ("install", "sql", None, f"CREATE TABLE IF NOT EXISTS main.{table} {flat(columns)}")
        )
    for table in BASE_TABLES:
        steps.append(("install", "sql", None, f"DELETE FROM main.{table}"))
    for table, columns in EXTRA_TABLES.items():
        steps.append(("install", "sql", None, f"DROP TABLE IF EXISTS main.{table}"))
        steps.append(
            ("install", "sql", None, f"CREATE TABLE main.{table} {flat(columns)}")
        )
    for table in [*BASE_TABLES, *EXTRA_TABLES]:
        steps.append(("install", "copy", f"main.{table}", table))
    for index in BASE_INDEXES + EXTRA_INDEXES:
        steps.append(("install", "sql", None, index))
    return steps


def write_package(g: GlobalVars, out: Path, version: int) -> None:
    pr.green_tmr("writing package")
    out.unlink(missing_ok=True)
    conn = sqlite3.connect(out)
    c = conn.cursor()

    c.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    c.executemany(
        "INSERT INTO meta VALUES (?, ?)",
        [
            ("id", PACKAGE_ID),
            ("version", str(version)),
            ("title", "Digital Pāḷi Dictionary"),
            (
                "description",
                f"DPD {version} with inflections, root and compound families "
                "and frequency",
            ),
            ("format", str(PACKAGE_FORMAT)),
        ],
    )
    c.execute(
        "CREATE TABLE commands (seq INTEGER PRIMARY KEY, "
        "phase TEXT NOT NULL DEFAULT 'install', op TEXT NOT NULL, "
        "target TEXT, arg TEXT)"
    )
    c.executemany(
        "INSERT INTO commands (phase, op, target, arg) VALUES (?, ?, ?, ?)",
        commands(),
    )

    # the tables the copy steps read, laid out as on the device
    for table, columns in {**BASE_TABLES, **EXTRA_TABLES}.items():
        c.execute(f"CREATE TABLE {table} {columns}")

    c.executemany("INSERT INTO dpd VALUES (?,?,?,?,?,?,?,?,?)", headword_rows(g))
    c.executemany("INSERT INTO dpd_inflections_to_headwords VALUES (?, ?)", g.i2h_rows)
    c.executemany(
        "INSERT INTO dpd_word_split VALUES (?, ?)",
        [(d["word"], d["breakup"]) for d in g.deconstructor_data_list],
    )
    c.executemany("INSERT INTO dpd_grammar VALUES (?, ?)", g.grammar_rows)
    for table, rows in g.extras.items():
        if rows:
            marks = ",".join("?" * len(rows[0]))
            c.executemany(f"INSERT INTO {table} VALUES ({marks})", rows)

    conn.commit()
    c.execute("VACUUM")
    conn.close()
    pr.yes(f"{out.stat().st_size / 1e6:.0f} MB")


def zip_package(out: Path) -> Path:
    pr.green_tmr("zipping")
    zip_path = out.with_suffix("").with_suffix(".pkg.zip")
    with ZipFile(zip_path, "w", ZIP_DEFLATED, compresslevel=9) as z:
        z.write(out, out.name)
    pr.yes(f"{zip_path.stat().st_size / 1e6:.1f} MB")
    return zip_path


def report(out: Path) -> None:
    """Counts, to compare one build with the last."""
    conn = sqlite3.connect(out)
    tables = [*BASE_TABLES, *EXTRA_TABLES]
    counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in tables}
    flags = conn.execute(
        "SELECT sum(has_inflections), sum(has_root_family), "
        "sum(has_compound_family), sum(has_freq) FROM dpd"
    ).fetchone()
    conn.close()
    counts["flags (inflect, root, compound, freq)"] = list(flags)
    print(json.dumps(counts, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ProjectPaths().dpd_db_path)
    parser.add_argument(
        "--version",
        type=int,
        required=True,
        help="package version, the DPD release date as yyyymmdd",
    )
    parser.add_argument(
        "--out", type=Path, default=Path("exporter/tpr/output/dpd.pkg.db")
    )
    args = parser.parse_args()

    pr.tic()
    pr.yellow_title("building the tpr package")
    args.out.parent.mkdir(parents=True, exist_ok=True)

    g = GlobalVars(args.db)
    tpr.generate_tpr_data(g)  # type: ignore[arg-type]
    tpr.generate_deconstructor_data(g)  # type: ignore[arg-type]
    tpr.add_spelling_mistakes(g)  # type: ignore[arg-type]
    make_i2h(g)
    make_grammar(g)
    make_extras(g)
    write_package(g, args.out, args.version)
    zip_package(args.out)
    report(args.out)
    pr.toc()


if __name__ == "__main__":
    main()
