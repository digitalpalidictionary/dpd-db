#!/usr/bin/env python3

"""Create CSV files for Anki study based on id list, which extracted from docx or based on some source."""

import csv
import re
import sys
import os
from rich.console import Console
from docx import Document

from typing import List

from db.models import DpdHeadword
from db.db_helpers import get_db_session

from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from tools.tic_toc import tic, toc
from tools.date_and_time import day



console = Console()

date = day()

header = ['ID', 'Pāli', 'POS', 'Grammar', 'Derived from',
        'Neg', 'Verb', 'Trans', 'Case', 'Meaning IN CONTEXT',
        'Literal Meaning', 'Sanskrit', 'Sk Root',
        'Sk Root Meaning', 'Sk Root Class', 'Pāli Root',
        'Root Group', 'Root Sign', 'Root Meaning', 'Base', 'Construction', 'Derivative',
        'Suffix', 'Phonetic Changes', 'Compound',
        'Compound Construction', 'Source 1',
        'Sutta 1', 'Example 1', 'Source 2', 'Sutta 2', 'Example 2',
        'Antonyms', 'Synonyms', 'Variant reading',  'Commentary',
        'Notes', 'Wiki Link', 'Date']


def main(header):
    tic()
    console.print("[bold bright_yellow]exporting csv for Anki")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()
    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    if dpspth.local_downloads_dir:
        console.print("[bold blue]Enter the name of the .docx file (without extension):")
        file_name = input("").strip()
        input_docx_file = f"{dpspth.local_downloads_dir}/{file_name}.docx"
    else:
        console.print("[bold red]no path to Downloads")
        sys.exit()

    if file_name:
        header = fromid(dpspth, dpd_db, input_docx_file, header)
    else:
        console.print("[bold yellow]Skipping the first process due to empty input.")

    console.print("[bold blue]Please enter the source string to check (e.g., VIN 1.1.1):")
    source_to_check = input("").strip()

    if source_to_check:
        fromsource(dpspth, dpd_db, source_to_check, header)
    else:
        console.print("[yellow]Skipping the second process due to empty input.")

    toc()


def remove_duplicates(ordered_ids):
    seen = set()
    ordered_ids_no_duplicates = [x for x in ordered_ids if not (x in seen or seen.add(x))]
    return ordered_ids_no_duplicates


def extract_ids_from_docx(filename):
    """
    Extracts IDs from tables inside a Word document.
    
    :param filename: Path to the .docx file.
    :return: List of extracted IDs.
    """
    doc = Document(filename)
    all_ids = []

    for table in doc.tables:
        for row in table.rows:
            # Assuming the ID is in the first cell of every row
            cell_content = row.cells[0].text.strip()
            # Check if the cell content is an integer
            try:
                _id = int(cell_content)
                all_ids.append(_id)
            except ValueError:
                # The content is not a number, so we skip it
                continue

    return all_ids


def fromsource(dpspth, dpd_db, source_to_check, header):

    console.print(f"[bold green]making anki_{source_to_check}.csv")

    words_set = set()

    for i in dpd_db:
        if (
            i.source_1 == source_to_check or i.source_2 == source_to_check
        ):
            words_set.update([i.id])

    def _needed(i: DpdHeadword):
        return i.id in words_set

    rows = [header]  # Add the header as the first row
    rows.extend(pali_row(i) for i in dpd_db if _needed(i))

    output_path = os.path.join(dpspth.anki_csvs_dps_dir, f"anki_{source_to_check}.csv")

    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)



def fromid(dpspth, dpd_db, docx_filename, header):

    console.print("[bold green]making anki_id_list.csv")

    ordered_ids = extract_ids_from_docx(docx_filename)
    ordered_ids = remove_duplicates(ordered_ids)

    def _is_needed(i: DpdHeadword):
        return i.id in ordered_ids

    rows = [header]  # Add the header as the first row
    rows.extend(pali_row(i) for i in dpd_db if _is_needed(i))

    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_id_list.csv")

    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)


def pali_row(i: DpdHeadword, output="anki") -> List[str]:
    fields = []

    fields.extend([
        i.id,
        i.lemma_1,
        i.pos,
        i.grammar,
        i.derived_from,
        i.neg,
        i.verb,
        i.trans,
        i.plus_case,
        i.meaning_1,
        i.meaning_lit,
        i.sanskrit,
    ])

    if i.rt is not None:
        if output == "dpd":
            root_key = i.root_key

            if i.rt.sanskrit_root_meaning == "":
                sanskrit_root_meaning = "0"
            else:
                sanskrit_root_meaning = i.rt.sanskrit_root_meaning

        else:
            root_key = re.sub(r" \d*$", "", str(i.root_key))
            sanskrit_root_meaning = i.rt.sanskrit_root_meaning

        fields.extend([
            i.rt.sanskrit_root,
            sanskrit_root_meaning,
            i.rt.sanskrit_root_class,
            root_key,
            i.rt.root_group,
            i.root_sign,
            i.rt.root_meaning,
            i.root_base,
        ])

    else:
        fields.extend([
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ])

    fields.extend([
        i.construction.replace("\n", "<br>") if i.construction else None,
        i.derivative,
        i.suffix,
        i.phonetic.replace("\n", "<br>") if i.phonetic else None,
        i.compound_type,
        i.compound_construction,
        i.source_1.replace("\n", "<br>") if i.source_1 else None,
        i.sutta_1.replace("\n", "<br>") if i.sutta_1 else None,
        i.example_1.replace("\n", "<br>") if i.example_1 else None,
        i.source_2.replace("\n", "<br>") if i.source_2 else None,
        i.sutta_2.replace("\n", "<br>") if i.sutta_2 else None,
        i.example_2.replace("\n", "<br>") if i.example_2 else None,
        i.antonym,
        i.synonym,
        i.variant,
        i.commentary.replace("\n", "<br>") if i.commentary else None,
        i.notes.replace("\n", "<br>") if i.notes else None,
        i.link.replace("\n", "<br>") if i.link else None,
        date
    ])

    return none_to_empty(fields)


def none_to_empty(values: List):
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))


if __name__ == "__main__":
    main(header)
