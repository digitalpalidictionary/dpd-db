"""Per-session in-memory index for CST example searches.

``find_cst_source_sutta_example`` re-reads and re-parses a book's XML on every
call, which costs ~0.5s per word across a book set. ``CstSourceIndex`` walks
the soups once at construction and stores flat per-element rows, so each
subsequent word search is a regex scan over in-memory strings (~30ms).

Gatha examples depend only on the element (never on the searched word), so
they are precomputed at build time, cached per gatha, with the stuck-loop
guard of ``find_gatha_example`` reproduced (a stuck element yields no
example — identical to the live path's timeout behaviour).

``find_examples`` output is byte-identical to concatenating
``find_cst_source_sutta_example(book, text_to_find)`` over the index's books.
"""

import re
import time
from dataclasses import dataclass

from bs4 import element

from tools.cst_source.examples import find_gatha_example, find_sentence_example
from tools.cst_source.extractor import make_book_parser
from tools.cst_source.loader import make_cst_soup
from tools.cst_source.models import CstSourceSuttaExample
from tools.cst_source.text_utils import clean_example
from tools.paths import ProjectPaths


@dataclass(slots=True)
class IndexRow:
    source: str
    sutta: str
    text: str
    is_gatha: bool
    gatha_examples: list[str]


def _resolve_gatha1(
    x: element.Tag | element.NavigableString | None,
) -> element.Tag | element.NavigableString | None:
    """Walk back to the gatha1 element the way ``find_gatha_example`` does,
    including its 1s stuck-loop guard. Returns None when stuck or exhausted.

    Deliberate divergence: a non-newline NavigableString or rend-less sibling
    returns None (no example) where the live path would crash — never seen in
    the corpus, and a stuck group costs 1s per element only at build time."""
    start_time = time.time()
    while x is not None:
        if x.text == "\n":
            x = x.previous_sibling
            continue
        if not isinstance(x, element.Tag):
            return None
        if x["rend"] == "gatha1":
            return x
        if x["rend"] in ("gatha2", "gatha3", "gathalast"):
            x = x.previous_sibling
            continue
        if time.time() - start_time > 1:
            return None
    return None


def _search_book_rows(
    rows: list[IndexRow], text_to_find: str
) -> list[CstSourceSuttaExample]:
    """Replicate ``find_cst_source_sutta_example``'s per-book semantics over
    indexed rows: same match test, same gatha/sentence split, same
    source/sutta guard, same within-book dedupe and ordering."""
    found: list[CstSourceSuttaExample] = []
    pattern = re.compile(text_to_find)
    for row in rows:
        if not pattern.findall(row.text):
            continue
        if row.is_gatha:
            examples = row.gatha_examples
        else:
            examples = find_sentence_example(row.text, text_to_find)
        for ex in examples:
            candidate = CstSourceSuttaExample(row.source, row.sutta, ex)
            if row.source and row.sutta and candidate not in found:
                found.append(candidate)
    return found


class CstSourceIndex:
    """One-off corpus index over a set of CST books for fast repeated
    example searches within a session."""

    def __init__(self, books: list[str], pth: ProjectPaths | None = None) -> None:
        self.books: list[str] = list(books)
        if pth is None:
            pth = ProjectPaths()
        self._rows: dict[str, list[IndexRow]] = {
            book: self._build_book(pth, book) for book in self.books
        }

    @staticmethod
    def _build_book(pth: ProjectPaths, book: str) -> list[IndexRow]:
        parser = make_book_parser(book)
        if parser is None:
            # no parser means the live path never records examples
            return []

        rows: list[IndexRow] = []
        gatha_cache: dict[int, list[str]] = {}
        for soup in make_cst_soup(pth, book):
            for x in soup.find_all(["head", "p"]):
                text = clean_example(x.text)
                rend = x.get("rend", "") or ""
                is_gatha = "gatha" in rend
                gatha_examples: list[str] = []
                if is_gatha:
                    gatha1 = _resolve_gatha1(x)
                    if gatha1 is not None:
                        key = id(gatha1)
                        if key not in gatha_cache:
                            gatha_cache[key] = find_gatha_example(x, "indexing")
                        gatha_examples = gatha_cache[key]
                parser.update(x)
                rows.append(
                    IndexRow(parser.source, parser.sutta, text, is_gatha, gatha_examples)
                )
        return rows

    def find_examples(self, text_to_find: str) -> list[CstSourceSuttaExample]:
        """Search all indexed books, in book order, for ``text_to_find``."""
        results: list[CstSourceSuttaExample] = []
        for book in self.books:
            results.extend(_search_book_rows(self._rows[book], text_to_find))
        return results
