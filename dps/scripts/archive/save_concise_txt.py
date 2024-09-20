#!/usr/bin/env python3

"""Save concise dpd+dps into txt"""

from rich.console import Console

from typing import List

from db.models import DpdHeadword
from db.db_helpers import get_db_session

from tools.pali_sort_key import pali_sort_key
from dps.tools.paths_dps import DPSPaths
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.date_and_time import day

date = day()
console = Console()


def main():
    tic()
    console.print("[bold bright_yellow]exporting dpd dps txt")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()
    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    save_concise_txt(dpspth, dpd_db)
    
    toc()




def save_concise_txt(dpspth, dpd_db):
    console.print("[bold blue]saving concise txt")

    header = ['lemma_1', 'grammar', 'meaning_1', 'meaning_lit', 'ru_meaning', 'ru_meaning_lit']

    def row_to_string(i: DpdHeadword) -> str:
        return " ,".join(map(str, pali_row(i)))

    rows = [" ,".join(map(str, header))]
    rows += [row_to_string(i) for i in dpd_db]

    with open(dpspth.dpd_dps_concise_txt_path, "w", encoding='utf-8') as f:
        f.write("\n".join(rows))


def pali_row(i: DpdHeadword, output="ai") -> List[str]:
    fields = []

    fields.extend([ 
        i.lemma_1,
        i.grammar,
        i.meaning_1 if i.meaning_1 else i.meaning_2,
        i.meaning_lit,
        i.ru.ru_meaning if i.ru else None,
        i.ru.ru_meaning_lit if i.ru else None,
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
    main()
