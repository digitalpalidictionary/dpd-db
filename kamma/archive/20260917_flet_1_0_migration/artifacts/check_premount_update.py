"""Phase 5: find `update()` calls that run *before* the control mounts.

Sibling of `check_premount_page.py`, which covers `self.page` reads. Flet 1.0's
`BaseControl.update` raises `RuntimeError` on an unmounted control where 0.28
made it a silent no-op, so any `update()` a constructor reaches — directly or
through a method it calls — is a crash rather than a wasted call.

Walks the call graph from every control subclass's `__init__`, the same way the
`self.page` scanner does, because every real instance found in this codebase was
one or two calls deep rather than in `__init__` itself.

Three shapes are recognised as safe and not reported:

* a call inside an `is_mounted(...)` test — the codebase's guard pattern;
* a call inside a nested function or lambda, which is a handler being *bound*
  rather than run, so it fires after mount;
* `target.update()` where `target` came from ``page or page_of(self)`` — that is
  BR-17's fix pattern and the receiver is the `Page`, which is always mounted.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_premount_update.py

Exit code 1 while any unguarded pre-mount `update()` remains.
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
    """Names of methods invoked as ``self.x(...)`` anywhere in `node`."""
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


def update_calls(node: ast.AST) -> list[tuple[int, str]]:
    """Every ``<something>.update()`` call, as (line, rendered receiver).

    Nested functions and lambdas are not descended into: a handler defined in a
    constructor is bound there, not called there.
    """
    found: list[tuple[int, str]] = []
    stack: list[ast.AST] = list(ast.iter_child_nodes(node))
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "update"
            and not n.args
            and not n.keywords
        ):
            found.append((n.lineno, ast.unparse(n.func.value)))
        stack.extend(ast.iter_child_nodes(n))
    return found


def page_aliases(node: ast.AST) -> set[str]:
    """Locals assigned from ``page or page_of(self)`` — BR-17's fix pattern.

    The receiver is then the `Page`, which is mounted by definition.
    """
    names: set[str] = set()
    for n in ast.walk(node):
        if not isinstance(n, ast.Assign) or not isinstance(n.value, ast.BoolOp):
            continue
        if not isinstance(n.value.op, ast.Or):
            continue
        rendered = ast.unparse(n.value)
        if "page" not in rendered:
            continue
        for target in n.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def guarded_lines(node: ast.AST) -> set[int]:
    """Lines inside the body of an ``if is_mounted(...)`` test."""
    safe: set[int] = set()
    for n in ast.walk(node):
        if not isinstance(n, ast.If):
            continue
        if not any(
            isinstance(t, ast.Call)
            and isinstance(t.func, ast.Name)
            and t.func.id == "is_mounted"
            for t in ast.walk(n.test)
        ):
            continue
        for stmt in n.body:
            for sub in ast.walk(stmt):
                if hasattr(sub, "lineno"):
                    safe.add(sub.lineno)  # pyright: ignore[reportAttributeAccessIssue]
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
        pages = page_aliases(method)
        for line, receiver in sorted(update_calls(method)):
            if line not in safe and receiver not in pages:
                hits.append(
                    f"{path.as_posix()}:{line}  {cls.name}.{name}"
                    f"   {receiver}.update()   via {chain[name]}"
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
                    continue
                hits.extend(scan_class(path, cls))

    print(f"Pre-mount `update()` calls reachable from __init__: {len(hits)}")
    for hit in hits:
        print(f"   {hit}")

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
