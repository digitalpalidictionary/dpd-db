#!/usr/bin/env python3.10

from rich import print

from helpers import get_paths, ResourcePaths
from html_components import render_header_tmpl
from html_components import render_dpd_defintion_templ
from html_components import render_button_box_templ
from html_components import render_grammar_templ
from html_components import render_example_templ
from html_components import render_inflection_templ
from html_components import render_family_root_templ

from db.db_helpers import get_db_session
from db.models import PaliWord, DerivedData, FamilyRoot
from tools.timeis import tic, toc, bip, bop
from tools.dprint import dprint

tic()
PTH: ResourcePaths = get_paths()
DB_SESSION = get_db_session("dpd.db")
ERROR_LOG = open(PTH.error_log_path, "w")


def main():
    print("[bright_yellow]exporting dpd")
    generate_dpd_html()

    ERROR_LOG.close()
    DB_SESSION.close()
    toc()


def generate_dpd_html():
    print("[green]generating dpd html")

    dpd_db = DB_SESSION.query(
        PaliWord, DerivedData, FamilyRoot
    ).outerjoin(
        DerivedData,
        PaliWord.pali_1 == DerivedData.pali_1
    ).outerjoin(
        FamilyRoot,
        PaliWord.root_key + " " + PaliWord.family_root == FamilyRoot.root_family
    ).all()

    # dpd_db = DB_SESSION.query(PaliWord).all()
    dpd_length = len(dpd_db)

    with open(PTH.dpd_css_path) as f:
        dpd_css = f.read()

    with open(PTH.buttons_js_path) as f:
        button_js = f.read()

    bip()
    for counter, (i, dd, fr) in enumerate(dpd_db):
        html: str = ""

        html += render_header_tmpl(dpd_css, button_js)
        html += "<body>"
        html += render_dpd_defintion_templ(i)
        html += render_button_box_templ(i)
        html += render_grammar_templ(i)
        html += render_example_templ(i)
        html += render_inflection_templ(i, dd)
        html += render_family_root_templ(i, fr)

        # word fam
        # compound fam
        # freqency
        # feedback
        html += "</body></html>"

        if counter % 5000 == 0 or counter % dpd_length == 0:
            with open(f"xxx delete/exporter_html/{i.pali_1}.html", "w") as f:
                f.write(html)
            print(f"{counter:>9,} / {dpd_length:9<,} {i.pali_1:<20} {bop():>9}")
            bip()


if __name__ == "__main__":
    main()
