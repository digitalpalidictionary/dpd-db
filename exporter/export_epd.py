import re
from minify_html import minify
from typing import List
from sqlalchemy.orm import Session
from rich import print
from css_html_js_minify import css_minify

from html_components import render_header_tmpl
from db.models import PaliWord, PaliRoot
from tools.timeis import bip, bop
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths


def generate_epd_html(DB_SESSION: Session, PTH: ProjectPaths, size_dict) -> list:
    """generate html for english to pali dicitonary"""

    print("[green]generating epd html")

    dpd_db: list = DB_SESSION.query(PaliWord).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.pali_1))
    dpd_db_length = len(dpd_db)

    roots_db: list = DB_SESSION.query(PaliRoot).all()
    roots_db_length = len(roots_db)

    epd: dict = {}
    pos_exclude_list = ["abbrev", "cs", "letter", "root", "suffix", "ve"]

    with open(PTH.epd_css_path) as f:
        epd_css: str = f.read()

    epd_css = css_minify(epd_css)

    header = render_header_tmpl(epd_css, js="")

    bip()
    for counter, i in enumerate(dpd_db):
        meanings_list = []
        i.meaning_1 = re.sub(r"\?\?", "", i.meaning_1)

        if (i.meaning_1 != "" and
                i.pos not in pos_exclude_list):

            # remove all space brackets
            meanings_clean = re.sub(r" \(.+?\)", "", i.meaning_1)
            # remove all brackets space
            meanings_clean = re.sub(r"\(.+?\) ", "", meanings_clean)
            # remove space at start and fin
            meanings_clean = re.sub(r"(^ | $)", "", meanings_clean)
            # remove double spaces
            meanings_clean = re.sub(r"  ", " ", meanings_clean)
            # remove space around ;
            meanings_clean = re.sub(r" ;|; ", ";", meanings_clean)
            # remove i.e.
            meanings_clean = re.sub(r"i\.e\. ", "", meanings_clean)
            # remove !
            meanings_clean = re.sub(r"!", "", meanings_clean)
            # remove ?
            meanings_clean = re.sub(r"\\?", "", meanings_clean)
            meanings_list = meanings_clean.split(";")

            for meaning in meanings_list:
                if meaning in epd.keys() and i.plus_case == "":
                    epd_string = f"{epd[meaning]}<br><b class = 'epd'>{i.pali_clean}</b> {i.pos}. {i.meaning_1}"
                    epd[meaning] = epd_string

                if meaning in epd.keys() and i.plus_case != "":
                    epd_string = f"{epd[meaning]}<br><b class = 'epd'>{i.pali_clean}</b> {i.pos}. {i.meaning_1} ({i.plus_case})"
                    epd[meaning] = epd_string

                if meaning not in epd.keys() and i.plus_case == "":
                    epd_string = f"<b class = 'epd'>{i.pali_clean}</b> {i.pos}. {i.meaning_1}"
                    epd.update(
                        {meaning: epd_string})

                if meaning not in epd.keys() and i.plus_case != "":
                    epd_string = f"<b class = 'epd'>{i.pali_clean}</b> {i.pos}. {i.meaning_1} ({i.plus_case})"
                    epd.update(
                        {meaning: epd_string})

        if counter % 10000 == 0:
            print(f"{counter:>10,} / {dpd_db_length:<10,} {i.pali_1[:20]:<20} {bop():>10}")
            bip()

    print("[green]adding roots to epd")

    for counter, i in enumerate(roots_db):

        root_meanings_list: list = i.root_meaning.split(", ")

        for root_meaning in root_meanings_list:
            if root_meaning in epd.keys():
                epd_string = f"{epd[root_meaning]}<br><b class = 'epd'>{i.root}</b> root. {i.root_meaning}"
                epd[root_meaning] = epd_string

            if root_meaning not in epd.keys():
                epd_string = f"<b class = 'epd'>{i.root}</b> root. {i.root_meaning}"
                epd.update(
                    {root_meaning: epd_string})

        if counter % 250 == 0:
            print(f"{counter:>10,} / {roots_db_length:<10,} {i.root:<20} {bop():>10}")
            bip()

    print("[green]compiling epd html")

    epd_data_list: List[dict] = []
    size_dict["epd_header"] = 0
    size_dict["epd"] = 0

    for counter, (word, html_string) in enumerate(epd.items()):
        html = header
        size_dict["epd_header"] += len(header)

        html += "<body>"
        html += f"<div class ='epd'><p>{html_string}</p></div>"
        html += "</body></html>"
        size_dict["epd"] += len(html) - len(header)

        html = minify(html)

        epd_data_list += [{
            "word": word,
            "definition_html": html,
            "definition_plain": "",
            "synonyms": ""
        }]

    return epd_data_list, size_dict
