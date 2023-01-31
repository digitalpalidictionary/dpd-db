#!/usr/bin/env python3.10
# coding: utf-8

import os
import sqlite3
import pandas as pd
import sys
import re

conn = sqlite3.connect('inflections.db')
c = conn.cursor()


def create_inflection_table_index():

    inflection_table_index_df = pd.read_excel(
        "../inflection generator/declensions & conjugations.xlsx", 
        sheet_name="index", dtype=str)

    inflection_table_index_df.fillna("", inplace=True)

    inflection_table_index_length = len(inflection_table_index_df)

    inflection_table_index_dict = dict(
        zip(inflection_table_index_df.iloc[:, 0], inflection_table_index_df.iloc[:, 2]))

    return inflection_table_index_df, inflection_table_index_length, inflection_table_index_dict


inflection_table_index_df, inflection_table_index_length, inflection_table_index_dict = create_inflection_table_index()

index = inflection_table_index_df.drop(["cell range", "irreg", "aka", "aka cell range"], axis=1)

index.to_sql("_index", conn, if_exists='replace', index=False)

def generate_inflection_tables_dict(
    inflection_table_index_df,
    inflection_table_index_length
    ):

    inflection_tables_dict = {}

    inflection_table_df = pd.read_excel(
        "../inflection generator/declensions & conjugations.xlsx", sheet_name="declensions", dtype=str)

    inflection_table_df = inflection_table_df.shift(periods=2)

    inflection_table_df.columns = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
                                "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
                                "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK", "AL", "AM",
                                "AN", "AO", "AP", "AQ", "AR", "AS", "AT", "AU", "AV", "AW", "AX", "AY", "AZ",
                                "BA", "BB", "BC", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BK", "BL", "BM",
                                "BN", "BO", "BP", "BQ", "BR", "BS", "BT", "BU", "BV", "BW", "BX", "BY", "BZ",
                                "CA", "CB", "CC", "CD", "CE", "CF", "CG", "CH", "CI", "CJ", "CK", "CL", "CM",
                                "CN", "CO", "CP", "CQ", "CR", "CS", "CT", "CU", "CV", "CW", "CX", "CY", "CZ",
                                "DA", "DB", "DC", "DD", "DE", "DF", "DG", "DH", "DI", "DJ", "DK"]

    inflection_table_df.fillna("", inplace=True)

    for row in range(inflection_table_index_length):
        inflection_name = inflection_table_index_df.iloc[row, 0]
        cell_range = inflection_table_index_df.iloc[row, 1]
        like = inflection_table_index_df.iloc[row, 2]

        col_range_1 = re.sub("(.+?)\\d*\\:.+", "\\1", cell_range)
        col_range_2 = re.sub(".+\\:(.[A-Z]*)\\d*", "\\1", cell_range)
        row_range_1 = int(re.sub(".+?(\\d{1,3}):.+", "\\1", cell_range))
        row_range_2 = int(re.sub(".+:.+?(\\d{1,3})", "\\1", cell_range))

        inflection_table_df_filtered = inflection_table_df.loc[row_range_1:row_range_2,
                                                         col_range_1:col_range_2]
        inflection_table_df_filtered.name = f"{inflection_name}"
        inflection_table_df_filtered.reset_index(drop=True, inplace=True)
        inflection_table_df_filtered.iloc[0, 0] = ""  # remove inflection name

        inflection_tables_dict[inflection_name] = {}
        inflection_tables_dict[inflection_name]["df"] = inflection_table_df_filtered
        inflection_tables_dict[inflection_name]["range"] = cell_range
        inflection_tables_dict[inflection_name]["like"] = like
        

    return inflection_tables_dict


inflection_tables_dict = generate_inflection_tables_dict(
    inflection_table_index_df, inflection_table_index_length)


for table_name, data in inflection_tables_dict.items():
        df = data["df"]
     
        new_cols = []
        for column, col in enumerate(df.columns):
            new_col = column
            new_cols.append(new_col)
        df.columns = new_cols

        df.to_sql(table_name, conn, if_exists='replace', index=False)

conn.commit()
c.close()
conn.close()



