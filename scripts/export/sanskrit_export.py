#!/usr/bin/env python3

"""
Export
1. Pāḷi
2. Sanskrit
3. POS
4. meaning_1
to .txt and .tsv
"""

from pathlib import Path

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def make_db() -> list[DpdHeadword]:
    pr.green("getting database")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    pr.yes(len(db))
    return sorted(db, key=lambda x: pali_sort_key(x.lemma_1))


def make_txt_entry(i: DpdHeadword) -> str:
    entry_line = f"{i.lemma_1}, {i.sanskrit}; ({i.pos}) {i.meaning_1}"
    return entry_line.replace("ṃ", "ṁ")


def make_tsv_entry(i: DpdHeadword) -> str:
    entry_line = f"{i.lemma_1}\t{i.sanskrit}\t{i.pos}\t{i.meaning_1}"
    return entry_line.replace("ṃ", "ṁ")


def process_db(db: list[DpdHeadword]) -> tuple[list[str], list[str]]:
    pr.green_title("processing db")
    txt_entry_list: list[str] = []
    tsv_entry_list: list[str] = []

    for counter, i in enumerate(db):
        if i.meaning_1 and i.sanskrit:
            txt_entry_list.append(make_txt_entry(i))
            tsv_entry_list.append(make_tsv_entry(i))
        if counter % 10000 == 0:
            pr.counter(counter, len(db), i.lemma_1)

    return txt_entry_list, tsv_entry_list


def save_txt(txt_entry_list: list[str]) -> None:
    txt_path = Path("temp/DPD Pāḷi Sanskrit.txt")
    pr.green(f"saving '{txt_path}'")
    txt_path.write_text("\n".join(txt_entry_list))
    pr.yes("ok")


def save_tsv(tsv_entry_list: list[str]) -> None:
    tsv_path = Path("temp/DPD Pāḷi Sanskrit.tsv")
    pr.green(f"saving '{tsv_path}'")
    header = "Pāḷi\tSanskrit\tPOS\tMeaning"
    tsv_content = [header] + tsv_entry_list
    tsv_path.write_text("\n".join(tsv_content), encoding="utf-8")
    pr.yes("ok")


def main():
    pr.tic()
    pr.title("making DPD Sanskrit dict")

    db = make_db()
    txt_entry_list, tsv_entry_list = process_db(db)
    save_txt(txt_entry_list)
    save_tsv(tsv_entry_list)

    pr.info(f"Exported {len(txt_entry_list)} entries")
    pr.toc()


if __name__ == "__main__":
    main()
