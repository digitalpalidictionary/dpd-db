#!/usr/bin/env python3

"""
Compiles DPD Abbreviations to markdown table and updates docs website.
"""

import re
from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import p_green, p_green_title, p_no, p_red, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv_dot_dict


def make_abbreviations_md(pth: ProjectPaths):
    p_green("compiling to markdown table")

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
    p_yes(len(data))

    data_md = "\n".join(data) + "\n"

    return data_md


def save_to_web(pth: ProjectPaths, abbrev_md):
    p_green("saving to website source")
    if pth.docs_abbreviations_md_path.exists():
        pth.docs_abbreviations_md_path.write_text(abbrev_md)
    else:
        p_no("failed")
        p_red(f"{pth.docs_abbreviations_md_path} not found")


def main():
    tic()
    p_title("saving abbreviations to docs website")

    if config_test("exporter", "make_abbrev", "no"):
        p_green_title("disabled in config.ini")
        toc()
        return

    pth = ProjectPaths()
    abbrev_md = make_abbreviations_md(pth)
    save_to_web(pth, abbrev_md)
    toc()


if __name__ == "__main__":
    main()
