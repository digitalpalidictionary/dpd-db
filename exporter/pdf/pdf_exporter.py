#!/usr/bin/env python3

"""Export DPD to PDF using Typst and Jinja templates."""

import re
# import subprocess
import typst

from jinja2 import Environment, FileSystemLoader

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound, FamilyIdiom, FamilyRoot, FamilyWord, Lookup
from tools.configger import config_test
from tools.date_and_time import year_month_day_dash
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import p_green, p_green_title, p_red, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv_dot_dict
from tools.zip_up import zip_up_file

debug = False

class GlobalVars():
    # database
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

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
    abbreviations_templ = env.get_template("abbreviations.typ")
    headword_templ = env.get_template("lite_headword.typ")
    epd_templ = env.get_template("lite_epd.typ")
    root_fam_templ = env.get_template("lite_family_root.typ")
    word_fam_templ = env.get_template("lite_family_word.typ")
    compound_fam_templ = env.get_template("lite_family_compound.typ")
    idiom_fam_templ = env.get_template("lite_family_idiom.typ")
    bibliography_templ = env.get_template("bibliography.typ")
    thanks_templ = env.get_template("thanks.typ")
    date = year_month_day_dash()

    # colours
    colour1: str = "#00A4CC"
    colour2: str = "#65DBFF"


def make_front_matter(g: GlobalVars):
    p_green("compiling front matter")
    g.typst_data.append(g.front_matter_templ.render())
    p_yes("ok")


def make_abbreviations(g: GlobalVars):
    p_green("compiling abbreviations")

    abbreviations_tsv = read_tsv_dot_dict(g.pth.abbreviations_tsv_path)
    abbreviations_data = []
    for i in abbreviations_tsv:
        # leave out book names which have a double capital JA 
        if not re.findall(r"[A-Z][A-z]", i.abbrev):
            abbreviations_data.append(i)

    g.typst_data.append("#heading(level: 1)[Abbreviations]\n")
    g.typst_data.append("#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 0.65em)\n")
    g.typst_data.append(g.abbreviations_templ.render(data=abbreviations_data))
    p_yes(len(abbreviations_data))


def make_pali_to_english(g: GlobalVars):
    p_green("compiling pali to english")

    if debug is True:
        dpd_db = g.db_session.query(DpdHeadword).limit(100).all()
    else:
        dpd_db = g.db_session.query(DpdHeadword).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#set page(columns: 1)\n")
    g.typst_data.append("#heading(level: 1)[Pāḷi to English Dictionary]\n")
    g.typst_data.append("#set par(first-line-indent: 0pt, hanging-indent: 1em, spacing: 0.65em)\n")

    for counter, i in enumerate(dpd_db):

        first_letter = i.lemma_1[0]
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.headword_templ.render(i=i, date=g.date))
    
    p_yes(len(dpd_db))


def make_english_to_pali(g: GlobalVars):
    p_green("compiling english to pali")

    if debug is True:
        epd_db = g.db_session.query(Lookup).filter(Lookup.epd != "").limit(100).all()
    else:
        epd_db = g.db_session.query(Lookup).filter(Lookup.epd != "").all()
    epd_db = sorted(epd_db, key=lambda x: x.lookup_key.casefold())


    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[English to Pāḷi Dictionary]\n")
    g.typst_data.append("#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 0.65em)\n")

    problem_characters = [" ", "'", "(", "*", "-", ".", "?", "√"]

    for counter, i in enumerate(epd_db):
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
    
    p_yes(len(epd_db))


def make_root_families(g: GlobalVars):
    p_green("compiling root families")

    if debug is True:
        root_fam_db = g.db_session.query(FamilyRoot).limit(100).all()
    else:
        root_fam_db = g.db_session.query(FamilyRoot).all()
    root_fam_db = sorted(root_fam_db, key=lambda x: (pali_sort_key(x.root_key), pali_sort_key(x.root_family)))

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Root Families]\n")

    for counter, i in enumerate(root_fam_db):

        if i.root_key.startswith("√"):
            first_letter = i.root_key[1]

            if first_letter not in g.used_letters_single:
                first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
                g.typst_data.append(first_letter_render)
                g.used_letters_single.append(first_letter)

        g.typst_data.append(g.root_fam_templ.render(i=i, date=g.date))
    
    p_yes(len(root_fam_db))


def make_word_families(g: GlobalVars):
    p_green("compiling word families")

    if debug is True:
        word_fam_db = g.db_session.query(FamilyWord).limit(100).all()
    else:
        word_fam_db = g.db_session.query(FamilyWord).all()
    word_fam_db = sorted(word_fam_db, key=lambda x: pali_sort_key(x.word_family))


    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Word Families]\n")

    for counter, i in enumerate(word_fam_db):
        first_letter = i.word_family[0]
 
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.word_fam_templ.render(i=i, date=g.date))
    
    p_yes(len(word_fam_db))


def make_compound_families(g: GlobalVars):
    p_green("compiling compound families")

    if debug is True:
        compound_fam_db = g.db_session.query(FamilyCompound).limit(100).all()
    else:
        compound_fam_db = g.db_session.query(FamilyCompound).all()
    compound_fam_db = sorted(compound_fam_db, key=lambda x: pali_sort_key(x.compound_family))

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Compound Families]\n")

    for counter, i in enumerate(compound_fam_db):
        first_letter = i.compound_family[0]
 
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.compound_fam_templ.render(i=i, date=g.date))
    
    p_yes(len(compound_fam_db))


def make_idiom_families(g: GlobalVars):
    p_green("compiling idiom families")

    if debug is True:
        idioms_fam_db = g.db_session.query(FamilyIdiom).limit(100).all()
    else:
        idioms_fam_db = g.db_session.query(FamilyIdiom).all()
    idioms_fam_db = sorted(idioms_fam_db, key=lambda x: pali_sort_key(x.idiom))

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Idiom Families]\n")

    for counter, i in enumerate(idioms_fam_db):
        first_letter = i.idiom[0]
 
        if first_letter not in g.used_letters_single:
            first_letter_render = g.first_letter_templ.render(first_letter=first_letter)
            g.typst_data.append(first_letter_render)
            g.used_letters_single.append(first_letter)
        
        g.typst_data.append(g.idiom_fam_templ.render(i=i, date=g.date))
    
    p_yes(len(idioms_fam_db))


def make_bibliography(g: GlobalVars):
    p_green("compiling bibliography")

    bibliography_data = read_tsv_dot_dict(g.pth.bibliography_tsv_path)

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Bibliography]\n")
    g.typst_data.append("An incomplete list of references works")
    g.typst_data.append(g.bibliography_templ.render(data=bibliography_data))
    
    p_yes(len(bibliography_data))


def make_thanks(g: GlobalVars):
    p_green("compiling thanks")

    thanks_tsv = read_tsv_dot_dict(g.pth.thanks_tsv_path)
    thanks_data = []
    for i in thanks_tsv:
        # underlines <i> > __ 
        i.what = i.what.replace("<i>", "_").replace("</i>", "_")
        # links
        i.what = i.what \
            .replace('<a href=”', '#link("') \
            .replace('”>', '")[') \
            .replace('</a>', ']')
        thanks_data.append(i)

    g.used_letters_single = []
    g.typst_data.append("#pagebreak()\n")
    g.typst_data.append("#heading(level: 1)[Thanks]\n")
    g.typst_data.append(g.thanks_templ.render(data=thanks_data))

    p_yes(len(thanks_data))


def clean_up_typst_data(g: GlobalVars):
    p_green("cleaning up")

    cleaned_data = []
    for i in g.typst_data:

        # remove double blank lines
        cleaned_string = re.sub(r"^$\n\n", "\n", i, flags=re.MULTILINE)

        # remove comments
        cleaned_string = re.sub(r"^//.+$\n", "", cleaned_string, flags=re.MULTILINE)

        # remove double lines with only spaces
        cleaned_string = re.sub(r"^ *$\n *\n", "", cleaned_string, flags=re.MULTILINE)

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

        typst.compile(str(g.pth.typst_lite_data_path), output=str(g.pth.typst_lite_pdf_path))
        
        # subprocess.run(
        #     [
        #         "typst",
        #         "compile",
        #         str(g.pth.typst_lite_data_path),
        #         str(g.pth.typst_lite_pdf_path)
        #     ]
        # )

        p_yes("ok")
    except Exception as e:
        p_red(f"\n{e}")


def zip_up_pdf(g: GlobalVars):
    p_green("zipping up pdf")

    zip_up_file(
        g.pth.typst_lite_pdf_path, g.pth.typst_lite_zip_path, compression_level=5
    )

    p_yes("ok")


def main():
    tic()
    p_title("export to pdf with typst")

    if not config_test("exporter", "make_pdf", "yes"):
        p_green_title("disabled in config.ini")
        toc()
        return
    
    g = GlobalVars()
    make_front_matter(g)
    make_abbreviations(g)
    make_pali_to_english(g)
    make_english_to_pali(g)
    make_root_families(g)
    make_word_families(g)
    make_compound_families(g)
    make_idiom_families(g)
    make_bibliography(g)
    make_thanks(g)
    clean_up_typst_data(g)
    save_typist_file(g)
    export_to_pdf(g)
    zip_up_pdf(g)
    toc()


if __name__ == "__main__":
    main()