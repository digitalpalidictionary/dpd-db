#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Read and write the inflection template TSV files.

The templates live in two kinds of files:

- one index file ``templates_index.tsv`` with the columns
  ``pattern``, ``like``;
- one grid file per template, ``templates/<pattern>.tsv``,
  shaped like the old spreadsheet block:
    row 0: pattern name, then column headings with empty
           grammar cells between them;
    rows 1+: row label, then forms, grammar label pairs.

Multiple forms in one cell are joined with ``", "`` and kept in Pāḷi
alphabetical order; an empty cell is an empty string; every row is written
at full width with LF line endings, UTF-8 and no quoting.

This module owns all reading and writing of these files.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from tools.pali_sort_key import pali_list_sorter, pali_sort_key

FORM_SEPARATOR = ", "
INDEX_COLUMNS = ["pattern", "like"]


@dataclass
class TemplateFile:
    """One template: its index row plus the unpacked grid data.

    ``data`` has the same shape as ``InflectionTemplates.data`` unpacked:
    ``data[row][cell] = list[str]``, with the top-left cell always ``[""]``.
    """

    pattern: str
    like: str
    data: list[list[list[str]]]


def grid_path(templates_dir: Path, pattern: str) -> Path:
    """The grid file for a pattern."""
    return templates_dir / f"{pattern}.tsv"


def _read_index(index_path: Path, require: bool = True) -> list[dict[str, str]]:
    """Read the index file as a list of clean row dicts.

    With ``require=True`` a missing file raises ``ValueError``.
    With ``require=False`` a missing file counts as an empty index.
    """
    if not index_path.exists():
        if require:
            raise ValueError(f"index file not found: {index_path}")
        return []
    with index_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        rows: list[dict[str, str]] = []
        for raw in reader:
            row = {col: raw.get(col) or "" for col in INDEX_COLUMNS}
            if not row["pattern"]:
                raise ValueError(f"index row without pattern in {index_path}")
            rows.append(row)
    return rows


def _write_index(rows: list[dict[str, str]], index_path: Path) -> None:
    """Rewrite the index sorted by pattern."""
    rows = sorted(rows, key=lambda r: pali_sort_key(r["pattern"]))
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(
            f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE
        )
        writer.writerow(INDEX_COLUMNS)
        for row in rows:
            writer.writerow([row["pattern"], row["like"]])


def _read_grid(pattern: str, grid_path: Path) -> list[list[list[str]]]:
    """Read one grid file into the unpacked nested list."""
    with grid_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        lines = list(reader)

    if not lines:
        raise ValueError(f"empty table file: {grid_path}")

    header = lines[0]
    if header[0] != pattern:
        raise ValueError(
            f"top-left cell '{header[0]}' does not equal '{pattern}' in {grid_path}"
        )
    width = len(header)

    data: list[list[list[str]]] = []
    for row_no, line in enumerate(lines):
        if len(line) != width:
            raise ValueError(
                f"row {row_no} has {len(line)} cells, expected {width} in {grid_path}"
            )
        row: list[list[str]] = []
        for cell_no, cell in enumerate(line):
            if row_no == 0 and cell_no == 0:
                row.append([""])
                continue
            # A form never holds a comma, so splitting on a bare comma also
            # accepts a hand-edited "ā,āse". The old spreadsheet loader sorted
            # multi-form cells; the files can now be edited by hand too.
            forms = [f.strip() for f in cell.split(",") if f.strip()]
            if len(forms) > 1:
                forms = pali_list_sorter(forms)
            row.append(forms if forms else [""])
        data.append(row)
    return data


def _write_grid(t: TemplateFile, templates_dir: Path) -> None:
    """Write one grid file. Multi-form cells are kept in Pāḷi order."""
    templates_dir.mkdir(parents=True, exist_ok=True)
    lines: list[list[str]] = []
    for row_no, row in enumerate(t.data):
        cells: list[str] = []
        for cell_no, cell in enumerate(row):
            if row_no == 0 and cell_no == 0:
                cells.append(t.pattern)
            elif len(cell) > 1:
                cells.append(FORM_SEPARATOR.join(pali_list_sorter(cell)))
            else:
                cells.append(cell[0])
        lines.append(cells)

    with grid_path(templates_dir, t.pattern).open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(
            f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE
        )
        writer.writerows(lines)


def load_templates(index_path: Path, templates_dir: Path) -> list[TemplateFile]:
    """Load all templates from the index and grid files, in index order.

    Raises ``ValueError`` naming the file if any check fails:
    an index row without a table file, a table file without an index row,
    duplicate pattern names, a wrong top-left cell, a ragged row,
    or an empty ``like``.
    """
    index_rows = _read_index(index_path)
    templates: list[TemplateFile] = []
    seen: set[str] = set()
    for row in index_rows:
        pattern = row["pattern"]
        if pattern in seen:
            raise ValueError(f"duplicate pattern '{pattern}' in {index_path}")
        seen.add(pattern)
        if not row["like"]:
            raise ValueError(f"empty like for '{pattern}' in {index_path}")
        path = grid_path(templates_dir, pattern)
        if not path.exists():
            raise ValueError(f"table file not found: {path}")
        data = _read_grid(pattern, path)
        templates.append(TemplateFile(pattern=pattern, like=row["like"], data=data))

    for path in sorted(templates_dir.glob("*.tsv")):
        if path.stem not in seen:
            raise ValueError(f"table file without index row: {path}")

    return templates


def write_template(t: TemplateFile, index_path: Path, templates_dir: Path) -> None:
    """Write one template's grid file and insert or replace its index row."""
    _write_grid(t, templates_dir)
    rows = [
        r for r in _read_index(index_path, require=False) if r["pattern"] != t.pattern
    ]
    rows.append({"pattern": t.pattern, "like": t.like})
    _write_index(rows, index_path)


def remove_template(pattern: str, index_path: Path, templates_dir: Path) -> None:
    """Delete one template's grid file and index row."""
    path = grid_path(templates_dir, pattern)
    if path.exists():
        path.unlink()
    rows = [
        r for r in _read_index(index_path, require=False) if r["pattern"] != pattern
    ]
    _write_index(rows, index_path)


def rename_template(old: str, new: str, index_path: Path, templates_dir: Path) -> None:
    """Rename one template: grid file, top-left cell and index row."""
    old_path = grid_path(templates_dir, old)
    new_path = grid_path(templates_dir, new)
    if new_path.exists():
        raise ValueError(f"table file already exists: {new_path}")
    old_path.rename(new_path)

    # the top-left cell must equal the file name
    with new_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        lines = list(reader)
    lines[0][0] = new
    with new_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(
            f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE
        )
        writer.writerows(lines)

    rows = _read_index(index_path, require=False)
    for row in rows:
        if row["pattern"] == old:
            row["pattern"] = new
    _write_index(rows, index_path)
