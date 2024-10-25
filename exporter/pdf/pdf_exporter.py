#!/usr/bin/env python3

"""Export DPD to PDF using Typst and Jinja templates."""


import re
import subprocess
import typst

from jinja2 import Environment, FileSystemLoader

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound, FamilyRoot
from tools.date_and_time import year_month_day_dash
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_green_title, p_red, p_title, p_yes
from tools.tic_toc import tic, toc


class GlobalVars():
    # database
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    # dpd_db = db_session.query(DpdHeadword).limit(100).all()
    dpd_db = db_session.query(DpdHeadword).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    root_fam_db = db_session.query(FamilyRoot).all()
    root_fam_db = sorted(root_fam_db, key=lambda x: (pali_sort_key(x.root_key), pali_sort_key(x.root_family)))

    compound_fam_db = db_session.query(FamilyCompound).all()
    compound_fam_db = sorted(compound_fam_db, key=lambda x: pali_sort_key(x.compound_family))
    
    # typst
    typst_data: list[str] = []
    used_letters_single: list[str] = []

    #jinja
    env = Environment(
        loader=FileSystemLoader("exporter/pdf/templates"), 
        autoescape=True,
        block_start_string="////",
        block_end_string="\\\\\\\\"

    )
    front_matter_templ = env.get_template("front_matter.typ")
    first_letter_templ = env.get_template("first_letter.typ")
    headword_templ = env.get_template("headword.typ")
    root_fam_templ = env.get_template("family_root.typ")
    compound_fam_templ = env.get_template("family_compound.typ")
    date = year_month_day_dash()

    # colours
    colour1: str = "#00A4CC"
    colour2: str = "#65DBFF"


def make_front_matter(g: GlobalVars):
    p_green("compiling front matter")
    g.typst_data.append(g.front_matter_templ.render())
    p_yes("ok")


def make_pali_to_english(g: GlobalVars):
    """Compile pali to english data"""

    p_green_title("compiling pali to english")

    for counter, i in enumerate(g.dpd_db):

        if counter % 10000 == 0:
            p_counter(counter, len(g.dpd_db), i.lemma_1)

        first_letter = i.lemma_1[0]
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.headword_templ.render(i=i, date=g.date))


def make_root_families(g: GlobalVars):
    """Compile root families."""

    p_green("compiling root families")

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#set page(columns: 1)\n")
    g.typst_data.append("#heading(level: 1)[Root Families]\n")

    for counter, i in enumerate(g.root_fam_db):

        if i.root_key.startswith("√"):
            first_letter = i.root_key[1]

            if first_letter not in g.used_letters_single:
                first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
                g.typst_data.append(first_letter_render)
                g.used_letters_single.append(first_letter)

        g.typst_data.append(g.root_fam_templ.render(i=i, date=g.date))
    
    p_yes(len(g.root_fam_db))


def make_compound_families(g: GlobalVars):
    """Compile compound families."""

    p_green("compiling compound families")

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Compound Families]\n")

    for counter, i in enumerate(g.compound_fam_db):
        first_letter = i.compound_family[0]
 
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.compound_fam_templ.render(i=i, date=g.date))
    
    p_yes(len(g.compound_fam_db))


def clean_up_typst_data(g: GlobalVars):
    """Remove extra lines, comments, etc."""

    p_green("cleaning up")

    cleaned_data = []
    for i in g.typst_data:

        # remove blank lines
        cleaned_string = re.sub(r"^$\n", "", i, flags=re.MULTILINE)

        # remove comments
        cleaned_string = re.sub(r"^//.+$\n", "", cleaned_string, flags=re.MULTILINE)

        # remove lines with only spaces
        cleaned_string = re.sub(r"^ *$\n", "", cleaned_string, flags=re.MULTILINE)

        cleaned_data.append(cleaned_string)

    g.typst_data = cleaned_data 
    p_yes("ok")


def save_typist_file(g: GlobalVars):
    """Save .typ file."""
   
    p_green("saving typst data")
    with open(g.pth.typst_data_path, "w") as f:
            f.write("".join(g.typst_data))
    p_yes("ok")


def export_to_pdf(g: GlobalVars):
    """Export to pdf."""

    p_green("rendering pdf")
    try:
        subprocess.run(
            [
                "typst",
                "compile",
                str(g.pth.typst_data_path),
                str(g.pth.typst_pdf_path)
            ]
        )
        # typst.compile(str(g.pth.typst_data_path), output=str(g.pth.typst_pdf_path))
        p_yes("ok")
    except Exception as e:
        p_red(f"\n{e}")


def main():
    tic()
    p_title("export to pdf with typst")
    g = GlobalVars()
    make_front_matter(g)
    make_pali_to_english(g)
    make_root_families(g)
    make_compound_families(g)
    clean_up_typst_data(g)
    save_typist_file(g)
    export_to_pdf(g)
    toc()


if __name__ == "__main__":
    main()