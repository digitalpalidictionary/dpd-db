"""Audit the `variant` column of DpdHeadword for data-quality issues.

Each DpdHeadword has a `variant` field listing spelling variants — words
that are alternate spellings of the same lemma but are NOT inflections.
Variants should point to real headwords (by lemma_clean) and should not
duplicate forms that are already generated inflections.

This script runs three read-only checks and prints the results:

1. has_lookup_no_lemma_clean — variant words that exist in the lookup table
   (so a user can find them) but have no matching lemma_clean headword.
   These are "dirty" variants: the lookup entry resolves to nothing.

2. no_lemma_clean — variant words that don't match any lemma_clean at all,
   whether or not they're in lookup. Broader catch than check 1.

3. is_inflection — variant words that are actually inflected forms of their
   own headword. These are redundant: inflections are already generated
   automatically and shouldn't be listed as variants.

Usage:
    uv run scripts/fix/variant_cleaner.py

No data is modified — review the output and fix entries manually in gui2.
"""

from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def has_lookup_no_lemma_clean(db_path: Path) -> None:
    """Print words in variant column that exist in lookup but not as lemma_clean."""
    pr.green_title("has_lookup_no_lemma_clean")

    db = get_db_session(db_path)

    lookup_keys: set[str] = {
        row.lookup_key for row in db.query(Lookup).filter(Lookup.headwords != "").all()
    }
    lemma_clean_set: set[str] = {row.lemma_clean for row in db.query(DpdHeadword).all()}

    results: list[tuple[str, str, str]] = []

    for hw in db.query(DpdHeadword).filter(DpdHeadword.variant != "").all():
        for variant_word in hw.variant_list:
            variant_word = variant_word.strip()
            if variant_word in lookup_keys and variant_word not in lemma_clean_set:
                results.append((hw.lemma_1, hw.pos, variant_word))

    if results:
        pr.cyan(f"{'lemma_1':<40} {'pos':<15} {'dirty variant'}")
        pr.cyan("-" * 80)
        for lemma_1, pos, dirty_variant in results:
            pr.white(f"{lemma_1:<40} {pos:<15} {dirty_variant}")
        pr.summary("total", str(len(results)))
    else:
        pr.green("No issues found.")

    db.close()


def no_lemma_clean(db_path: Path) -> None:
    """Print variants that are not in the lemma_clean set at all."""
    pr.green_title("no_lemma_clean")

    db = get_db_session(db_path)

    lemma_clean_set: set[str] = {row.lemma_clean for row in db.query(DpdHeadword).all()}

    results: list[tuple[str, str, str]] = []

    for hw in db.query(DpdHeadword).filter(DpdHeadword.variant != "").all():
        for variant_word in hw.variant_list:
            variant_word = variant_word.strip()
            if variant_word not in lemma_clean_set:
                results.append((hw.lemma_1, hw.pos, variant_word))

    if results:
        pr.cyan(f"{'lemma_1':<40} {'pos':<15} {'variant not in lemma_clean'}")
        pr.cyan("-" * 80)
        for lemma_1, pos, variant_word in results:
            pr.white(f"{lemma_1:<40} {pos:<15} {variant_word}")
        pr.summary("total", str(len(results)))
    else:
        pr.green("No issues found.")

    db.close()


def is_inflection(db_path: Path) -> None:
    """Print variants that are inflections of their own headword."""
    pr.green_title("is_inflection")

    db = get_db_session(db_path)

    results: list[tuple[str, str, str]] = []

    for hw in db.query(DpdHeadword).filter(DpdHeadword.variant != "").all():
        inflections: set[str] = set(hw.inflections_list)
        for variant_word in hw.variant_list:
            variant_word = variant_word.strip()
            if variant_word in inflections:
                results.append((hw.lemma_1, hw.pos, variant_word))

    if results:
        pr.cyan(f"{'lemma_1':<40} {'pos':<15} {'variant is inflection'}")
        pr.cyan("-" * 80)
        for lemma_1, pos, variant_word in results:
            pr.white(f"{lemma_1:<40} {pos:<15} {variant_word}")
        pr.summary("total", str(len(results)))
    else:
        pr.green("No issues found.")

    db.close()


def main() -> None:
    pth = ProjectPaths()
    db_path = pth.dpd_db_path
    has_lookup_no_lemma_clean(db_path)
    no_lemma_clean(db_path)
    is_inflection(db_path)


if __name__ == "__main__":
    main()
