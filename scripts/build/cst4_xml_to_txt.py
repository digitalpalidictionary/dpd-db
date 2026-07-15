#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Convert VRI Chaṭṭha Saṅgāyana Devanagari xml to Roman txt.

Rerun after the CST XML submodule updates; output feeds tools/cst_sc_text_sets.py
and, from there, live consumers like scripts/find/pass2pre_an_counts.py."""

from pathlib import Path

from bs4 import BeautifulSoup
from rich import print

from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.yellow_title("convert cst4 xml to txt")

    pth = ProjectPaths()

    filenames = [
        p.name
        for p in sorted(pth.cst_xml_dir.iterdir())
        if p.name != ".DS_Store" and "xml" in p.name and "toc" not in p.name
    ]

    for counter, filename in enumerate(filenames, start=1):
        pr.counter(counter, len(filenames), filename)
        try:
            xml_path: Path = pth.cst_xml_dir.joinpath(filename)
            with open(xml_path, "r", encoding="UTF-16") as f:
                contents = f.read()
            soup = BeautifulSoup(contents, "xml")
            text_tags = soup.find_all("text")
            text = "".join(f"{tag.get_text()}\n" for tag in text_tags).lower()

            txt_path: Path = pth.cst_txt_dir.joinpath(filename).with_suffix(".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)

        except Exception as e:
            # Broad on purpose: a bad XML file (parser error, encoding issue, etc.)
            # must not abort the whole 217-file batch — log it and keep going.
            print(f"[bright_red]ERROR: {filename} failed: {e}")

    pr.toc()


if __name__ == "__main__":
    main()
