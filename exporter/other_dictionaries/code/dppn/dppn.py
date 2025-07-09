# -*- coding: utf-8 -*-
import json
import re

from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    """Export Ven. Ānandajoti's edit of DPPN to Goldendict"""

    pr.tic()
    pr.title("exporting DPPN")

    pth = ProjectPaths()

    dict_data: list[DictEntry] = []

    with open(pth.dppn_source_path) as f:
        dppn_json = json.load(f)

    for i in dppn_json:
        clean_lemma = re.sub(r"<[^>]+>", "", i["name"].strip())
        synonyms = []

        # split on "."
        parts = re.split(
            r"v\.l\.|also called|Also called|Sometimes called|wrongly called| or | and |called|\.|,|\(",
            clean_lemma,
        )

        # remove whitespace
        parts = [part.strip() for part in parts if part.strip()]

        # clean parts
        for part in parts:
            match part:
                # remove lemma numbering: Saṅgharakkhita 07
                case _ if re.findall(r"\s\d+$", part):
                    synonyms.append(re.sub(r"\s\d+$", "", part))

                # remove JA bracket
                case _ if re.findall(r"Ja\s\d+", part):
                    synonyms.append(part.replace(")", ""))

                case _:
                    synonyms.append(part)

        dict_entry = DictEntry(
            word=i["name"].strip(),
            definition_html=i["entry"],
            definition_plain="",
            synonyms=synonyms,
        )
        dict_data.append(dict_entry)

    dict_info = DictInfo(
        bookname="Dictionary of Pāli Proper Names",
        author="G. P. Malalasekera",
        description="Revised by Ānandajoti Bhikkhu, June 2025",
        website="https://ancient-buddhist-texts.net/Textual-Studies/DPPN/index.htm",
        source_lang="pi",
        target_lang="en",
    )

    dict_vars = DictVariables(
        css_paths=[pth.dppn_css_path],
        js_paths=None,
        gd_path=pth.dppn_gd_path,
        md_path=pth.dppn_mdict_path,
        dict_name="dppn",
        icon_path=None,
        zip_up=True,
        delete_original=True,
    )

    pr.yes(len(dict_data))

    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_vars,
        dict_data,
    )

    pr.toc()


if __name__ == "__main__":
    main()
