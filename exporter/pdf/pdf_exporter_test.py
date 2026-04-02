#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export DPD to PDF using Typst and Jinja templates.

Memory-efficient test version:
- Streams rendered typst data directly to disk instead of accumulating in a list
- Frees DB objects between sections with expire_all() + gc.collect()
- Runs typst compilation as a subprocess to isolate its memory usage
"""

import gc
import re
import subprocess
from io import TextIOWrapper

from jinja2 import Environment, FileSystemLoader

from db.db_helpers import get_db_session
from db.models import (
    DpdHeadword,
    FamilyCompound,
    FamilyIdiom,
    FamilyRoot,
    FamilyWord,
    Lookup,
)
from tools.configger import config_test
from tools.date_and_time import year_month_day_dash
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dot_dict
from tools.zip_up import zip_up_file

debug = False


class GlobalVars:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)

        self.env = Environment(
            loader=FileSystemLoader("exporter/pdf/templates"),
            autoescape=True,
            block_start_string="////",
            block_end_string="\\\\\\\\",
        )

        self.layout_templ = self.env.get_template("layout.typ")
        self.front_matter_templ = self.env.get_template("front_matter.typ")
        self.first_letter_templ = self.env.get_template("first_letter.typ")
        self.abbreviations_templ = self.env.get_template("abbreviations.typ")
        self.headword_templ = self.env.get_template("lite_headword.typ")
        self.epd_templ = self.env.get_template("lite_epd.typ")
        self.root_fam_templ = self.env.get_template("lite_family_root.typ")
        self.word_fam_templ = self.env.get_template("lite_family_word.typ")
        self.compound_fam_templ = self.env.get_template("lite_family_compound.typ")
        self.idiom_fam_templ = self.env.get_template("lite_family_idiom.typ")
        self.bibliography_templ = self.env.get_template("bibliography.typ")
        self.thanks_templ = self.env.get_template("thanks.typ")
        self.date = year_month_day_dash()

        self.typst_file: TextIOWrapper | None = None


def make_layout(g: GlobalVars) -> None:
    pr.green_tmr("compiling layout")
    assert g.typst_file is not None
    g.typst_file.write(g.layout_templ.render())
    pr.yes("ok")


def make_front_matter(g: GlobalVars) -> None:
    pr.green_tmr("compiling front matter")
    assert g.typst_file is not None
    g.typst_file.write(g.front_matter_templ.render())
    pr.yes("ok")


def make_abbreviations(g: GlobalVars) -> None:
    pr.green_tmr("compiling abbreviations")
    assert g.typst_file is not None

    abbreviations_tsv = read_tsv_dot_dict(g.pth.abbreviations_tsv_path)
    abbreviations_data = []
    for i in abbreviations_tsv:
        if not re.findall(r"[A-Z][A-z]", i.abbrev):
            abbreviations_data.append(i)

    g.typst_file.write("#heading(level: 1)[Abbreviations]\n")
    g.typst_file.write(
        "#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 0.65em)\n"
    )
    g.typst_file.write(g.abbreviations_templ.render(data=abbreviations_data))
    pr.yes(len(abbreviations_data))


def make_pali_to_english(g: GlobalVars) -> None:
    pr.green_tmr("compiling pali to english")
    assert g.typst_file is not None

    if debug is True:
        dpd_db = g.db_session.query(DpdHeadword).limit(100).all()
    else:
        dpd_db = g.db_session.query(DpdHeadword).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    g.typst_file.write("#pagebreak()\n")
    g.typst_file.write("#set page(columns: 1)\n")
    g.typst_file.write("#heading(level: 1)[Pāḷi to English Dictionary]\n")
    g.typst_file.write(
        "#set par(first-line-indent: 0pt, hanging-indent: 1em, spacing: 0.65em)\n"
    )

    used_letters: list[str] = []
    for i in dpd_db:
        first_letter = i.lemma_1[0]
        if first_letter not in used_letters:
            g.typst_file.write(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)
        g.typst_file.write(g.headword_templ.render(i=i, date=g.date))

    pr.yes(len(dpd_db))

    g.db_session.expire_all()
    del dpd_db
    gc.collect()


def make_english_to_pali(g: GlobalVars) -> None:
    pr.green_tmr("compiling english to pali")
    assert g.typst_file is not None

    if debug is True:
        epd_db = g.db_session.query(Lookup).filter(Lookup.epd != "").limit(100).all()
    else:
        epd_db = g.db_session.query(Lookup).filter(Lookup.epd != "").all()
    epd_db = sorted(epd_db, key=lambda x: x.lookup_key.casefold())

    g.typst_file.write("#pagebreak()\n")
    g.typst_file.write("#heading(level: 1)[English to Pāḷi Dictionary]\n")
    g.typst_file.write(
        "#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 0.65em)\n"
    )

    problem_characters = [" ", "'", "(", "*", "-", ".", "?", "√"]
    used_letters: list[str] = []

    for i in epd_db:
        try:
            first_letter = i.lookup_key[0].casefold()
        except IndexError:
            continue

        if first_letter in problem_characters or re.findall(
            "^[A-Z][A-Z]", i.lookup_key
        ):
            continue

        if first_letter not in used_letters:
            g.typst_file.write(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)

        g.typst_file.write(g.epd_templ.render(i=i, date=g.date))

    pr.yes(len(epd_db))

    g.db_session.expire_all()
    del epd_db
    gc.collect()


def make_root_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling root families")
    assert g.typst_file is not None

    if debug is True:
        root_fam_db = g.db_session.query(FamilyRoot).limit(100).all()
    else:
        root_fam_db = g.db_session.query(FamilyRoot).all()
    root_fam_db = sorted(
        root_fam_db,
        key=lambda x: (pali_sort_key(x.root_key), pali_sort_key(x.root_family)),
    )

    g.typst_file.write("#pagebreak()\n")
    g.typst_file.write("#heading(level: 1)[Root Families]\n")

    used_letters: list[str] = []
    for i in root_fam_db:
        if i.root_key.startswith("√"):
            first_letter = i.root_key[1]

            if first_letter not in used_letters:
                g.typst_file.write(
                    g.first_letter_templ.render(first_letter=first_letter)
                )
                used_letters.append(first_letter)

        g.typst_file.write(g.root_fam_templ.render(i=i, date=g.date))

    pr.yes(len(root_fam_db))

    g.db_session.expire_all()
    del root_fam_db
    gc.collect()


def make_word_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling word families")
    assert g.typst_file is not None

    word_fam_db: list[FamilyWord]
    if debug is True:
        word_fam_db = g.db_session.query(FamilyWord).limit(100).all()
    else:
        word_fam_db = g.db_session.query(FamilyWord).all()

    word_fam_db = sorted(word_fam_db, key=lambda x: pali_sort_key(x.word_family))  # type: ignore

    g.typst_file.write("#pagebreak()\n")
    g.typst_file.write("#heading(level: 1)[Word Families]\n")

    used_letters: list[str] = []
    for i in word_fam_db:
        first_letter = i.word_family[0]

        if first_letter not in used_letters:
            g.typst_file.write(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)

        g.typst_file.write(g.word_fam_templ.render(i=i, date=g.date))

    pr.yes(len(word_fam_db))

    g.db_session.expire_all()
    del word_fam_db
    gc.collect()


def make_compound_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling compound families")
    assert g.typst_file is not None

    if debug is True:
        compound_fam_db = g.db_session.query(FamilyCompound).limit(100).all()
    else:
        compound_fam_db = g.db_session.query(FamilyCompound).all()
    compound_fam_db = sorted(
        compound_fam_db, key=lambda x: pali_sort_key(x.compound_family)
    )

    g.typst_file.write("#pagebreak()\n")
    g.typst_file.write("#heading(level: 1)[Compound Families]\n")

    used_letters: list[str] = []
    for i in compound_fam_db:
        first_letter = i.compound_family[0]

        if first_letter not in used_letters:
            g.typst_file.write(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)

        g.typst_file.write(g.compound_fam_templ.render(i=i, date=g.date))

    pr.yes(len(compound_fam_db))

    g.db_session.expire_all()
    del compound_fam_db
    gc.collect()


def make_idiom_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling idiom families")
    assert g.typst_file is not None

    if debug is True:
        idioms_fam_db = g.db_session.query(FamilyIdiom).limit(100).all()
    else:
        idioms_fam_db = g.db_session.query(FamilyIdiom).all()
    idioms_fam_db = sorted(idioms_fam_db, key=lambda x: pali_sort_key(x.idiom))

    g.typst_file.write("#pagebreak()\n")
    g.typst_file.write("#heading(level: 1)[Idiom Families]\n")

    used_letters: list[str] = []
    for i in idioms_fam_db:
        first_letter = i.idiom[0]

        if first_letter not in used_letters:
            g.typst_file.write(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)

        g.typst_file.write(g.idiom_fam_templ.render(i=i, date=g.date))

    pr.yes(len(idioms_fam_db))

    g.db_session.expire_all()
    del idioms_fam_db
    gc.collect()


def make_bibliography(g: GlobalVars) -> None:
    pr.green_tmr("compiling bibliography")
    assert g.typst_file is not None

    bibliography_data = read_tsv_dot_dict(g.pth.bibliography_tsv_path)

    g.typst_file.write("#pagebreak()\n")
    g.typst_file.write("#heading(level: 1)[Bibliography]\n")
    g.typst_file.write("An incomplete list of references works")
    g.typst_file.write(g.bibliography_templ.render(data=bibliography_data))

    pr.yes(len(bibliography_data))


def make_thanks(g: GlobalVars) -> None:
    pr.green_tmr("compiling thanks")
    assert g.typst_file is not None

    thanks_tsv = read_tsv_dot_dict(g.pth.thanks_tsv_path)
    thanks_data = []
    for i in thanks_tsv:
        i.what = i.what.replace("<i>", "_").replace("</i>", "_")
        i.what = (
            i.what.replace("<a href=\u201d", '#link("')
            .replace("\u201d>", '")[')
            .replace("</a>", "]")
        )
        thanks_data.append(i)

    g.typst_file.write("#pagebreak()\n")
    g.typst_file.write("#heading(level: 1)[Thanks]\n")
    g.typst_file.write(g.thanks_templ.render(data=thanks_data))

    pr.yes(len(thanks_data))


def clean_up_typst_file(g: GlobalVars) -> None:
    pr.green_tmr("cleaning up")

    with open(g.pth.typst_lite_data_path, "r") as f:
        content = f.read()

    content = re.sub(r"^$\n\n", "\n", content, flags=re.MULTILINE)
    content = re.sub(r"^//.+$\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"^ *$\n *\n", "", content, flags=re.MULTILINE)

    with open(g.pth.typst_lite_data_path, "w") as f:
        f.write(content)

    pr.yes("ok")


def export_to_pdf(g: GlobalVars) -> None:
    pr.green_tmr("rendering pdf")

    try:
        result = subprocess.run(
            [
                "typst",
                "compile",
                str(g.pth.typst_lite_data_path),
                str(g.pth.typst_lite_pdf_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pr.red(f"\n{result.stderr}")
        else:
            pr.yes("ok")
    except FileNotFoundError:
        pr.red("\ntypst CLI not found, falling back to python binding")
        try:
            import typst

            typst.compile(
                str(g.pth.typst_lite_data_path),
                output=str(g.pth.typst_lite_pdf_path),
            )
            pr.yes("ok")
        except Exception as e:
            pr.red(f"\n{e}")


def zip_up_pdf(g: GlobalVars) -> None:
    pr.green_tmr("zipping up pdf")

    zip_up_file(
        g.pth.typst_lite_pdf_path, g.pth.typst_lite_zip_path, compression_level=5
    )

    pr.yes("ok")


def main() -> None:
    pr.tic()
    pr.yellow_title("export to pdf with typst (test)")

    if not config_test("exporter", "make_pdf", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g = GlobalVars()

    with open(g.pth.typst_lite_data_path, "w") as f:
        g.typst_file = f
        make_layout(g)
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

    g.typst_file = None

    clean_up_typst_file(g)
    export_to_pdf(g)
    zip_up_pdf(g)
    pr.toc()


if __name__ == "__main__":
    main()
