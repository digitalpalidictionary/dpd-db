#!/usr/bin/env python3

"""Transliterate tipitaka.lk texts from Sinhala to Roman script."""

from os import walk
from rich import print
from pathlib import Path
from tools.pali_text_files import bjt_texts
from tools.printer import p_green, p_title, p_yes
from tools.sinhala_tools import translit_si_to_ro
from tools.tic_toc import tic, toc


sinhala_dir = Path("resources/tipitaka.lk/public/static/text/")
roman_dir = Path("resources/tipitaka.lk/public/static/text_roman")


def main():
    tic()
    p_title("transliterating tipitaka.lk")
    # pth = ProjectPaths()

    for root, dirs, files in walk(sinhala_dir):
        for counter, file in enumerate(files, 1):
            p_green(f"{counter:<10}{file}")
            in_path = sinhala_dir.joinpath(file)
            out_path = roman_dir.joinpath(file)
            
            with open(in_path) as f:
                sinhala = f.read()
            
            roman = translit_si_to_ro(sinhala)
            
            with open(out_path, "w") as f:
                f.write(roman)
            
            p_yes("")
    toc()


def get_file_names():
    p_green("get actual file names")
    file_list = []
    for root, dirs, files in walk(sinhala_dir):
        for counter, file in enumerate(files, 1):
            file_list.append(file)
    file_list = sorted(file_list)
    p_yes(len(file_list))
    return file_list


def test_file_names():
    p_title("test file names")

    file_names = get_file_names()

    p_green("get dict file names")

    counter = 0
    bjt_files = []
    for book in bjt_texts:
        for file_name in bjt_texts[book]:
            bjt_files.append(file_name)
            counter += 1
    p_yes(counter)

    p_green("difference 1")
    x = set(bjt_files).symmetric_difference(set(file_names))
    p_yes(f"{x}")
    p_green("difference 2")
    x = set(file_names).symmetric_difference(set(bjt_files))
    p_yes(f"{x}")

if __name__ == "__main__":
    # main()
    test_file_names()
