#!/usr/bin/env python3

"""Convert VRI Chaṭṭha Saṅgāyana Devanagari xml to Roman txt."""

import os

from bs4 import BeautifulSoup
from aksharamukha import transliterate
from rich import print

from tools.paths import ProjectPaths


def main():
    """Run it."""
    print("[bright_yellow]convert cst4 xml to txt")

    pth = ProjectPaths()

    for filename in sorted(os.listdir(pth.cst_xml_dir)):
        if "xml" in filename and "toc" not in filename:
            print(f"[green]{filename:<40}", end="")

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

                    print("ok")

            except Exception:
                print(f"[bright_red]ERROR: {filename} failed!")

        # else:
        #     print("[red]not .xml file: skipped")


if __name__ == "__main__":
    main()
