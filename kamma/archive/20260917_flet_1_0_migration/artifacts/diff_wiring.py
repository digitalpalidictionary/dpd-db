"""Phase 7 — diff the live wiring inventory against the frozen 0.28 baseline.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/capture_wiring.py > /tmp/wiring_now.txt
    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/diff_wiring.py /tmp/wiring_now.txt

Every difference must be an *intended* rename or a change with a named reason.
A handler that vanished without explanation is a migration bug, not diff noise,
so the script classifies each difference and exits non-zero if any is left
unaccounted for.

Line numbers are stripped before comparing: every file in scope moved lines
during the migration, so comparing them would bury the real signal.
"""

import re
import sys
from collections import Counter
from pathlib import Path

ARTIFACTS = Path("kamma/threads/20260917_flet_1_0_migration/artifacts")
BASELINE = ARTIFACTS / "wiring_baseline.txt"

# The baseline is the frozen 0.28 record and carries rows from a directory
# that is not in this thread's scope. Dropped from both sides.
OUT_OF_SCOPE: tuple[str, ...] = ("resources/dpd-updater/",)

# Each rule rewrites a baseline row into the row the migration should produce.
# The comment is the reason the difference is intended; an unrewritten row that
# still fails to match is reported as unexplained.
RENAMES: tuple[tuple[str, str, str], ...] = (
    (r"\bft\.ElevatedButton\b", "ft.Button", "BR-7: ElevatedButton is gone"),
    (
        r"(ft\.Dropdown(?: \[[^\]]*\])?  )on_change=",
        r"\1on_select=",
        "BR-1: Dropdown.on_change does not exist in 1.0",
    ),
    (
        # 1.0's pop_dialog() closes the topmost dialog and takes no argument,
        # so the dialog named in the 0.28 lambda could not be carried over.
        r"self\.page\.close\([^)]*\)",
        "self.page.pop_dialog()",
        "BR-8: page.close(dlg) -> page.pop_dialog()",
    ),
)

# Bindings the migration removes outright. Each needs a reason, and each is
# expected to be gone — a *surviving* one is the finding.
DELETIONS: tuple[tuple[str, str], ...] = (
    (
        "gui2/main.py  ft.Tabs  on_click=self._on_tab_activated",
        "BR-14: 0.28 bound both on_click and on_change and fired the handler "
        "twice per tab activation; 1.0 binds on_change only, so the single "
        "fire is the preserved behaviour",
    ),
)


def rows(text: str) -> Counter[str]:
    """Bindings only, line numbers stripped, out-of-scope files dropped."""
    out: Counter[str] = Counter()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if any(prefix in line for prefix in OUT_OF_SCOPE):
            continue
        out[re.sub(r":\d+  ", "  ", line)] += 1
    return out


def apply_renames(row: str) -> tuple[str, str | None]:
    """Return the row as the migration should have left it, and why it changed."""
    why: str | None = None
    for pattern, replacement, reason in RENAMES:
        new = re.sub(pattern, replacement, row)
        if new != row:
            row, why = new, reason
    return row, why


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: diff_wiring.py <fresh inventory>", file=sys.stderr)
        return 2

    before = rows(BASELINE.read_text(encoding="utf-8"))
    after = rows(Path(sys.argv[1]).read_text(encoding="utf-8"))

    print(f"baseline (in scope): {sum(before.values())} bindings")
    print(f"current:             {sum(after.values())} bindings\n")

    deletions = dict(DELETIONS)
    explained: Counter[str] = Counter()
    remaining = after.copy()
    unexplained_gone: list[str] = []
    survived: list[str] = []

    for row, count in sorted(before.items()):
        for _ in range(count):
            if row in deletions:
                if remaining[row] > 0:
                    remaining[row] -= 1
                    survived.append(row)
                else:
                    explained[deletions[row]] += 1
                continue
            if remaining[row] > 0:
                remaining[row] -= 1
                continue
            migrated, why = apply_renames(row)
            if why is not None and remaining[migrated] > 0:
                remaining[migrated] -= 1
                explained[why] += 1
                continue
            unexplained_gone.append(row)

    unexplained_new = sorted(row for row, n in remaining.items() for _ in range(n))

    if explained:
        print("Intended renames, matched one-for-one:")
        for reason, count in sorted(explained.items()):
            print(f"  {count:>4}  {reason}")
        print()

    if survived:
        print(f"EXPECTED TO BE REMOVED but still bound: {len(survived)}")
        for row in survived:
            print(f"  ! {row}")
    if unexplained_gone:
        print(f"GONE without explanation: {len(unexplained_gone)}")
        for row in unexplained_gone:
            print(f"  - {row}")
    if unexplained_new:
        print(f"NEW without explanation: {len(unexplained_new)}")
        for row in unexplained_new:
            print(f"  + {row}")

    if not unexplained_gone and not unexplained_new and not survived:
        print("Zero unexplained differences.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
