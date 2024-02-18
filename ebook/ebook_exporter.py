#!/usr/bin/env python3
"""Create an EPUB and MOBI version of DPD. 
The word set is limited to  
- CST EBTS
- Sutta Central EBTS
- words in deconstruted compounds."""

import os
import subprocess

from datetime import datetime
from mako.template import Template
from rich import print
from typing import Dict
from zipfile import ZipFile, ZIP_DEFLATED

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, Lookup

from tools.configger import config_test
from tools.cst_sc_text_sets import make_cst_text_set
from tools.cst_sc_text_sets import make_sc_text_set
from tools.diacritics_cleaner import diacritics_cleaner
from tools.first_letter import find_first_letter
from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import summarize_construction
from tools.meaning_construction import degree_of_completion
from tools.niggahitas import add_niggahitas
from tools.pali_alphabet import pali_alphabet
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths
from tools.deconstructed_words import make_words_in_deconstructions
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv_dict


def render_xhtml():

    print(f"[green]{'querying dpd db':<40}", end="")
    pth = ProjectPaths()
    db_sesssion = get_db_session(pth.dpd_db_path)
    dpd_db = db_sesssion.query(DpdHeadwords).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
    print(f"{len(dpd_db):>10,}")


    # limit the extent of the dictionary to an ebt text set
    ebt_books = [
        "vin1", "vin2", "vin3", "vin4",
        "dn1", "dn2", "dn3",
        "mn1", "mn2", "mn3",
        "sn1", "sn2", "sn3", "sn4", "sn5",
        "an1", "an2", "an3", "an4", "an5",
        "an6", "an7", "an8", "an9", "an10", "an11",
        "kn1", "kn2", "kn3", "kn4", "kn5",
        "kn8", "kn9",
        ]

    # all words in cst and sc texts
    print(f"[green]{'making cst text set':<40}", end="")
    cst_text_set = make_cst_text_set(pth, ebt_books)
    print(f"{len(cst_text_set):>10,}")

    print(f"[green]{'making sc text set':<40}", end="")
    sc_text_set = make_sc_text_set(pth, ebt_books)
    print(f"{len(sc_text_set):>10,}")
    combined_text_set = cst_text_set | sc_text_set


    # words in deconstructor in cst_text_set & sc_text_set
    print(f"[green]{'querying lookup table for deconstructor':<40}", end="")
    deconstructor_db = db_sesssion \
        .query(Lookup) \
        .filter(
            Lookup.deconstructor != "", 
            Lookup.lookup_key.in_(combined_text_set)) \
        .all()
        
    words_in_deconstructor_set = make_words_in_deconstructions(db_sesssion)
    print(f"{len(words_in_deconstructor_set):>10,}")


    # all_words_set = cst_text_set + sc_text_set + words in deconstrutor compounds
    all_words_set = combined_text_set | words_in_deconstructor_set
    print(f"[green]{'all_words_set':<40}{len(all_words_set):>10,}")


    # only include inflections which exist in all_words_set
    print(f"[green]{'creating inflections dict':<40}", end="")

    inflections_dict: Dict[int, list[str]] = {}
    inflections_counter = 0
    for i in dpd_db:
        # only add inflections in all words set
        inflections_set: set[str] = set(i.inflections_list) & all_words_set

        # # add one clean inflection without diacritics
        # inflections_set.add(diacritics_cleaner(i.lemma_clean))

        # add niggahitas
        inflections_set = set(add_niggahitas(list(inflections_set), all=False))

        # sort into pali alphabetical order
        inflections_sorted: list[str] = pali_list_sorter(list(inflections_set))

        # update dict
        inflections_dict[i.id] = inflections_sorted
        inflections_counter += len(inflections_sorted)

    print(f"{inflections_counter:>10,}")


    # a dictionary for entries of each letter of the alphabet
    print(f"[green]{'initialising letter dict':<40}")
    letter_dict: dict = {}
    for letter in pali_alphabet:
        letter_dict[letter] = []


    # add all words
    print("[green]creating entries")
    id_counter = 1
    for counter, i in enumerate(dpd_db):
        inflection_list: list = inflections_dict[i.id]
        first_letter = find_first_letter(i.lemma_1)
        entry = render_ebook_entry(pth, id_counter, i, inflection_list)
        letter_dict[first_letter] += [entry]
        id_counter += 1

        if counter % 5000 == 0:
            print(f"{counter:>10,} / {len(dpd_db):<10,} {i.lemma_1}")


    # add deconstructor words which are in all_words_set
    print("[green]add deconstructor words")
    for counter, i in enumerate(deconstructor_db):
        if bool(set(i.lookup_key) & all_words_set):
            first_letter = find_first_letter(i.lookup_key)
            entry = render_deconstructor_entry(pth, id_counter, i)
            letter_dict[first_letter] += [entry]
            id_counter += 1

        if counter % 5000 == 0:
            print(f"{counter:>10,} / {len(deconstructor_db):<10,} {i.lookup_key}")


    # save to a single file for each letter of the alphabet
    print(f"[green]{'saving entries xhtml':<40}", end="")
    total = 0

    for counter, (letter, entries) in enumerate(letter_dict.items()):
        ascii_letter = diacritics_cleaner(letter)
        total += len(entries)
        entries = "".join(entries)
        xhtml = render_ebook_letter_templ(pth, letter, entries)
        output_path = pth.epub_text_dir.joinpath(
            f"{counter}_{ascii_letter}.xhtml")

        with open(output_path, "w") as f:
            f.write(xhtml)

    print(f"{total:>10,}")

    db_sesssion.close()
    return id_counter+1

# --------------------------------------------------------------------------------------
# functions to create the various templates


def render_ebook_entry(
        pth: ProjectPaths, counter: int, i: DpdHeadwords, inflections: list) -> str:
    """Render single word entry."""

    summary = f"{i.pos}. "
    if i.plus_case:
        summary += f"({i.plus_case}) "
    summary += make_meaning_html(i)

    construction = summarize_construction(i)
    if construction:
        summary += f" [{construction}]"

    summary += f" {degree_of_completion(i)}"

    if "&" in summary:
        summary = summary.replace("&", "and")

    grammar_table = render_grammar_templ(pth, i)
    if "&" in grammar_table:
        grammar_table = grammar_table.replace("&", "and")

    examples = render_example_templ(pth, i)

    ebook_entry_templ = Template(filename=str(pth.ebook_entry_templ_path))

    return str(ebook_entry_templ.render(
            counter=counter,
            lemma_1=i.lemma_1,
            lemma_clean=i.lemma_clean,
            inflections=inflections,
            summary=summary,
            grammar_table=grammar_table,
            examples=examples))


def render_grammar_templ(pth: ProjectPaths, i: DpdHeadwords) -> str:
    """html table of grammatical information"""

    if i.meaning_1:
        if i.construction is not None:
            i.construction = i.construction.replace("\n", "<br/>")
        if i.phonetic is not None:
            i.phonetic = i.phonetic.replace("\n", "<br/>")
        if i.commentary is not None:
            i.commentary = i.commentary.replace("\n", "<br/>")

        grammar = i.grammar
        if i.neg:
            grammar += f", {i.neg}"
        if i.verb:
            grammar += f", {i.verb}"
        if i.trans:
            grammar += f", {i.trans}"
        if i.plus_case:
            grammar += f" ({i.plus_case})"

        meaning = f"{make_meaning_html(i)}"

        ebook_grammar_templ = Template(filename=str(pth.ebook_grammar_templ_path))

        return str(
            ebook_grammar_templ.render(
                i=i,
                grammar=grammar,
                meaning=meaning,))

    else:
        return ""


def render_example_templ(pth: ProjectPaths, i: DpdHeadwords) -> str:
    """render sutta examples html"""
    if i.example_1 is not None:
        i.example_1 = i.example_1.replace("\n", "<br/>")
    if i.example_2 is not None:
        i.example_2 = i.example_2.replace("\n", "<br/>")
    if i.sutta_1 is not None:
        i.sutta_1 = i.sutta_1.replace("\n", "<br/>")
    if i.sutta_2 is not None:
        i.sutta_2 = i.sutta_2.replace("\n", "<br/>")

    ebook_example_templ = Template(filename=str(pth.ebook_example_templ_path))

    if i.meaning_1 and i.example_1:
        return str(
            ebook_example_templ.render(
                i=i))
    else:
        return ""


def render_deconstructor_entry(
        pth: ProjectPaths, counter: int, i: Lookup) -> str:
    """Render deconstructor word entry."""

    construction = i.lookup_key
    deconstruction = "<br/>".join(i.deconstructor_unpack)

    ebook_deconstructor_templ = Template(
        filename=str(
            pth.ebook_deconstructor_templ_path))

    return str(ebook_deconstructor_templ.render(
            counter=counter,
            construction=construction,
            deconstruction=deconstruction))


def render_ebook_letter_templ(
        pth: ProjectPaths, letter: str, entries: str) -> str:
    """Render all entries for a single letter."""
    ebook_letter_templ = Template(filename=str(pth.ebook_letter_templ_path))
    return str(ebook_letter_templ.render(
            letter=letter,
            entries=entries))


def save_abbreviations_xhtml_page(pth: ProjectPaths, id_counter):
    """Render xhtml of all DPD abbreviaitons and save as a page."""
    print(f"[green]{'saving abbrev xhtml':<40}", end="")
    abbreviations_list = []

    file_path = pth.abbreviations_tsv_path
    abbreviations_list = read_tsv_dict(file_path)

    abbreviation_entries = []
    for i in abbreviations_list:
        abbreviation_entries += [
            render_abbreviation_entry(pth, id_counter, i)]
        id_counter += 1

    entries = "".join(abbreviation_entries)
    entries = entries.replace(" > ", " &gt; ")
    xhtml = render_ebook_letter_templ(pth, "Abbreviations", entries)

    with open(pth.epub_abbreviations_path, "w") as f:
        f.write(xhtml)

    print(f"{len(abbreviations_list):>10,}")


def render_abbreviation_entry(pth: ProjectPaths, counter: int, i: dict) -> str:
    """Render a single abbreviations entry."""

    ebook_abbreviation_entry_templ = Template(
        filename=str(pth.ebook_abbrev_entry_templ_path))

    return str(ebook_abbreviation_entry_templ.render(
            counter=counter,
            i=i))


def save_title_page_xhtml(pth: ProjectPaths):
    """Save date and time in title page xhtml."""
    print(f"[green]{'saving titlepage xhtml':<40}", end="")
    current_datetime = datetime.now()
    date = current_datetime.strftime("%Y-%m-%d")
    time = current_datetime.strftime("%H:%M")

    ebook_title_page_templ = Template(
        filename=str(pth.ebook_title_page_templ_path))

    xhtml = str(ebook_title_page_templ.render(
            date=date,
            time=time))

    with open(pth.epub_titlepage_path, "w") as f:
        f.write(xhtml)

    print(f"{'OK':>10}")

    save_content_opf_xhtml(pth, current_datetime)


def save_content_opf_xhtml(pth: ProjectPaths, current_datetime):
    """Save date and time in content.opf."""
    print(f"[green]{'saving content.opf':<40}", end="")

    date_time_zulu = current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    ebook_content_opf_templ = Template(
        filename=str(pth.ebook_content_opf_templ_path))

    content = str(ebook_content_opf_templ.render(
            date_time_zulu=date_time_zulu))

    with open(pth.epub_content_opf_path, "w") as f:
        f.write(content)

    print(f"{'OK':>10}")


def zip_epub(pth: ProjectPaths):
    """Zip up the epub dir and name it dpd-kindle.epub."""
    print("[green]zipping up epub")
    with ZipFile(pth.dpd_epub_path, "w", ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(pth.epub_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, pth.epub_dir))


def make_mobi(pth: ProjectPaths):
    """Run kindlegen to convert epub to mobi."""
    print("[green]converting epub to mobi")

    process = subprocess.Popen(
        [str(pth.kindlegen_path), str(pth.dpd_epub_path)],
        stdout=subprocess.PIPE, text=True)

    if process.stdout is not None:
        for line in process.stdout:
            print(line, end='')
    process.wait()


def main():
    tic()
    print("[bright_yellow]rendering dpd for ebook")
    if config_test("exporter", "make_ebook", "yes"):
        id_counter = render_xhtml()
        pth = ProjectPaths()
        save_abbreviations_xhtml_page(pth, id_counter)
        save_title_page_xhtml(pth)
        zip_epub(pth)
        make_mobi(pth)
    else:
        print("generating is disabled in the config")
    toc()


if __name__ == "__main__":
    main()

