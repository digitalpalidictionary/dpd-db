"""Single source of truth and translator for CST book identifiers.

Four identifier types, any of which can be translated into the others:

1. ``cst_filename``  e.g. ``s0101m.mul`` (stem, matches ``romn/<stem>.xml``)
2. ``cst_book_name`` e.g. ``Dīghanikāya, Sīlakkhandhavagga``
3. ``gui_book_code`` e.g. ``dn1`` (as used in ``gui2.dpd_fields_examples``)
4. ``dpd_book_code`` e.g. ``DN`` / ``DNa`` (as used in
   ``shared_data/help/abbreviations.tsv`` and bold_definitions ``file_list``)

Data lives next to this module in ``cst_book_translator.tsv``.

Examples:
    >>> from tools.cst_book_translator import from_cst_filename, from_dpd_code
    >>> from_cst_filename("s0101m.mul").gui_book_code
    'dn1'
    >>> [b.cst_filename for b in from_dpd_code("DN")][:3]
    ['s0101m.mul', 's0102m.mul', 's0103m.mul']
"""

import csv
from dataclasses import dataclass
from pathlib import Path

from tools.paths import ProjectPaths

_TSV_PATH = Path(__file__).with_suffix(".tsv")


@dataclass(frozen=True)
class BookInfo:
    cst_filename: str
    cst_book_name: str
    gui_book_code: str | None
    dpd_book_code: str | None

    @property
    def cst_xml_path(self) -> Path:
        return ProjectPaths().cst_xml_dir / f"{self.cst_filename}.xml"


def _load() -> tuple[
    list[BookInfo],
    dict[str, BookInfo],
    dict[str, list[BookInfo]],
    dict[str, list[BookInfo]],
    dict[str, BookInfo],
]:
    all_books: list[BookInfo] = []
    by_filename: dict[str, BookInfo] = {}
    by_gui: dict[str, list[BookInfo]] = {}
    by_dpd: dict[str, list[BookInfo]] = {}
    by_book_name: dict[str, BookInfo] = {}

    with _TSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            book = BookInfo(
                cst_filename=row["cst_filename"],
                cst_book_name=row["cst_book_name"],
                gui_book_code=row["gui_book_code"] or None,
                dpd_book_code=row["dpd_book_code"] or None,
            )
            all_books.append(book)
            by_filename[book.cst_filename] = book
            if book.gui_book_code:
                by_gui.setdefault(book.gui_book_code.lower(), []).append(book)
            if book.dpd_book_code:
                by_dpd.setdefault(book.dpd_book_code.lower(), []).append(book)
            if book.cst_book_name:
                by_book_name[book.cst_book_name.lower()] = book

    return all_books, by_filename, by_gui, by_dpd, by_book_name


_ALL, _BY_FILENAME, _BY_GUI, _BY_DPD, _BY_BOOK_NAME = _load()


def all_books() -> list[BookInfo]:
    return list(_ALL)


def from_cst_filename(stem: str) -> BookInfo | None:
    return _BY_FILENAME.get(stem)


def from_gui_code(gui_code: str) -> list[BookInfo]:
    return list(_BY_GUI.get(gui_code.lower(), []))


def from_dpd_code(dpd_code: str) -> list[BookInfo]:
    return list(_BY_DPD.get(dpd_code.lower(), []))


def from_cst_book_name(name: str) -> list[BookInfo]:
    book = _BY_BOOK_NAME.get(name.lower())
    return [book] if book else []


def translate(value: str) -> list[BookInfo]:
    """Auto-detect which identifier type ``value`` is and return matching rows."""
    if not value:
        return []
    if value in _BY_FILENAME:
        return [_BY_FILENAME[value]]
    key = value.lower()
    if key in _BY_GUI:
        return list(_BY_GUI[key])
    if key in _BY_DPD:
        return list(_BY_DPD[key])
    if key in _BY_BOOK_NAME:
        return [_BY_BOOK_NAME[key]]
    return []
