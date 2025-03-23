#!/usr/bin/env python3

"""
Compiles DPD Abbreviations to markdown table and updates docs website.
"""

import re
from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import p_green, p_green_title, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv_dot_dict


def make_abbreviations_md(pth: ProjectPaths):
    p_green("compiling to markdown table")

    abbreviations_tsv = read_tsv_dot_dict(pth.abbreviations_tsv_path)
    data = []

    data.append("# Abbreviations")
    data.append(
        "The easiest way to find any abbreviation in DPD is simply to __double-click__ on it!"
    )
    data.append(
        "But if you prefer the old fashioned method of looking things up in a table, here you go..."
    )
    data.append("")
    data.append("There are two types of abbreviations: Grammatical and Textual.")
    data.append("## Grammatical Abbreviations")
    data.append("|Abbreviation|Meaning|Explanation|")
    data.append("|:---|:---|:---|")

    data_upper = []
    data_upper.append("## Textual Abbreviations")
    data_upper.append("|Abbreviation|Meaning|Info|")
    data_upper.append("|:---|:---|:---|")

    for i in abbreviations_tsv:
        if i.abbrev:
            # test for upper case letters, which are book titles
            if not re.findall(r"^[A-Z]", i.abbrev):
                data.append(f"|{i.abbrev}|{i.meaning}|{i.explanation}|")
            else:
                data_upper.append(f"|{i['abbrev']}|{i['meaning']}|{i['explanation']}|")
        else:
            print("huh", i)

    data.extend(data_upper)
    p_yes(len(data))

    data_md = "\n".join(data) + "\n"

    return data_md


def save_to_web(pth, abbrev_md):
    p_green("saving to website source")
    with open(pth.abbreviations_md_path, "w") as f:
        f.write(abbrev_md)
    p_yes("ok")


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
