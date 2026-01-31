#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Extract bold defined words from the CST corpus and add to database.
Refactored version that strictly follows original structure to avoid regression."""

import json
import re
from pathlib import Path
from typing import cast
from bs4 import BeautifulSoup, Tag
from rich import print

from db.bold_definitions.functions import useless_endings
from db.bold_definitions.functions import file_list
from db.bold_definitions.functions import dissolve_empty_siblings
from db.bold_definitions.functions import get_bold_strings
from db.bold_definitions.functions import get_nikaya_headings_div
from db.bold_definitions.functions import get_headings_no_div
from db.bold_definitions.functions import BoldDefinitionEntry

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import write_tsv_dot_dict


def extract_bold_definitions(pth):
    """extract commentary definitions from xml."""

    pr.green_title("extracting bold definitions")

    bold_definitions_list = []
    bold_total = 0

    for file_name, ref_code in file_list.items():
        print(f"{file_name}\t{ref_code}", end="\t")

        bold_count1 = 0
        bold_count2 = 0
        no_meaning_count = 0
        nikaya, book, title, subhead = ["", "", "", ""]

        # open xml file
        xml_path = pth.cst_xml_dir.joinpath(file_name)
        if not xml_path.exists():
            print(f"[red]File not found: {xml_path}")
            continue

        with open(xml_path, "r", encoding="UTF-16") as file:
            xml = file.read()

        soup = BeautifulSoup(xml, "xml")

        # Pre-processing
        for pb in soup.find_all("pb"):
            cast(Tag, pb).decompose()
        for note in soup.find_all("note"):
            cast(Tag, note).decompose()
        for hi in soup.find_all("hi", rend=["paranum", "dot"]):
            cast(Tag, hi).unwrap()

        # SPLIT BOLDS: Split bold tags containing internal dots (e.g. <hi>phrase one. phrase two</hi>)
        # We find all hi tags FIRST to avoid re-processing newly inserted ones
        bolds_to_check = soup.find_all("hi", rend="bold")
        for bold in bolds_to_check:
            bold_tag = cast(Tag, bold)
            # Ensure it's still in the tree (not already decomposed by a previous split)
            if not bold_tag.parent:
                continue
                
            text = bold_tag.get_text()
            if "." in text[:-1]:
                parts = text.split(". ")
                ends_with_dot = text.strip().endswith(".")
                valid_parts = [p.strip() for p in parts if p.strip()]
                
                if len(valid_parts) > 1:
                    for i, part in enumerate(valid_parts):
                        new_hi = soup.new_tag("hi", rend="bold")
                        if i < len(valid_parts) - 1 or ends_with_dot:
                            new_hi.string = part + "."
                        else:
                            new_hi.string = part
                        
                        bold_tag.insert_before(new_hi)
                        if i < len(valid_parts) - 1:
                            bold_tag.insert_before(" ")
                    bold_tag.decompose()

        bold_count1 = len(soup.find_all("hi", rend="bold"))

        # BRANCH 1: Has DIV (Nikaya Suttas etc)
        if soup.div is not None:
            nikaya_tags = soup.find_all("p", rend="nikaya")
            if nikaya_tags:
                nikaya = str(cast(Tag, nikaya_tags[0]).string)

            book_tags = soup.find_all("head", rend="book")
            if book_tags:
                book = str(cast(Tag, book_tags[0]).string)

            divs = soup.find_all(
                "div",
                type=["sutta", "vagga", "chapter", "samyutta", "kanda", "khandaka"],
            )

            ant = [
                "s0401t.tik.xml",
                "s0402t.tik.xml",
                "s0403t.tik.xml",
                "s0404t.tik.xml",
            ]
            if file_name in ant:
                divs = soup.find_all("div", type=["book"])

            for div in divs:
                paras = cast(Tag, div).find_all("p")
                for para in paras:
                    title, subhead = get_nikaya_headings_div(
                        file_name, cast(Tag, div), cast(Tag, para), subhead
                    )

                    bolds = cast(Tag, para).find_all("hi", rend=["bold"])
                    bolds = dissolve_empty_siblings(para, bolds)

                    for bold in bolds:
                        # BUG FIX: Removed 'if bold.next_sibling is not None'
                        bold_clean, bold_e, bold_comp, bold_n = get_bold_strings(bold)

                        # only write substantial examples
                        bold_comp_clean = re.sub(r"<b>|</b>", "", bold_comp)
                        
                        # Relaxed check: if it's identical to the cleaned string AND 
                        # there's only one bold word, it's likely a heading or duplicate.
                        if f"{bold_clean}{bold_e}" == bold_comp_clean.strip():
                            if bold_comp.count("<b>") <= 1:
                                no_meaning_count += 1
                                continue
                        
                        # Only skip useless endings if it's the ONLY bold word in the snippet.
                        if bold_n in useless_endings and bold_comp.count("<b>") <= 1:
                            no_meaning_count += 1
                            continue
                        
                        entry = BoldDefinitionEntry(
                            file_name=file_name,
                            ref_code=ref_code,
                            nikaya=nikaya,
                            book=book,
                            title=title,
                            subhead=subhead,
                            bold=bold_clean,
                            bold_end=bold_e,
                            commentary=bold_comp,
                        )
                        bold_definitions_list.append(entry.to_dict())
                        bold_count2 += 1

        # BRANCH 2: No DIV (Vinaya, Khuddaka, Vism)
        else:
            paras = soup.find_all("p")
            for para in paras:
                nikaya, book, title, subhead = get_headings_no_div(
                    cast(Tag, para), file_name, nikaya, book, title, subhead
                )

                bolds = cast(Tag, para).find_all("hi", rend="bold")
                bolds = dissolve_empty_siblings(para, bolds)

                for bold in bolds:
                    # BUG FIX: Removed 'if bold.next_sibling is not None'
                    bold_clean, bold_e, bold_comp, bold_n = get_bold_strings(bold)

                    bold_comp_clean = re.sub(r"<b>|</b>", "", bold_comp)
                    
                    # Relaxed check for multi-bold sentences
                    if f"{bold_clean}{bold_e}" == bold_comp_clean.strip():
                        if bold_comp.count("<b>") <= 1:
                            no_meaning_count += 1
                            continue
                    
                    if bold_n in useless_endings and bold_comp.count("<b>") <= 1:
                        no_meaning_count += 1
                        continue
                    
                    entry = BoldDefinitionEntry(
                        file_name=file_name,
                        ref_code=ref_code,
                        nikaya=nikaya,
                        book=book,
                        title=title,
                        subhead=subhead,
                        bold=bold_clean,
                        bold_end=bold_e,
                        commentary=bold_comp,
                    )
                    bold_definitions_list.append(entry.to_dict())
                    bold_count2 += 1

        print(f"{bold_count1}\t{bold_count2}\t{no_meaning_count}")
        bold_total += bold_count2

    pr.green("bold_total")
    pr.yes(len(bold_definitions_list))
    return bold_definitions_list


def export_json(pth, bold_definitions_list):
    """convert to tsv and json."""
    pr.green("saving json")
    output_dir = Path("db/bold_definitions")
    output_dir.mkdir(parents=True, exist_ok=True)

    tsv_path = output_dir.joinpath("bold_definitions.tsv")
    write_tsv_dot_dict(tsv_path, bold_definitions_list)

    json_path = output_dir.joinpath("bold_definitions.json")
    with open(json_path, "w") as file:
        json.dump(bold_definitions_list, file, indent=2, ensure_ascii=False)
    pr.yes("ok")


def main():
    pr.tic()
    pr.title("building database of bolded definitions")
    pth = ProjectPaths()
    bold_definitions = extract_bold_definitions(pth)
    export_json(pth, bold_definitions)
    pr.toc()


if __name__ == "__main__":
    main()
