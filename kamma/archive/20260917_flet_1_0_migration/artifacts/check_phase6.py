"""Phase 6 verification — the Flet consumers outside gui2's main editor.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/check_phase6.py

Three checks, all static or import-time, so none of them opens a window:

1. every file imports cleanly (or compiles, for the one file whose entry point
   runs at module level);
2. the entry point named in the plan actually resolves to a callable;
3. no 0.28-only Flet API survives anywhere in these trees.

Exits non-zero on any failure.
"""

import ast
import importlib
import py_compile
import re
import sys
from pathlib import Path

SCAN_ROOTS: tuple[Path, ...] = (
    Path("db_tests/gui"),
    Path("gui2/utilities"),
)

EXTRA_FILES: tuple[Path, ...] = (Path("gui2/test_app.py"),)

SKIP_DIRS: frozenset[str] = frozenset({"__pycache__", ".venv", "build", "archive"})

# db_tests/gui/main.py calls ft.run() at module level, so importing it would
# launch the app. It is compiled and AST-checked instead.
LAUNCH_ON_IMPORT: frozenset[str] = frozenset({"db_tests/gui/main.py"})

# (module path, attribute) pairs the plan names as entry points.
ENTRY_POINTS: tuple[tuple[str, str], ...] = (
    ("db_tests.gui.main", "main"),
    ("gui2.test_app", "main"),
    ("gui2.utilities.find_words_with_examples", "run_gui"),
    ("gui2.utilities.sandhi_contraction_find_replace_gui", "main"),
)

# Every 0.28-only spelling this migration removed. A survivor here raises at
# the moment the line executes, which for most of them is view-construction
# time — so a clean import is not evidence on its own.
DEAD_API: tuple[tuple[str, str], ...] = (
    (r"\bft\.app\(", "BR-6: ft.app is gone, use ft.run"),
    (r"\bft\.ElevatedButton\b", "BR-7: use ft.Button"),
    (r"\bft\.padding\.(all|only|symmetric)\(", "BR-10: use ft.Padding"),
    (r"\bft\.border_radius\.all\(", "BR-10: use ft.BorderRadius"),
    (r"\bft\.border\.all\(", "BR-2: use ft.Border.all"),
    (r"\bft\.alignment\.[a-z]", "BR-3: constants are uppercase on ft.Alignment"),
    (r"\bpage\.set_clipboard\b", "BR-5: clipboard is an awaitable service"),
    (r"\bpage\.get_clipboard\b", "BR-5: clipboard is an awaitable service"),
    (r"\bpage\.snack_bar\s*=", "BR-8: use page.show_dialog"),
    (r"\bpage\.open\(", "BR-8: use page.show_dialog"),
    (r"\bpage\.close\(", "BR-8: use page.pop_dialog"),
    (r"\bDropdown\([^)]*on_change=", "BR-1: Dropdown takes on_select"),
    (r"\bSwitch\([^)]*label_style=", "BR-15: use label_text_style"),
    (r"\bflet\.version\.version\b", "BR-12: use flet.__version__"),
    (r"\btab_content\s*=", "BR-14: Tab takes label="),
    (r"\bft\.Tabs\([^)]*tabs=", "BR-14: Tabs takes content=, tabs live on TabBar"),
)


def in_scope_files() -> list[Path]:
    found: list[Path] = []
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            if SKIP_DIRS & set(path.parts):
                continue
            found.append(path)
    return found + list(EXTRA_FILES)


def check_imports(files: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in files:
        posix = path.as_posix()
        if posix in LAUNCH_ON_IMPORT:
            try:
                py_compile.compile(str(path), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append(f"{posix}: does not compile — {exc}")
            continue
        module = posix.removesuffix(".py").replace("/", ".")
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 — any failure is a real finding
            failures.append(f"{posix}: import failed — {type(exc).__name__}: {exc}")
    return failures


def check_entry_points() -> list[str]:
    failures: list[str] = []
    for module, attr in ENTRY_POINTS:
        path = Path(module.replace(".", "/") + ".py")
        if path.as_posix() in LAUNCH_ON_IMPORT:
            # Resolve by AST rather than by import, for the same reason.
            tree = ast.parse(path.read_text(encoding="utf-8"))
            names = {
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            if attr not in names:
                failures.append(f"{module}: no top-level def {attr}")
            continue
        obj = getattr(importlib.import_module(module), attr, None)
        if not callable(obj):
            failures.append(f"{module}.{attr} is not callable (got {obj!r})")
    return failures


def check_dead_api(files: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in files:
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if line.lstrip().startswith("#"):
                continue
            for pattern, why in DEAD_API:
                if re.search(pattern, line):
                    failures.append(f"{path}:{lineno}: {why} — {line.strip()}")
    return failures


def main() -> int:
    files = in_scope_files()
    print(f"Phase 6 scope: {len(files)} files")

    sections = (
        ("dead 0.28 API", check_dead_api(files)),
        ("imports", check_imports(files)),
        ("entry points", check_entry_points()),
    )

    failed = False
    for label, failures in sections:
        if failures:
            failed = True
            print(f"\n{label}: {len(failures)} FAILED")
            for failure in failures:
                print(f"  {failure}")
        else:
            print(f"{label}: clean")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
