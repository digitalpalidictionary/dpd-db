"""Regression + coverage tests for the ``tools.cst_source`` package.

History: this file began as a live old-vs-new parity harness during the
refactor of the former ``tools.cst_source_sutta_example`` single module. That
parity was verified byte-for-byte across all 91 books; the old module has since
been retired to ``archive/tools/``. These remaining tests guard the package
standalone (book/file coverage, determinism, and a few captured output counts).

    uv run pytest tests/tools/test_cst_source_refactor_parity.py
"""

import pytest

from tools.cst_source import find_cst_source_sutta_example
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths

ALL_BOOKS: list[str] = sorted(cst_texts.keys())

# (book, word) -> expected example count, captured from the verified package.
CURATED_COUNTS: dict[tuple[str, str], int] = {
    ("vin5", "adhipātimokkh"): 10,
    ("an4", "udakāsay"): 1,
    ("dn1", "brahmajāl"): 2,
    ("mn1", "mūlapariyāy"): 4,
}


def test_all_books_listed() -> None:
    """The package is anchored on exactly 91 books."""
    assert len(ALL_BOOKS) == 91


def test_every_xml_covered_exactly_once() -> None:
    """Every CST XML file on disk is referenced by exactly one book, and every
    referenced file exists on disk (217 files)."""
    pth = ProjectPaths()
    disk: set[str] = {p.name for p in pth.cst_xml_dir.glob("*.xml")}

    referenced: dict[str, list[str]] = {}
    for book, files in cst_texts.items():
        for txt in files:
            xml = txt.replace(".txt", ".xml")
            referenced.setdefault(xml, []).append(book)

    duplicated = {xml: books for xml, books in referenced.items() if len(books) > 1}
    assert not duplicated, f"files referenced by more than one book: {duplicated}"

    assert set(referenced) == disk, (
        f"missing on disk: {set(referenced) - disk}; "
        f"unreferenced on disk: {disk - set(referenced)}"
    )
    assert len(referenced) == 217


@pytest.mark.slow
@pytest.mark.parametrize("book", ["kn1"])
def test_is_deterministic(book: str) -> None:
    """Same input, same output — extraction must be deterministic."""
    assert find_cst_source_sutta_example(book, ".") == find_cst_source_sutta_example(
        book, "."
    )


@pytest.mark.slow
@pytest.mark.parametrize("book,word", sorted(CURATED_COUNTS))
def test_curated_word_counts(book: str, word: str) -> None:
    """Captured output counts for representative (book, word) pairs; every
    returned row has non-empty source and sutta."""
    results = find_cst_source_sutta_example(book, word)
    assert len(results) == CURATED_COUNTS[(book, word)]
    assert all(r.source and r.sutta for r in results)
