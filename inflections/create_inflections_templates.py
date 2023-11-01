#!/usr/bin/env python3

"""Import inflection templates from Excel file and save to database."""

import pandas as pd
import re
import json

from typing import List
from pathlib import Path
from rich import print

from db.get_db_session import get_db_session
from db.models import InflectionTemplates
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc

tic()
print("[bright_yellow]create inflection templates")

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
db_session.query(InflectionTemplates).delete()
inflection_templates_path = Path("inflections/inflection_templates.xlsx")

# create index
inflection_template_index_df = pd.read_excel(
    inflection_templates_path, sheet_name="index", dtype=str)
inflection_template_index_df.fillna("", inplace=True)
inflection_template_index_length = len(inflection_template_index_df)

# create templates
inflection_template_df = pd.read_excel(
    inflection_templates_path, sheet_name="declensions", dtype=str)
inflection_template_df = inflection_template_df.shift(periods=2)
inflection_template_df.columns = [
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
inflection_template_df.fillna("", inplace=True)

templates: List[InflectionTemplates] = []

for row in range(inflection_template_index_length):
    inflection_name = inflection_template_index_df.iloc[row, 0]
    cell_range = inflection_template_index_df.iloc[row, 1]
    like = inflection_template_index_df.iloc[row, 2]

    col_range_1 = re.sub("(.+?)\\d*\\:.+", "\\1", cell_range)
    col_range_2 = re.sub(".+\\:(.[A-Z]*)\\d*", "\\1", cell_range)
    row_range_1 = int(re.sub(".+?(\\d{1,3}):.+", "\\1", cell_range))
    row_range_2 = int(re.sub(".+:.+?(\\d{1,3})", "\\1", cell_range))

    single_template = inflection_template_df.loc[
        row_range_1:row_range_2, col_range_1:col_range_2]
    single_template.name = f"{inflection_name}"
    single_template.reset_index(drop=True, inplace=True)
    single_template.iloc[0, 0] = ""  # remove inflection name

    rows = []
    for row in range(len(single_template)):

        row = (single_template.iloc[row, :]).to_list()
        new_row = []
        for cell in row:
            cell = cell.split("\n")
            if len(cell) > 1:
                cell = pali_list_sorter(cell)
            new_row.append(cell)
        rows += [new_row]

    t = InflectionTemplates(
        pattern=inflection_name,
        like=like,
        data=json.dumps(rows, ensure_ascii=False)
    )

    search = db_session.query(
        InflectionTemplates
        ).filter(
            InflectionTemplates.pattern == t.pattern
        ).all()

    if len(search) == 0:
        db_session.add(t)
    else:
        print(f"duplicate found {t.pattern}")

db_session.commit()
db_session.close()
toc()
