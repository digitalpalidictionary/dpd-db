#!/usr/bin/env python3

"""
Compiles DPD Abbreviations to markdown table and updates docs website.
"""

import re
from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict
from dps.scripts.rus_exporter.paths_ru import RuPaths


def make_abbreviations_md(pth: ProjectPaths, rupth: RuPaths, lang: str):
    pr.green(f"compiling to markdown table ({lang})") 

    abbreviations_tsv = read_tsv_dot_dict(pth.abbreviations_tsv_path)

    if lang == "ru":
        # === Russian Version ===
        data = [
            "# Сокращения",
            "Самый простой способ найти любое сокращение в DPD — просто __дважды__ щелкнуть по нему!",
            "Но если вы предпочитаете старомодный метод поиска в таблице, вот он...",
            "",
            "Существует два типа сокращений: грамматические и текстовые.",
            "## Грамматические сокращения",
            "|Сокращение|Значение|",
            "|:---|:---|",
        ]

        data_upper = [
            "",
            "## Текстовые сокращения",
            "|Сокращение|Значение|",
            "|:---|:---|",
        ]

    else:
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
            if lang == "ru":
                abbrev_display = i.ru_abbrev if i.ru_abbrev else i.abbrev
                meaning_display = i.ru_meaning if i.ru_meaning else i.meaning
                if i.ru_abbrev and not i.ru_meaning:
                    pr.red(f"Attention: '{i.ru_abbrev}' noes not have 'ru_meaning'.")
            # test for upper case letters, which are book titles
            if not re.findall(r"^[A-Z]", i.abbrev):
                if lang == "ru":
                    data.append(f"|{abbrev_display}|{meaning_display}|")
                else:
                    data.append(f"|{i.abbrev}|{i.meaning}|{i.explanation}|")
            else:
                if lang == "ru":
                    data_upper.append(f"|{abbrev_display}|{meaning_display}|")
                else:
                    data_upper.append(f"|{i.abbrev}|{i.meaning}|{i.explanation}|")
        else:
            print("huh", i)

    data.extend(data_upper)
    pr.yes(len(data))

    data_md = "\n".join(data) + "\n"

    return data_md


def save_to_web(pth: ProjectPaths, rupth: RuPaths, abbrev_md: str, lang: str):
    pr.green(f"saving to website source ({lang})")
    output_path = pth.docs_abbreviations_md_path
    if lang == "ru":
        output_path = rupth.ru_docs_abbreviations_md_path

    if output_path.exists():
        output_path.write_text(abbrev_md)
        # output_path.write_text(abbrev_md, encoding='utf-8') # Ensure UTF-8 for Russian
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
    
    # language
    lang = "en"
    if config_test("exporter", "language", "ru"):
        lang = "ru"

    pth = ProjectPaths()
    rupth = RuPaths()
    abbrev_md = make_abbreviations_md(pth, rupth, lang)
    save_to_web(pth, rupth, abbrev_md, lang)
    pr.toc()


if __name__ == "__main__":
    main()
