import re

from json import loads
from rich import print
from sqlalchemy.orm import Session
from typing import List
from minify_html import minify

from helpers import add_nigahitas
from html_components import render_header_tmpl
from html_components import render_sandhi_templ
from helpers import ResourcePaths
from db.models import PaliWord, Sandhi
from tools.timeis import bip, bop


def generate_sandhi_html(DB_SESSION: Session, PTH: ResourcePaths) -> list:
    """generate html for sandhi split compounds"""

    print("[green]generating sandhi html")

    dpd_db: list = DB_SESSION.query(PaliWord).all()
    dpd_db_length = len(dpd_db)

    sandhi_db = DB_SESSION.query(Sandhi).all()
    sandhi_db_length: int = len(sandhi_db)
    sandhi_data_list: list = []

    clean_headwords_set: set = set([i.pali_clean for i in dpd_db])

    with open(PTH.sandhi_css_path) as f:
        sandhi_css = f.read()

    header = render_header_tmpl(css=sandhi_css, js="")

    bip()
    for counter, i in enumerate(sandhi_db):

        splits = loads(i.split)

        if i.sandhi not in clean_headwords_set:
            html = header
            html += "<body>"
            html += render_sandhi_templ(splits)
            html += "</body></html>"

            html = minify(
                html,
                minify_js=True,
                minify_css=True,
                minify_html=True,
                keep_closing_tags=True,
                remove_processing_instructions=True
            )

            synonyms = add_nigahitas([i.sandhi])
            synonyms += loads(i.sinhala)
            synonyms += loads(i.devanagari)
            synonyms += loads(i.thai)

            sandhi_data_list += [{
                "word": i.sandhi,
                "definition_html": html,
                "definition_plain": "",
                "synonyms": synonyms
            }]

            if counter % 25000 == 0:
                with open(f"xxx delete/exporter_sandhi/{i.sandhi}.html", "w") as f:
                    f.write(html)
                print(
                    f"{counter:>10} / {sandhi_db_length:<10,} {i.sandhi[:20]:<20} {bop():>10}")

    return sandhi_data_list
