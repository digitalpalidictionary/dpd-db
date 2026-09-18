"""Find calls to Flet methods that became coroutines in 1.0 but are not awaited.

This is the quietest breaking change in the whole migration. In 0.28 these were
ordinary methods; in 1.0 they are coroutines, so calling one without `await`
returns a coroutine object, does nothing, and raises nothing. Python only
mutters `RuntimeWarning: coroutine '...' was never awaited` on garbage
collection, which is easy to scroll past.

Three of these reached the user before anyone noticed:
  * `window.close()` — Ctrl+Q silently stopped quitting;
  * `control.focus()` — every "move to the next field" became a no-op, so the
    cursor jumped back to whichever control has `autofocus`;
  * `scroll_to` — PageUp/PageDown did nothing.

The method-name list is read from the **installed** Flet rather than written
out, so it stays correct across versions.

Two acceptable shapes are recognised and not reported: `await x.method()`, and
a scheduled call such as `page.run_task(x.method)` — the latter is how
synchronous handler code legitimately fires one of these.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_unawaited.py

Exit code 1 if anything is found. Expect a few false positives on names Flet
shares with ordinary Python (`get`, `set`, `clear`, `remove`, `open`, `close`)
— each hit needs reading, not blind fixing.
"""

import ast
import inspect
import sys
from pathlib import Path

import flet as ft

SCAN_ROOTS: tuple[Path, ...] = (
    Path("gui2"),
    Path("db_tests/gui"),
)

SKIP_DIRS: frozenset[str] = frozenset({"__pycache__", "build", ".venv", "archive"})

# Names Flet shares with dicts, sets, lists, files and this codebase's own
# managers. Including them would bury the real hits in noise; `focus`,
# `scroll_to`, `close` and the rest of the genuinely Flet-only names remain.
AMBIGUOUS: frozenset[str] = frozenset(
    {
        "get",
        "set",
        "clear",
        "remove",
        "open",
        "close",
        "reset",
        "render",
        "capture",
        "enable",
        "disable",
        "pan",
        "zoom",
        "login",
        "contains_key",
        "get_keys",
        "get_image",
        "set_image",
        "get_files",
        "set_files",
        "is_enabled",
    }
)


def coroutine_method_names() -> set[str]:
    names: set[str] = set()
    for attr in dir(ft):
        cls = getattr(ft, attr)
        if not isinstance(cls, type):
            continue
        for name, fn in vars(cls).items():
            if not name.startswith("_") and inspect.iscoroutinefunction(fn):
                names.add(name)
    return names - AMBIGUOUS


def main() -> int:
    targets = coroutine_method_names()
    hits: list[str] = []

    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if not SKIP_DIRS.isdisjoint(path.parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

            awaited = {
                id(node.value) for node in ast.walk(tree) if isinstance(node, ast.Await)
            }
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if not isinstance(func, ast.Attribute):
                    continue
                if func.attr not in targets:
                    continue
                if id(node) in awaited:
                    continue
                hits.append(
                    f"{path.as_posix()}:{node.lineno}  {ast.unparse(func)}() "
                    f"— not awaited"
                )

    print(f"Unawaited Flet coroutine calls: {len(hits)}")
    for hit in hits:
        print(f"   {hit}")

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
