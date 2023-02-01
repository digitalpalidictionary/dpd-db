#!/usr/bin/env python3.10
# coding: utf-8

import re
import sqlite3
import json

from sorter import sort_key
from tqdm import tqdm
from db.db_helpers import create_db_if_not_exists, get_db_session
from db.models import PaliWord, PaliRoot
from typing import Tuple, List
from pathlib import Path

conn = sqlite3.connect('inflections.db')
cursor = conn.cursor()

dpd_db_path = Path("dpd.db")
db_session = get_db_session(dpd_db_path)
dpd_db = db_session.query(PaliWord).all()

inflection_tables_dict: dict = {}


def generate_inflection_table(stem: str, pattern: str, rows: Tuple) -> List[str]:

    inflections_set: set = set()
    html_table: str = "<table class='inflection'>"
    tipitaka_words = ["āharantiyā"]

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
                            if word_clean in tipitaka_words:
                                word = f"{stem}<b>{inflection}</b>"
                            else:
                                word = f"<span style='gray'>{stem}<b>{inflection}</b></span>"

                            if len(inflections) == 1:
                                html_table += f"<td title='{title}'>{word}</td>"
                            else:
                                if inflection == inflections[0]:
                                    html_table += f"<td title='{title}'>{word}<br>"
                                elif inflection != inflections[-1]:
                                    html_table += f"{word}<br>"
                                else:
                                    html_table += f"{word}</td>"
                            inflections_set.add(word_clean)
            
    return html_table, inflections_set


def main():
    print("generating tables and inflection lists")

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # find all changed, missing zero!
    # make a list of all tipitaka words!
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    for i in tqdm(dpd_db):

        if i.pattern != "":
            table_rows: List[Tuple] = cursor.execute(f"SELECT * FROM '{i.pattern}'").fetchall()
            
            html_table, inflections_set = generate_inflection_table(
                i.stem, i.pattern, table_rows)

            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # how to sort the list in pali alphabetical order??
            # inflections_list: list = sorted(
            #     list(inflections_set), key=lambda x: x.map(sort_key))
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            i.inflections = json.dumps(
                list(inflections_set), ensure_ascii=False)
            
            i.inflection_table = html_table

            inflection_tables_dict[i.pali_1] = {
                "stem": i.stem, "pattern": i.pattern, "html_table": html_table}
        
        else:
            pali_1_clean: str = re.sub(r" \d.*$", "", i.pali_1)
            i.inflections = json.dumps(
                list([pali_1_clean]), ensure_ascii=False)

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # export list of changed headwords
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    db_session.commit()
    db_session.close()
    conn.close()

if __name__ == "__main__":
    main()

