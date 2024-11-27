#!/usr/bin/env python3

"""Export DPD for GoldenDict and MDict."""

import csv
import pickle

from sqlalchemy.orm import Session
from typing import List

from exporter.goldendict.export_dpd import generate_dpd_html
from exporter.goldendict.export_roots import generate_root_html
from exporter.goldendict.export_epd import generate_epd_html
from exporter.goldendict.export_variant_spelling import generate_variant_spelling_html
from exporter.goldendict.export_help import generate_help_html

from exporter.goldendict.helpers import make_roots_count_dict

from db.db_helpers import get_db_session
from exporter.goldendict.ru_components.tools.paths_ru import RuPaths
from tools.cache_load import load_cf_set, load_idioms_set
from tools.configger import config_read, config_test
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.paths import ProjectPaths
from tools.printer import p_green, p_green_title, p_title, p_yes
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.tic_toc import tic, toc
from tools.utils import RenderedSizes, sum_rendered_sizes

from exporter.goldendict.ru_components.tools.tools_for_ru_exporter import \
    mdict_ru_title, mdict_ru_description


class ProgData():
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.rupth = RuPaths()
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.sandhi_contractions = make_sandhi_contraction_dict(self.db_session)
        self.cf_set: set = load_cf_set()
        self.idioms_set: set = load_idioms_set()
        self.roots_count_dict = make_roots_count_dict(self.db_session)
        self.rendered_sizes: List[RenderedSizes] = []
        self.data_limit = int(config_read("dictionary", "data_limit") or "0")
        self.dict_data: list[DictEntry]

        # config tests
        self.make_mdict: bool = False
        if config_test("dictionary", "make_mdict", "yes"):
            self.make_mdict: bool = True
        self.make_link: bool = False
        if config_test("dictionary", "make_link", "yes"):
            self.make_link: bool = True
        self.show_sbs_data: bool = False
        self.show_ru_data: bool = False
        
        # language
        if config_test("exporter", "language", "en"):
            self.lang = "en"
        elif config_test("exporter", "language", "ru"):
            self.lang = "ru"
        # add another lang here "elif ..." and 
        # add conditions if lang = "{your_language}" in every instance in the code.
        else:
            raise ValueError("Invalid language parameter")

        if config_test("dictionary", "show_sbs_data", "yes") and self.lang == "en":
            self.show_sbs_data: bool = True

        if config_test("dictionary", "show_ru_data", "yes"):
            self.show_ru_data: bool = True
        
        # paths
        if self.lang == "en":
            self.paths = self.pth
        elif self.lang == "ru":
            self.paths = self.rupth
        

def main():
    tic()
    p_title("exporting dpd to goldendict and mdict")
    
    if not config_test("exporter", "make_dpd", "yes"):
        p_green_title("disabled in config.ini")
        toc()
        return
    
    g = ProgData()
    
    dpd_data_list, sizes = generate_dpd_html(
        g.db_session, g.pth, g.rupth, g.sandhi_contractions, g.cf_set, g.idioms_set, g.make_link, g.show_sbs_data, g.show_ru_data, g.lang, g.data_limit)
    g.rendered_sizes.append(sizes)

    if g.data_limit == 0:

        root_data_list, sizes = generate_root_html(g.db_session, g.pth, g.roots_count_dict, g.rupth, g.lang, g.show_ru_data)
        g.rendered_sizes.append(sizes)

        variant_spelling_data_list, sizes = generate_variant_spelling_html(g.pth, g.rupth, g.lang)
        g.rendered_sizes.append(sizes)

        epd_data_list, sizes = generate_epd_html(g.db_session, g.pth, g.rupth, g.make_link, g.show_ru_data, g.lang)
        g.rendered_sizes.append(sizes)
        
        help_data_list, sizes = generate_help_html(g.db_session, g.pth, g.rupth, g.lang, g.show_ru_data)
        g.rendered_sizes.append(sizes)

        g.db_session.close()
    
    else:
        root_data_list = []
        variant_spelling_data_list = []
        epd_data_list = []
        help_data_list = []

    g.dict_data = (
        dpd_data_list + 
        root_data_list +
        variant_spelling_data_list +
        epd_data_list +
        help_data_list
    )

    write_limited_datalist(g)
    write_size_dict(g.pth, sum_rendered_sizes(g.rendered_sizes))
    prepare_export_to_goldendict_mdict(g)

    toc()


def prepare_export_to_goldendict_mdict(g: ProgData) -> None:
    """Prepare info and variables for export."""

    description = """
    <p>Digital Pāḷi Dictionary by Bodhirasa</p>
    <p>For more information, please visit
    <a href=\"https://digitalpalidictionary.github.io\">
    the Digital Pāḷi Dictionary website</a></p>
    """

    dict_info = DictInfo(
        bookname="Digital Pāḷi Dictionary",
        author="Bodhirasa",
        description = description,
        website="https://digitalpalidictionary.github.io/",
        source_lang="pi",
        target_lang="en"
    )

    dict_name="dpd"

    if g.lang == "ru":
        dict_info.bookname = mdict_ru_title
        dict_info.author = "Bodhirasa, переведено Devamitta"
        dict_info.description = mdict_ru_description
        dict_info.website = "https://digitalpalidictionary.github.io/rus"
        dict_info.source_lang = "pi"
        dict_info.target_lang = "ru"
        dict_name = "ru-dpd"
    
    dict_var = DictVariables(
        css_path=g.paths.dpd_css_path,
        js_paths=[
            g.paths.family_compound_json,
            g.paths.family_compound_template_js,
            g.paths.family_idiom_json,
            g.paths.family_idiom_template_js,
            g.paths.family_root_json,
            g.paths.family_root_template_js,
            g.paths.family_set_json,
            g.paths.family_set_template_js,
            g.paths.family_word_json,
            g.paths.family_word_template_js,
            g.paths.feedback_template_js,
            g.paths.frequency_template_js,
            g.paths.main_js_path,
        ],
        gd_path=g.paths.share_dir,
        md_path=g.paths.share_dir,
        dict_name=dict_name,
        icon_path=g.paths.icon_path,
        zip_up=False,
        delete_original=False
    )   

    export_to_goldendict_with_pyglossary(
        dict_info, dict_var, g.dict_data,
        zip_synonyms=True,
        include_slob=False
    )

    if g.make_mdict and g.data_limit == 0:
        export_to_mdict(dict_info, dict_var, g.dict_data)


def write_size_dict(pth: ProjectPaths, size_dict):
    p_green("writing size_dict")
    filename = pth.temp_dir.joinpath("size_dict.tsv")

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        for key, value in size_dict.items():
            writer.writerow([key, value])

    p_yes("ok")


def write_limited_datalist(g: ProgData):
    """A limited dataset for troubleshooting purposes"""

    limited_data = [
        item for item in g.dict_data if item.word.startswith("ab")]

    with open("temp/limited_data_list", "wb") as file:
        pickle.dump(limited_data, file)


if __name__ == "__main__":
    main()
