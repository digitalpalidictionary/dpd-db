"""Find the DpdHeadword columns that the contributor corpus consumers read.

Loads the corpus with load_only(<columns>, raiseload=True), runs the two
consumers a contributor reaches (the synonym and phonetic detector, and the
inflection sets), and adds every column that raises, until a run is clean.

    find_columns.py --db <copy of dpd.db> --out <markdown file>

Run from the repo root, on a copy of dpd.db, never the live file.
"""

import argparse
import gc
import os
import random
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

START_COLUMNS = [
    "lemma_1",
    "meaning_1",
    "pos",
    "grammar",
    "construction",
    "root_key",
    "root_sign",
    "root_base",
    "family_root",
    "var_phonetic",
    "var_text",
    "synonym",
    "variant",
    "freq_data",
    "inflections",
    "inflections_api_ca_eva_iti",
]
SAMPLE_RANDOM = 2000
SAMPLE_EXTRA = 200
MAX_ROUNDS = 40


def pick_sample(session: Any) -> list[int]:
    """Fixed-seed sample: random rows plus the awkward ones."""
    from db.models import DpdHeadword

    rng = random.Random(0)
    all_ids = [r[0] for r in session.query(DpdHeadword.id).all()]
    groups = [
        (all_ids, SAMPLE_RANDOM),
        (
            [
                r[0]
                for r in session.query(DpdHeadword.id).filter(
                    DpdHeadword.meaning_1 == ""
                )
            ],
            SAMPLE_EXTRA,
        ),
        (
            [
                r[0]
                for r in session.query(DpdHeadword.id).filter(
                    DpdHeadword.meaning_1.like("%; %")
                )
            ],
            SAMPLE_EXTRA,
        ),
        (
            [
                r[0]
                for r in session.query(DpdHeadword.id).filter(
                    DpdHeadword.freq_data == ""
                )
            ],
            SAMPLE_EXTRA,
        ),
    ]
    sample: set[int] = set()
    for ids, size in groups:
        sample.update(rng.sample(ids, min(size, len(ids))))
    return sorted(sample)


def load_rows(session: Any, columns: set[str]) -> list[Any]:
    from sqlalchemy.orm import load_only

    from db.models import DpdHeadword

    attrs = [getattr(DpdHeadword, name) for name in sorted(columns)]
    return session.query(DpdHeadword).options(load_only(*attrs, raiseload=True)).all()


def exercise(
    rows: list[Any], sample: list[int], stage: dict[str, str], sets: bool
) -> int:
    """Run both consumers. Returns how often the frequency path was taken
    with an empty meaning_1 (the only place freq_data is read)."""
    import tools.synonym_variant as synonym_variant

    freq_calls = 0
    original = synonym_variant.has_textual_occurrence

    def counting(hw: Any) -> bool:
        nonlocal freq_calls
        if not hw.meaning_1:
            freq_calls += 1
        return original(hw)

    setattr(synonym_variant, "has_textual_occurrence", counting)
    try:
        stage["now"] = "detector build"
        detector = synonym_variant.RelationshipDetector(rows)
        by_id = {row.id: row for row in rows}
        stage["now"] = "find_synonyms"
        for row_id in sample:
            detector.find_synonyms(by_id[row_id])
        stage["now"] = "find_phonetic_variants"
        for row_id in sample:
            detector.find_phonetic_variants(by_id[row_id])
        if sets:
            stage["now"] = "inflection sets"
            for row in rows:
                _ = row.inflections_list_all
                _ = row.meaning_1
    finally:
        setattr(synonym_variant, "has_textual_occurrence", original)
    return freq_calls


def run(db_path: Path, out: Path, sets: bool) -> int:
    from sqlalchemy.exc import InvalidRequestError

    from db.db_helpers import get_db_session

    session = get_db_session(db_path)
    sample = pick_sample(session)
    columns = set(START_COLUMNS)
    if not sets:
        columns -= {"inflections", "inflections_api_ca_eva_iti"}
    added: dict[str, str] = {}
    stage = {"now": "start"}
    freq_calls = -1
    rounds = 0
    for rounds in range(1, MAX_ROUNDS + 1):
        rows = load_rows(session, columns)
        try:
            freq_calls = exercise(rows, sample, stage, sets)
            break
        except InvalidRequestError as exc:
            found = re.search(r"DpdHeadword\.(\w+)", str(exc))
            if not found:
                raise
            name = found.group(1)
            columns.add(name)
            added[name] = stage["now"]
        finally:
            del rows
            gc.collect()
    else:
        sys.stderr.write("gave up: column set still growing\n")
        return 1

    lines = [
        "# Columns the contributor corpus consumers read",
        "",
        f"Database: `{db_path.name}`. Sample: {len(sample)} headwords (fixed seed 0: "
        f"{SAMPLE_RANDOM} random, plus up to {SAMPLE_EXTRA} each with empty "
        "`meaning_1`, a multi-meaning `meaning_1`, and empty `freq_data`).",
        f"Rounds: {rounds}. Final run: 0 raises. Inflection-set consumer: {'on' if sets else 'off (--no-sets)'}.",
        f"`has_textual_occurrence` took the frequency path {freq_calls} times "
        "(empty `meaning_1`) in the final run.",
        "",
        f"## Final set S ({len(columns) + 1} columns with `id`)",
        "",
        "| Column | Started in S | First needed by |",
        "|---|---|---|",
    ]
    for name in sorted(columns):
        lines.append(
            f"| {name} | {'yes' if name in START_COLUMNS else 'no'} | "
            f"{added.get(name, 'start list')} |"
        )
    lines += ["| id | primary key | always loaded |"]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.write(f"0 raises after {rounds} rounds; S has {len(columns)} columns\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--no-sets",
        action="store_true",
        help="skip the inflection-set consumer and its columns (the L5 case)",
    )
    args = parser.parse_args()
    os.environ["DPD_GUI2_ROLE"] = "contributor-server"
    os.environ["DPD_GUI2_USERNAME"] = "memprobe"
    os.environ["DPD_GUI2_DATA_DIR"] = tempfile.mkdtemp(prefix="findcols_")
    return run(Path(args.db), Path(args.out), not args.no_sets)


if __name__ == "__main__":
    sys.exit(main())
