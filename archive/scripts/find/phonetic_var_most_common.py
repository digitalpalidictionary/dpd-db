#!/usr/bin/env python3

"""Report the headwords with the most phonetic variants (var_phonetic), most first."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths

TOP_N = 20


def main() -> None:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_data: list[DpdHeadword] = (
        db_session.query(DpdHeadword).filter(DpdHeadword.var_phonetic != "").all()
    )

    phonetic_dict: dict[str, list[str]] = {}
    phonetic_counter = 0

    for i in db_data:
        if i.var_phonetic:
            phonetic_counter += 1
            phonetic_dict[i.lemma_clean] = i.var_phonetic.split(", ")

    ordered = sorted(phonetic_dict.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (hw, listed) in enumerate(ordered[:TOP_N]):
        full_list = pali_list_sorter(listed + [hw])
        print(f"{i:>4}:{len(full_list):>2} {', '.join(full_list)}")

    print(f"\ntotal {phonetic_counter}")


if __name__ == "__main__":
    main()
