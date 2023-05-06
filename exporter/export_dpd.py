
from minify_html import minify
from json import loads
from rich import print
from typing import List
from sqlalchemy import and_
from css_html_js_minify import css_minify, js_minify

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
from tools.add_niggahitas import add_niggahitas
from tools.timeis import bip, bop


def generate_dpd_html(DB_SESSION, PTH, SANDHI_CONTRACTIONS, size_dict):
    print("[green]generating dpd html")

    with open(PTH.dpd_css_path) as f:
        dpd_css = f.read()

    dpd_css = css_minify(dpd_css)

    with open(PTH.buttons_js_path) as f:
        button_js = f.read()
    button_js = js_minify(button_js)

    dpd_data_list: List[dict] = []

    dpd_db = (
        DB_SESSION.query(
            PaliWord, DerivedData, FamilyRoot, FamilyWord
        ).outerjoin(
            DerivedData,
            PaliWord.id == DerivedData.id
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
    size_dict["dpd_header"] = 0
    size_dict["dpd_summary"] = 0
    size_dict["dpd_button_box"] = 0
    size_dict["dpd_grammar"] = 0
    size_dict["dpd_example"] = 0
    size_dict["dpd_inflection_table"] = 0
    size_dict["dpd_family_root"] = 0
    size_dict["dpd_family_word"] = 0
    size_dict["dpd_family_compound"] = 0
    size_dict["dpd_family_sets"] = 0
    size_dict["dpd_frequency"] = 0
    size_dict["dpd_feedback"] = 0
    size_dict["dpd_synonyms"] = 0

    bip()
    for counter, (i, dd, fr, fw) in enumerate(dpd_db):

        # replace \n with html line break
        i.meaning_1 = i.meaning_1.replace("\n", "<br>")
        i.sanskrit = i.sanskrit.replace("\n", "<br>")
        i.phonetic = i.phonetic.replace("\n", "<br>")
        i.compound_construction = i.compound_construction.replace("\n", "<br>")
        i.commentary = i.commentary.replace("\n", "<br>")
        i.link = i.link.replace("\n", "<br>")
        i.sutta_1 = i.sutta_1.replace("\n", "<br>")
        i.sutta_2 = i.sutta_2.replace("\n", "<br>")
        i.example_1 = i.example_1.replace("\n", "<br>")
        i.example_2 = i.example_2.replace("\n", "<br>")
        i.construction = i.construction.replace("\n", "<br>")

        html: str = ""
        header = render_header_tmpl(dpd_css, button_js)
        html += header
        size_dict["dpd_header"] += len(header)

        html += "<body>"

        summary = render_dpd_defintion_templ(i)
        html += summary
        size_dict["dpd_summary"] += len(summary)

        button_box = render_button_box_templ(i)
        html += button_box
        size_dict["dpd_button_box"] += len(button_box)

        grammar = render_grammar_templ(i)
        html += grammar
        size_dict["dpd_grammar"] += len(grammar)

        example = render_example_templ(i)
        html += example
        size_dict["dpd_example"] += len(example)

        inflection_table = render_inflection_templ(i, dd)
        html += inflection_table
        size_dict["dpd_inflection_table"] += len(inflection_table)

        family_root = render_family_root_templ(i, fr)
        html += family_root
        size_dict["dpd_family_root"] += len(family_root)

        family_word = render_family_word_templ(i, fw)
        html += family_word
        size_dict["dpd_family_word"] += len(family_word)

        family_compound = render_family_compound_templ(i, DB_SESSION)
        html += family_compound
        size_dict["dpd_family_compound"] += len(family_compound)

        family_sets = render_family_sets_templ(i, DB_SESSION)
        html += family_sets
        size_dict["dpd_family_sets"] += len(family_sets)

        frequency = render_frequency_templ(i, dd)
        html += frequency
        size_dict["dpd_frequency"] += len(frequency)

        feedback = render_feedback_templ(i)
        html += feedback
        size_dict["dpd_feedback"] += len(feedback)

        html += "</body></html>"
        html = minify(html)

        synonyms: list = loads(dd.inflections)
        synonyms = add_niggahitas(synonyms)
        for synonym in synonyms:
            if synonym in SANDHI_CONTRACTIONS:
                contractions = SANDHI_CONTRACTIONS[synonym]["contractions"]
                synonyms.extend(contractions)
        synonyms += loads(dd.sinhala)
        synonyms += loads(dd.devanagari)
        synonyms += loads(dd.thai)
        synonyms += i.family_set_list
        synonyms += [str(i.id)]
        size_dict["dpd_synonyms"] += len(str(synonyms))

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

    return dpd_data_list, size_dict
