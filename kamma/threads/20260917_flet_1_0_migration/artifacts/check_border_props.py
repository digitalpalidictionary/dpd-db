"""Classify every border_* kwarg in gui2/ by the class it is passed to.

BR-22: `border_radius`/`border_color`/`border_width` are deprecated on
FormFieldControl (TextField, Dropdown) but remain valid on Container and
friends, so a flat grep over-counts. Also lists the form fields that set no
border property at all — those are the ones that lost their rounded corners.
"""

import ast
from pathlib import Path

DEPRECATED = {"border_radius", "border_color", "border_width"}
FORM_FIELD_NAMES = {
    "TextField",
    "Dropdown",
    "DpdTextField",
    "DpdDropdown",
    "DpdText",
    "AutoComplete",
    "SearchBar",
}
BORDER_KWARGS = DEPRECATED | {
    "border",
    "focused_border_color",
    "focused_border_width",
}


def callee_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return "<expr>"


def main() -> None:
    root = Path("gui2")
    form_field_hits: list[tuple[str, int, str, str]] = []
    other_hits: list[tuple[str, int, str, str]] = []
    unstyled: list[tuple[str, int, str]] = []

    for path in sorted(root.rglob("*.py")):
        if "build" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = callee_name(node)
            kwargs = {kw.arg for kw in node.keywords if kw.arg}
            is_form_field = name in FORM_FIELD_NAMES
            for kw in node.keywords:
                if kw.arg in DEPRECATED:
                    value = ast.unparse(kw.value)
                    entry = (str(path), kw.value.lineno, name, f"{kw.arg}={value}")
                    (form_field_hits if is_form_field else other_hits).append(entry)
            if is_form_field and not (kwargs & BORDER_KWARGS):
                unstyled.append((str(path), node.lineno, name))

    print(f"=== deprecated on form fields: {len(form_field_hits)} ===")
    for file, line, name, kw in form_field_hits:
        print(f"{file}:{line}  {name}  {kw}")
    print(
        f"\n=== same kwarg names, NOT form fields (leave alone): {len(other_hits)} ==="
    )
    for file, line, name, kw in sorted(other_hits):
        print(f"{file}:{line}  {name}  {kw}")
    print(f"\n=== form fields with no border setting at all: {len(unstyled)} ===")
    for file, line, name in unstyled:
        print(f"{file}:{line}  {name}")


if __name__ == "__main__":
    main()
