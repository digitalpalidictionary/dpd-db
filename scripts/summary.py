#!/usr/bin/env python3

"""Compile a summary of latest dictionary data to accompany a release."""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, PaliRoot, Sandhi, DerivedData
from tools.pali_sort_key import pali_sort_key
from tools.tic_toc import tic, toc
from tools.configger import config_read, config_update
from tools.paths import ProjectPaths
from tools.uposatha_day import uposatha_today


def main():
    tic()
    print("[bright_yellow]summary")
    print("[green]reading db tables")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()
    roots_db = db_session.query(PaliRoot).all()
    sandhi_db = db_session.query(Sandhi).all()
    derived_db = db_session.query(DerivedData).all()
    last_count = config_read("uposatha", "count", default_value=74657)

    print("[green]summarizing data")
    line1, line5, root_families = dpd_size(dpd_db)
    line2 = root_size(roots_db, root_families)
    line3 = sandhi_size(sandhi_db)
    line4 = inflection_size(derived_db)
    line6 = root_data(roots_db)
    new_words_string = new_words(db_session, last_count)

    print()
    print(line1)
    print(line2)
    print(line3)
    print(line4)
    print(line5)
    print(line6)
    print("- 100% dictionary recognition up to and including ")
    print()
    print(f"new words include: {new_words_string}")

    if uposatha_today():
        print("[green]updating uposatha count")
        config_update("uposatha", "count", len(dpd_db))

    toc()


def dpd_size(dpd_db):
    total_headwords = len(dpd_db)
    total_complete = 0
    total_partially_complete = 0
    total_incomplete = 0
    root_families: dict = {}
    total_data = 0

    columns = PaliWord.__table__.columns
    column_names = [c.name for c in columns]
    exceptions = ["id", "created_at", "updated_at"]

    for i in dpd_db:
        if i.meaning_1:
            if i.example_1:
                total_complete += 1
            else:
                total_partially_complete += 1
        else:
            total_incomplete += 1
        if i.root_key:
            subfamily = f"{i.root_key} {i.family_root}"
            if subfamily in root_families:
                root_families[f"{i.root_key} {i.family_root}"] += 1
            else:
                root_families[f"{i.root_key} {i.family_root}"] = 1

        for column in column_names:
            if column not in exceptions:
                cell_value = getattr(i, column)
                if cell_value:
                    total_data += 1

    line1 = "- "
    line1 += f"{total_headwords:_} headwords, "
    line1 += f"{total_complete:_} complete, "
    line1 += f"{total_partially_complete:_} partially complete, "
    line1 += f"{total_incomplete:_} incomplete entries"
    line1 = line1.replace("_", " ")

    line5 = f"- {total_data:_} cells of Pāḷi word data"
    line5 = line5.replace("_", " ")
    return line1, line5, root_families


def new_words(db_session, last_count):
    db = db_session.query(PaliWord).filter(PaliWord.id > last_count).all()

    new_words = [i.pali_1 for i in db]
    new_words = sorted(new_words, key=pali_sort_key)
    new_words_string = ""
    for nw in new_words:
        if nw != new_words[-1]:
            new_words_string += f"{nw}, "
        else:
            new_words_string += f"{nw} "
    new_words_string += f"[{len(new_words)}]"

    return new_words_string


def root_size(roots_db, root_families):
    total_roots = len(roots_db)
    total_root_families = len(root_families)
    total_derived_from_roots = 0
    for family in root_families:
        total_derived_from_roots += root_families[family]

    line2 = "- "
    line2 += f"{total_roots:_} roots, "
    line2 += f"{total_root_families:_} root families, "
    line2 += f"{total_derived_from_roots:_} words derived from roots"
    line2 = line2.replace("_", " ")

    return line2


def sandhi_size(sandhi_db):
    total_sandhis = len(sandhi_db)
    line3 = f"- {total_sandhis:_} deconstructed compounds"
    line3 = line3.replace("_", " ")
    return line3


def inflection_size(derived_db):
    total_inflections = 0
    all_inflection_set = set()

    for i in derived_db:
        inflections = i.inflections_list
        total_inflections += len(inflections)
        all_inflection_set.update(inflections)

    # print(total_inflections)
    # print(len(all_inflection_set))

    line4 = f"- {total_inflections:_} unique inflected forms recognised"
    line4 = line4.replace("_", " ")

    return line4


def root_data(roots_db):
    columns = PaliRoot.__table__.columns
    column_names = [c.name for c in columns]
    exceptions = ["root_info", "root_matrix", "created_at", "updated_at"]
    total_roots_data = 0

    for i in roots_db:
        for column in column_names:
            if column not in exceptions:
                cell_value = getattr(i, column)
                if cell_value:
                    total_roots_data += 1

    line6 = f"- {total_roots_data:_} cells of Pāḷi root data"
    line6 = line6.replace("_", " ")

    return line6


if __name__ == "__main__":
    main()
