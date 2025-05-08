#!/usr/bin/env python3

"""
Compiles DPD Abbreviations to markdown table and updates docs website.
"""

import re

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict


def make_abbreviations_md(pth: ProjectPaths):
    pr.green("compiling to markdown table")

    abbreviations_tsv = read_tsv_dot_dict(pth.abbreviations_tsv_path)

    data = [
        "# Abbreviations",
        "The easiest way to find any abbreviation in DPD is simply to __double-click__ on it!",
        "But if you prefer the old fashioned method of looking things up in a table, here you go...",
        "",
        "There are two types of abbreviations: Grammatical and Textual.",
        "## Grammatical Abbreviations",
        "|Abbreviation|Meaning|Explanation|",
        "|:---|:---|:---|",
    ]

    data_upper = [
        "",
        "## Textual Abbreviations",
        "|Abbreviation|Meaning|Info|",
        "|:---|:---|:---|",
    ]

    for i in abbreviations_tsv:
        if i.abbrev:
            # test for upper case letters, which are book titles
            if not re.findall(r"^[A-Z]", i.abbrev):
                data.append(f"|{i.abbrev}|{i.meaning}|{i.explanation}|")
            else:
                data_upper.append(f"|{i.abbrev}|{i.meaning}|{i.explanation}|")
        else:
            print("huh", i)

    data.extend(data_upper)
    pr.yes(len(data))

    data_md = "\n".join(data) + "\n"

    return data_md


def save_to_web(pth: ProjectPaths, abbrev_md: str):
    pr.green("saving to website source")
    output_path = pth.docs_abbreviations_md_path

    if output_path.exists():
        output_path.write_text(abbrev_md)
        pr.yes("ok")
    else:
        pr.no("failed")
        pr.red(f"{output_path} not found")


def main():
    pr.tic()
    pr.title("saving abbreviations to docs website")

    if config_test("exporter", "make_abbrev", "no"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    abbrev_md = make_abbreviations_md(pth)
    save_to_web(pth, abbrev_md)
    pr.toc()


if __name__ == "__main__":
    main()
