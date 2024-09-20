#!/usr/bin/env python3

import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()

    clean_headwords = set()
    for i in dpd_db:
        if not re.findall(r"\b(nom|acc|instr|dat|abl|gen|loc|voc|1st|2nd|reflx|pl)\b", i.grammar):
            clean_headwords.add(i.lemma_clean)

    clean_headwords = pali_list_sorter(list(clean_headwords))

    with open("temp/dpd_headwords.csv", "w") as file:
        for i in clean_headwords:
            file.write(f"{i}\n")


if __name__ == "__main__":
    main()
