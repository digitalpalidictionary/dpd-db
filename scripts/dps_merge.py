#!/usr/bin/env python3.11
import csv
import re
import pickle
import pyperclip

from rich import print
from rich.prompt import Prompt

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths as PTH

# make a generic system that adjusts according to column name
# import csvs as dicts
# if user_id = key then add to specific field
# print grammar, meaning, added field
# copy to pyperclip for db searches


def main():
    print("[bright_yellow]merging dps columns")
    db_session = get_db_session("dpd.db")
    dpd_db = db_session.query(PaliWord).all()

    columns = [
        # "commentary",
        # "compound_construction",
        # "compound_type",
        "construction",
        "derivative",
        "example_1",
        "example_2",
        "meaning_1",
        "meaning_lit",
        "notes",
        "phonetic",
        "plus_case",
        "root_base",
        # "root_pali",
        "sanskrit",
        "suffix",
        "variant",
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

        if break_flag is True:
            break

        dict = {}
        with open(
            PTH.dps_merge_dir.joinpath(
                    column).with_suffix(".csv")) as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                dict[int(row["id"])] = row[column]

        print(len(dict))

        for counter, i in enumerate(dpd_db):
            if break_flag is True:
                break

            column_value_old = getattr(i, column)

            if (
                not column_value_old and
                i.user_id in dict and
                i.user_id not in exceptions_dict[column]
            ):
                column_value_new = dict[i.user_id].replace("<br/>", "\n")
                print()
                print(f"{i.pali_1} [green]({column})")
                print(f"[white]old: [green]{column_value_old}")
                print(f"[white]new: [cyan]{column_value_new}")

                question = "(r)eplace (p)ass (e)xception (b)reak"
                choice = Prompt.ask(question)

                if choice == "r":
                    setattr(i, column, column_value_new)
                    db_session.commit()
                    pyperclip.copy(f"/^{i.pali_1}$/")

                if choice == "e":
                    exceptions_dict[column] += [i.user_id]

                if choice == "b":
                    break_flag = True
                    break

    print()
    print("[green]saving exceptions_dict")
    try:
        with open("dps/exceptions_dict", "wb") as file:
            pickle.dump(exceptions_dict, file)
    except:
        print("[red]not saved!")


if __name__ == "__main__":
    main()


# ask devamitta for latest versions, bold