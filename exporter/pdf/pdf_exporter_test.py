#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export DPD to PDF using Typst and Jinja templates.

Memory-efficient test version:
- Splits the document into sections, compiles each to a separate PDF
- Merges section PDFs with pypdf to produce the final output
- Frees DB objects between sections with expire_all() + gc.collect()
- Runs typst compilation as a subprocess to isolate its memory usage
"""

import gc
import re
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pypdf import PdfWriter

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

SECTION_NAMES = [
    "front_matter",
    "abbreviations",
    "pali_to_english",
    "english_to_pali",
    "root_families",
    "word_families",
    "compound_families",
    "idiom_families",
    "bibliography",
    "thanks",
]


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

        self.layout_preamble: str = ""
        self.section_dir = self.pth.typst_lite_data_path.parent / "sections"
        self.section_dir.mkdir(exist_ok=True)


def get_layout_preamble(g: GlobalVars) -> str:
    """Get the layout template content that must prefix every section."""
    return g.layout_templ.render()


def section_typ_path(g: GlobalVars, name: str) -> Path:
    return g.section_dir / f"{name}.typ"


def section_pdf_path(g: GlobalVars, name: str) -> Path:
    return g.section_dir / f"{name}.pdf"


def clean_typst_content(content: str) -> str:
    content = re.sub(r"^$\n\n", "\n", content, flags=re.MULTILINE)
    content = re.sub(r"^//.+$\n", "", content, flags=re.MULTILINE)
    content = re.sub(r"^ *$\n *\n", "", content, flags=re.MULTILINE)
    return content


def compile_section(g: GlobalVars, name: str, content: str) -> None:
    """Write a section .typ file and compile it to PDF."""

    full_content = g.layout_preamble + "\n" + content
    full_content = clean_typst_content(full_content)

    typ_path = section_typ_path(g, name)
    pdf_path = section_pdf_path(g, name)

    typ_path.write_text(full_content)

    try:
        result = subprocess.run(
            ["typst", "compile", str(typ_path), str(pdf_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pr.red(f"\ntypst error in {name}: {result.stderr}")
        else:
            pr.yes("ok")
    except FileNotFoundError:
        pr.red("\ntypst CLI not found, falling back to python binding")
        try:
            import typst

            typst.compile(str(typ_path), output=str(pdf_path))
            pr.yes("ok")
        except Exception as e:
            pr.red(f"\n{e}")


def make_front_matter(g: GlobalVars) -> None:
    pr.green_tmr("compiling front matter")

    content = g.front_matter_templ.render()
    compile_section(g, "front_matter", content)


def make_abbreviations(g: GlobalVars) -> None:
    pr.green_tmr("compiling abbreviations")

    abbreviations_tsv = read_tsv_dot_dict(g.pth.abbreviations_tsv_path)
    abbreviations_data = []
    for i in abbreviations_tsv:
        if not re.findall(r"[A-Z][A-z]", i.abbrev):
            abbreviations_data.append(i)

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#heading(level: 1)[Abbreviations]\n")
    lines.append(
        "#set par(first-line-indent: 0pt, hanging-indent: 0em, spacing: 0.65em)\n"
    )
    lines.append(g.abbreviations_templ.render(data=abbreviations_data))

    compile_section(g, "abbreviations", "".join(lines))


def make_pali_to_english(g: GlobalVars) -> None:
    pr.green_tmr("compiling pali to english")

    if debug is True:
        dpd_db = g.db_session.query(DpdHeadword).limit(100).all()
    else:
        dpd_db = g.db_session.query(DpdHeadword).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#set page(columns: 1)\n")
    lines.append("#heading(level: 1)[Pāḷi to English Dictionary]\n")
    lines.append(
        "#set par(first-line-indent: 0pt, hanging-indent: 1em, spacing: 0.65em)\n"
    )

    used_letters: list[str] = []
    for i in dpd_db:
        first_letter = i.lemma_1[0]
        if first_letter not in used_letters:
            lines.append(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)
        lines.append(g.headword_templ.render(i=i, date=g.date))

    count = len(dpd_db)

    g.db_session.expire_all()
    del dpd_db
    gc.collect()

    compile_section(g, "pali_to_english", "".join(lines))
    del lines
    gc.collect()

    pr.yes(count)


def make_english_to_pali(g: GlobalVars) -> None:
    pr.green_tmr("compiling english to pali")

    if debug is True:
        epd_db = g.db_session.query(Lookup).filter(Lookup.epd != "").limit(100).all()
    else:
        epd_db = g.db_session.query(Lookup).filter(Lookup.epd != "").all()
    epd_db = sorted(epd_db, key=lambda x: x.lookup_key.casefold())

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#heading(level: 1)[English to Pāḷi Dictionary]\n")
    lines.append(
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
            lines.append(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)

        lines.append(g.epd_templ.render(i=i, date=g.date))

    count = len(epd_db)

    g.db_session.expire_all()
    del epd_db
    gc.collect()

    compile_section(g, "english_to_pali", "".join(lines))
    del lines
    gc.collect()

    pr.yes(count)


def make_root_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling root families")

    if debug is True:
        root_fam_db = g.db_session.query(FamilyRoot).limit(100).all()
    else:
        root_fam_db = g.db_session.query(FamilyRoot).all()
    root_fam_db = sorted(
        root_fam_db,
        key=lambda x: (pali_sort_key(x.root_key), pali_sort_key(x.root_family)),
    )

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#heading(level: 1)[Root Families]\n")

    used_letters: list[str] = []
    for i in root_fam_db:
        if i.root_key.startswith("√"):
            first_letter = i.root_key[1]

            if first_letter not in used_letters:
                lines.append(g.first_letter_templ.render(first_letter=first_letter))
                used_letters.append(first_letter)

        lines.append(g.root_fam_templ.render(i=i, date=g.date))

    count = len(root_fam_db)

    g.db_session.expire_all()
    del root_fam_db
    gc.collect()

    compile_section(g, "root_families", "".join(lines))
    del lines
    gc.collect()

    pr.yes(count)


def make_word_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling word families")

    word_fam_db: list[FamilyWord]
    if debug is True:
        word_fam_db = g.db_session.query(FamilyWord).limit(100).all()
    else:
        word_fam_db = g.db_session.query(FamilyWord).all()

    word_fam_db = sorted(word_fam_db, key=lambda x: pali_sort_key(x.word_family))  # type: ignore

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#heading(level: 1)[Word Families]\n")

    used_letters: list[str] = []
    for i in word_fam_db:
        first_letter = i.word_family[0]

        if first_letter not in used_letters:
            lines.append(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)

        lines.append(g.word_fam_templ.render(i=i, date=g.date))

    count = len(word_fam_db)

    g.db_session.expire_all()
    del word_fam_db
    gc.collect()

    compile_section(g, "word_families", "".join(lines))
    del lines
    gc.collect()

    pr.yes(count)


def make_compound_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling compound families")

    if debug is True:
        compound_fam_db = g.db_session.query(FamilyCompound).limit(100).all()
    else:
        compound_fam_db = g.db_session.query(FamilyCompound).all()
    compound_fam_db = sorted(
        compound_fam_db, key=lambda x: pali_sort_key(x.compound_family)
    )

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#heading(level: 1)[Compound Families]\n")

    used_letters: list[str] = []
    for i in compound_fam_db:
        first_letter = i.compound_family[0]

        if first_letter not in used_letters:
            lines.append(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)

        lines.append(g.compound_fam_templ.render(i=i, date=g.date))

    count = len(compound_fam_db)

    g.db_session.expire_all()
    del compound_fam_db
    gc.collect()

    compile_section(g, "compound_families", "".join(lines))
    del lines
    gc.collect()

    pr.yes(count)


def make_idiom_families(g: GlobalVars) -> None:
    pr.green_tmr("compiling idiom families")

    if debug is True:
        idioms_fam_db = g.db_session.query(FamilyIdiom).limit(100).all()
    else:
        idioms_fam_db = g.db_session.query(FamilyIdiom).all()
    idioms_fam_db = sorted(idioms_fam_db, key=lambda x: pali_sort_key(x.idiom))

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#heading(level: 1)[Idiom Families]\n")

    used_letters: list[str] = []
    for i in idioms_fam_db:
        first_letter = i.idiom[0]

        if first_letter not in used_letters:
            lines.append(g.first_letter_templ.render(first_letter=first_letter))
            used_letters.append(first_letter)

        lines.append(g.idiom_fam_templ.render(i=i, date=g.date))

    count = len(idioms_fam_db)

    g.db_session.expire_all()
    del idioms_fam_db
    gc.collect()

    compile_section(g, "idiom_families", "".join(lines))
    del lines
    gc.collect()

    pr.yes(count)


def make_bibliography(g: GlobalVars) -> None:
    pr.green_tmr("compiling bibliography")

    bibliography_data = read_tsv_dot_dict(g.pth.bibliography_tsv_path)

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#heading(level: 1)[Bibliography]\n")
    lines.append("An incomplete list of references works")
    lines.append(g.bibliography_templ.render(data=bibliography_data))

    compile_section(g, "bibliography", "".join(lines))


def make_thanks(g: GlobalVars) -> None:
    pr.green_tmr("compiling thanks")

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

    lines: list[str] = []
    lines.append('#set page(numbering: "1 / 1")\n')
    lines.append("#heading(level: 1)[Thanks]\n")
    lines.append(g.thanks_templ.render(data=thanks_data))

    compile_section(g, "thanks", "".join(lines))


def merge_pdfs(g: GlobalVars) -> None:
    pr.green_tmr("merging section pdfs")

    writer = PdfWriter()

    for name in SECTION_NAMES:
        pdf_path = section_pdf_path(g, name)
        if pdf_path.exists():
            writer.append(str(pdf_path))
        else:
            pr.red(f"\nmissing section pdf: {name}")

    writer.write(str(g.pth.typst_lite_pdf_path))
    writer.close()

    pr.yes("ok")


def cleanup_sections(g: GlobalVars) -> None:
    pr.green_tmr("cleaning up section files")

    for name in SECTION_NAMES:
        typ_path = section_typ_path(g, name)
        pdf_path = section_pdf_path(g, name)
        if typ_path.exists():
            typ_path.unlink()
        if pdf_path.exists():
            pdf_path.unlink()

    if g.section_dir.exists():
        try:
            g.section_dir.rmdir()
        except OSError:
            pass

    pr.yes("ok")


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
    g.layout_preamble = get_layout_preamble(g)

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
    merge_pdfs(g)
    cleanup_sections(g)
    zip_up_pdf(g)
    pr.toc()


if __name__ == "__main__":
    main()
