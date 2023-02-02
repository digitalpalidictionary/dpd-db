#!/usr/bin/env python3.10
# coding: utf-8

import re
import sqlite3
import json
import pickle

from rich import print
from sorter import sort_key
from tqdm import tqdm
from db.db_helpers import create_db_if_not_exists, get_db_session
from db.models import PaliWord, PaliRoot
from typing import Tuple, List, Dict
from pathlib import Path

conn = sqlite3.connect('inflections.db')
cursor = conn.cursor()
tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table';").fetchall()

dpd_db_path = Path("dpd.db")
db_session = get_db_session(dpd_db_path)
dpd_db = db_session.query(PaliWord).all()

inflection_tables_dict: dict = {}
changed_patterns: list = []
changed_headwords: list = []
regenerate_all: bool = True

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# how is all_tipitaka_words getting generated?
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

with open("share/all_tipitaka_words", "rb") as f:
    all_tipitaka_words: set = pickle.load(f)

def test_inflection_table_changed():
    print(f"[blue]testing for changed inflection patterns")

    with open("inflections/tests/inflection_pattern_dict", "rb") as f:
        old_tables: dict = pickle.load(f)

    # find added and changed patterns
    for table in tables:
        new_table_name = table[0]
        new_table_data = cursor.execute(f"SELECT * FROM '{new_table_name}'").fetchall()
        if new_table_name not in old_tables:
            print(f"\t{new_table_name} [red]added")
            changed_patterns.append(new_table_name)

        try:
            old_table_data: List(Tuple) = old_tables[new_table_name]
            if old_table_data != new_table_data:
                print(f"\t{new_table_name} [red]changed")
                changed_patterns.append(new_table_name)
        except:
            pass
            # print(f"\t{new_table_name} [red]added")
            # changed_patterns.append(new_table_name)

    # find deleted patterns

    for old_table_name, old_table_data in old_tables.items():
        try:
            new_table_data = cursor.execute(f"SELECT * FROM '{old_table_name}'").fetchall()
        except:
            print(f"\t{old_table_name} [red]deleted")
            changed_patterns.append(old_table_name)

    # find changed "like"

    if "_index" in changed_patterns:
        changed_patterns.remove('_index')
        
        # make useable dictionaries
        old_index_dict: dict = {}
        for i in range(len(old_tables["_index"])):
            pattern = old_tables["_index"][i][0]
            like = old_tables["_index"][i][1]
            old_index_dict[pattern] = like
        
        new_index_dict: dict = {}
        new_index: List[Tuple] = cursor.execute(
            f"SELECT * FROM '_index'").fetchall()
    
        for i in range(len(new_index)):
            pattern = new_index[i][0]
            like = new_index[i][1]
            new_index_dict[pattern] = like
        
        # find added patterns

        for pattern in new_index_dict:
            if pattern not in old_index_dict:
                print(f"\t{pattern} [red]index added")
                changed_patterns.append(pattern)

        # find deleted patterns

        for pattern in old_index_dict:
            if pattern not in new_index_dict:
                print(f"\t{pattern} [red]index deleted")
                changed_patterns.append(pattern)

        # find changed "like"

        for pattern in new_index_dict:
            try:
                if new_index_dict[pattern] != old_index_dict[pattern]:
                    print(f"\t{pattern} [red]like changed")
                    changed_patterns.append(pattern)
            except:
                # find missing patterns
                print(f"\t{pattern} [red]like added")
                changed_patterns.append(pattern)

    
    def save_pickle() -> None:
        inflection_pattern_dict = {}
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';").fetchall()

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM '{table_name}'")
            table_data = cursor.fetchall()
            for row in table_data:
                inflection_pattern_dict[table_name] = table_data
    
        with open("inflections/tests/inflection_pattern_dict", "wb") as f:
            pickle.dump(inflection_pattern_dict, f)

    save_pickle()


def test_missing_pattern() -> None:
    print("[blue]testing for missing patterns")

    for i in dpd_db:
        if i.pattern == "" and i.stem != "-":
            print(f"\t{i.pali_1} {i.pos} [red]has a missing pattern")
            new_pattern = input(f"\twhat is the new pattern? ")
            i.pattern = new_pattern
    db_session.commit()


def test_wrong_pattern() -> None:
    print("[blue]testing for wrong patterns")

    tables_list = []
    for i in tables:
        tables_list += [i[0]]
    
    wrong_pattern_db = db_session.query(PaliWord).filter(
        PaliWord.pattern.notin_(tables_list)).filter(
            PaliWord.pattern != "").all()
    for i in wrong_pattern_db:
        print(f"\t{i.pali_1} {i.pos} [red]has the wrong pattern")

        new_pattern = ""
        while new_pattern not in tables_list:
            new_pattern = input(f"\twhat is the new pattern? ")
            i.pattern = new_pattern

    db_session.commit()


def test_changes_in_stem_pattern_etc() -> None:
    print("[blue]testing for changes in stem and pattern, missing inflection tables and inflection lists")

    with open("share/headword_stem_pattern_dict", "rb") as f:
        old_headword_stem_pattern_dict: dict = pickle.load(f)

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # the follow block is slow, how to make it faster? 
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    for i in dpd_db:
        
        # testing for chnanged stem pattern

        try:
            if i.stem != old_headword_stem_pattern_dict[i.pali_1]["stem"]:
                print(f"\t{i.pali_1} [red] stem changed")
                changed_headwords.append(i.pali_1)

            if i.pattern != old_headword_stem_pattern_dict[i.pali_1]["pattern"]:
                print(f"\t{i.pali_1} [red] pattern changed")
                changed_headwords.append(i.pali_1)

        except:
            print(f"\t{i.pali_1} [red] headword missing")
            changed_headwords.append(i.pali_1)
        
        # testing for missing stem

        if i.stem == "":
            print(f"\t{i.pali_1} [red] stem missing[white]", end=" ")

            changed_headwords.append(i.pali_1)
            new_stem = input(f"\t{i.pali_1} {i.pos} what's the correct stem? ")
            i.stem = new_stem

        # testing for missing pattern
        
        if i.pattern == "" and i.stem != "-":
            print(f"\t{i.pali_1} [red] pattern missing[white]", end=" ")
            changed_headwords.append(i.pali_1)
            new_pattern = input(f"\t{i.pali_1} {i.pos} what's the correct pattern? ")
            i.stem = new_pattern
        
        # testing for missing inflection tables

        if i.inflection_table == "" and i.stem != "-":
            print(f"\t{i.pali_1} [red] inflection table missing")
            changed_headwords.append(i.pali_1)

    
        # testing for missing inflection lists

        if i.inflections == "" and i.stem != "-":
            print(f"\t{i.pali_1} [red] inflction list missing")
            changed_headwords.append(i.pali_1)
    
    db_session.commit()


    def save_pickle() -> None:
        headword_stem_pattern_dict: Dict[Dict[str]] = {}
        for i in dpd_db:
            headword_stem_pattern_dict[i.pali_1] = {"stem": i.stem, "pattern": i.pattern}

        with open("share/headword_stem_pattern_dict", "wb") as f:
            pickle.dump(headword_stem_pattern_dict, f)
    
    save_pickle()


def test_changes() -> None:
    test_inflection_table_changed()
    test_missing_pattern()
    test_wrong_pattern()
    test_changes_in_stem_pattern_etc()


def generate_inflection_table(stem: str, pattern: str, rows: Tuple) -> List[str]:

    inflections_list: list = []
    html_table: str = "<table class='inflection'>"
    stem = re.sub(r"\!|\*", "", stem)

    # row 0 is the top header
    # column 0 is the grammar header
    # odd rows > 0 are inflections
    # even rows > 0 are grammar info

    for row in enumerate(rows):
        row_number: int = row[0]
        row_data: Tuple = row[1]
        html_table += "<tr>"
        for column in enumerate(row_data):
            column_number: int = column[0]
            cell_data: Tuple = column[1]
            if row_number == 0:
                if column_number == 0:
                    html_table += f"<th></th>"
                if column_number % 2 == 1:
                    html_table += f"<th>{cell_data}</th>"
            elif row_number > 0:
                if column_number == 0:
                    html_table += f"<th>{cell_data}</th>"
                elif column_number % 2 == 1 and column_number > 0:
                    title: str = row_data[column_number+1]
                    inflections: lst = cell_data.split("\n")

                    for inflection in inflections:
                        if inflection == "":
                            html_table += f"<td title='{title}'></td>"
                        else:
                            word_clean = f"{stem}{inflection}"
                            if word_clean in all_tipitaka_words:
                                word = f"{stem}<b>{inflection}</b>"
                            else:
                                word = f"<span style='color: gray;'>{stem}<b>{inflection}</b></span>"

                            if len(inflections) == 1:
                                html_table += f"<td title='{title}'>{word}</td>"
                            else:
                                if inflection == inflections[0]:
                                    html_table += f"<td title='{title}'>{word}<br>"
                                elif inflection != inflections[-1]:
                                    html_table += f"{word}<br>"
                                else:
                                    html_table += f"{word}</td>"
                            if word_clean not in inflections_list:
                                inflections_list.append(word_clean)

    return html_table, inflections_list


def main():
    print("[yellow]generating tables and inflection lists")

    test_changes()

    html_table_save_dict: dict = {}

    print("[blue]generating html tables and inflection lists")
    for i in tqdm(dpd_db):

        test1 = i.pali_1 in changed_headwords
        test2 = i.pattern in changed_patterns
        test3 = regenerate_all == True

        if test1 or test2 or test3:

            if i.pattern != "":
                table_rows: List[Tuple] = cursor.execute(f"SELECT * FROM '{i.pattern}'").fetchall()
                
                html_table, inflections_list = generate_inflection_table(
                    i.stem, i.pattern, table_rows)

                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                # how to sort the list in pali alphabetical order??
                # inflections_list: list = sorted(
                #     list(inflections_set), key=lambda x: x.map(sort_key))
                # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                i.inflections = json.dumps(
                    inflections_list, ensure_ascii=False)
                
                i.inflection_table = html_table

                inflection_tables_dict[i.pali_1] = {
                    "stem": i.stem, "pattern": i.pattern, "html_table": html_table}
            
            else:
                pali_1_clean: str = re.sub(r" \d.*$", "", i.pali_1)
                i.inflections = json.dumps(
                    list([pali_1_clean]), ensure_ascii=False)
        
            if i.id % 500 == 0:
                html_table_save_dict[i.pali_1] = html_table

    for headword in html_table_save_dict:
        with open(f"xxx delete/html tables/{headword}.html", "w") as f:
            f.write(html_table_save_dict[headword])

    with open("share/changed_headwords", "wb") as f:
        piclke.dump(changed_headwords, f)

    with open("share/changed_patterns", "wb") as f:
        piclke.dump(changed_patterns, f)

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # find all unused patterns
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    db_session.commit()
    db_session.close()
    conn.close()

if __name__ == "__main__":
    main()

