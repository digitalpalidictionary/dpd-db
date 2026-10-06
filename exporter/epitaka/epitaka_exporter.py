#!/usr/bin/env python3

"""Export DPD into the local ePitaka app's dpd-dictionary.db."""

import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

import psutil
from sqlalchemy import literal_column
from sqlalchemy.orm import Session, joinedload

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, FamilyRoot, Lookup
from tools.configger import config_read, config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr

# Copied verbatim from the upstream file, so the schema text matches it.
SCHEMA = [
    """CREATE TABLE dpd_headwords (
            id           INTEGER PRIMARY KEY,
            lemma_1      TEXT,
            meaning_html TEXT,
            antonym      TEXT,
            synonym      TEXT,
            stem         TEXT,
            pattern      TEXT
        )""",
    "CREATE INDEX idx_dpd_headwords_lemma_1 ON dpd_headwords(lemma_1)",
    """CREATE TABLE dpd_lookup (
            lookup_key    TEXT,
            headwords     TEXT,  -- JSON array of ints -> dpd_headwords.id
            deconstructor TEXT
        )""",
    "CREATE INDEX idx_dpd_lookup_key ON dpd_lookup(lookup_key)",
    "CREATE INDEX idx_dpd_lookup_lookup_key ON dpd_lookup(lookup_key)",
]


def make_headword_html(i: DpdHeadword) -> str:
    """Build the meaning_html of one headword."""

    meaning_parts: list[str] = []
    if i.meaning_1.strip():
        meaning_parts.append(f"<b>{i.meaning_1.strip()}</b>")
    if i.meaning_2.strip():
        meaning_parts.append(i.meaning_2.strip())
    if i.meaning_lit.strip():
        meaning_parts.append(f"(lit. {i.meaning_lit.strip()})")
    if i.root_key:
        root = i.root_key
        if i.suffix.strip():
            root += f" + {i.suffix.strip()}"
        meaning_parts.append(f"[{root}: {i.rt.root_meaning}]")
    summary = f"<i>{i.pos}</i> {' '.join(meaning_parts)}"

    detail = f"<div class='dpd-grammar'><b>Grammar:</b> {i.grammar.strip()}</div>"
    if i.sanskrit.strip():
        detail += (
            f"<div class='dpd-sanskrit'><b>Sanskrit:</b> {i.sanskrit.strip()}</div>"
        )
    if i.root_key:
        root = f"{i.root_key} {i.root_sign.strip() or i.rt.root_sign}"
        if i.root_base.strip():
            root += f" ({i.root_base.strip()})"
        if i.construction.strip():
            root += f" - {i.construction.strip()}"
        detail += f"<div class='dpd-root'><b>Root:</b> {root}</div>"
    if i.compound_type.strip():
        compound = i.compound_type.strip()
        if i.compound_construction.strip():
            compound += f" ({i.compound_construction.strip()})"
        detail += f"<div class='dpd-compound'><b>Compound:</b> {compound}</div>"
    if i.example_1.strip():
        detail += (
            f"<div class='dpd-example'><b>Example:</b> {i.example_1.strip()}</div>"
        )

    return (
        f"<details class='dpd-meaning'><summary>{summary}</summary>"
        f"<div class='dpd-meaning-detail'>{detail}</div></details>"
    )


def make_root_html(r: DpdRoot, word_count: int, families: list[FamilyRoot]) -> str:
    """Build the meaning_html of one root, with its family tables."""

    summary = f"<b>{r.root}</b> {r.root_meaning}"
    if r.sanskrit_root.strip():
        summary += f" [skt. {r.sanskrit_root} ({r.sanskrit_root_meaning})]"

    detail = (
        f"<div class='dpd-root-group'><b>Group:</b> {r.root_group}{r.root_sign}</div>"
    )
    if r.root_example.strip():
        detail += (
            f"<div class='dpd-root-example'><b>Example:</b> "
            f"{r.root_example.strip()}</div>"
        )
    detail += (
        f"<div class='dpd-dhatupatha'><b>Dhātupāṭha:</b> "
        f"{r.dhatupatha_pali.strip()} - {r.dhatupatha_english.strip()}</div>"
        f"<div class='dpd-dhatumanjusa'><b>Dhātumañjūsā:</b> "
        f"{r.dhatumanjusa_pali.strip()} - {r.dhatumanjusa_english.strip()}</div>"
    )
    if r.note.strip():
        detail += f"<div class='dpd-root-note'><b>Note:</b> {r.note.strip()}</div>"
    detail += f"<div class='dpd-root-count'><b>Word count:</b> {word_count}</div>"
    detail += "".join(f.html for f in families)

    return (
        f"<details class='dpd-root-meaning'><summary>{summary}</summary>"
        f"<div class='dpd-meaning-detail'>{detail}</div></details>"
    )


def make_root_ids(roots: list[DpdRoot], max_headword_id: int) -> dict[str, int]:
    """Number the roots after the last headword id, in plain sort order."""

    return {
        root: max_headword_id + 1 + n
        for n, root in enumerate(sorted(r.root for r in roots))
    }


def make_lookup_row(
    lookup: Lookup, root_ids: dict[str, int]
) -> tuple[str, str | None, str | None]:
    """Convert one lookup row into (lookup_key, headwords, deconstructor)."""

    ids = lookup.headwords_unpack + [root_ids[root] for root in lookup.roots_unpack]
    deconstructor = lookup.deconstructor_unpack
    return (
        lookup.lookup_key,
        json.dumps(ids) if ids else None,
        json.dumps(deconstructor, ensure_ascii=False) if deconstructor else None,
    )


def build_db(db_session: Session, out_path: Path) -> None:
    """Write a fresh dpd-dictionary.db at out_path."""

    out_path.unlink(missing_ok=True)
    conn = sqlite3.connect(out_path)
    for statement in SCHEMA:
        conn.execute(statement)

    pr.green_tmr("headwords")
    headwords = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.rt)).all()
    conn.executemany(
        "INSERT INTO dpd_headwords VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            (
                i.id,
                i.lemma_1,
                make_headword_html(i),
                i.antonym,
                i.synonym,
                i.stem,
                i.pattern,
            )
            for i in headwords
        ),
    )
    pr.yes(len(headwords))

    pr.green_tmr("roots")
    roots = db_session.query(DpdRoot).all()
    root_ids = make_root_ids(roots, max(i.id for i in headwords))
    # Insertion order is the order the family builder made (Pāḷi order of each
    # family's first word), which is the order the upstream file shows.
    families: dict[str, list[FamilyRoot]] = {}
    for f in db_session.query(FamilyRoot).order_by(literal_column("rowid")).all():
        families.setdefault(f.root_key, []).append(f)
    word_counts: dict[str, int] = {}
    for i in headwords:
        if i.root_key:
            word_counts[i.root_key] = word_counts.get(i.root_key, 0) + 1
    conn.executemany(
        "INSERT INTO dpd_headwords (id, lemma_1, meaning_html) VALUES (?, ?, ?)",
        (
            (
                root_ids[r.root],
                r.root,
                make_root_html(r, word_counts.get(r.root, 0), families.get(r.root, [])),
            )
            for r in roots
        ),
    )
    pr.yes(len(roots))

    pr.green_tmr("lookup")
    lookups = db_session.query(Lookup).all()
    conn.executemany(
        "INSERT INTO dpd_lookup VALUES (?, ?, ?)",
        (make_lookup_row(lookup, root_ids) for lookup in lookups),
    )
    pr.yes(len(lookups))

    conn.commit()
    conn.close()


def prebuild_norm_table(out_path: Path, repo_path: str) -> None:
    """Build the app's folded-search table with ePitaka's own Dart tool,
    so the app does not spend minutes building it at launch."""

    pr.green_tmr("search table")
    dart = shutil.which("dart")
    if not repo_path or not Path(repo_path).is_dir() or dart is None:
        pr.no("skipped")
        pr.red("no [epitaka] repo_path or no dart; ePitaka builds it at launch")
        return

    result = subprocess.run(
        [dart, "run", "tool/build_dpd_norm.dart", str(out_path.resolve())],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pr.no("failed")
        pr.red(result.stderr or result.stdout)
        return
    pr.yes("ok")


def app_processes() -> list[psutil.Process]:
    """Running ePitaka processes."""

    return [p for p in psutil.process_iter(["name"]) if p.info["name"] == "epitaka"]


def close_app(procs: list[psutil.Process], timeout: float = 30) -> bool:
    """Ask ePitaka to quit. True when every process has exited."""

    pr.green_tmr("close epitaka")
    for p in procs:
        try:
            p.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(procs, timeout=timeout)
    if alive:
        pr.no("still on")
        return False
    pr.yes("ok")
    return True


def open_app() -> None:
    """Start ePitaka through its desktop entry, detached from this build."""

    pr.green_tmr("open epitaka")
    subprocess.Popen(
        ["gtk-launch", "epitaka"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    pr.yes("ok")


def install(out_path: Path, dest: Path, baseline_path: Path) -> bool:
    """Copy the output into the app's file through SQLite's backup,
    which handles the destination's WAL file correctly. The backup waits
    for as long as another process holds a write lock, so close the app
    first."""

    pr.green_tmr("install")
    if not baseline_path.exists():
        # The live file is the only copy of the upstream build on this machine.
        pr.no("refused")
        pr.red(f"save the upstream file as {baseline_path} first")
        return False

    src = sqlite3.connect(out_path)
    dst = sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    pr.yes("ok")
    return True


def main() -> None:
    pr.tic()
    pr.yellow_title("export dpd to epitaka")

    if not config_test("exporter", "make_epitaka", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    db_path = config_read("epitaka", "db_path") or ""
    if not db_path or not Path(db_path).parent.is_dir():
        pr.red(f"[epitaka] db_path folder not found: '{db_path}'")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    build_db(db_session, pth.epitaka_dpd_db_path)
    prebuild_norm_table(
        pth.epitaka_dpd_db_path, config_read("epitaka", "repo_path") or ""
    )

    procs = app_processes()
    if procs and not close_app(procs):
        pr.red("ePitaka did not close, not installed; close it and run again")
        pr.toc()
        return
    install(pth.epitaka_dpd_db_path, Path(db_path), pth.epitaka_baseline_db_path)
    if procs:
        open_app()
    pr.toc()


if __name__ == "__main__":
    main()
