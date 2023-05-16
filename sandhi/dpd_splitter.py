#!/usr/bin/env python3.11

import json
import os
from pathlib import Path

from css_html_js_minify import css_minify
from rich import print
from mako.template import Template
from minify_html import minify

from db.models import Sandhi
from db.get_db_session import get_db_session

from tools.paths import ProjectPaths as PTH
from tools.timeis import tic, toc
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.cst_sc_text_sets import make_mula_words_set


# !!! minify

def main():
    tic()
    print("[bright_yellow]making dpd splitter goldendict mdict")
    mula_word_set = make_mula_words_set()
    sandhi_dict = make_sandhi_dict(mula_word_set)
    dpr_breakup_dict = make_dpr_breakup_dict(PTH)
    make_golden_dict(PTH, sandhi_dict, dpr_breakup_dict)
    unzip_and_copy(PTH)
    toc()


def make_sandhi_dict(mula_word_set):
    """Make a python dict of sandhi words and splits,
    exluding words in the mula_word_set,
    i.e. only aṭṭḥakathā, ṭīkā and aññā words are included."""

    print(f"[green]{'making sandhi dict':<40}", end="")
    db_session = get_db_session("dpd.db")
    sandhi_db = db_session.query(Sandhi).all()

    sandhi_dict = {}
    for i in sandhi_db:
        if i.sandhi not in mula_word_set:
            sandhi_dict[i.sandhi] = i.split_list
    print(f"{len(sandhi_dict):>10,}")
    return sandhi_dict


def make_dpr_breakup_dict(PTH):
    print(f"[green]{'making dpr breakup dict':<40}", end="")
    with open(PTH.dpr_breakup) as f:
        dpr_breakup = json.load(f)

    dpr_breakup_dict = {}

    for headword, breakup in dpr_breakup.items():
        html = "<div class='dpr'>"
        html += "<h4 class='dpr'>DPR Analysis</h4>"
        html += "<p class='sandhi'>"
        html += breakup     # .replace(" (", "<br>(")
        html += "</p></div>"
        dpr_breakup_dict[headword] = html

    print(f"{len(dpr_breakup_dict):>10,}")

    return dpr_breakup_dict


def make_golden_dict(PTH, sandhi_dict, dpr_breakup_dict):

    print(f"[green]{'generating goldendict':<40}", end="")

    with open(PTH.sandhi_css_path) as f:
        sandhi_css = f.read()

    sandhi_css = css_minify(sandhi_css)

    header_tmpl = Template(filename=str(
        PTH.header_sandhi_splitter_templ_path))

    sandhi_header = str(header_tmpl.render(css=sandhi_css))

    sandhi_data_list = []
    for sandhi, splits in sandhi_dict.items():

        html_string = sandhi_header
        html_string += "<body><div class='sandhi'><p class='sandhi'>"

        for split in splits:
            html_string += split

            if split != splits[-1]:
                html_string += "<br>"
            else:
                html_string += "</p></div>"

        if sandhi in dpr_breakup_dict:
            html_string += dpr_breakup_dict[sandhi]

        html_string += "</body>"

        sandhi_data_list += [{
            "word": sandhi,
            "definition_html": html_string,
            "definition_plain": "",
            "synonyms": ""
        }]
    
    # include words
    # for word, breakup in dpr_breakup_dict.items():
    #     if word not in sandhi_dict:
    #         html_string = sandhi_header
    #         html_string += f"<body>{breakup}</body>"

    #         html_string = minify(html_string)

    #         sandhi_data_list += [{
    #             "word": word,
    #             "definition_html": html_string,
    #             "definition_plain": "",
    #             "synonyms": ""
    #         }]

    zip_path = PTH.sandhi_zip_path

    ifo = ifo_from_opts({
        "bookname": "DPD Splitter",
        "author": "Bodhirasa",
        "description": "DPD Splitter & DPR Analysis",
        "website": "https://digitalpalidictionary.github.io/"
        })

    export_words_as_stardict_zip(sandhi_data_list, ifo, zip_path)

    print(f"{len(sandhi_data_list):>10,}")


def unzip_and_copy(PTH):

    print(f"[green]{'unipping and copying goldendict':<40}", end="")

    local_goldendict_path = Path("/home/bhikkhu/Documents/Golden Dict")
    if local_goldendict_path.exists():
        os.popen(
            f'unzip -o {PTH.sandhi_zip_path} -d "/home/bhikkhu/Documents/Golden Dict"')
        print(f"[white]{'OK':>10}")
    else:
        print("[red]local GoldenDict directory not found")


if __name__ == "__main__":
    main()
