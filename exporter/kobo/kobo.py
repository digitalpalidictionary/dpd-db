#!/usr/bin/env python3

"""Export simplified DPD data for Kobo Reader"""
from jinja2 import Environment, FileSystemLoader

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green_title, p_title
from tools.tic_toc import tic, toc

from pathlib import Path
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.kobo_exporter import export_to_kobo_with_pyglossary, DictVariablesKobo


pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)
dict_data: list[DictEntry] = []
env = Environment(loader=FileSystemLoader("exporter/kobo/template"), autoescape=True)
template = env.get_template("/kobo.html")
with open("exporter/kobo/template/kobo.css") as f:
    css = f.read()


def compile_dict_data():
    p_green_title("compiling dict data")
    db = db_session.query(DpdHeadwords).all()
    db = sorted(db, key=lambda x: pali_sort_key(x.lemma_1))
    db_len = len(db)
    for count, i in enumerate(db):
        html = template.render(
            i=i,
            css=css
        )

        # # testing
        # with open("temp/kobo.html", "w") as f:
        #     f.write(html)
        # print(i.lemma_1)
        # input()

        dict_entry = DictEntry(
            word = i.lemma_1,
            definition_html = html,
            definition_plain = "",
            synonyms = i.inflections_list)
        dict_data.append(dict_entry)

        if count % 10000 == 0:
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
    )

    dict_var_gd = DictVariables(
        css_path = None, 
        js_paths = None, 
        gd_path = pth.share_dir, 
        md_path = pth.share_dir, 
        dict_name = "dpd-kobo", 
        icon_path = None, 
        zip_up = False,
        delete_original = False

    )

    export_to_kobo_with_pyglossary(
        dict_info, dict_vars, dict_data
    )
    
    export_to_goldendict_with_pyglossary(
        dict_info, dict_var_gd, dict_data
    )

    toc()
        
if __name__ == "__main__":
    main()

