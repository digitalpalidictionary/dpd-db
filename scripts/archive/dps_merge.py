#!/usr/bin/env python3

"""Merge DPS data into DpdHeadword table."""

import csv
import pickle
import pyperclip

from rich import print
from rich.prompt import Prompt

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

# make a generic system that adjusts according to column name
# import csvs as dicts
# if id = key then add to specific field
# print grammar, meaning, added field
# copy to pyperclip for db searches


def main():
    print("[bright_yellow]merging dps columns")
    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()

    columns = [
        # "commentary",
        # "compound_construction",
        # "compound_type",
        # "construction",
        # "derivative",
        "example_1",
        # "example_2",
        # "meaning_1",
        # "meaning_lit",
        # "notes",
        # "phonetic",
        # "plus_case",
        # "root_base",
        # "root_pali",
        # "sanskrit",
        # "source_1",
        # "source_2",
        # "suffix",
        # "sutta_1",
        # "sutta_2",
        # "variant",
    ]
    break_flag = False

    try:
        with open("dps/exceptions_dict", "rb") as file:
            exceptions_dict = pickle.load(file)
            print(exceptions_dict)
    except FileNotFoundError:
        exceptions_dict = {}

    for column in columns:
        print(f"[green]{column:<30}", end="")
        try:
            print(f"exceptions: {exceptions_dict[column]}")
        except KeyError:
            exceptions_dict[column] = []

        if break_flag:
            break

        dict = {}
        with open(
            dpspth.dps_merge_dir.joinpath(
                    column).with_suffix(".csv")) as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                dict[int(row["id"])] = row[column]

        print(len(dict))

        for __counter__, i in enumerate(dpd_db):
            if break_flag:
                break

            column_value_old = getattr(i, column)

            if (
                i.id in dict and
                i.id not in exceptions_dict[column] and
                not column_value_old
            ):
                column_value_new = dict[i.id].replace("<br/>", "\n")
                if column_value_old != column_value_new:
                    print()
                    print(f"{i.lemma_1} [green]({column})")
                    print(f"[violet]{i.meaning_1}")
                    print(f"[white]old: [green]{column_value_old}")
                    print(f"[white]new: [cyan]{column_value_new}")

                    question = "(a)dd / replace (p)ass (e)xception (b)reak"
                    choice = Prompt.ask(question)

                    if choice == "a":
                        # if True:
                        setattr(i, column, column_value_new)
                        setattr(i, "origin", "dps")
                        pyperclip.copy(f"/^{i.lemma_1}$/")
                        # db_session.commit()

                    if choice == "e":
                        exceptions_dict[column] += [i.id]

                    if choice == "b":
                        break_flag = True
                        break

    db_session.commit()
    print()
    print("[green]saving exceptions_dict")
    try:
        with open("dps/exceptions_dict", "wb") as file:
            pickle.dump(exceptions_dict, file)
    except Exception:
        print("[red]not saved!")


if __name__ == "__main__":
    main()
