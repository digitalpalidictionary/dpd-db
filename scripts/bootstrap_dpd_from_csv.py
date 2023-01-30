#!/usr/bin/env python3

import sys
import csv
from typing import Dict, List
from pathlib import Path

from sqlalchemy.orm import Session

from dpd.models import PaliWord, PaliRoot
from dpd.db_helpers import create_db_if_not_exists, get_db_session

def _csv_row_to_root(x: Dict[str, str]) -> PaliRoot:
    # Ignored columns:
    # 'Count'
    # 'Fin'
    # 'Base'
    # 'Padaūpasiddhi'
    # 'PrPāli'
    # 'PrEnglish'
    # 'blanks'
    # 'same/diff'

    # Replace '-' value with empty string.
    def _to_empty(s: str) -> str:
        if s.strip() == "-":
            return ""
        else:
            return s

    x = {k:_to_empty(v) for (k,v) in x.items()}

    return PaliRoot(
        root =                         x['Root']                          if x['Root'] != "" else None,
        root_in_comps =         x['In Comps']                      if x['In Comps'] != "" else None,
        root_has_verb =         x['V']                             if x['V'] != "" else None,
        root_group =        int(x['Group'])                        if x['Group'] != "" else None,
        root_sign =             x['Sign']                          if x['Sign'] != "" else None,
        root_meaning =          x['Meaning']                       if x['Meaning'] != "" else None,
        sanskrit_root =         x['Sk Root']                       if x['Sk Root'] != "" else None,
        sanskrit_root_meaning = x['Sk Root Mn']                    if x['Sk Root Mn'] != "" else None,
        sanskrit_root_class =   x['Cl']                            if x['Cl'] != "" else None,
        root_example =          x['Example']                       if x['Example'] != "" else None,
        dhatupatha_num =        x['Dhātupātha']                    if x['Dhātupātha'] != "" else None,
        dhatupatha_root =       x['DpRoot']                        if x['DpRoot'] != "" else None,
        dhatupatha_pali =       x['DpPāli']                        if x['DpPāli'] != "" else None,
        dhatupatha_english =    x['DpEnglish']                     if x['DpEnglish'] != "" else None,
        dhatumanjusa_num =  int(x['Kaccāyana Dhātu Mañjūsā'])      if x['Kaccāyana Dhātu Mañjūsā'] != "" else None,
        dhatumanjusa_root =     x['DmRoot']                        if x['DmRoot'] != "" else None,
        dhatumanjusa_pali =     x['DmPāli']                        if x['DmPāli'] != "" else None,
        dhatumanjusa_english =  x['DmEnglish']                     if x['DmEnglish'] != "" else None,
        dhatumala_root =        x['Saddanītippakaraṇaṃ Dhātumālā'] if x['Saddanītippakaraṇaṃ Dhātumālā'] != "" else None,
        dhatumala_pali =        x['SnPāli']                        if x['SnPāli'] != "" else None,
        dhatumala_english =     x['SnEnglish']                     if x['SnEnglish'] != "" else None,
        panini_root =           x['Pāṇinīya Dhātupāṭha']           if x['Pāṇinīya Dhātupāṭha'] != "" else None,
        panini_sanskrit =       x['PdSanskrit']                    if x['PdSanskrit'] != "" else None,
        panini_english =        x['PdEnglish']                     if x['PdEnglish'] != "" else None,
        note =                  x['Note']                          if x['Note'] != "" else None,
        matrix_test =           x['matrix test']                   if x['matrix test'] != "" else None,
    )

def _csv_row_to_pali_word(x: Dict[str, str]) -> PaliWord:
    # Ignored columns:
    # 'Fin'
    # 'Sk Root'
    # 'Sk Root Mn'
    # 'Cl'
    # 'Root In Comps'
    # 'V'
    # 'Grp'
    # 'Root Meaning'

    return PaliWord(
        id =                    x['ID']                                       if x['ID'] != "" else None,
        pali_1 =                x['Pāli1']                                 if x['Pāli1'] != "" else None,
        pali_2 =                x['Pāli2']                                 if x['Pāli2'] != "" else None,
        pos =                   x['POS']                                   if x['POS'] != "" else None,
        grammar =               x['Grammar']                               if x['Grammar'] != "" else None,
        derived_from =          x['Derived from']                          if x['Derived from'] != "" else None,
        neg =                   x['Neg']                                   if x['Neg'] != "" else None,
        verb =                  x['Verb']                                  if x['Verb'] != "" else None,
        trans =                 x['Trans']                                 if x['Trans'] != "" else None,
        plus_case =             x['Case']                                  if x['Case'] != "" else None,
        meaning_1 =             x['Meaning IN CONTEXT']                    if x['Meaning IN CONTEXT'] != "" else None,
        meaning_lit =           x['Literal Meaning']                       if x['Literal Meaning'] != "" else None,
        non_ia =                x['Non IA']                                if x['Non IA'] != "" else None,
        sanskrit =              x['Sanskrit']                              if x['Sanskrit'] != "" else None,
        root_key =              x['Pāli Root']                             if x['Pāli Root'] != "" else None,
        root_sign =             x['Sgn']                                   if x['Sgn'] != "" else None,
        root_base =                  x['Base']                                  if x['Base'] != "" else None,
        family_root =           x['Family']                                if x['Family'] != "" else None,
        family_word =           x['Word Family']                           if x['Word Family'] != "" else None,
        family_compound =       x['Family2']                               if x['Family2'] != "" else None,
        construction =          x['Construction']                          if x['Construction'] != "" else None,
        derivative =            x['Derivative']                            if x['Derivative'] != "" else None,
        suffix =                x['Suffix']                                if x['Suffix'] != "" else None,
        phonetic =              x['Phonetic Changes']                      if x['Phonetic Changes'] != "" else None,
        compound_type =         x['Compound']                              if x['Compound'] != "" else None,
        compound_construction = x['Compound Construction']                 if x['Compound Construction'] != "" else None,
        non_root_in_comps =     x['Non-Root In Comps']                     if x['Non-Root In Comps'] != "" else None,
        source_1 =              x['Source1']                               if x['Source1'] != "" else None,
        sutta_1 =               x['Sutta1']                                if x['Sutta1'] != "" else None,
        example_1 =             x['Example1']                              if x['Example1'] != "" else None,
        source_2 =              x['Source 2']                              if x['Source 2'] != "" else None,
        sutta_2 =               x['Sutta2']                                if x['Sutta2'] != "" else None,
        example_2 =             x['Example 2']                             if x['Example 2'] != "" else None,
        antonym =               x['Antonyms']                              if x['Antonyms'] != "" else None,
        synonym =               x['Synonyms – different word']             if x['Synonyms – different word'] != "" else None,
        variant =               x['Variant – same constr or diff reading'] if x['Variant – same constr or diff reading'] != "" else None,
        commentary =            x['Commentary']                            if x['Commentary'] != "" else None,
        notes =                 x['Notes']                                 if x['Notes'] != "" else None,
        cognate =               x['Cognate']                               if x['Cognate'] != "" else None,
        category =              x['Category']                              if x['Category'] != "" else None,
        link =                  x['Link']                                  if x['Link'] != "" else None,
        stem =                  x['Stem']                                  if x['Stem'] != "" else None,
        pattern =               x['Pattern']                               if x['Pattern'] != "" else None,
        meaning_2 =             x['Buddhadatta']                           if x['Buddhadatta'] != "" else None,
    )


def add_pali_roots(db_session: Session, csv_path: Path):
    print("=== add_pali_roots() ===")

    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)

    def _is_count_not_zero_or_empty(x: Dict[str, str]) -> bool:
        s = x['Count'].strip()
        return (not (s == "0" or s == "-" or s == ""))

    items: List[PaliRoot] = list(map(_csv_row_to_root, filter(_is_count_not_zero_or_empty, rows)))

    try:
        for i in items:
            # print(f"PaliRoot: {i.root}")

            # Check if item is a duplicate.
            res = db_session.query(PaliRoot).filter_by(root = i.root).first()
            if res:
                print(f"WARN: Duplicate found, skipping!\nAlready in DB:\n{res}\nConflicts with:\n{i}")
                continue

            db_session.add(i)

        db_session.commit()

    except Exception as e:
        print(f"ERROR: Adding to db failed:\n{e}")

def add_pali_words(db_session: Session, csv_path: Path):
    print("=== add_pali_words() ===")

    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)

    items: List[PaliWord] = list(map(_csv_row_to_pali_word, rows))

    try:
        for i in items:
            # print(f"PaliWord: {i.pali1}")

            # Check if item is a duplicate.
            res = db_session.query(PaliWord).filter_by(pali1 = i.pali1).first()
            if res:
                print(f"WARN: Duplicate found, skipping!\nAlready in DB:\n{res}\nConflicts with:\n{i}")
                continue

            db_session.add(i)

        db_session.commit()

    except Exception as e:
        print(f"ERROR: Adding to db failed:\n{e}")

def main():
    dpd_db_path = Path("dpd.sqlite3")
    roots_csv_path = Path("../csvs/roots.csv")
    dpd_full_path = Path("../csvs/dpd-full.csv")

    if dpd_db_path.exists():
        dpd_db_path.unlink()

    create_db_if_not_exists(dpd_db_path)

    for p in [roots_csv_path, dpd_full_path]:
        if not p.exists():
            print(f"File does not exist: {p}")
            sys.exit(1)

    db_session = get_db_session(dpd_db_path)

    add_pali_roots(db_session, roots_csv_path)
    add_pali_words(db_session, dpd_full_path)

    db_session.close()

if __name__ == "__main__":
    main()
