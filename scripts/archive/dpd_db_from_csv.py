#!/usr/bin/env python3
"""Coverts the PALI and ROOTS tables from the original dpd.ods into the DB."""

import sys
import csv

from rich import print
from typing import Dict, List
from sqlalchemy.orm import Session
from pathlib import Path

from db.models import DpdHeadword, DpdRoot
from db.db_helpers import create_db_if_not_exists
from db.db_helpers import get_db_session
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths


def _csv_row_to_root(x: Dict[str, str]) -> DpdRoot:
    # Ignored columns:
    # 'Count'
    # 'Fin'
    # 'Base'
    # 'Padaūpasiddhi'
    # 'PrPāli'
    # 'PrEnglish'
    # 'blanks'
    # 'same/diff'

    return DpdRoot(
        root=x['Root'],
        root_in_comps=x['In Comps'],
        root_has_verb=x['V'],
        root_group=int(x['Group']),
        root_sign=x['Sign'],
        root_meaning=x['Meaning'],
        sanskrit_root=x['Sk Root'],
        sanskrit_root_meaning=x['Sk Root Mn'],
        sanskrit_root_class=x['Cl'],
        root_example=x['Example'],
        dhatupatha_num=x['Dhātupātha'],
        dhatupatha_root=x['DpRoot'],
        dhatupatha_pali=x['DpPāli'],
        dhatupatha_english=x['DpEnglish'],
        dhatumanjusa_num=(x['Kaccāyana Dhātu Mañjūsā']),
        dhatumanjusa_root=x['DmRoot'],
        dhatumanjusa_pali=x['DmPāli'],
        dhatumanjusa_english=x['DmEnglish'],
        dhatumala_root=x['Saddanītippakaraṇaṃ Dhātumālā'],
        dhatumala_pali=x['SnPāli'],
        dhatumala_english=x['SnEnglish'],
        panini_root=x['Pāṇinīya Dhātupāṭha'],
        panini_sanskrit=x['PdSanskrit'],
        panini_english=x['PdEnglish'],
        note=x['Note'],
        matrix_test=x['matrix test'],
    )


def _csv_row_to_pali_word(x: Dict[str, str]) -> DpdHeadword:
    # Ignored columns:
    # 'Fin'
    # 'Sk Root'
    # 'Sk Root Mn'
    # 'Cl'
    # 'Root In Comps'
    # 'V'
    # 'Grp'
    # 'Root Meaning'

    return DpdHeadword(
        user_id=x['ID'],
        lemma_1=x['Pāli1'],
        lemma_2=x['Pāli2'],
        pos=x['POS'],
        grammar=x['Grammar'],
        derived_from=x['Derived from'],
        neg=x['Neg'],
        verb=x['Verb'],
        trans=x['Trans'],
        plus_case=x['Case'],
        meaning_1=x['Meaning IN CONTEXT'],
        meaning_lit=x['Literal Meaning'],
        non_ia=x['Non IA'],
        sanskrit=x['Sanskrit'],
        root_key=x['Pāli Root'],
        root_sign=x['Sgn'],
        root_base=x['Base'],
        family_root=x['Family'],
        family_word=x['Word Family'],
        family_compound=x['Family2'],
        construction=x['Construction'],
        derivative=x['Derivative'],
        suffix=x['Suffix'],
        phonetic=x['Phonetic Changes'],
        compound_type=x['Compound'],
        compound_construction=x['Compound Construction'],
        non_root_in_comps=x['Non-Root In Comps'],
        source_1=x['Source1'],
        sutta_1=x['Sutta1'],
        example_1=x['Example1'],
        source_2=x['Source 2'],
        sutta_2=x['Sutta2'],
        example_2=x['Example 2'],
        antonym=x['Antonyms'],
        synonym=x['Synonyms – different word'],
        variant=x['Variant – same constr or diff reading'],
        commentary=x['Commentary'],
        notes=x['Notes'],
        cognate=x['Cognate'],
        family_set=x['Category'],
        link=x['Link'],
        origin=x['Origin'],
        stem=x['Stem'],
        pattern=x['Pattern'],
        meaning_2=x['Buddhadatta'],
    )


def add_dpd_roots(db_session: Session, csv_path: Path):
    print("[green]processing pali roots")

    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            for key, value in row.items():
                row[key] = value.replace("<br>", "\n")
            rows.append(row)

    def _is_count_not_zero_or_empty(x: Dict[str, str]) -> bool:
        s = x['Count'].strip()
        return (not (s == "0" or s == "-" or s == ""))

    items: List[DpdRoot] = list(map(
        _csv_row_to_root, filter(_is_count_not_zero_or_empty, rows)))

    print("[green]adding to db")
    try:
        for i in items:

            # Check if item is a duplicate.
            res = db_session.query(DpdRoot).filter_by(root=i.root).first()
            if res:
                print(f"[bright_red]Duplicate found, skipping!\n\
                    Already in DB:\n{res}\nConflicts with:\n{i}")

                continue

            db_session.add(i)

        db_session.commit()

    except Exception as e:
        print(f"[bright_red]ERROR: Adding to db failed:\n{e}")


def add_dpd_headwords(db_session: Session, csv_path: Path):
    print("[green]processing pali words")

    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            for key, value in row.items():
                row[key] = value.replace("<br>", "\n")
            rows.append(row)

    items: List[DpdHeadword] = list(map(_csv_row_to_pali_word, rows))

    print("[green]adding to db")
    try:
        for i in items:
            db_session.add(i)

        db_session.commit()

    except Exception as e:
        print(f"[bright_red]ERROR: Adding to db failed:\n{e}")


def main():
    tic()

    print("[bright_yellow]convert dpd.csv to dpd.db")

    pth = ProjectPaths()
    if pth.dpd_db_path.exists():
        pth.dpd_db_path.unlink()

    create_db_if_not_exists(pth.dpd_db_path)

    for p in [pth.old_roots_csv_path, pth.old_dpd_full_path]:
        if not p.exists():
            print(f"[bright_red]File does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session(pth.dpd_db_path)

    add_dpd_roots(db_session, pth.old_roots_csv_path)
    add_dpd_headwords(db_session, pth.old_dpd_full_path)

    db_session.close()
    toc()


if __name__ == "__main__":
    main()
