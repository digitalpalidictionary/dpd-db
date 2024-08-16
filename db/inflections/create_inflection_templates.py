#!/usr/bin/env python3

"""
1. Import inflection templates from Excel file
2. Change the format into nested lists
3. Save to database as JSON
4. Save a pickle of added, updated or deleted templates
"""

import pandas as pd
import pickle
import re

from pandas.core.frame import DataFrame
from pandas.core.series import Series

from db.db_helpers import get_db_session
from db.models import InflectionTemplates, DbInfo
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.printer import p_title, p_green_title


class GlobalVars():
    """Variables used globally."""

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    # main dataframes
    index_df: DataFrame
    infl_templ_df: DataFrame

    # index
    index_row: int
    index_data: Series
    
    # template_df data
    template_df: DataFrame
    inflection_name: str
    cell_range: str
    like: str
    data_list: list[list]

    # add to the db
    infl_templ: InflectionTemplates
    added_templates: list[str] = []
    changed_templates: list[str] = []


def make_index_dataframe(g:GlobalVars):
    """
    The index contains 
    1. inflection pattern name
    2. cell range of the inflection table
    3. like
    """
    
    g.index_df = pd.read_excel(
        g.pth.inflection_templates_path,
        sheet_name="index",
        dtype=str
    )
    g.index_df.fillna("", inplace=True)


def make_infl_templ_dataframe(g: GlobalVars):
    """A massive xy spread of inflection templates."""

    g.infl_templ_df: DataFrame = pd.read_excel(
        g.pth.inflection_templates_path,
        sheet_name="declensions",
        dtype=str,
    )
    g.infl_templ_df = g.infl_templ_df.shift(periods=2)
    g.infl_templ_df.fillna("", inplace=True)
    
    g.infl_templ_df.columns = [
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


def extract_template_df(g: GlobalVars):
    """Extract the template_df from the main df."""

    # parse data
    g.inflection_name, g.cell_range, g.like = g.index_data

    # parse cell_range
    start_range, end_range = g.cell_range.split(":")

    # parse start
    col_start, row_start = re.findall(
        "(.[A-Z]*)(.[0-9]*)",
        start_range
    )[0]
    
    # parse end
    col_end, row_end = re.findall(
        "(.[A-Z]*)(.[0-9]*)",
        end_range
    )[0]
    
    # isolate template
    g.template_df = g.infl_templ_df.loc[
        int(row_start):int(row_end),
        col_start:col_end
    ]

    #rename template
    g.template_df.name = f"{g.inflection_name}"

    # reset template index
    g.template_df.reset_index(drop=True, inplace=True)

    # remove template inflection name
    g.template_df.iloc[0, 0] = ""
    

def convert_template_df_to_datalist(g: GlobalVars):
    """Convert dataframe to nested list.
    table   [
    row         [ [cell], [cell], ... ],
    row         [ [cell], [cell], ... ], 
            ]
    """

    g.data_list = []
    for row_no, data in g.template_df.iterrows():
        row = data.to_list()
        
        new_row = []
        for cell in row:
            cell = cell.split("\n")
            if len(cell) > 1:
                cell = pali_list_sorter(cell)
            new_row.append(cell)

        g.data_list += [new_row]


def make_inflection_template(g: GlobalVars):
    """Make an InflectionTemplates and add to db_session"""

    g.infl_templ = InflectionTemplates(
        pattern=g.inflection_name,
        like=g.like
    )
    g.infl_templ.inflection_template_pack(g.data_list)
    
    g.added_templates.append(g.infl_templ.pattern)


def add_to_db(g: GlobalVars):
    """
    Add the template to the database if 
    1. changed or 
    2. does not exist,
    and update changed_templates pickle.
    """

    template_in_db = g.db_session \
        .query(InflectionTemplates) \
        .filter(InflectionTemplates.pattern == g.inflection_name) \
        .first()

    # added
    if not template_in_db:
        p_green_title(f"{g.inflection_name} added")
        g.db_session.add(g.infl_templ) 
        g.changed_templates.append(g.inflection_name)
    
    # updated
    else:
        if (
            template_in_db.pattern != g.infl_templ.pattern
            or template_in_db.like != g.infl_templ.like
            or template_in_db.data != g.infl_templ.data
        ):
            p_green_title(f"{g.inflection_name} updated")
            g.db_session.delete(template_in_db)
            g.db_session.add(g.infl_templ) 
            g.changed_templates.append(g.inflection_name)


def test_deleted_templates(g: GlobalVars):
    """
    Test if there are extra templates in the db
    and delete them.
    """

    db_templates = g.db_session.query(InflectionTemplates).all()
    for t in db_templates:
        if t.pattern not in g.added_templates:
            p_green_title(f"{t.pattern} deleted")
            g.db_session.delete(t)
            g.changed_templates.append(t.pattern)


def save_changed_templates(g: GlobalVars):
    """Save changed templates to pickle."""

    with open(g.pth.template_changed_path, "wb") as f:
        pickle.dump(g.changed_templates, f)

    # save to db_info tables
    changed_templates_list = g.db_session.query(DbInfo) \
        .filter_by(key="changed_templates_list") \
        .first()
    if not changed_templates_list:
        changed_templates_list = DbInfo(key="changed_templates_list")
    changed_templates_list.value_pack(g.changed_templates)
    g.db_session.add(changed_templates_list)


def main():
    tic()
    p_title("create inflection templates")
    g = GlobalVars()

    # make the dataframes
    make_index_dataframe(g)
    make_infl_templ_dataframe(g)

    # process all items in index_df
    for g.index_row, g.index_data in g.index_df.iterrows():
        extract_template_df(g)
        convert_template_df_to_datalist(g)
        make_inflection_template(g)
        add_to_db(g)

    # save and close
    test_deleted_templates(g)
    save_changed_templates(g)
    g.db_session.commit()
    g.db_session.close()

    toc()


if __name__ == "__main__":
    main()

