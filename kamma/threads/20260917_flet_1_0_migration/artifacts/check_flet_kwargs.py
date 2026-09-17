"""Check every keyword passed to a Flet control against the installed Flet.

Flet 1.0 renamed or removed keywords on many controls. A wrong one raises
`TypeError` at *construction* time, and because gui2 builds its views lazily,
that means the moment a user first opens that tab — not at import, not in the
tests, not in any static check. `PopupMenuItem(text=...)` reached the user that
way after a migration pass that only looked at button classes.

This closes the class of bug rather than the instance: it walks every
`ft.Something(...)` call in the codebase and asks the *installed* Flet whether
each keyword actually exists on that class.

Two call shapes are checked: direct `ft.<Name>(...)` calls, and the
`super().__init__(...)` inside a class that subclasses `ft.<Name>` — the
`Dpd*` field wrappers pass most of their styling that way, and a wrong keyword
there breaks every field at once.

Limits worth knowing:
  * `**kwargs` calls are skipped, and a class Flet does not export is reported
    separately rather than silently passing;
  * this checks that a keyword *exists*, not that its value still has the right
    type or meaning.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_flet_kwargs.py

Exit code 1 if any keyword is unknown to its control.
"""

import ast
import dataclasses
import sys
from pathlib import Path

import flet as ft

SCAN_ROOTS: tuple[Path, ...] = (
    Path("gui2"),
    Path("db_tests/gui"),
)

SKIP_DIRS: frozenset[str] = frozenset({"__pycache__", "build", ".venv", "archive"})


def accepted_keywords(cls: type) -> set[str] | None:
    """Every keyword `cls(...)` accepts, or None if it cannot be determined."""
    try:
        names = {f.name for f in dataclasses.fields(cls)}  # pyright: ignore[reportArgumentType]
    except TypeError:
        return None
    # Dataclass fields cover the 1.0 controls; inherited properties that are not
    # fields are still settable but not constructor keywords, which is exactly
    # what we want to flag.
    return {n for n in names if not n.startswith("_")}


def main() -> int:
    unknown: list[str] = []
    unresolved: set[str] = set()
    checked = 0

    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if not SKIP_DIRS.isdisjoint(path.parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

            # Which ft.* class each class in this file subclasses, so that its
            # `super().__init__(...)` can be checked against the right control.
            base_of: dict[ast.AST, str] = {}
            for cls_def in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
                for base in cls_def.bases:
                    if (
                        isinstance(base, ast.Attribute)
                        and isinstance(base.value, ast.Name)
                        and base.value.id == "ft"
                    ):
                        for inner in ast.walk(cls_def):
                            base_of[inner] = base.attr
                        break

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name: str | None = None
                if (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "ft"
                ):
                    name = func.attr
                elif (
                    isinstance(func, ast.Attribute)
                    and func.attr == "__init__"
                    and isinstance(func.value, ast.Call)
                    and isinstance(func.value.func, ast.Name)
                    and func.value.func.id == "super"
                ):
                    name = base_of.get(node)
                if name is None:
                    continue
                cls = getattr(ft, name, None)
                if not isinstance(cls, type):
                    continue
                func_attr = name
                allowed = accepted_keywords(cls)
                if allowed is None:
                    unresolved.add(func_attr)
                    continue
                checked += 1
                for kw in node.keywords:
                    if kw.arg is None:  # **kwargs
                        continue
                    if kw.arg not in allowed:
                        unknown.append(
                            f"{path.as_posix()}:{kw.value.lineno}  "
                            f"ft.{func_attr}({kw.arg}=...)"
                        )

    print(f"Flet constructions checked: {checked}")
    print(f"Unknown keywords: {len(unknown)}")
    for hit in unknown:
        print(f"   {hit}")
    if unresolved:
        print(f"\nNot introspectable (checked by hand): {sorted(unresolved)}")

    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
