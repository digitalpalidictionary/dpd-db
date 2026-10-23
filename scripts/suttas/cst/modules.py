# -*- coding: utf-8 -*-
"""Shared helpers for the CST sutta extractors: XML soup, TSV writer, sutta number."""

import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag


def make_soup(xml_file_path: Path) -> BeautifulSoup:
    """Parse a UTF-16 CST XML file into a BeautifulSoup tree."""
    with open(xml_file_path, "r", encoding="utf-16") as f:
        xml_content = f.read()
    soup = BeautifulSoup(xml_content, "xml")
    return soup


def write_cst_tsv(
    output_tsv: str, cst_data: list[dict[str, str | Path | None]]
) -> None:
    """Write the extracted CST rows to a quoted, tab-separated file."""
    with open(output_tsv, "w", newline="", encoding="utf-8") as tsv_file:
        fieldnames = cst_data[0].keys()
        writer = csv.DictWriter(
            tsv_file, fieldnames=fieldnames, delimiter="\t", quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        for data in cst_data:
            writer.writerow(data)
    print(f"Data saved to {output_tsv}")


def get_sutta_num(x: Tag) -> str:
    """Return the leading sutta number of a heading, or '-' if it has no digits."""
    if re.findall(r"\d", x.text.strip()):
        sutta_num = re.sub(r"\.* .+", "", x.text.strip())
    else:
        sutta_num = "-"
    return sutta_num
