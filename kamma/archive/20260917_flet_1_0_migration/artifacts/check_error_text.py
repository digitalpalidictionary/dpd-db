"""BR-27 guard — `error_text` is dead on a Flet 1.0 TextField.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_error_text.py

1.0 renamed `TextField.error_text` to `error` but left `Dropdown.error_text`
alone, so the two control types spell it differently. Assigning the old name on
a TextField is **silently accepted** — it writes a dead instance attribute that
never reaches the UI — so every validation message and every red border in the
editor stopped appearing, with no error anywhere.

A blanket grep cannot check this: `error_text` is still correct on `Dropdown`
and on the `Dpd*` wrappers that forward it. So this walks each file's AST,
records which local attributes are built from a bare `ft.TextField(...)`, and
flags only `.error_text` assignments onto those.

Exits non-zero on any finding.
"""

import ast
import sys
from pathlib import Path

SCAN_ROOTS: tuple[Path, ...] = (Path("gui2"), Path("db_tests"))
SKIP_DIRS: frozenset[str] = frozenset({"__pycache__", "build", "archive", ".venv"})

# Classes that legitimately keep the 0.28 spelling: Dropdown never renamed it,
# and the Dpd* wrappers forward it on purpose (see dpd_fields_classes.py).
RENAMED_CONSTRUCTORS: frozenset[str] = frozenset({"TextField"})


def _is_renamed_constructor(value: ast.expr | None) -> bool:
    """`ft.TextField(...)` or a bare `TextField(...)` from a direct import."""
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    if isinstance(func, ast.Attribute):
        return func.attr in RENAMED_CONSTRUCTORS
    return isinstance(func, ast.Name) and func.id in RENAMED_CONSTRUCTORS


def raw_textfield_names(tree: ast.AST) -> set[str]:
    """Names bound to a bare `TextField(...)` in this file.

    Both `self.x = ft.TextField(...)` (recorded as `x`) and the local
    `f = ft.TextField(...)` (recorded as `f`), and the annotated forms of each.
    Attribute and local names share one set: a false positive needs the same
    identifier used for a control of each kind in one file, which is far
    cheaper than missing a silently dead assignment.
    """
    found: set[str] = set()

    def record(target: ast.expr) -> None:
        if isinstance(target, ast.Attribute):
            found.add(target.attr)
        elif isinstance(target, ast.Name):
            found.add(target.id)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _is_renamed_constructor(node.value):
            for target in node.targets:
                record(target)
        elif isinstance(node, ast.AnnAssign) and _is_renamed_constructor(node.value):
            record(node.target)
    return found


def bad_assignments(tree: ast.AST, raw: set[str]) -> list[tuple[int, str]]:
    """`<something in raw>.error_text = ...` — the silently dead assignment.

    Covers plain, annotated and augmented assignment; `+=` on a dead attribute
    is just as silent as `=`.
    """
    bad: list[tuple[int, str]] = []

    def owner(target: ast.expr) -> str | None:
        if not (isinstance(target, ast.Attribute) and target.attr == "error_text"):
            return None
        base = target.value
        if isinstance(base, ast.Attribute) and base.attr in raw:
            return base.attr
        if isinstance(base, ast.Name) and base.id in raw:
            return base.id
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets: list[ast.expr] = list(node.targets)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        else:
            continue
        for target in targets:
            name = owner(target)
            if name is not None:
                bad.append((node.lineno, name))
    return bad


def main() -> int:
    findings: list[str] = []
    scanned = 0

    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if SKIP_DIRS & set(path.parts):
                continue
            scanned += 1
            tree = ast.parse(path.read_text(encoding="utf-8"))
            raw = raw_textfield_names(tree)
            if not raw:
                continue
            for lineno, name in bad_assignments(tree, raw):
                findings.append(
                    f"{path}:{lineno}: self.{name} is a bare ft.TextField — "
                    "`error_text` is dead on it in 1.0, use `error`"
                )

    print(f"scanned {scanned} files")
    if findings:
        print(f"\n{len(findings)} dead error_text assignment(s):")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print("clean: no error_text assignment onto a bare ft.TextField")
    return 0


if __name__ == "__main__":
    sys.exit(main())
