#!/usr/bin/env python3.10
# coding: utf-8
import re
import sqlite3

from typing import Tuple, List

conn = sqlite3.connect('inflections/inflection_tables.sqlite3')
cursor = conn.cursor()


def generate_inflection_table(stem: str, pattern: str, rows) -> List[str]:
    
    inflections_set: set = set()
    html: str = "<table class='inflection'>"
    tipitaka_words = ["āharantiyā"]

    # row 0 is the top header
    # column 0 is the grammar header
    # odd rows > 0 are inflections
    # even rows > 0 are grammar info

    for row in enumerate(rows):
        row_number: int = row[0]
        row_data: Tuple = row[1]
        html += "<tr>"
        for column in enumerate(row_data):
            column_number: int = column[0]
            cell_data: Tuple = column[1]
            if row_number == 0:
                if column_number == 0:
                    html += f"<th></th>"
                if column_number % 2 == 1:
                    html += f"<th>{cell_data}</th>"
            elif row_number > 0:
                if column_number == 0:
                    html += f"<th>{cell_data}</th>"
                elif column_number % 2 == 1 and column_number > 0:
                    title: str = row_data[column_number+1]
                    inflections: lst = cell_data.split("\n")

                    for inflection in inflections:
                        if inflection == "":
                            html += f"<td title='{title}'></td>"
                        else:
                            word_clean = f"{stem}{inflection}"
                            if word_clean in tipitaka_words:
                                word = f"{stem}<b>{inflection}</b>"
                            else:
                                word = f"<span style='gray'>{stem}<b>{inflection}</b></span>"

                            if len(inflections) == 1:
                                html += f"<td title='{title}'>{word}</td>"
                            else:
                                if inflection == inflections[0]:
                                    html += f"<td title='{title}'>{word}<br>"
                                elif inflection != inflections[-1]:
                                    html += f"{word}<br>"
                                else:
                                    html += f"{word}</td>"
                            inflections_set.add(word_clean)
            
    with open("inflections/xxx tabletest.html", "w") as f:
        f.write(html)
    print(sorted(inflections_set))
    return html, inflections_set


def main():

    stem = "anicc"
    pattern = "a adj"
    rows = cursor.execute(f"SELECT * FROM '{pattern}'")
    print(type(rows))
    generate_inflection_table(stem, pattern, rows)

    conn.close()

if __name__ == "__main__":
    main()


# in the db make a table with json object = inflection tables and headword / stem pattern combos