#!/usr/bin/env python3.10
# coding: utf-8

import pandas as pd
import re
import json

from typing import List
from pathlib import Path

from tools.sorter import pali_list_sorter
from db.db_helpers import get_db_session
from db.models import InflectionTables

dpd_db_path = Path("dpd.db")
db_session = get_db_session(dpd_db_path)

db_session.query(InflectionTables).delete()

inflection_table_index_df = pd.read_excel(
    "../inflection generator/declensions & conjugations.xlsx",
    sheet_name="index", dtype=str)

inflection_table_index_df.fillna("", inplace=True)

inflection_table_index_length = len(inflection_table_index_df)

inflection_table_df = pd.read_excel(
    "../inflection generator/declensions & conjugations.xlsx",
    sheet_name="declensions", dtype=str)

inflection_table_df = inflection_table_df.shift(periods=2)

inflection_table_df.columns = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
    "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
    "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK", "AL",
    "AM", "AN", "AO", "AP", "AQ", "AR", "AS", "AT", "AU", "AV", "AW", "AX",
    "AY", "AZ", "BA", "BB", "BC", "BD", "BE", "BF", "BG", "BH", "BI", "BJ",
    "BK", "BL", "BM", "BN", "BO", "BP", "BQ", "BR", "BS", "BT", "BU", "BV",
    "BW", "BX", "BY", "BZ", "CA", "CB", "CC", "CD", "CE", "CF", "CG", "CH",
    "CI", "CJ", "CK", "CL", "CM", "CN", "CO", "CP", "CQ", "CR", "CS", "CT",
    "CU", "CV", "CW", "CX", "CY", "CZ", "DA", "DB", "DC", "DD", "DE", "DF",
    "DG", "DH", "DI", "DJ", "DK"]

inflection_table_df.fillna("", inplace=True)

tables: List[InflectionTables] = []

for row in range(inflection_table_index_length):
    inflection_name = inflection_table_index_df.iloc[row, 0]
    cell_range = inflection_table_index_df.iloc[row, 1]
    like = inflection_table_index_df.iloc[row, 2]

    col_range_1 = re.sub("(.+?)\\d*\\:.+", "\\1", cell_range)
    col_range_2 = re.sub(".+\\:(.[A-Z]*)\\d*", "\\1", cell_range)
    row_range_1 = int(re.sub(".+?(\\d{1,3}):.+", "\\1", cell_range))
    row_range_2 = int(re.sub(".+:.+?(\\d{1,3})", "\\1", cell_range))

    single_table = inflection_table_df.loc[
        row_range_1:row_range_2, col_range_1:col_range_2]
    single_table.name = f"{inflection_name}"
    single_table.reset_index(drop=True, inplace=True)
    single_table.iloc[0, 0] = ""  # remove inflection name

    rows = []
    for row in range(len(single_table)):

        row = (single_table.iloc[row, :]).to_list()
        new_row = []
        for cell in row:
            cell = cell.split("\n")
            if len(cell) > 1:
                cell = pali_list_sorter(cell)
            new_row.append(cell)
        rows += [new_row]

    t = InflectionTables(
        pattern=inflection_name,
        like=like,
        data=json.dumps(rows, ensure_ascii=False)
    )

    search = db_session.query(
        InflectionTables).filter(InflectionTables.pattern == t.pattern).all()

    if len(search) == 0:
        db_session.add(t)
    else:
        print(f"duplicate found {t.pattern}")

db_session.commit()
db_session.close()
