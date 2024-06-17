#!/usr/bin/env python3

"""Export Sinhala Version of DPD for GoldenDict and MDict."""

import pandas as pd

from aksharamukha import transliterate
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.date_and_time import year_month_day_dash
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables, export_to_goldendict_with_pyglossary
from tools.mdict_exporter2 import export_to_mdict
from tools.meaning_construction import make_meaning_html
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_green_title, p_red, p_title, p_yes


class ProgData():
    p_title("exporting dpd sinhala")
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.df = pd.read_excel("exporter/sinhala/dpd sinhala test 1.1.xlsx") # TODO add to paths
        self.df_length = len(self.df)
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.env = Environment(loader=FileSystemLoader('.'))
        self.template = self.env.get_template("exporter/sinhala/dpd_sinhala_template.html") # TODO add to paths


class SinhalaDataRow:
    def __init__(self, row):
        self.id: int = row[0]
        self.lemma_1: str = row[1]
        self.meaning: str = row[2]
        self.pos: str = row[4]
        self.pos_full: str = row[5]

    def __repr__(self) -> str:
        return f"{self.id}. {self.pos}. {self.lemma_1} {self.meaning}"


def main():
    p_green("initializing data sources")
    g = ProgData()
    error_list: list[str] = []
    dict_data: list[DictEntry] = []
    p_yes("ok")

    p_green_title("iterating over xlsx")
    for count, row in g.df.iterrows():
        s = SinhalaDataRow(row.to_list())
        matching_lemma = True

        sinhala_lemma_roman: str = transliterate.process(
            "Sinhala", "IASTPali", s.lemma_1) #type:ignore
        sinhala_lemma_roman = sinhala_lemma_roman \
            .replace("ĕ", "e") \
            .replace("ŏ", "o") \
            .replace("ü", "u")
        
        # get dpd entry

        dpd = g.db_session.query(DpdHeadwords) \
            .filter_by(id=s.id) \
            .first()
        
        if not dpd:
            # find missing headwords
            error_list.append(f"{s.id}: {sinhala_lemma_roman} != xxx")
        
        else:
            # find changed headwords

            if dpd.lemma_1 != sinhala_lemma_roman:
                # print(dpd.lemma_1)
                # print(sinhala_lemma_roman)
                # print()
                error_list.append(f"{s.id}: {s.lemma_1} {dpd.lemma_1}")
                matching_lemma = False

            # compile all the components for html
            english_meaning = make_meaning_html(dpd)
            date = year_month_day_dash()
            html = g.template.render(
                s=s,
                dpd=dpd,
                english_meaning=english_meaning,
                matching_lemma=matching_lemma,
                date=date)
            
            # compile synonyms
            synonyms = dpd.inflections_list # TODO remove this once finished testing ??
            synonyms.extend(dpd.inflections_sinhala_list) 
            synonyms.append(str(dpd.id))
            
            dict_entry = DictEntry(
                word = s.lemma_1,
                definition_html = html,
                definition_plain = "",
                synonyms = synonyms
            )

            dict_data.append(dict_entry)
        
        if count % 5000 == 0: # type: ignore
            p_counter(count, g.df_length, dpd.lemma_1) # type: ignore


    dict_info = DictInfo(
        bookname = "DPD Sinhala Test",
        author= "Bodhirasa",
        description = "DPD Sinhala Test",
        website = "https://digitalpalidictionary.github.io/",
        source_lang = "pi",
        target_lang = "si"
    )

    dict_var = DictVariables(
        css_path = Path("exporter/sinhala/dpd_sinhala.css"),
        js_paths = None,
        gd_path = g.pth.share_dir,
        md_path = g.pth.share_dir,
        dict_name = "dpd-sinhala-test",
        icon_path = None,
        zip_up = True,
        delete_original = True
    )

    export_to_goldendict_with_pyglossary(
        dict_info = dict_info,
        dict_var = dict_var,
        dict_data = dict_data,
        zip_synonyms = True
    )

    export_to_mdict(
        dict_info = dict_info,
        dict_var = dict_var,
        dict_data = dict_data,
        h3_header = True
    )

    p_red("errors:")
    for error in error_list:
        p_red(error)
    p_red(len(error_list))


if __name__ == "__main__":
    main()