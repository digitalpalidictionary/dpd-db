from rich import print
from sqlalchemy.orm import Session
from minify_html import minify
from css_html_js_minify import css_minify

from html_components import render_header_tmpl
from html_components import render_sandhi_templ

from db.models import PaliWord, Sandhi
from tools.niggahitas import add_niggahitas
from tools.timeis import bip, bop
from tools.cst_sc_text_sets import make_mula_words_set
from tools.paths import ProjectPaths


def generate_sandhi_html(
    DB_SESSION: Session,
        PTH: ProjectPaths,
        SANDHI_CONTRACTIONS: dict,
        size_dict) -> list:
    """Generate html for sandhi split compounds.
    Only include words which are not already in DPD,
    and are in the mūla texts of CST and SC."""

    print("[green]generating sandhi html")

    # reduce to only mūla books to limit number of sandhi incluced in dpd
    mula_word_set: set = make_mula_words_set()

    dpd_db: list = DB_SESSION.query(PaliWord).all()
    sandhi_db = DB_SESSION.query(Sandhi).all()
    sandhi_db_length: int = len(sandhi_db)
    sandhi_data_list: list = []

    # don't include words already in dpd
    clean_headwords_set: set = set([i.pali_clean for i in dpd_db])

    with open(PTH.sandhi_css_path) as f:
        sandhi_css = f.read()
    sandhi_css = css_minify(sandhi_css)

    header = render_header_tmpl(css=sandhi_css, js="")

    size_dict["sandhi_header"] = 0
    size_dict["sandhi_sandhi"] = 0
    size_dict["sandhi_synonyms"] = 0

    bip()
    for counter, i in enumerate(sandhi_db):

        splits = i.split_list

        if (i.sandhi not in clean_headwords_set and
                i.sandhi in mula_word_set):

            html = header
            size_dict["sandhi_header"] += len(header)

            html += "<body>"

            sandhi = render_sandhi_templ(i, splits)
            html += sandhi
            size_dict["sandhi_sandhi"] += len(sandhi)

            html += "</body></html>"

            html = minify(html)

            synonyms = add_niggahitas([i.sandhi])
            synonyms += i.sinhala_list
            synonyms += i.devanagari_list
            synonyms += i.thai_list
            if i.sandhi in SANDHI_CONTRACTIONS:
                contractions = SANDHI_CONTRACTIONS[i.sandhi]["contractions"]
                synonyms.extend(contractions)

            size_dict["sandhi_synonyms"] += len(str(synonyms))

            sandhi_data_list += [{
                "word": i.sandhi,
                "definition_html": html,
                "definition_plain": "",
                "synonyms": synonyms
            }]

            if counter % 5000 == 0:
                with open(f"xxx delete/exporter_sandhi/{i.sandhi}.html", "w") as f:
                    f.write(html)
                print(
                    f"{counter:>10,} / {sandhi_db_length:<10,} {i.sandhi[:20]:<20} {bop():>10}")
                bip()

    return sandhi_data_list, size_dict
