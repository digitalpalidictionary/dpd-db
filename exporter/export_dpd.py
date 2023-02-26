from json import loads
from rich import print
from typing import List
from sqlalchemy import and_

from db.models import PaliWord, DerivedData
from db.models import FamilyRoot, FamilyWord
from html_components import render_header_tmpl
from html_components import render_dpd_defintion_templ
from html_components import render_button_box_templ
from html_components import render_grammar_templ
from html_components import render_example_templ
from html_components import render_inflection_templ
from html_components import render_family_root_templ
from html_components import render_family_word_templ
from html_components import render_family_compound_templ
from html_components import render_family_sets_templ
from html_components import render_frequency_templ
from html_components import render_feedback_templ
from helpers import add_nigahitas
from tools.timeis import bip, bop


def generate_dpd_html(DB_SESSION, PTH):
    print("[green]generating dpd html")

    dpd_db = (
        DB_SESSION.query(
            PaliWord, DerivedData, FamilyRoot, FamilyWord
        ).outerjoin(
            DerivedData,
            PaliWord.pali_1 == DerivedData.pali_1
        ).outerjoin(
            FamilyRoot,
            and_(
                PaliWord.root_key == FamilyRoot.root_id,
                PaliWord.family_root == FamilyRoot.root_family)
        ).outerjoin(
            FamilyWord,
            PaliWord.family_word == FamilyWord.word_family
        ).all()
    )

    dpd_length = len(dpd_db)

    with open(PTH.dpd_css_path) as f:
        dpd_css = f.read()

    with open(PTH.buttons_js_path) as f:
        button_js = f.read()

    dpd_data_list: List[dict] = []

    bip()
    for counter, (i, dd, fr, fw) in enumerate(dpd_db):
        
        html: str = ""
        html += render_header_tmpl(dpd_css, button_js)
        html += "<body>"
        html += render_dpd_defintion_templ(i)
        html += render_button_box_templ(i)
        html += render_grammar_templ(i)
        html += render_example_templ(i)
        html += render_inflection_templ(i, dd)
        html += render_family_root_templ(i, fr)
        html += render_family_word_templ(i, fw)
        html += render_family_compound_templ(i, DB_SESSION)
        html += render_family_sets_templ(i, DB_SESSION)
        html += render_frequency_templ(i, dd)
        html += render_feedback_templ(i)
        html += "</body></html>"

        synonyms: list = loads(dd.inflections)
        synonyms = add_nigahitas(synonyms)
        synonyms += loads(dd.sinhala)
        synonyms += loads(dd.devanagari)
        synonyms += loads(dd.thai)

        dpd_data_list += [{
            "word": i.pali_1,
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms
        }]

        if counter % 10000 == 0:
            with open(f"xxx delete/exporter_dpd/{i.pali_1}.html", "w") as f:
                f.write(html)
            print(f"{counter:>10,} / {dpd_length:<10,} {i.pali_1:<20} {bop():>10}")
            bip()

    return dpd_data_list
