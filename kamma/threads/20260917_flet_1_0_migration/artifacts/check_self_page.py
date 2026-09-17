"""BR-17 checker: find `self.page = ...` inside Flet control subclasses.

In Flet 1.0 `Control.page` is a read-only property, so assigning it raises
``AttributeError: property 'page' of 'X' object has no setter`` at construction.
In 0.28 it was an ordinary writable attribute.

The same assignment on a **plain** class is still perfectly fine, and this repo
has 28 of those. That is why this is an AST check and not a grep: a textual
find-and-replace over ``self.page =`` would break every one of them.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_self_page.py

Exit code 1 while any control-subclass assignment remains, so it doubles as the
verification gate for the BR-17 task.
"""

import ast
import sys
from pathlib import Path

SCAN_ROOTS: tuple[Path, ...] = (
    Path("gui2"),
    Path("db_tests/gui"),
    Path("resources/dpd-updater"),
)

# resources/dpd-updater carries its own nested .venv; scanning it would report
# Flet's own internals as hits.
SKIP_DIRS: frozenset[str] = frozenset({"__pycache__", "build", ".venv", "archive"})


def page_assignments(cls: ast.ClassDef) -> list[int]:
    """Line numbers of every ``self.page = ...`` in a class body."""
    lines: list[int] = []
    for node in ast.walk(cls):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        for target in targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "page"
                and isinstance(target.value, ast.Name)
                and target.value.id == "self"
            ):
                lines.append(target.lineno)
    return lines


def main() -> int:
    breaks: list[str] = []
    safe: list[str] = []

    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if not SKIP_DIRS.isdisjoint(path.parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for cls in ast.walk(tree):
                if not isinstance(cls, ast.ClassDef):
                    continue
                bases = [ast.unparse(base) for base in cls.bases]
                is_control = any(base.startswith("ft.") for base in bases)
                for lineno in page_assignments(cls):
                    entry = (
                        f"{path.as_posix()}:{lineno}  {cls.name}({', '.join(bases)})"
                    )
                    (breaks if is_control else safe).append(entry)

    print(f"BR-17 — breaks in Flet 1.0: {len(breaks)}")
    for entry in breaks:
        print(f"   {entry}")
    print(f"\nSafe (plain classes, leave alone): {len(safe)}")
    for entry in safe:
        print(f"   {entry}")

    return 1 if breaks else 0


if __name__ == "__main__":
    sys.exit(main())
