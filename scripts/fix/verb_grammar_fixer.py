"""Apply the unambiguous grammar redirects found by `verb_finder.py`.

The rule: a derived form's `grammar` names the present-tense verb it comes from
when that verb exists in the dictionary, and the prefixes + root when it does
not. `verb_finder.py` buckets every derived form against that rule; this script
writes back only the two buckets where the correction is unambiguous:

- `would_change_to_root` — grammar names a verb absent from the dictionary and
  no pr verb exists at that (family_root, root_key), so it becomes the root.
- `would_change_to_verb` — grammar names a root (or an absent verb) and exactly
  one pr verb exists at that (family_root, root_key), so it becomes that verb.

The ambiguous, rootless, malformed and mismatched buckets are left alone — they
need a human.

Proposals are recomputed live from the database on every run, so there is no
stale-TSV hazard. Nothing is written without `--apply`.

CLOSE gui2 BEFORE RUNNING WITH --apply — it writes to the same database.

Usage:
    uv run scripts/fix/verb_grammar_fixer.py            # dry run, writes the diff file
    uv run scripts/fix/verb_grammar_fixer.py --apply    # writes to the database
"""

import argparse
from pathlib import Path

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.fix.verb_finder import (
    build_pr_verb_index,
    scan_derived_forms,
    write_tsv,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr

APPLY_BUCKETS = ("would_change_to_root", "would_change_to_verb")
SAMPLE_SIZE = 25
DIFF_FILENAME = "proposed_grammar_changes.tsv"


def collect_changes(db: Session) -> list[dict]:
    """Recompute the two unambiguous buckets and flatten them into one change list."""
    pr_index, pr_lemma_map = build_pr_verb_index(db)
    buckets = scan_derived_forms(db, pr_index, pr_lemma_map)

    changes: list[dict] = []
    for bucket in APPLY_BUCKETS:
        for row in buckets[bucket]:
            proposed = row["grammar_proposed"]
            # A blank or unchanged proposal is not a correction — never write one.
            if not proposed or proposed == row["grammar_current"]:
                continue
            changes.append(
                {
                    "id": row["id"],
                    "lemma_1": row["lemma_1"],
                    "pos": row["pos"],
                    "family_root": row["family_root"],
                    "grammar_current": row["grammar_current"],
                    "grammar_proposed": proposed,
                    "bucket": bucket,
                }
            )
    changes.sort(key=lambda r: r["id"])
    return changes


def apply_changes(db: Session, changes: list[dict]) -> int:
    """Write the new `grammar` values, skipping any row that has moved underneath us."""
    by_id = {c["id"]: c for c in changes}
    headwords = (
        db.query(DpdHeadword).filter(DpdHeadword.id.in_(list(by_id.keys()))).all()
    )

    written = 0
    for hw in headwords:
        change = by_id[hw.id]
        if hw.grammar != change["grammar_current"]:
            pr.red(f"skipped {hw.lemma_1} — grammar changed since the scan")
            continue
        hw.grammar = change["grammar_proposed"]
        written += 1

    db.commit()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write the changes to the database (default is a dry run)",
    )
    args = parser.parse_args()

    pr.yellow_title("verb grammar fixer")
    pr.tic()

    pth = ProjectPaths()
    db = get_db_session(pth.dpd_db_path)
    output_dir: Path = pth.temp_dir / "verb_finder"

    changes = collect_changes(db)
    write_tsv(changes, output_dir / DIFF_FILENAME)

    for bucket in APPLY_BUCKETS:
        pr.summary(bucket, str(sum(1 for c in changes if c["bucket"] == bucket)))
    pr.summary("total changes", str(len(changes)))

    pr.green_title(f"sample (first {SAMPLE_SIZE})")
    for change in changes[:SAMPLE_SIZE]:
        pr.white(
            f"  {change['lemma_1']:<24} {change['grammar_current']:<34}"
            f" ->  {change['grammar_proposed']}"
        )

    if args.apply:
        written = apply_changes(db, changes)
        pr.summary("rows written", str(written))
        pr.green("database updated — run `just backup` next")
    else:
        pr.amber("dry run — nothing written")
        pr.white(f"full diff: {output_dir / DIFF_FILENAME}")

    pr.toc()


if __name__ == "__main__":
    main()
