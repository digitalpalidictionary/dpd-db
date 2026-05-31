#!/usr/bin/env python3

"""Find the words with most common phonetic variants"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_data: list[DpdHeadword] = (
        db_session.query(DpdHeadword).filter(DpdHeadword.var_phonetic != "").all()
    )

    phonetic_dict: dict[str, tuple[int, list[str]]] = {}
    phonetic_counter = 0

    for i in db_data:
        if i.var_phonetic:
            phonetic_counter += 1
            ph_vars = i.var_phonetic.split(", ")
            phonetic_dict[i.lemma_clean] = (len(ph_vars), ph_vars)

    ordered = sorted(phonetic_dict.items(), key=lambda x: x[1][0], reverse=True)
    for i in range(20):
        hw = ordered[i][0]
        counted, listed = ordered[i][1]
        full_list = pali_list_sorter(listed + [hw])
        print(f"{i:>4}:{len(full_list):>2} {', '.join(full_list)}")
        # print(counted, pali_list_sorter(listed.append(hw)))

    print(f"\ntotal {phonetic_counter}")


if __name__ == "__main__":
    main()
