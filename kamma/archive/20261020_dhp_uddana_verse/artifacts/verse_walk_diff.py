"""Compare the old and new verse walk on every gatha line in the CST corpus.

Usage (from the project root):
    git show <old-ref>:tools/cst_source/examples.py > <scratch>/old_examples.py
    uv run kamma/threads/20261020_dhp_uddana_verse/artifacts/verse_walk_diff.py \
        <scratch>/old_examples.py <report.txt>

The old walk stalls 1 s on every line it cannot place, so a full run takes ~7 minutes.
"""

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

from bs4 import element

from tools.cst_source.examples import find_gatha_example as new_find
from tools.cst_source.loader import get_cst_filenames, make_cst_soup
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths

VERSE = ("gatha1", "gatha2", "gatha3", "gathalast")


def load_old(path: str):
    spec = importlib.util.spec_from_file_location("old_examples", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.find_gatha_example


def rend(x: element.PageElement | None) -> str:
    return str(x.get("rend", "")) if isinstance(x, element.Tag) else ""


def sibling(x: element.Tag, forward: bool) -> element.Tag | None:
    sib = x.next_sibling if forward else x.previous_sibling
    while sib is not None and not isinstance(sib, element.Tag):
        sib = sib.next_sibling if forward else sib.previous_sibling
    return sib


def is_clean_verse(x: element.Tag) -> bool:
    """The class the old walk handled correctly: walking back reaches gatha1
    without crossing a gathalast, and that gatha1 reaches its own gathalast
    through gatha2/gatha3 lines only."""
    start: element.Tag | None = x
    while start is not None and rend(start) != "gatha1":
        if rend(start) not in VERSE or (start is not x and rend(start) == "gathalast"):
            return False
        start = sibling(start, forward=False)
    if start is None:
        return False
    line: element.Tag | None = sibling(start, forward=True)
    while line is not None and rend(line) in ("gatha2", "gatha3"):
        line = sibling(line, forward=True)
    return rend(line) == "gathalast"


def main() -> None:
    old_find = load_old(sys.argv[1])
    report_path = Path(sys.argv[2])
    pth = ProjectPaths()

    done: set[str] = set()
    unchanged = 0
    changed: list[tuple[str, str, str, str]] = []
    clean_changed = 0
    for book in cst_texts:
        filenames = get_cst_filenames(book)
        if all(f in done for f in filenames):
            continue
        for filename, soup in zip(filenames, make_cst_soup(pth, book)):
            if filename in done:
                continue
            done.add(filename)
            for x in soup.find_all(["head", "p"]):
                if "gatha" not in rend(x):
                    continue
                with contextlib.redirect_stdout(io.StringIO()):
                    try:
                        old = old_find(x, "diff")
                    except Exception as e:  # the old walk can raise on odd markup
                        old = [f"<old raised {type(e).__name__}: {e}>"]
                new = new_find(x)
                if old == new:
                    unchanged += 1
                    continue
                if is_clean_verse(x):
                    clean_changed += 1
                changed.append((filename, x.text.strip(), repr(old), repr(new)))

    seen: set[tuple[str, str]] = set()
    lines = [
        f"files: {len(done)}",
        f"gatha lines unchanged: {unchanged}",
        f"gatha lines changed: {len(changed)}",
        f"changed lines in the clean-verse class (must be 0): {clean_changed}",
        "",
    ]
    for filename, text, old, new in changed:
        if (filename, new) in seen:
            continue
        seen.add((filename, new))
        lines += [f"## {filename} | {text}", f"old: {old}", f"new: {new}", ""]
    lines.insert(4, f"changed verses (deduped by new text): {len(seen)}")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:5]))


if __name__ == "__main__":
    main()
