"""Phase 2b gate: every file in the wiring inventory is named in the catalogue.

The plan asks for "a throwaway script listing inventory entries with no
catalogue mention; report that count as zero". This is that check, kept rather
than thrown away because Phase 7 walks the catalogue again after the migration
and needs the same answer.

Matching is on the **path suffix**, not the bare filename: `main.py` exists in
both `gui2/` and `db_tests/gui/`, so a bare-name match reports the second as
covered when only the first is written up.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_catalogue_coverage.py

Exits non-zero while any in-scope file is uncatalogued. Phase 6 files
(`db_tests/gui/`, `resources/dpd-updater/`) are reported separately and do not
fail the check — they are catalogued in Phase 6, not in Phase 2b.
"""

import sys
from collections import Counter
from pathlib import Path

ARTIFACTS = Path("kamma/threads/20260917_flet_1_0_migration/artifacts")
INVENTORY = ARTIFACTS / "wiring_baseline.txt"
CATALOGUE = ARTIFACTS / "behaviour_catalogue.md"

# Catalogued in Phase 6 alongside their migration, not in the Phase 2b catalogue.
PHASE_6_PREFIXES: tuple[str, ...] = ("db_tests/gui/",)

# Dropped from the thread on 2026-09-17 (user: "a failed side project"). The
# baseline is the frozen 0.28 record and still lists its bindings, so they are
# excluded here rather than regenerated away — regenerating the baseline now
# would capture migrated 1.0 code and destroy the comparison point.
OUT_OF_SCOPE_PREFIXES: tuple[str, ...] = ("resources/dpd-updater/",)


def bindings_per_file(inventory: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for line in inventory.splitlines():
        if line and not line.startswith("#"):
            counts[line.split(":")[0]] += 1
    return counts


def is_mentioned(path: str, catalogue: str, ambiguous: set[str]) -> bool:
    """True if the catalogue names this file unambiguously.

    The catalogue writes most files by bare name (`dpd_fields.py`), so the bare
    name has to count. But `main.py` exists in three of the scanned trees, so a
    bare-name match there would let `gui2/main.py`'s write-up satisfy
    `db_tests/gui/main.py`. `ambiguous` carries the names that need a directory
    component to disambiguate.
    """
    parts = Path(path).parts
    first = 1 if parts[-1] in ambiguous else 0
    for start in range(len(parts) - 1, first - 1, -1):
        if "/".join(parts[start:]) in catalogue:
            return True
    return False


def ambiguous_names(paths: list[str]) -> set[str]:
    """Bare filenames that occur in more than one directory in the inventory."""
    seen: Counter[str] = Counter()
    for path in paths:
        seen[Path(path).name] += 1
    return {name for name, count in seen.items() if count > 1}


def main() -> int:
    inventory = INVENTORY.read_text(encoding="utf-8")
    catalogue = CATALOGUE.read_text(encoding="utf-8")
    counts = bindings_per_file(inventory)
    ambiguous = ambiguous_names(list(counts))

    covered: list[tuple[str, int]] = []
    missing: list[tuple[str, int]] = []
    deferred: list[tuple[str, int]] = []
    dropped: list[tuple[str, int]] = []

    for path, count in sorted(counts.items()):
        if path.startswith(OUT_OF_SCOPE_PREFIXES):
            dropped.append((path, count))
        elif path.startswith(PHASE_6_PREFIXES):
            deferred.append((path, count))
        elif is_mentioned(path, catalogue, ambiguous):
            covered.append((path, count))
        else:
            missing.append((path, count))

    total = sum(counts.values())
    print(f"inventory: {total} bindings across {len(counts)} files\n")
    print(
        f"catalogued:        {len(covered):3d} files, {sum(n for _, n in covered):3d} bindings"
    )
    print(
        f"deferred to Ph.6:  {len(deferred):3d} files, {sum(n for _, n in deferred):3d} bindings"
    )
    print(
        f"UNCATALOGUED:      {len(missing):3d} files, {sum(n for _, n in missing):3d} bindings"
    )

    if dropped:
        print(
            f"out of scope:      {len(dropped):3d} files, "
            f"{sum(n for _, n in dropped):3d} bindings"
        )
    for path, count in dropped:
        print(f"   [dropped]  {path}  ({count})")
    for path, count in deferred:
        print(f"   [phase 6] {path}  ({count})")
    for path, count in missing:
        print(f"   [MISSING] {path}  ({count})")

    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
