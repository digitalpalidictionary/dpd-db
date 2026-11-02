"""Check that each lever gives the same answers as today's code.

    equivalence.py --db <copy of dpd.db> --step <step> --out <folder>

Steps, each in its own process so no process holds two corpora:
    detector_full, detector_slim   synonym and phonetic lists for a sample
    sets_full, sets_direct         the all_inflections set
    wordfinder_full, wordfinder_interned   word finder results
    compare                        diff the saved pairs, write equivalence.md
    lookup                         set versus the lookup table, and query time

Run from the repo root, on a copy of dpd.db, never the live file.
"""

import argparse
import json
import os
import random
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from find_columns import pick_sample

DEFAULT_COLUMNS_MD = "kamma/threads/20261102_contrib_mem_savings/artifacts/columns.md"
QUERY_WORDS = 10_000
SEARCH_TYPES = ["EXACT", "STARTS_WITH", "CONTAINS", "REGEX"]


def slim_columns(columns_md: Path) -> list[str]:
    names: list[str] = []
    for line in columns_md.read_text(encoding="utf-8").splitlines():
        cells = [x.strip() for x in line.strip("|").split("|")]
        if len(cells) == 3 and cells[1] in ("yes", "no"):
            names.append(cells[0])
    return names


def load_rows(session: Any, columns: list[str] | None) -> list[Any]:
    """Today's load_corpus query, or the slim one with raiseload."""
    from sqlalchemy.orm import defer, load_only

    from db.models import DpdHeadword

    query = session.query(DpdHeadword)
    if columns is None:
        return query.options(
            defer(DpdHeadword.inflections_html),
            defer(DpdHeadword.freq_html),
            defer(DpdHeadword.inflections_sinhala),
            defer(DpdHeadword.inflections_devanagari),
            defer(DpdHeadword.inflections_thai),
        ).all()
    attrs = [getattr(DpdHeadword, name) for name in columns]
    return query.options(load_only(*attrs, raiseload=True)).all()


def load_split_rows(session: Any, columns: list[str]) -> list[Any]:
    """No inflection columns; freq_data only for headwords with no meaning."""
    from sqlalchemy.orm import load_only

    from db.models import DpdHeadword

    drop = {"inflections", "inflections_api_ca_eva_iti"}
    with_freq = [getattr(DpdHeadword, n) for n in columns if n not in drop]
    without_freq = [
        getattr(DpdHeadword, n) for n in columns if n not in drop | {"freq_data"}
    ]
    query = session.query(DpdHeadword)
    has_meaning = (
        query.filter(DpdHeadword.meaning_1 != "")
        .options(load_only(*without_freq, raiseload=True))
        .all()
    )
    no_meaning = (
        query.filter(DpdHeadword.meaning_1 == "")
        .options(load_only(*with_freq, raiseload=True))
        .all()
    )
    return sorted(has_meaning + no_meaning, key=lambda row: row.id)


def detector_answers(rows: list[Any], sample: list[int]) -> dict[str, Any]:
    from tools.synonym_variant import RelationshipDetector

    detector = RelationshipDetector(rows)
    by_id = {row.id: row for row in rows}
    return {
        str(row_id): {
            "syn": detector.find_synonyms(by_id[row_id]),
            "pho": [
                list(pair) for pair in detector.find_phonetic_variants(by_id[row_id])
            ],
        }
        for row_id in sample
    }


def wordfinder_queries(manager: Any) -> list[tuple[str, str]]:
    """50 fixed words, each as four query types."""
    rng = random.Random(1)
    words = sorted({w for freq in manager.cst_file_freq.values() for w in freq})
    queries: list[tuple[str, str]] = []
    for word in rng.sample([w for w in words if len(w) >= 6], 50):
        queries += [
            ("EXACT", word),
            ("STARTS_WITH", word[:3]),
            ("CONTAINS", word[2:5]),
            ("REGEX", f"^{word[:3]}.{{2}}"),
        ]
    return queries


def wordfinder_answers(manager: Any) -> dict[str, Any]:
    answers: dict[str, Any] = {}
    for search_type, word in wordfinder_queries(manager):
        manager.search_for(word, search_type, printer=False, max_results=100000)
        answers[f"{search_type}|{word}"] = [list(r) for r in manager.search_results]
    return answers


def interned_load(manager: Any) -> None:
    def intern_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        return {sys.intern(key): value for key, value in pairs}

    with open(manager.pth.cst_file_freq, encoding="utf-8") as handle:
        manager.cst_file_freq = json.load(handle, object_pairs_hook=intern_keys)


def save(folder: Path, name: str, data: Any) -> None:
    (folder / f"{name}.json").write_text(
        json.dumps(data, sort_keys=True), encoding="utf-8"
    )


def load(folder: Path, name: str) -> Any:
    return json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))


def diff_report(title: str, old: Any, new: Any) -> tuple[bool, list[str]]:
    if isinstance(old, dict):
        keys = sorted(set(old) | set(new))
        bad = [k for k in keys if old.get(k) != new.get(k)]
        total = len(keys)
    else:
        bad_set = set(old) ^ set(new)
        bad = sorted(bad_set)
        total = len(set(old) | set(new))
    ok = not bad
    lines = [
        f"- {title}: {'PASS' if ok else 'FAIL'} ({len(bad)} differences in {total})"
    ]
    for key in bad[:10]:
        if isinstance(old, dict):
            lines.append(f"  - {key}: today {old.get(key)!r} / new {new.get(key)!r}")
        else:
            lines.append(f"  - {key!r} in {'today' if key in set(old) else 'new'} only")
    return ok, lines


def step_compare(folder: Path) -> int:
    pairs = [
        ("(a) detector lists, slim against full", "detector_full", "detector_slim"),
        ("(b) all_inflections, direct query against today", "sets_full", "sets_direct"),
        ("(c) word finder results, interned against today", "wordfinder_full", "wordfinder_interned"),
        ("(d) detector lists, split corpus against full", "detector_full", "detector_split"),
    ]  # fmt: skip
    lines = ["# Equivalence results", ""]
    all_ok = True
    for title, old_name, new_name in pairs:
        if (
            not (folder / f"{old_name}.json").exists()
            or not (folder / f"{new_name}.json").exists()
        ):
            lines.append(f"- {title}: MISSING input")
            all_ok = False
            continue
        ok, text = diff_report(title, load(folder, old_name), load(folder, new_name))
        all_ok = all_ok and ok
        lines += text
    check = folder / "hash_check.json"
    if check.exists():
        data = json.loads(check.read_text(encoding="utf-8"))
        ok_hash = (
            data["members_answered_no"] == 0 and data["negatives_answered_yes"] == 0
        )
        all_ok = all_ok and ok_hash
        lines.append(
            f"- (e) compact set: {'PASS' if ok_hash else 'FAIL'} "
            f"({data['members_answered_no']} of {data['today']} members answered no; "
            f"{data['negatives_answered_yes']} of {data['negatives_tested']} non-members answered yes; "
            f"{data['compact_unique_hashes']} unique hashes)"
        )
    existing = folder / "equivalence.md"
    lookup_part = ""
    if existing.exists() and "## Lookup" in existing.read_text(encoding="utf-8"):
        lookup_part = existing.read_text(encoding="utf-8").split("## Lookup", 1)[1]
        lines += ["", "## Lookup" + lookup_part.rstrip("\n")]
    existing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.write("\n".join(lines[:12]) + "\n")
    return 0 if all_ok else 1


def step_sets_hash(db_path: Path, folder: Path) -> int:
    """The compact set must answer yes for every word of today's set, and no
    for words that are not in it."""
    from db.db_helpers import get_db_session
    from db.models import DpdHeadword
    from lever_probe import HashedWords

    session = get_db_session(db_path)

    def words() -> Any:
        for first, second in session.query(
            DpdHeadword.inflections, DpdHeadword.inflections_api_ca_eva_iti
        ):
            yield from first.split(",")
            yield from second.split(",")

    compact = HashedWords(words())
    today = set(load(folder, "sets_full"))
    missing = [w for w in sorted(today) if w not in compact]
    rng = random.Random(2)
    pool = sorted(today)
    negatives: set[str] = set()
    while len(negatives) < 200_000:
        word = rng.choice(pool)
        for candidate in (word + "x", word[:-1] + "q", "q" + word):
            if candidate not in today:
                negatives.add(candidate)
    false_yes = [w for w in sorted(negatives) if w in compact]
    save(
        folder,
        "hash_check",
        {
            "today": len(today),
            "compact_unique_hashes": len(compact),
            "members_answered_no": len(missing),
            "negatives_tested": len(negatives),
            "negatives_answered_yes": len(false_yes),
            "examples": (missing + false_yes)[:10],
        },
    )
    sys.stdout.write(
        f"sets_hash: {len(missing)} members lost, {len(false_yes)} false yes\n"
    )
    return 0


def step_lookup(db_path: Path, folder: Path) -> int:
    from sqlalchemy import select

    from db.db_helpers import get_db_session
    from db.models import Lookup
    from tools.cst_sc_text_sets import make_cst_text_list

    session = get_db_session(db_path)
    today = set(load(folder, "sets_full"))
    keys = {
        r[0]
        for r in session.execute(
            select(Lookup.lookup_key).where(Lookup.headwords != "")
        )
    }
    only_set = sorted(today - keys)
    only_lookup = sorted(keys - today)
    words = make_cst_text_list(["an1"], dedupe=True, show_errors=False)[:QUERY_WORDS]
    start = time.perf_counter()
    in_set = sum(1 for w in words if w in today)
    set_s = time.perf_counter() - start
    start = time.perf_counter()
    table_hits: list[bool] = []
    for word in words:
        row = session.execute(
            select(Lookup.lookup_key)
            .where(Lookup.lookup_key == word, Lookup.headwords != "")
            .limit(1)
        ).first()
        table_hits.append(row is not None)
    query_s = time.perf_counter() - start
    in_table = sum(table_hits)
    agree = sum(1 for w, hit in zip(words, table_hits) if (w in today) == hit)
    lines = [
        "",
        "## Lookup (task 1.3, check L5)",
        "",
        f"- Words in today's `all_inflections`: {len(today)}. Lookup keys with a non-empty `headwords`: {len(keys)}.",
        f"- In the set but not in the table: {len(only_set)}. Examples: {only_set[:10]!r}.",
        f"- In the table but not in the set: {len(only_lookup)}. Examples: {only_lookup[:10]!r}.",
        f"- {len(words)} distinct words of CST `an1`: {in_set} found by the set, {in_table} by the table, {agree} answered the same by both.",
        f"- Time for {len(words)} words: set {set_s:.4f} s, table {query_s:.2f} s ({query_s / len(words) * 1e6:.0f} µs per query).",
    ]
    existing = folder / "equivalence.md"
    head = (
        existing.read_text(encoding="utf-8").split("\n## Lookup")[0]
        if existing.exists()
        else "# Equivalence results\n"
    )
    existing.write_text(
        head.rstrip("\n") + "\n" + "\n".join(lines) + "\n", encoding="utf-8"
    )
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


def run(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    folder = Path(args.out)
    folder.mkdir(parents=True, exist_ok=True)
    if args.step == "compare":
        return step_compare(folder)

    from db.db_helpers import get_db_session

    if args.step == "lookup":
        return step_lookup(db_path, folder)
    columns = slim_columns(Path(args.columns_md))
    if args.step == "sets_hash":
        return step_sets_hash(db_path, folder)
    if args.step in (
        "detector_full",
        "detector_slim",
        "detector_split",
        "sets_full",
        "sets_direct",
    ):
        session = get_db_session(db_path)
        if args.step in ("detector_full", "detector_slim", "detector_split"):
            sample = pick_sample(session)
            if args.step == "detector_split":
                rows = load_split_rows(session, columns)
            else:
                rows = load_rows(
                    session, None if args.step == "detector_full" else columns
                )
            save(folder, args.step, detector_answers(rows, sample))
        elif args.step == "sets_full":
            rows = load_rows(session, None)
            found: set[str] = set()
            for row in rows:
                found.update(row.inflections_list_all)
            save(folder, args.step, sorted(found))
        else:
            from db.models import DpdHeadword

            found = set()
            for row in session.query(
                DpdHeadword.inflections, DpdHeadword.inflections_api_ca_eva_iti
            ):
                found.update(row[0].split(",") + row[1].split(","))
            save(folder, args.step, sorted(found))
    elif args.step in ("wordfinder_full", "wordfinder_interned"):
        from tools.wordfinder_manager import WordFinderManager

        manager = WordFinderManager()
        if args.step == "wordfinder_interned":
            interned_load(manager)
        save(folder, args.step, wordfinder_answers(manager))
    else:
        sys.stderr.write(f"unknown step {args.step}\n")
        return 2
    sys.stdout.write(f"{args.step}: saved\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--step", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--columns-md", default=DEFAULT_COLUMNS_MD)
    args = parser.parse_args()
    os.environ["DPD_GUI2_ROLE"] = "contributor-server"
    os.environ["DPD_GUI2_USERNAME"] = "memprobe"
    os.environ["DPD_GUI2_DATA_DIR"] = tempfile.mkdtemp(prefix="equiv_")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
