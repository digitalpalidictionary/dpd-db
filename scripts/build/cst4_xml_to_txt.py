#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Convert VRI Chaṭṭha Saṅgāyana Devanagari xml to Roman txt."""

import os

from bs4 import BeautifulSoup
from rich import print

from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    """Run it."""

    pr.tic()
    pr.title("convert cst4 xml to txt")

    pth = ProjectPaths()

    counter = 1
    for filename in sorted(os.listdir(pth.cst_xml_dir)):
        if filename == ".DS_Store":
            continue
        if "xml" in filename and "toc" not in filename:
            pr.counter(counter, 217, filename)
            try:
                with open(
                    pth.cst_xml_dir.joinpath(filename), "r", encoding="UTF-16"
                ) as f:
                    contents = f.read()
                    soup = BeautifulSoup(contents, "xml")
                    text_tags = soup.find_all("text")

                    text_extract = []

                    for text_tag in text_tags:
                        text_extract.append(f"{text_tag.get_text()}\n")

                    text = "".join(text_extract).lower()

                    with open(
                        pth.cst_txt_dir.joinpath(filename).with_suffix(".txt"), "w"
                    ) as f:
                        f.write(text)

            except Exception:
                print(f"[bright_red]ERROR: {filename} failed!")

            counter += 1
    pr.toc()


if __name__ == "__main__":
    main()
