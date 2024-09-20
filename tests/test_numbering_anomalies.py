#!/usr/bin/env python3

"""Find anomalies in the headword numbering.
Looks for words with different roots or words families."""

import re
import pyperclip

from rich import print
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    print("[bright_yellow]finding numbering anomalies")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()
    root_numbering(dpd_db)
    root_numbering_dot(dpd_db)
    compound_numbering(dpd_db)
    compound_numbering_dot(dpd_db)


def root_numbering(dpd_db):
    hw_rt_dict = {}
    counter = 0

    for i in dpd_db:
        if (
            re.findall(r"\d", i.lemma_1) and
            "." not in i.lemma_1
        ):
            if i.lemma_clean not in hw_rt_dict:
                hw_rt_dict[i.lemma_clean] = i.root_key
            else:
                if hw_rt_dict[i.lemma_clean] != i.root_key:
                    db_search = fr"/^{i.lemma_clean} \d/"
                    print(i.lemma_clean, end=" ")
                    pyperclip.copy(db_search)
                    input()
                    counter += 1

    print(f"{'root numbering':<30}{counter}")


def root_numbering_dot(dpd_db):
    hw_rt_dict = {}
    counter = 0

    for i in dpd_db:
        if (
            re.findall(r"\d", i.lemma_1) and
            "." in i.lemma_1
        ):
            first_number = re.sub(r"\..+", "", i.lemma_1)

            if first_number not in hw_rt_dict:
                hw_rt_dict[first_number] = i.root_key
            else:
                if hw_rt_dict[first_number] != i.root_key:
                    db_search = fr"/^{i.lemma_clean} /"
                    print(first_number, end=" ")
                    pyperclip.copy(db_search)
                    input()
                    counter += 1

    print(f"{'root numbering dot':<30}{counter}")


def compound_numbering(dpd_db):
    hw_cnstr_dict = {}
    counter = 0
    exceptions = ["koṭṭhāsa"]

    for i in dpd_db:
        if (
            i.lemma_clean not in exceptions and
            re.findall(r"\d", i.lemma_1) and
            "." not in i.lemma_1 and
            re.findall(r"\bcomp\b", i.grammar) and
            i.meaning_1
        ):
            if i.lemma_clean not in hw_cnstr_dict:
                hw_cnstr_dict[i.lemma_clean] = i.family_compound
            else:
                if hw_cnstr_dict[i.lemma_clean] != i.family_compound:
                    db_search = fr"/^{i.lemma_clean} \d/"
                    print(i.lemma_clean, end=" ")
                    pyperclip.copy(db_search)
                    input()
                    counter += 1

    print(f"{'compound numbering':<30}{counter}")


def compound_numbering_dot(dpd_db):
    hw_cnstr_dict = {}
    counter = 0

    for i in dpd_db:
        if (
            re.findall(r"\d", i.lemma_1) and
            "." in i.lemma_1 and
            re.findall(r"\bcomp\b", i.grammar) and
            i.meaning_1
        ):
            first_number = re.sub(r"\..+", "", i.lemma_1)

            if first_number not in hw_cnstr_dict:
                hw_cnstr_dict[first_number] = i.family_compound
            else:
                if hw_cnstr_dict[first_number] != i.family_compound:
                    db_search = fr"/^{i.lemma_clean} /"
                    print(first_number, end=" ")
                    pyperclip.copy(db_search)
                    input()
                    counter += 1

    print(f"{'compound numbering dot':<30}{counter}")


if __name__ == "__main__":
    main()
