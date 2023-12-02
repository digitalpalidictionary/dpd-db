#!/usr/bin/env python3

"""Create TSV files for Anki study."""

import csv
import re
import pandas as pd
from rich import print

from typing import List

from sqlalchemy.orm.session import Session

from db.models import PaliWord, PaliRoot
from db.get_db_session import get_db_session

from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.tsv_read_write import write_tsv_list
from tools.date_and_time import day

date = day()


def main():
    tic()
    print("[bright_yellow]exporting anki csv")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()
    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.pali_1))
    # roots_db = db_session.query(PaliRoot).all()

    vocab(pth, dpd_db)
    commentary(pth, dpd_db)
    pass1(pth, dpd_db)
    # full_db(dpd_db)
    # roots(db_session, roots_db)
    toc()


def vocab(pth: ProjectPaths, dpd_db):

    def _is_needed(i: PaliWord):
        return (i.meaning_1 and i.example_1)

    rows = [pali_row(i) for i in dpd_db if _is_needed(i)]

    with open(pth.vocab_csv_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)


def pali_row(i: PaliWord, output="anki") -> List[str]:
    fields = []

    fields.extend([
        i.id,
        i.pali_1,
        i.pali_2,
    ])

    if i.sutta_1 and i.sutta_2:
        sign = "√√"
    elif i.sutta_1 and not i.sutta_2:
        sign = "√"
    else:
        sign = ""

    fields.append(sign)

    fields.extend([
        i.pos,
        i.grammar,
        i.derived_from,
        i.neg,
        i.verb,
        i.trans,
        i.plus_case,
        i.meaning_1,
        i.meaning_lit,
        i.non_ia,
        i.sanskrit,
    ])

    if i.rt is not None:
        if output == "dpd":
            root_key = i.root_key
            if not i.rt.root_in_comps:
                root_in_comps = "0"
            else:
                root_in_comps = i.rt.root_in_comps

            if not i.rt.sanskrit_root_meaning:
                sanskrit_root_meaning = "0"
            else:
                sanskrit_root_meaning = i.rt.sanskrit_root_meaning

        else:
            root_key = re.sub(r" \d*$", "", str(i.root_key))
            root_in_comps = i.rt.root_in_comps
            sanskrit_root_meaning = i.rt.sanskrit_root_meaning

        fields.extend([
            i.rt.sanskrit_root,
            sanskrit_root_meaning,
            i.rt.sanskrit_root_class,
            root_key,
            root_in_comps,
            i.rt.root_has_verb,
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
            "",
            "",
        ])

    fields.extend([
        i.family_root,
        i.family_word,
        i.family_compound,
        i.construction.replace("\n", "<br>"),
        i.derivative,
        i.suffix,
        i.phonetic.replace("\n", "<br>"),
        i.compound_type,
        i.compound_construction,
        i.non_root_in_comps,
        i.source_1.replace("\n", "<br>"),
        i.sutta_1.replace("\n", "<br>"),
        i.example_1.replace("\n", "<br>"),
        i.source_2.replace("\n", "<br>"),
        i.sutta_2.replace("\n", "<br>"),
        i.example_2.replace("\n", "<br>"),
        i.antonym,
        i.synonym,
        i.variant,
        i.commentary.replace("\n", "<br>"),
        i.notes.replace("\n", "<br>"),
        i.cognate,
        i.family_set,
        i.link.replace("\n", "<br>"),
        i.stem,
        i.pattern,
        i.meaning_2,
        i.origin,
        date
    ])

    return none_to_empty(fields)


def commentary(pth: ProjectPaths, dpd_db):
    print("[green]making commentary csv")
    rows = []

    for i in dpd_db:
        if (
            i.meaning_1 and
            not i.example_1
        ):
            rows.append(pali_row(i))

    with open(pth.commentary_csv_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)


def pass1(pth: ProjectPaths, dpd_db):
    print("[green]making pass1 csv")

    rows = []
    for i in dpd_db:
        if (
            not i.meaning_1 and
            "pass1" in i.origin

        ):
            rows.append(pali_row(i))

    output_file = pth.pass1_csv_path
    header = []
    write_tsv_list(str(output_file), header, rows)


def full_db(pth: ProjectPaths, dpd_db):
    print("[green]making dpd-full csv")
    rows = []
    header = ['ID', 'Pāli1', 'Pāli2', 'Fin', 'POS', 'Grammar', 'Derived from',
                    'Neg', 'Verb', 'Trans', 'Case', 'Meaning IN CONTEXT',
                    'Literal Meaning', 'Non IA', 'Sanskrit', 'Sk Root',
                    'Sk Root Mn', 'Cl', 'Pāli Root', 'Root In Comps', 'V',
                    'Grp', 'Sgn', 'Root Meaning', 'Base', 'Family',
                    'Word Family', 'Family2', 'Construction', 'Derivative',
                    'Suffix', 'Phonetic Changes', 'Compound',
                    'Compound Construction', 'Non-Root In Comps', 'Source1',
                    'Sutta1', 'Example1', 'Source 2', 'Sutta2', 'Example 2',
                    'Antonyms', 'Synonyms – different word',
                    'Variant – same constr or diff reading',  'Commentary',
                    'Notes', 'Cognate', 'Category', 'Link', 'Stem', 'Pattern',
                    'Buddhadatta', 'Origin', 'Test']

    rows.append(header)

    for i in dpd_db:
        rows.append(pali_row(i, output="dpd"))

    with open(pth.dpd_full_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    dpd_df = pd.read_csv(pth.dpd_full_path, sep="\t", dtype=str)
    dpd_df.sort_values(
        by=["Pāli1"], inplace=True, ignore_index=True,
        key=lambda x: x.map(pali_sort_key))
    dpd_df.to_csv(
        pth.dpd_full_path, sep="\t", index=False,
        quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


def roots(pth: ProjectPaths, db_session: Session, roots_db):

    print("[green]making roots list")
    roots_list = []
    for i in roots_db:
        roots_list += [i.root]

    print("[green]making roots count dictionary")
    root_count_dict = {}
    for root in roots_list:
        count = db_session.query(PaliWord).filter(
            PaliWord.root_key == root).count()
        root_count_dict[root] = count

    print("[green]making roots.csv")
    rows = []
    roots_header = [
        "Fin", "Count", "Root", "In Comps", "V", "Group", "Sign",
        "Base", "Meaning", "Sk Root", "Sk Root Mn", "Cl", "Example",
        "Dhātupātha", "DpRoot", "DpPāli", "DpEnglish",
        "Kaccāyana Dhātu Mañjūsā", "DmRoot", "DmPāli", "DmEnglish",
        "Saddanītippakaraṇaṃ Dhātumālā", "SnPāli", "SnEnglish",
        "Pāṇinīya Dhātupāṭha", "PdSanskrit", "PdEnglish", "Note",
        "Padaūpasiddhi", "PrPāli", "PrEnglish", "blanks", "same/diff",
        "matrix test"]

    rows.append(roots_header)

    for i in roots_db:
        rows.append(root_row(i, root_count_dict))

    with open(pth.roots_csv_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(rows)

    dpd_df = pd.read_csv(pth.roots_csv_path, sep="\t", dtype=str)
    dpd_df.sort_values(
        by=["Root"], inplace=True, ignore_index=True,
        key=lambda x: x.map(pali_sort_key))
    dpd_df.to_csv(
        pth.roots_csv_path, sep="\t", index=False,
        quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


def root_row(i: PaliRoot, root_count_dict: dict) -> List[str]:
    root_fields = []

    root_fields.extend([
        "",
        root_count_dict[i.root],
        i.root,
        i.root_in_comps,
        i.root_has_verb,
        i.root_group,
        i.root_sign,
        "",     # base
        i.root_meaning,
        i.sanskrit_root,
        i.sanskrit_root_meaning,
        i.sanskrit_root_class,
        i.root_example,
        i.dhatupatha_num,
        i.dhatupatha_root,
        i.dhatupatha_pali,
        i.dhatupatha_english,
        i.dhatumanjusa_num,
        i.dhatumanjusa_root,
        i.dhatumanjusa_pali,
        i.dhatumanjusa_english,
        i.dhatumala_root,
        i.dhatumala_pali,
        i.dhatumala_english,
        i.panini_root,
        i.panini_sanskrit,
        i.panini_english,
        i.note,
        "",     # rupasiddhi
        "",
        "",
        "",     # blanks
        "",     # same/diff
        i.matrix_test
    ])

    return none_to_empty(root_fields)


def none_to_empty(values: List):
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))


if __name__ == "__main__":
    main()
