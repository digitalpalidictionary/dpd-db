"""A fingerprint of a contributor's JSON entry, shared by gui2 (which logs it
when the maintainer processes an entry) and scripts/server_contrib (which uses
it to see that main has already processed an entry)."""

import hashlib
import json
from pathlib import Path

# The per-contributor files the server delivers to main, as (glob pattern, kind).
# History, daily log, presets and stash files are never delivered. One list for
# push, reconcile and the merge script, so they cannot disagree.
DELIVERED_KINDS: tuple[tuple[str, str], ...] = (
    ("additions_*.json", "additions"),
    ("corrections_*.json", "corrections"),
    ("user_dictionary_*.txt", "user_dictionary"),
    ("checked_*.csv", "checked"),
    ("manual_corrections_*.tsv", "manual_corrections"),
    ("variant_readings_*.tsv", "variant_readings"),
    ("spelling_mistakes_*.tsv", "spelling_mistakes"),
    ("db_test_exceptions_*.tsv", "db_test_exceptions"),
)


def delivered_files(data_dir: Path) -> dict[str, list[Path]]:
    """The delivered contributor files in data_dir, grouped by kind. The
    `*_added` review logs match the additions and corrections patterns, so they
    are left out."""
    found: dict[str, list[Path]] = {}
    for pattern, kind in DELIVERED_KINDS:
        found[kind] = [
            path for path in sorted(data_dir.glob(pattern)) if "_added" not in path.name
        ]
    return found


def entry_hash(entry: dict) -> str:
    """sha1 of the entry as sorted-key JSON, so the hash does not depend on key
    order or on whether the entry was just built or loaded back from a file."""
    text = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()
