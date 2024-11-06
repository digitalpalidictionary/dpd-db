#!/usr/bin/env python3

"""Export DPD to PDF using Typst and Jinja templates."""

import re
import subprocess
# import typst

from jinja2 import Environment, FileSystemLoader

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound, FamilyIdiom, FamilyRoot, FamilyWord, Lookup
from tools.date_and_time import year_month_day_dash
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import p_green, p_red, p_title, p_yes
from tools.tic_toc import tic, toc

debug = False

class GlobalVars():
    # database
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # db queries
    if debug is True:
        dpd_db = db_session.query(DpdHeadword).limit(100).all()
        epd_db = db_session.query(Lookup).filter(Lookup.epd != "").limit(100).all()
        root_fam_db = db_session.query(FamilyRoot).limit(100).all()
        word_fam_db = db_session.query(FamilyWord).limit(100).all()
        compound_fam_db = db_session.query(FamilyCompound).limit(100).all()
        idioms_fam_db = db_session.query(FamilyIdiom).limit(100).all()
    else:
        dpd_db = db_session.query(DpdHeadword).all()
        epd_db = db_session.query(Lookup).filter(Lookup.epd != "").all()
        root_fam_db = db_session.query(FamilyRoot).all()
        word_fam_db = db_session.query(FamilyWord).all()
        compound_fam_db = db_session.query(FamilyCompound).all()
        idioms_fam_db = db_session.query(FamilyIdiom).all()

    # sorting
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
    epd_db = sorted(epd_db, key=lambda x: x.lookup_key.casefold())
    root_fam_db = sorted(root_fam_db, key=lambda x: (pali_sort_key(x.root_key), pali_sort_key(x.root_family)))
    word_fam_db = sorted(word_fam_db, key=lambda x: pali_sort_key(x.word_family))
    compound_fam_db = sorted(compound_fam_db, key=lambda x: pali_sort_key(x.compound_family))
    idioms_fam_db = sorted(idioms_fam_db, key=lambda x: pali_sort_key(x.idiom))

    # typst
    typst_data: list[str] = []
    used_letters_single: list[str] = []

    #jinja env
    env = Environment(
        loader=FileSystemLoader("exporter/pdf/templates"), 
        autoescape=True,
        block_start_string="////",
        block_end_string="\\\\\\\\"
    )

    # templates
    front_matter_templ = env.get_template("front_matter.typ")
    first_letter_templ = env.get_template("first_letter.typ")
    headword_templ = env.get_template("lite_headword.typ")
    epd_templ = env.get_template("lite_epd_table.typ")
    root_fam_templ = env.get_template("lite_family_root.typ")
    word_fam_templ = env.get_template("lite_family_word.typ")
    compound_fam_templ = env.get_template("lite_family_compound.typ")
    idiom_fam_templ = env.get_template("lite_family_idiom.typ")
    date = year_month_day_dash()

    # colours
    colour1: str = "#00A4CC"
    colour2: str = "#65DBFF"


def make_front_matter(g: GlobalVars):
    p_green("compiling front matter")
    g.typst_data.append(g.front_matter_templ.render())
    p_yes("ok")


def make_pali_to_english(g: GlobalVars):
    p_green("compiling pali to english")

    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#set page(columns: 1)\n")
    g.typst_data.append("#heading(level: 1)[Pāḷi to English Dictionary]\n")
    g.typst_data.append("#set par(first-line-indent: 0pt, hanging-indent: 1em, spacing: 0.65em)\n")

    for counter, i in enumerate(g.dpd_db):

        first_letter = i.lemma_1[0]
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.headword_templ.render(i=i, date=g.date))
    
    p_yes(len(g.dpd_db))


def make_english_to_pali(g: GlobalVars):
    p_green("compiling epd families")

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[English to Pāḷi Dictionary]\n")
    g.typst_data.append("#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 0.65em)\n")

    problem_characters = [" ", "'", "(", "*", "-", ".", "?", "√"]

    for counter, i in enumerate(g.epd_db):
        first_letter = i.lookup_key[0].casefold() # consider "A" and "a" as the same letter

        if (
            first_letter in problem_characters
            # ignore sutta codes, they start with a double capital letter
            or re.findall("^[A-Z][A-Z]", i.lookup_key)
        ):
            continue
        
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.epd_templ.render(i=i, date=g.date))
    
    p_yes(len(g.epd_db))


def make_root_families(g: GlobalVars):
    p_green("compiling root families")

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
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



def make_word_families(g: GlobalVars):
    p_green("compiling word families")

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Word Families]\n")

    for counter, i in enumerate(g.word_fam_db):
        first_letter = i.word_family[0]
 
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.word_fam_templ.render(i=i, date=g.date))
    
    p_yes(len(g.word_fam_db))


def make_compound_families(g: GlobalVars):
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


def make_idiom_families(g: GlobalVars):
    p_green("compiling idiom families")

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Idiom Families]\n")

    for counter, i in enumerate(g.idioms_fam_db):
        first_letter = i.idiom[0]
 
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.idiom_fam_templ.render(i=i, date=g.date))
    
    p_yes(len(g.idioms_fam_db))


def clean_up_typst_data(g: GlobalVars):
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
    p_green("saving typst data")

    with open(g.pth.typst_lite_data_path, "w") as f:
            f.write("".join(g.typst_data))
    p_yes("ok")


def export_to_pdf(g: GlobalVars):
    p_green("rendering pdf")

    try:
        # python version currently only support typst 0.11, so use subprocess
        # typst.compile(str(g.pth.typst_lite_data_path), output=str(g.pth.typst_lite_pdf_path))
        subprocess.run(
            [
                "typst",
                "compile",
                str(g.pth.typst_lite_data_path),
                str(g.pth.typst_lite_pdf_path)
            ]
        )
        p_yes("ok")
    except Exception as e:
        p_red(f"\n{e}")


def main():
    tic()
    p_title("export to pdf with typst")
    g = GlobalVars()
    make_front_matter(g)
    make_pali_to_english(g)
    make_english_to_pali(g)
    make_root_families(g)
    make_word_families(g)
    make_compound_families(g)
    make_idiom_families(g)
    # clean_up_typst_data(g)
    save_typist_file(g)
    export_to_pdf(g)
    toc()


if __name__ == "__main__":
    main()