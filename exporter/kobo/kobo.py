#!/usr/bin/env python3

"""Export simplified DPD data for Kobo Reader"""

from jinja2 import Environment, FileSystemLoader

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.cst_sc_text_sets import make_cst_text_set, make_sc_text_set
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green_title, p_title
from tools.tic_toc import tic, toc

from pathlib import Path
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.kobo_exporter import export_to_kobo_with_pyglossary, DictVariablesKobo

class GlobalData():

    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.dict_data: list[DictEntry] = []
        self.env = Environment(loader=FileSystemLoader("exporter/kobo/templates"), autoescape=True)
        self.dpd_template = self.env.get_template("/dpd_headword.html")
        self.lookup_template = self.env.get_template("/lookup.html")
        with open("exporter/kobo/templates/kobo.css") as f:
            self.css = f.read()
        self.word_set = self.make_word_set()
    
    def make_word_set(self):
        """limit the extent of the dictionary to an vinaya and sutta text set"""
        ebt_books = [
            "vin1", "vin2", "vin3", "vin4",
            "dn1", "dn2", "dn3",
            "mn1", "mn2", "mn3",
            "sn1", "sn2", "sn3", "sn4", "sn5",
            "an1", "an2", "an3", "an4", "an5",
            "an6", "an7", "an8", "an9", "an10", "an11",
            "kn1", "kn2", "kn3", "kn4", "kn5",
            "kn8", "kn9",
            ]
        cst_text_set = make_cst_text_set(self.pth, ebt_books)
        sc_text_set = make_sc_text_set(self.pth, ebt_books)
        return cst_text_set | sc_text_set


def compile_dict_data(g: GlobalData):
    p_green_title("compiling dict data")
    
    db = g.db_session.query(DpdHeadword).all()
    db = sorted(db, key=lambda x: pali_sort_key(x.lemma_1))
    db_len = len(db)
    for count, i in enumerate(db):
        html = g.dpd_template.render(
            i=i,
            css=g.css
        )

        dict_entry = DictEntry(
            word = i.lemma_1,
            definition_html = html,
            definition_plain = "",
            synonyms = i.inflections_list_all)
        g.dict_data.append(dict_entry)

        if count % 10000 == 0:
            p_counter(count, db_len, i.lemma_1)


def compile_lookup_data(g: GlobalData):
    p_green_title("compiling lookup data")
    
    db = g.db_session \
        .query(Lookup) \
        .filter(Lookup.lookup_key.in_(g.word_set)) \
        .all()
    db = sorted(db, key=lambda x: pali_sort_key(x.lookup_key))
    db_len = len(db)
    
    for count, i in enumerate(db):
        if (
            i.deconstructor
            or i.spelling
            or i.variant
        ):
            html = g.lookup_template.render(
                i=i,
                css=g.css
            )

            dict_entry = DictEntry(
                word = i.lookup_key,
                definition_html = html,
                definition_plain = "",
                synonyms = [i.lookup_key])
            g.dict_data.append(dict_entry)

        if count % 10000 == 0:
            p_counter(count, db_len, i.lookup_key)


def main():
    """Export DPD for Kobo Reader"""
    tic()
    p_title("exporting dpd for kobo")
    g = GlobalData()
    compile_dict_data(g)
    compile_lookup_data(g)
    
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
        gd_path = g.pth.share_dir, 
        md_path = g.pth.share_dir, 
        dict_name = "dpd-kobo", 
        icon_path = None, 
        zip_up = False,
        delete_original = False

    )

    export_to_kobo_with_pyglossary(
        dict_info, dict_vars, g.dict_data
    )
    
    export_to_goldendict_with_pyglossary(
        dict_info, dict_var_gd, g.dict_data
    )

    toc()
        
if __name__ == "__main__":
    main()
