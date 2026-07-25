"""One-off migration: move every `variant` token into `var_text`.

`DpdHeadword.variant` is the legacy column; `var_text` is its successor and
means the same thing — variant readings of the headword found in other Pāḷi
texts. The schema was split years ago but the data was never migrated, which is
why `db_tests_columns.tsv` carries a rule literally named
"variant: not empty, move".

For each headword with a non-empty `variant`, every token is handed to
`tools.synonym_variant.assign_relationship(hw, token, "var_text")`, which:
- adds the token to `var_text`
- discards it from `variant`, `synonym` and `var_phonetic` (exclusivity)
- rewrites all four columns Pāḷi-sorted and comma-space joined

Links are moved literally — a one-way `variant` link stays a one-way `var_text`
link. No reciprocal backfill.

A second pass then normalises any `var_text` value that is not already
Pāḷi-sorted and comma-space joined. Values written by hand rather than through
`assign_relationship` had drifted out of order.

Run once. Afterwards `variant` is empty table-wide and the db test goes green.
Re-running is harmless — both passes are idempotent.

CLOSE gui2 BEFORE RUNNING — it writes to the same database.

Usage:
    uv run scripts/fix/variant_to_var_text.py --dry-run
    uv run scripts/fix/variant_to_var_text.py
"""

import argparse
from pathlib import Path

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.synonym_variant import (
    assign_relationship,
    assign_relationship_dict,
    split_field,
)

SAMPLE_SIZE = 20


def preview_row(hw: DpdHeadword) -> dict[str, str]:
    """Compute the post-migration field values without touching the ORM row."""
    fields: dict[str, str] = {
        "synonym": hw.synonym,
        "variant": hw.variant,
        "var_phonetic": hw.var_phonetic,
        "var_text": hw.var_text,
    }
    for token in sorted(split_field(hw.variant)):
        fields = assign_relationship_dict(fields, token, "var_text")
    return fields


def normalise_var_text(db: Session, dry_run: bool) -> None:
    """Rewrite any `var_text` that is not Pāḷi-sorted and comma-space joined.

    Catches values entered by hand rather than through `assign_relationship`.
    """
    pr.green_title("normalise var_text rendering")

    fixed = 0
    samples: list[tuple[str, str, str]] = []

    for hw in db.query(DpdHeadword).filter(DpdHeadword.var_text != "").all():
        canonical = ", ".join(pali_list_sorter(split_field(hw.var_text)))
        if canonical == hw.var_text:
            continue
        if len(samples) < SAMPLE_SIZE:
            samples.append((hw.lemma_1, hw.var_text, canonical))
        fixed += 1
        if not dry_run:
            hw.var_text = canonical

    for lemma_1, before, after in samples:
        pr.white(f"{lemma_1}")
        pr.white(f"    before: {before}")
        pr.white(f"    after:  {after}")

    pr.summary("rows normalised", str(fixed))


def migrate(db_path: Path, dry_run: bool) -> None:
    pr.green_title("variant -> var_text")

    db = get_db_session(db_path)
    headwords = db.query(DpdHeadword).filter(DpdHeadword.variant != "").all()

    rows_touched = 0
    tokens_moved = 0
    merges = 0
    samples: list[tuple[str, str, str, str]] = []

    for hw in headwords:
        tokens = sorted(split_field(hw.variant))
        if not tokens:
            continue

        old_variant = hw.variant
        old_var_text = hw.var_text

        if dry_run:
            new_var_text = preview_row(hw)["var_text"]
        else:
            for token in tokens:
                assign_relationship(hw, token, "var_text")
            new_var_text = hw.var_text

        rows_touched += 1
        tokens_moved += len(tokens)
        if old_var_text:
            merges += 1
            if len(samples) < SAMPLE_SIZE:
                samples.append((hw.lemma_1, old_variant, old_var_text, new_var_text))

    if samples:
        pr.cyan("merged rows (variant + existing var_text):")
        for lemma_1, old_variant, old_var_text, new_var_text in samples:
            pr.white(f"{lemma_1}")
            pr.white(f"    variant:  {old_variant}")
            pr.white(f"    var_text: {old_var_text}")
            pr.white(f"    result:   {new_var_text}")

    pr.summary("rows touched", str(rows_touched))
    pr.summary("tokens moved", str(tokens_moved))
    pr.summary("merged rows", str(merges))

    normalise_var_text(db, dry_run)

    if dry_run:
        db.rollback()
        pr.amber("dry run — nothing written")
    else:
        db.commit()
        remaining = db.query(DpdHeadword).filter(DpdHeadword.variant != "").count()
        pr.summary("rows with variant remaining", str(remaining))
        if remaining:
            pr.red("variant column is not empty — investigate before backing up")
        else:
            pr.green("variant column is empty — run `just backup` next")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="report what would change without writing to the database",
    )
    args = parser.parse_args()

    pth = ProjectPaths()
    migrate(pth.dpd_db_path, args.dry_run)


if __name__ == "__main__":
    main()
