#!/usr/bin/env python3

"""Compile and count all the instances of plus_case in DpdHeadword table and
save to TSV."""


import re

from rich import print
from collections import Counter
from collections import namedtuple

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.tsv_read_write import write_tsv_list
from tools.meaning_construction import make_meaning_combo


def main():
    print("[bright_yellow]finding case relationships")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()
    plus_case_list = []
    d = namedtuple("Data", ["lemma_1", "pos", "plus_case", "meaning"])

    for i in dpd_db:
        if i.plus_case and i.meaning_1:
            meaning = make_meaning_combo(i)
            if " or " in i.plus_case:
                first_case = re.sub(" or.+", "", i.plus_case)
                second_case = re.sub(".+ or ", "", i.plus_case)
                plus_case_list += [d(i.lemma_1, i.pos, first_case, meaning)]
                plus_case_list += [d(i.lemma_1, i.pos, second_case, meaning)]
            else:
                plus_case_list += [d(i.lemma_1, i.pos, i.plus_case, meaning)]

    # sort by case then lemma_1
    plus_case_list = sorted(
        plus_case_list, key=lambda x: (x.plus_case, pali_sort_key(x.lemma_1)))

    # write to tsv
    file_path = pth.temp_dir.joinpath("plus_case.tsv")
    header = ["lemma_1", "pos", "plus_case", "meaning"]
    write_tsv_list(str(file_path), header, plus_case_list)

    # counts
    plus_case_counts = Counter(i[2] for i in plus_case_list)
    plus_case_count_list = [
        (count, case) for case, count in plus_case_counts.items()]
    plus_case_count_list.sort(reverse=True)

    # write to tsv
    file_path = pth.temp_dir.joinpath("plus_case_counts.tsv")
    header = ["count", "plus_case", ]
    write_tsv_list(str(file_path), header, plus_case_count_list)


if __name__ == "__main__":
    main()
