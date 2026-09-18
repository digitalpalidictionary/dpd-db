"""Find `.page` reads that can run before the control is mounted.

Flet 1.0 made `Control.page` a property that walks up to the `Page` and
**raises `RuntimeError` when the control is not mounted**. In 0.28 it was a
plain attribute that read `None`. Two whole idioms break as a result:

1. caching a control's page in a plain helper object built from a view's
   constructor (`self.page = ui.page`) — raises at construction;
2. testing for mounting with `if control.page` / `control.page is None` —
   raises the very error it was written to avoid.

`check_premount_page.py` only walks within one control subclass, so it cannot
see either: the first lives in a *different* class, and the second reads
someone else's attribute. This catches both, repo-wide, by shape.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_page_reads.py

Exit code 1 if anything is found. Handler bodies are not exempt by default —
read each hit and judge it; a `page_of()`/`is_mounted()` call is the fix for a
mounted test, a lazy `page` property for a cached one.
"""

import ast
import sys
from pathlib import Path

SCAN_ROOTS: tuple[Path, ...] = (
    Path("gui2"),
    Path("db_tests/gui"),
)

SKIP_DIRS: frozenset[str] = frozenset({"__pycache__", "build", ".venv", "archive"})

# `toolkit.page` and `self.page` on a plain class hold a real Page object, not
# a control's resolved property, so they never raise.
SAFE_OWNERS: frozenset[str] = frozenset({"toolkit", "self"})


def is_page_attr(node: ast.AST) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "page"


def owner_name(node: ast.Attribute) -> str:
    value = node.value
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return value.attr
    return ""


def cached_in_init(tree: ast.Module, path: Path) -> list[str]:
    """`self.page = <something>.page` inside an __init__."""
    hits = []
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        for method in cls.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if method.name != "__init__":
                continue
            for node in ast.walk(method):
                if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                    continue
                targets: list[ast.expr] = (
                    list(node.targets)
                    if isinstance(node, ast.Assign)
                    else [node.target]
                )
                if not any(is_page_attr(t) for t in targets):
                    continue
                value = node.value
                if (
                    isinstance(value, ast.Attribute)
                    and value.attr == "page"
                    and owner_name(value) not in SAFE_OWNERS
                ):
                    hits.append(
                        f"{path.as_posix()}:{node.lineno}  {cls.name}.__init__  "
                        f"caches {ast.unparse(value)}"
                    )
    return hits


def mounted_tests(tree: ast.AST, path: Path) -> list[str]:
    """`x.page is None` / `x.page is not None` / `if x.page:` as a mount test."""
    hits = []
    for node in ast.walk(tree):
        tests: list[ast.expr] = []
        if isinstance(node, ast.If):
            tests = [node.test]
        elif isinstance(node, ast.BoolOp):
            tests = list(node.values)
        for test in tests:
            for sub in [test] + (
                list(test.comparators) + [test.left]
                if isinstance(test, ast.Compare)
                else []
            ):
                if is_page_attr(sub):
                    assert isinstance(sub, ast.Attribute)
                    hits.append(
                        f"{path.as_posix()}:{sub.lineno}  mount test on "
                        f"{ast.unparse(sub)}"
                    )
    return hits


def main() -> int:
    cached: list[str] = []
    tests: list[str] = []
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if not SKIP_DIRS.isdisjoint(path.parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            cached.extend(cached_in_init(tree, path))
            tests.extend(mounted_tests(tree, path))

    print(f"Cached `.page` in a constructor: {len(cached)}")
    for hit in cached:
        print(f"   {hit}")
    print(f"\n`.page` used as a mount test: {len(sorted(set(tests)))}")
    for hit in sorted(set(tests)):
        print(f"   {hit}")

    return 1 if cached or tests else 0


if __name__ == "__main__":
    sys.exit(main())
