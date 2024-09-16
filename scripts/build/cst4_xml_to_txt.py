#!/usr/bin/env python3

"""Convert VRI Chaṭṭha Saṅgāyana Devanagari xml to Roman txt."""

import os

from bs4 import BeautifulSoup
from aksharamukha import transliterate
from rich import print

from tools.paths import ProjectPaths
from tools.printer import p_counter, p_title
from tools.tic_toc import tic, toc


def main():
    """Run it."""

    tic()
    p_title("convert cst4 xml to txt")

    pth = ProjectPaths()

    counter = 1
    for filename in sorted(os.listdir(pth.cst_xml_dir)):
        if "xml" in filename and "toc" not in filename:
            p_counter(counter, 217, filename)
            try:
                with open(
                        pth.cst_xml_dir.joinpath(filename), 'r',
                        encoding="UTF-16") as f:

                    contents = f.read()
                    soup = BeautifulSoup(contents, 'xml')
                    text_tags = soup.find_all('text')

                    text_extract = ""

                    for text_tag in text_tags:
                        text_extract += text_tag.get_text() + "\n"

                    text_translit = transliterate.process(
                        "autodetect", "IASTPali", text_extract)

                    with open(
                            pth.cst_txt_dir.joinpath(filename).with_suffix(
                                ".txt"), "w") as f:
                        f.write(text_translit)

            except Exception:
                print(f"[bright_red]ERROR: {filename} failed!")
            
            counter += 1
    toc()


if __name__ == "__main__":
    main()
