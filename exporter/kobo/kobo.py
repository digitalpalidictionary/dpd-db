#!/usr/bin/env python3

"""Export simplified DPD data for Kobo Reader"""

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_green_title, p_red, p_title, p_white, p_yes
from tools.tic_toc import tic, toc
from tools.headwords_clean_set import make_clean_headwords_set
from tools.tsv_read_write import read_tsv
from tools.uposatha_day import uposatha_today
from exporter.goldendict.helpers import TODAY

from pathlib import Path
from tools.goldendict_exporter import DictEntry, DictInfo
from tools.kobo_exporter import export_to_kobo_with_pyglossary, DictVariablesKobo


pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
dict_data: list[DictEntry] = []


def compile_dict_data():
    p_green_title("compiling dict data")
    db = db_session.query(DpdHeadwords).all()
    db = sorted(db, key=lambda x: pali_sort_key(x.lemma_1))
    db_len = len(db)
    for count, i in enumerate(db):
        html = "<html>"
        html += f"{i.pos}. "
        if i.plus_case:
            html += f"({i.plus_case}) "
        html += f"{i.meaning_combo_html}. "
        html += f"[{i.construction_summary}] "
        html += f"{i.degree_of_completion_html}"

        dict_entry = DictEntry(
            word = i.lemma_1,
            definition_html = html,
            definition_plain = "",
            synonyms = i.inflections_list)
        dict_data.append(dict_entry)

        if count % 5000 == 0:
            p_counter(count, db_len, i.lemma_1)


def main():
    """Export DPD for Kobo Reader"""
    tic()
    p_title("exporting dpd for kob")
    compile_dict_data()
    
    dict_info = DictInfo(
        bookname = "DPD for Kobo",
        author = "Bodhirasa Bhikkhu",
        description = "A light version of DPD for Kobo",
        website = "www.dpdict.net",
        source_lang = "pi",
        target_lang = "en"
    )

    dict_vars = DictVariablesKobo(
        kobo_path = Path("exporter/share/"),
        dict_name= "dpd-kobo",
    )

    export_to_kobo_with_pyglossary(
        dict_info, dict_vars, dict_data)

    toc()
        
if __name__ == "__main__":
    main()

