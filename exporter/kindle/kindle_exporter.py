#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create an EPUB and MOBI version of DPD.
The word set is limited to
- CST EBTS
- Sutta Central EBTS
- words in deconstructed compounds."""

import subprocess
import platform
import shutil
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from mako.template import Template
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.configger import config_test
from tools.cst_sc_text_sets import make_cst_text_set, make_sc_text_set
from tools.deconstructed_words import make_words_in_deconstructions
from tools.diacritics_cleaner import diacritics_cleaner
from tools.first_letter import find_first_letter
from tools.meaning_construction import make_grammar_line
from tools.niggahitas import add_niggahitas
from tools.pali_alphabet import pali_alphabet
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_dict


def render_xhtml(
    pth: ProjectPaths,
):
    pr.green("querying dpd db")
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
    pr.yes(len(dpd_db))

    # limit the extent of the dictionary to an ebt text set
    ebt_books = [
        "vin1",
        "vin2",
        "vin3",
        "vin4",
        "dn1",
        "dn2",
        "dn3",
        "mn1",
        "mn2",
        "mn3",
        "sn1",
        "sn2",
        "sn3",
        "sn4",
        "sn5",
        "an1",
        "an2",
        "an3",
        "an4",
        "an5",
        "an6",
        "an7",
        "an8",
        "an9",
        "an10",
        "an11",
        "kn1",
        "kn2",
        "kn3",
        "kn4",
        "kn5",
        "kn8",
        "kn9",
    ]

    # all words in cst and sc texts
    cst_text_set = make_cst_text_set(pth, ebt_books)

    sc_text_set = make_sc_text_set(pth, ebt_books)
    combined_text_set = cst_text_set | sc_text_set

    # words in deconstructor in cst_text_set & sc_text_set
    pr.green("querying lookup for deconstructor")

    # Process in chunks to avoid SQLite's "too many SQL variables" error
    chunk_size = 900  # Leave some buffer under SQLite's 999 limit
    deconstructor_db = []

    combined_text_list = list(combined_text_set)
    for i in range(0, len(combined_text_list), chunk_size):
        chunk = combined_text_list[i : i + chunk_size]
        chunk_result = (
            db_session.query(Lookup)
            .filter(Lookup.deconstructor != "", Lookup.lookup_key.in_(chunk))
            .all()
        )
        deconstructor_db.extend(chunk_result)

    words_in_deconstructor_set = make_words_in_deconstructions(db_session)
    pr.yes(len(words_in_deconstructor_set))

    # all_words_set = cst_text_set + sc_text_set + words in deconstructor compounds
    pr.green("making all words set")
    all_words_set = combined_text_set | words_in_deconstructor_set
    pr.yes(len(all_words_set))

    pr.green("creating inflections dict")

    inflections_dict: dict[int, list[str]] = {}
    inflections_counter = 0
    for i in dpd_db:
        # only add inflections in all words set
        inflections_set: set[str] = (
            set(i.inflections_list_all) & all_words_set
        )  # include api ca eva iti

        # # add one clean inflection without diacritics
        # inflections_set.add(diacritics_cleaner(i.lemma_clean))

        # add niggahitas
        inflections_set = set(add_niggahitas(list(inflections_set), all=False))

        # sort into pali alphabetical order
        inflections_sorted: list[str] = pali_list_sorter(list(inflections_set))

        # Filter out empty or whitespace-only strings to prevent Kindle errors
        inflections_filtered: list[str] = [
            inf for inf in inflections_sorted if inf and inf.strip()
        ]

        # update dict
        inflections_dict[i.id] = inflections_filtered
        inflections_counter += len(inflections_filtered)

    pr.yes(inflections_counter)

    # a dictionary for entries of each letter of the alphabet

    pr.green_title("creating letter dict entries")
    letter_dict: dict = {}
    for letter in pali_alphabet:
        letter_dict[letter] = []

    # add all words
    id_counter = 1
    for counter, i in enumerate(dpd_db):
        inflection_list: list[str] = inflections_dict[i.id]
        first_letter = find_first_letter(i.lemma_1)
        entry = render_ebook_entry(pth, id_counter, i, inflection_list)
        letter_dict[first_letter] += [entry]
        id_counter += 1

        if counter % 5000 == 0:
            pr.counter(counter, len(dpd_db), i.lemma_1)

    # add deconstructor words which are in all_words_set
    pr.green_title("add deconstructor words")
    for counter, i in enumerate(deconstructor_db):
        if bool(set(i.lookup_key) & all_words_set):
            first_letter = find_first_letter(i.lookup_key)
            entry = render_deconstructor_entry(pth, id_counter, i)
            letter_dict[first_letter] += [entry]
            id_counter += 1

        if counter % 5000 == 0:
            pr.counter(counter, len(deconstructor_db), i.lookup_key)

    # save to a single file for each letter of the alphabet
    pr.green("saving entries xhtml")
    total = 0

    for counter, (letter, entries) in enumerate(letter_dict.items()):
        ascii_letter = diacritics_cleaner(letter)
        total += len(entries)
        entries = "".join(entries)

        xhtml = render_ebook_letter_templ(pth, letter, entries)
        output_path = pth.epub_text_dir.joinpath(f"{counter}_{ascii_letter}.xhtml")

        with open(output_path, "w") as f:
            f.write(xhtml)

    pr.yes(total)

    db_session.close()
    return id_counter + 1


# --------------------------------------------------------------------------------------
# functions to create the various templates


def render_ebook_entry(
    pth: ProjectPaths,
    counter: int,
    i: DpdHeadword,
    inflections: list,
) -> str:
    """Render single word entry."""

    summary = f"{i.pos}. "
    if i.plus_case:
        summary += f"({i.plus_case}) "
    summary += i.meaning_combo_html

    construction = i.construction_summary
    if construction:
        summary += f" [{construction}]"

    summary += f" {i.degree_of_completion_html}"

    if "&" in summary:
        summary = summary.replace(" & ", " &amp; ")

    # clean up html line breaks and < >
    for attr_name in [
        "root_base",
        "construction",
        "sanskrit",
        "compound_type",
        "phonetic",
        "example_1",
        "example_2",
        "sutta_1",
        "sutta_2",
        "commentary",
        "notes",
        "cognate",
    ]:
        attr_value = getattr(i, attr_name)
        if isinstance(attr_value, str):
            setattr(i, attr_name, html_friendly(attr_value))

    grammar_table = render_grammar_templ(pth, i)
    if "&" in grammar_table:
        grammar_table = grammar_table.replace(" & ", " &amp; ")

    examples = render_example_templ(pth, i)

    ebook_entry_templ = Template(filename=str(pth.ebook_entry_templ_path))

    return str(
        ebook_entry_templ.render(
            counter=counter,
            lemma_1=i.lemma_1,
            lemma_clean=i.lemma_clean,
            inflections=inflections,
            summary=summary,
            grammar_table=grammar_table,
            examples=examples,
        )
    )


def render_grammar_templ(
    pth: ProjectPaths,
    i: DpdHeadword,
) -> str:
    """html table of grammatical information"""

    if i.meaning_1:
        grammar = make_grammar_line(i)
        ebook_grammar_templ = Template(filename=str(pth.ebook_grammar_templ_path))

        return str(
            ebook_grammar_templ.render(
                i=i,
                grammar=grammar,
                meaning=i.meaning_combo_html,
            )
        )

    else:
        return ""


def render_example_templ(
    pth: ProjectPaths,
    i: DpdHeadword,
) -> str:
    """render sutta examples html"""

    ebook_example_templ = Template(filename=str(pth.ebook_example_templ_path))

    if i.meaning_1 and i.example_1:
        return str(ebook_example_templ.render(i=i))
    else:
        return ""


def render_deconstructor_entry(pth: ProjectPaths, counter: int, i: Lookup) -> str:
    """Render deconstructor word entry."""

    construction = i.lookup_key
    deconstruction = "<br/>".join(i.deconstructor_unpack)

    ebook_deconstructor_templ = Template(
        filename=str(pth.ebook_deconstructor_templ_path)
    )

    return str(
        ebook_deconstructor_templ.render(
            counter=counter, construction=construction, deconstruction=deconstruction
        )
    )


def render_ebook_letter_templ(pth: ProjectPaths, letter: str, entries: str) -> str:
    """Render all entries for a single letter."""
    ebook_letter_templ = Template(filename=str(pth.ebook_letter_templ_path))
    return str(ebook_letter_templ.render(letter=letter, entries=entries))


def save_abbreviations_xhtml_page(pth: ProjectPaths, id_counter):
    """Render xhtml of all DPD abbreviations and save as a page."""

    pr.green("saving abbrev xhtml")
    abbreviations_list = []

    file_path = pth.abbreviations_tsv_path
    abbreviations_list = read_tsv_dict(file_path)

    abbreviation_entries = []
    for i in abbreviations_list:
        for key, value in i.items():
            if value == ">":
                value = "&gt;"
            i[key] = html_friendly(value)
        abbreviation_entries += [render_abbreviation_entry(pth, id_counter, i)]
        id_counter += 1

    entries = "".join(abbreviation_entries)

    xhtml = render_ebook_letter_templ(pth, "Abbreviations", entries)
    with open(pth.epub_abbreviations_path, "w") as f:
        f.write(xhtml)

    pr.yes(len(abbreviations_list))


def render_abbreviation_entry(
    pth: ProjectPaths,
    counter: int,
    i: dict,
) -> str:
    """Render a single abbreviations entry."""

    ebook_abbreviation_entry_templ = Template(
        filename=str(pth.ebook_abbrev_entry_templ_path)
    )

    return str(ebook_abbreviation_entry_templ.render(counter=counter, i=i))


def save_title_page_xhtml(pth: ProjectPaths):
    """Save date and time in title page xhtml."""

    pr.green("saving titlepage xhtml")
    current_datetime = datetime.now()
    date = current_datetime.strftime("%Y-%m-%d")
    time = current_datetime.strftime("%H:%M")

    ebook_title_page_templ = Template(filename=str(pth.ebook_title_page_templ_path))

    xhtml = str(ebook_title_page_templ.render(date=date, time=time))

    with open(pth.epub_titlepage_path, "w") as f:
        f.write(xhtml)

    pr.yes("OK")

    save_content_opf_xhtml(pth, current_datetime)


def save_content_opf_xhtml(
    pth: ProjectPaths,
    current_datetime,
):
    """Save date and time in content.opf."""
    pr.green("saving content.opf")

    date_time_zulu = current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    ebook_content_opf_templ = Template(filename=str(pth.ebook_content_opf_templ_path))

    content = str(ebook_content_opf_templ.render(date_time_zulu=date_time_zulu))

    with open(pth.epub_content_opf_path, "w") as f:
        f.write(content)

    pr.yes("OK")


def zip_epub(pth: ProjectPaths):
    """Zip up the epub dir and name it dpd-kindle.epub."""
    pr.green("zipping up epub")
    epub_dir_path = Path(pth.epub_dir)
    with ZipFile(pth.dpd_epub_path, "w", ZIP_DEFLATED) as zipf:
        for file_path in epub_dir_path.rglob("*"):
            if file_path.is_file():
                zipf.write(file_path, file_path.relative_to(epub_dir_path))
    pr.yes("OK")


def make_mobi(pth: ProjectPaths):
    """Convert epub to mobi using available tool."""
    pr.green_title("converting epub to mobi")

    system = platform.system()
    epub_path = str(pth.dpd_epub_path)
    mobi_path = epub_path.replace(".epub", ".mobi")

    if system == "Darwin":
        # Try Calibre
        # brew install --cask calibre
        if shutil.which("ebook-convert"):
            process = subprocess.Popen(
                ["ebook-convert", epub_path, mobi_path],
                stdout=subprocess.PIPE,
                text=True,
            )
            if process.stdout is not None:
                for line in process.stdout:
                    print(line, end="")
            process.wait()
            pr.yes("Converted with Calibre")
            return
        else:
            pr.red("No compatible MOBI converter found on macOS.")
            return
    else:
        # Default: try kindlegen
        process = subprocess.Popen(
            [str(pth.kindlegen_path), epub_path],
            stdout=subprocess.PIPE,
            text=True,
        )
        if process.stdout is not None:
            for line in process.stdout:
                print(line, end="")
        process.wait()
        pr.yes("Converted with kindlegen")


def html_friendly(text: str):
    try:
        text = text.replace("\n", "<br/>")
        text = text.replace(" > ", " &gt; ")
        text = text.replace(" < ", " &lt; ")
        return text
    except Exception:
        return text


def main():
    pr.tic()
    pr.title("rendering dpd for ebook")
    if config_test("exporter", "make_ebook", "yes"):
        pth = ProjectPaths()
        id_counter: int = render_xhtml(pth)
        save_abbreviations_xhtml_page(pth, id_counter)
        save_title_page_xhtml(pth)
        zip_epub(pth)
        make_mobi(pth)
    else:
        pr.green_title("disabled in config.ini")
    pr.toc()


if __name__ == "__main__":
    main()
