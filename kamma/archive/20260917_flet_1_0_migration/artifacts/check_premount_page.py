"""BR-17 companion: find `self.page` reads that run *before* the control mounts.

`check_self_page.py` covers the assignment BR-17 names. This covers the other
half of the same breakage. Once the constructor's `self.page = page` is gone,
`self.page` is `None` until Flet mounts the control, so anything a constructor
reaches that reads `self.page` now raises.

A direct read inside `__init__` is easy to spot by eye. A read inside a method
that `__init__` calls is not, and every real instance in this codebase was of
that shape — two of them (`FilterTabView._add_filter_row` and
`._on_column_checkbox_change`, reached via `_initialize_filters`) were missed by
both of the thread's reviews and by the plan through revision 8. Hence this
walks the call graph transitively rather than looking at `__init__` alone.

The fix pattern is to pass the page down from constructor scope and read
`(page or self.page)`. Those reads are recognised and not reported.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_premount_page.py

Exit code 1 while any unguarded pre-mount read remains.
"""

import ast
import sys
from pathlib import Path

SCAN_ROOTS: tuple[Path, ...] = (
    Path("gui2"),
    Path("db_tests/gui"),
)

SKIP_DIRS: frozenset[str] = frozenset({"__pycache__", "build", ".venv", "archive"})

Method = ast.FunctionDef | ast.AsyncFunctionDef


def self_calls(node: ast.AST) -> set[str]:
    """Names of methods invoked as ``self.x(...)`` anywhere in `node`.

    A binding such as ``on_click=self._add_filter_row`` is deliberately not a
    match — it is an attribute reference, not a call, and runs after mount.
    """
    found: set[str] = set()
    for n in ast.walk(node):
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "self"
        ):
            found.add(n.func.attr)
    return found


def page_reads(node: ast.AST) -> list[int]:
    return [
        n.lineno
        for n in ast.walk(node)
        if isinstance(n, ast.Attribute)
        and n.attr == "page"
        and isinstance(n.value, ast.Name)
        and n.value.id == "self"
    ]


def guarded_lines(node: ast.AST) -> set[int]:
    """Lines where `self.page` is only the fallback in ``(page or self.page)``."""
    safe: set[int] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            first = n.values[0]
            if isinstance(first, ast.Name) and first.id == "page":
                for value in n.values[1:]:
                    for sub in ast.walk(value):
                        if isinstance(sub, ast.Attribute) and sub.attr == "page":
                            safe.add(sub.lineno)
    return safe


def scan_class(path: Path, cls: ast.ClassDef) -> list[str]:
    methods: dict[str, Method] = {
        m.name: m
        for m in cls.body
        if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if "__init__" not in methods:
        return []

    hits: list[str] = []
    seen: set[str] = set()
    queue: list[str] = ["__init__"]
    chain: dict[str, str] = {"__init__": "__init__"}

    while queue:
        name = queue.pop()
        if name in seen or name not in methods:
            continue
        seen.add(name)
        method = methods[name]
        safe = guarded_lines(method)
        for line in sorted(page_reads(method)):
            if line not in safe:
                hits.append(
                    f"{path.as_posix()}:{line}  {cls.name}.{name}   via {chain[name]}"
                )
        for callee in self_calls(method):
            if callee not in seen:
                chain.setdefault(callee, f"{chain[name]} -> {callee}")
                queue.append(callee)

    return hits


def main() -> int:
    hits: list[str] = []
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if not SKIP_DIRS.isdisjoint(path.parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for cls in ast.walk(tree):
                if not isinstance(cls, ast.ClassDef):
                    continue
                if not any(ast.unparse(b).startswith("ft.") for b in cls.bases):
                    continue  # plain classes keep their own writable `page`
                hits.extend(scan_class(path, cls))

    print(f"Pre-mount `self.page` reads reachable from __init__: {len(hits)}")
    for hit in hits:
        print(f"   {hit}")

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
