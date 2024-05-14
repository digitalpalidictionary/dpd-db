#!/usr/bin/env python3

"""Export DPD for GoldenDict and MDict."""

import csv
from pathlib import Path
import pickle
import shutil

from rich import print
from sqlalchemy.orm import Session
from typing import List

from export_dpd import generate_dpd_html
from export_roots import generate_root_html
from export_epd import generate_epd_html
from export_variant_spelling import generate_variant_spelling_html
from export_help import generate_help_html

from helpers import make_roots_count_dict

from db.get_db_session import get_db_session
from exporter.ru_components.tools.paths_ru import RuPaths
from tools.cache_load import load_cf_set, load_idioms_set
from tools.configger import config_read, config_test
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter2 import export_to_mdict
from tools.paths import ProjectPaths
from tools.printer import p_green_title
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.tic_toc import tic, toc, bip, bop
from tools.utils import RenderedSizes, sum_rendered_sizes

from exporter.ru_components.tools.tools_for_ru_exporter import \
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
        self.dps_data: bool = False
        if config_test("dictionary", "show_dps_data", "yes"):
            self.dps_data: bool = True
        
        # language
        if config_test("exporter", "language", "en"):
            self.lang = "en"
        elif config_test("exporter", "language", "ru"):
            self.lang = "ru"
        # add another lang here "elif ..." and 
        # add conditions if lang = "{your_language}" in every instance in the code.
        else:
            raise ValueError("Invalid language parameter")
        
        # paths
        if self.lang == "en":
            self.paths = self.pth
        elif self.lang == "ru":
            self.paths = self.rupth
        

def main():
    tic()
    print("[bright_yellow]exporting dpd to goldendict and mdict")
    
    if not config_test("exporter", "make_dpd", "yes"):
        print("[green]disabled in config.ini")
        toc()
        return
    
    g = ProgData()
    
    dpd_data_list, sizes = generate_dpd_html(
        g.db_session, g.pth, g.rupth, g.sandhi_contractions, g.cf_set, g.idioms_set, g.make_link, g.dps_data, g.lang, g.data_limit)
    g.rendered_sizes.append(sizes)

    root_data_list, sizes = generate_root_html(g.db_session, g.pth, g.roots_count_dict, g.rupth, g.lang, g.dps_data)
    g.rendered_sizes.append(sizes)

    variant_spelling_data_list, sizes = generate_variant_spelling_html(g.pth, g.rupth, g.lang)
    g.rendered_sizes.append(sizes)

    epd_data_list, sizes = generate_epd_html(g.db_session, g.pth, g.rupth, g.make_link, g.dps_data, g.lang)
    g.rendered_sizes.append(sizes)
    
    help_data_list, sizes = generate_help_html(g.db_session, g.pth, g.rupth, g.lang, g.dps_data)
    g.rendered_sizes.append(sizes)

    g.db_session.close()

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

    # FIXME delete once done
    # copy_css_js_to_temp_dir()

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

    # FIXME
    dict_name="dpd-test"

    if g.lang == "ru":
        dict_info.bookname = mdict_ru_title
        dict_info.author = "Bodhirasa, переведено Devamitta"
        dict_info.description = mdict_ru_description
        dict_info.website = "https://digitalpalidictionary.github.io/rus"
        dict_info.source_lang = "pi"
        dict_info.target_lang = "ru"
        dict_name = "ru-dpd"
    
    # FIXME add all the js to paths

    dict_var = DictVariables(
        css_path=g.paths.dpd_css_path,
        js_paths=[
            g.paths.family_compound_json,
            Path("exporter/goldendict/javascript/family_compound_template.js"),
            g.paths.family_idiom_json,
            Path("exporter/goldendict/javascript/family_idiom_template.js"),
            g.paths.family_root_json,
            Path("exporter/goldendict/javascript/family_root_template.js"),
            g.paths.family_set_json,
            Path("exporter/goldendict/javascript/family_set_template.js"),
            g.paths.family_word_json,
            Path("exporter/goldendict/javascript/family_word_template.js"),
            Path("exporter/goldendict/javascript/feedback_template.js"),
            Path("exporter/goldendict/javascript/main.js"),
        ],
        output_path=g.paths.share_dir,
        dict_name=dict_name,
        icon_path=g.paths.icon_path
    )

    export_to_goldendict_with_pyglossary(dict_info, dict_var, g.dict_data)

    if g.make_mdict:
        export_to_mdict(dict_info, dict_var, g.dict_data)


def write_size_dict(pth: ProjectPaths, size_dict):
    bip()
    print("[green]writing size_dict", end=" ")
    filename = pth.temp_dir.joinpath("size_dict.tsv")

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        for key, value in size_dict.items():
            writer.writerow([key, value])

    print(f"{bop():>37}")


def write_limited_datalist(g: ProgData):
    """A limited dataset for troubleshooting purposes"""

    limited_data = [
        item for item in g.dict_data if item.word.startswith("ab")]

    with open("temp/limited_data_list", "wb") as file:
        pickle.dump(limited_data, file)


# FIXME delete once done
def copy_css_js_to_temp_dir():
    p_green_title("copy files to temp dir")
    files_to_copy = [
        "exporter/goldendict/css/dpd.css",
        "exporter/goldendict/javascript/family_compound_json.js",
        "exporter/goldendict/javascript/family_compound_template.js",
        "exporter/goldendict/javascript/family_idiom_json.js",
        "exporter/goldendict/javascript/family_idiom_template.js",
        "exporter/goldendict/javascript/family_root_json.js",
        "exporter/goldendict/javascript/family_root_template.js",
        "exporter/goldendict/javascript/family_set_json.js",
        "exporter/goldendict/javascript/family_set_template.js",
        "exporter/goldendict/javascript/family_word_json.js",
        "exporter/goldendict/javascript/family_word_template.js",
        "exporter/goldendict/javascript/feedback_template.js",
        "exporter/goldendict/javascript/main.js",
    ]
    
    destination_dir = "dpd_js_test"

    for file_path in files_to_copy:
        shutil.copy(file_path, destination_dir)
    
    # # goldendict
    # shutil.copytree(
    #     "exporter/share/dpd-test/",
    #     "dpd_js_test/goldendict",
    #     dirs_exist_ok=True)

    # # mdict
    # files_to_copy = [
    #     "exporter/share/dpd-test-mdict.mdx", 
    #     "exporter/share/dpd-test-mdict.mdd"
    # ]
    # destination_dir = "dpd_js_test/mdict"
    # for file_path in files_to_copy:
    #     shutil.copy(file_path, destination_dir)

    # destination_dir = "/home/bodhirasa/Documents/GoldenDict"
    # for file_path in files_to_copy:
    #     shutil.copy(file_path, destination_dir)

if __name__ == "__main__":
    main()
