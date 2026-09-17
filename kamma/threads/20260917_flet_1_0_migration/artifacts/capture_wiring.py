"""AST wiring inventory for the Flet 0.28 -> 1.0 migration.

Emits every event-handler binding in the Flet-consuming parts of the repo, so
the same scan can be re-run after the migration and diffed. A lost binding is a
migration bug; the diff is what catches it.

Regex cannot do this job. The eight main editor dropdown fields never name
``ft.Dropdown`` at their binding site -- they are declared as ``FieldConfig``
entries and fanned out through ``DpdDropdown`` -- so a grep for ``ft.Dropdown``
reports zero of them. That indirection is exactly where BR-1 (``Dropdown`` has
no ``on_change`` in 1.0) does its damage, which is why this resolves it.

Run from the project root:

    uv run kamma/threads/20260917_flet_1_0_migration/artifacts/capture_wiring.py
"""

import ast
from collections import Counter
from pathlib import Path

# Everything in the repo that imports flet. gui2/ is the editor; the db_tests
# helpers and the updater are the other two consumers, both in scope.
SCAN_ROOTS: tuple[Path, ...] = (
    Path("gui2"),
    Path("db_tests/gui"),
    Path("resources/dpd-updater"),
)

SKIP_DIRS: frozenset[str] = frozenset(
    {"__pycache__", "build", "archive", ".venv", "storage", "assets"}
)

OUTPUT_PATH = Path(
    "kamma/threads/20260917_flet_1_0_migration/artifacts/wiring_baseline.txt"
)

# ``FieldConfig`` declares a field; ``DpdFields.create_fields`` turns it into a
# concrete control chosen by ``field_type``. That dispatch is read out of the
# source at scan time rather than hardcoded here, so adding a field type cannot
# silently drop its bindings from the inventory.
FIELD_CONFIG_CLASS = "FieldConfig"
FIELD_CONFIG_DISPATCH_FILE = Path("gui2/dpd_fields.py")
FIELD_CONFIG_DISPATCH_FUNC = "create_fields"
FIELD_CONFIG_DEFAULT_TYPE = "text"


def in_scope_files() -> list[Path]:
    """Every in-scope ``.py`` file, sorted. Non-``.py`` files are never counted."""
    found: list[Path] = []
    for root in SCAN_ROOTS:
        for path in root.rglob("*.py"):
            if SKIP_DIRS.isdisjoint(path.parts):
                found.append(path)
    return sorted(found)


def dotted_name(node: ast.expr) -> str | None:
    """Render ``ft.Dropdown`` / ``self.foo.bar`` as a dotted string."""
    parts: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def describe_handler(node: ast.expr) -> str:
    """A stable, diffable rendering of whatever was bound to an ``on_*`` keyword."""
    if isinstance(node, ast.Lambda):
        # Lambdas have no name, so fall back to the expression they evaluate.
        # Keeps two different lambdas on the same control distinguishable.
        return f"lambda -> {ast.unparse(node.body)}"
    if isinstance(node, ast.Constant) and node.value is None:
        return "None"
    name = dotted_name(node)
    return name if name is not None else ast.unparse(node)


def class_bases(files: list[Path], trees: dict[Path, ast.Module]) -> dict[str, str]:
    """Map every locally defined class to its immediate base, e.g. DpdDropdown -> ft.Dropdown."""
    bases: dict[str, str] = {}
    for path in files:
        for node in ast.walk(trees[path]):
            if isinstance(node, ast.ClassDef) and node.bases:
                base = dotted_name(node.bases[0])
                if base is not None:
                    bases[node.name] = base
    return bases


def resolve_control(name: str, bases: dict[str, str]) -> str:
    """Walk a local subclass up to the Flet control it is really constructing."""
    seen: set[str] = set()
    current = name
    while current in bases and current not in seen:
        seen.add(current)
        current = bases[current]
    return current


def field_type_dispatch(tree: ast.Module) -> dict[str, str]:
    """Read ``create_fields``'s ``field_type`` -> control-class dispatch from source.

    Returns e.g. ``{"dropdown": "DpdDropdown", "meaning": "DpdMeaningField"}``.
    """
    dispatch: dict[str, str] = {}
    for func in ast.walk(tree):
        if not (
            isinstance(func, ast.FunctionDef)
            and func.name == FIELD_CONFIG_DISPATCH_FUNC
        ):
            continue
        for branch in ast.walk(func):
            if not isinstance(branch, ast.If):
                continue
            test = branch.test
            if not (
                isinstance(test, ast.Compare)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and isinstance(test.comparators[0].value, str)
            ):
                continue
            field_type = test.comparators[0].value
            for stmt in branch.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and isinstance(stmt.value, ast.Call)
                    and (target := dotted_name(stmt.value.func)) is not None
                ):
                    dispatch[field_type] = target
                    break
    return dispatch


class BindingCollector(ast.NodeVisitor):
    """Collects every call that binds at least one ``on_*`` keyword."""

    def __init__(
        self,
        path: Path,
        bases: dict[str, str],
        dispatch: dict[str, str],
    ) -> None:
        self.path = path
        self.bases = bases
        self.dispatch = dispatch
        self.rows: list[tuple[str, int, str, str, str]] = []
        self.class_stack: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Tracked so a ``super().__init__(on_change=...)`` inside a wrapper can be
        # attributed to the control the wrapper subclasses. That call is where
        # DpdDropdown binds its handlers, so leaving it unresolved would hide the
        # single highest-leverage binding in the codebase.
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        # A handler can be bound by assignment as well as by keyword —
        # ``page.on_keyboard_event = self.on_keyboard``. Those never appear in a
        # call's keywords, so scanning calls alone silently omits them, BR-4's
        # keyboard handler included.
        for target in node.targets:
            if isinstance(target, ast.Attribute) and target.attr.startswith("on_"):
                owner = dotted_name(target.value) or ast.unparse(target.value)
                self.rows.append(
                    (
                        self.path.as_posix(),
                        target.lineno,
                        f"{owner} (assigned)",
                        target.attr,
                        describe_handler(node.value),
                    )
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        handlers = [kw for kw in node.keywords if kw.arg and kw.arg.startswith("on_")]
        if handlers:
            constructed = dotted_name(node.func) or ast.unparse(node.func)
            control = self._control_for(constructed, node)
            for keyword in handlers:
                assert keyword.arg is not None  # guarded by the filter above
                self.rows.append(
                    (
                        self.path.as_posix(),
                        node.lineno,
                        control,
                        keyword.arg,
                        describe_handler(keyword.value),
                    )
                )
        self.generic_visit(node)

    def _control_for(self, constructed: str, node: ast.Call) -> str:
        """The Flet control this call really builds, annotated when it was indirect."""
        if constructed == "super().__init__" and self.class_stack:
            owner = self.class_stack[-1]
            resolved = resolve_control(owner, self.bases)
            return f"{resolved} [via super() in {owner}]"

        if constructed == FIELD_CONFIG_CLASS:
            field_type = FIELD_CONFIG_DEFAULT_TYPE
            for keyword in node.keywords:
                if (
                    keyword.arg == "field_type"
                    and isinstance(keyword.value, ast.Constant)
                    and isinstance(keyword.value.value, str)
                ):
                    field_type = keyword.value.value
            wrapper = self.dispatch.get(field_type)
            if wrapper is None:
                return f"{constructed}(field_type={field_type!r}) -> UNRESOLVED"
            resolved = resolve_control(wrapper, self.bases)
            return f"{resolved} [via {constructed}(field_type={field_type!r}) -> {wrapper}]"

        resolved = resolve_control(constructed, self.bases)
        if resolved != constructed:
            return f"{resolved} [via {constructed}]"
        return resolved


def main() -> None:
    files = in_scope_files()
    trees: dict[Path, ast.Module] = {
        path: ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for path in files
    }
    bases = class_bases(files, trees)
    dispatch = field_type_dispatch(trees[FIELD_CONFIG_DISPATCH_FILE])

    rows: list[tuple[str, int, str, str, str]] = []
    for path in files:
        collector = BindingCollector(path, bases, dispatch)
        collector.visit(trees[path])
        rows.extend(collector.rows)

    # Sorted so the post-migration diff shows real changes, not reordering.
    rows.sort()

    per_root: Counter[str] = Counter()
    per_handler: Counter[str] = Counter()
    gui2_handler: Counter[str] = Counter()
    for file_name, _, _, handler, _ in rows:
        root = next(
            (r.as_posix() for r in SCAN_ROOTS if file_name.startswith(r.as_posix())),
            "other",
        )
        per_root[root] += 1
        per_handler[handler] += 1
        if root == "gui2":
            gui2_handler[handler] += 1

    lines = [
        "# Flet event-handler wiring inventory",
        f"# files scanned: {len(files)}",
        f"# bindings: {len(rows)}",
        "#",
        "# format: <file>:<line>  <control>  <handler>=<callable>",
        "# '[via X]' means the binding site names X, which subclasses the control shown.",
        "#",
    ]
    for root, count in sorted(per_root.items()):
        lines.append(f"# {root}: {count} bindings")
    lines.append("#")
    for handler, count in sorted(per_handler.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"# {handler}: {count} ({gui2_handler[handler]} in gui2)")
    lines.append("")
    for file_name, lineno, control, handler, callable_name in rows:
        lines.append(f"{file_name}:{lineno}  {control}  {handler}={callable_name}")

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"{len(files)} files, {len(rows)} bindings -> {OUTPUT_PATH}")
    for root, count in sorted(per_root.items()):
        print(f"  {root}: {count}")
    print(f"  field_type dispatch read from source: {dispatch}")


if __name__ == "__main__":
    main()
