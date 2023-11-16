#!/usr/bin/env python3

"""Export DPD for GoldenDict and MDict."""

import zipfile
import csv
import pickle

from os import popen
from pathlib import Path
from rich import print
from sqlalchemy.orm import Session
from multiprocessing.managers import ListProxy
from multiprocessing import Manager

from export_dpd import generate_dpd_html
from export_roots import generate_root_html
from export_epd import generate_epd_html
from export_variant_spelling import generate_variant_spelling_html
from export_help import generate_help_html

from helpers import cf_set_gen, make_roots_count_dict
from mdict_exporter import export_to_mdict

from db.get_db_session import get_db_session
from tools.goldendict_path import goldedict_path
from tools.tic_toc import tic, toc, bip, bop
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.paths import ProjectPaths
from tools.configger import config_test
from tools.utils import RenderedSizes, default_rendered_sizes
from tools import time_log

tic()

def main():
    print("[bright_yellow]exporting dpd")

    time_log.start(start_new=True)
    time_log.log("exporter.py::main()")

    pth = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)
    sandhi_contractions = make_sandhi_contraction_dict(db_session)

    cf_set = cf_set_gen(pth)

    # check config
    if config_test("dictionary", "make_mdict", "yes"):
        make_mdct: bool = True
    else:
        make_mdct: bool = False

    manager = Manager()
    dpd_data_list: ListProxy = manager.list()
    rendered_sizes: ListProxy = manager.list()

    time_log.log("make_roots_count_dict()")
    roots_count_dict = make_roots_count_dict(db_session)

    time_log.log("generate_dpd_html()")
    generate_dpd_html(db_session, pth, sandhi_contractions, cf_set, dpd_data_list, rendered_sizes)

    time_log.log("generate_root_html()")
    generate_root_html(db_session, pth, roots_count_dict, dpd_data_list, rendered_sizes)

    time_log.log("generate_variant_spelling_html()")
    generate_variant_spelling_html(pth, dpd_data_list, rendered_sizes)

    time_log.log("generate_epd_html()")
    generate_epd_html(db_session, pth, dpd_data_list, rendered_sizes)

    time_log.log("generate_help_html()")
    generate_help_html(db_session, pth, dpd_data_list, rendered_sizes)

    db_session.close()

    time_log.log("write_limited_datalist()")
    write_limited_datalist(dpd_data_list)

    time_log.log("write_size_dict()")
    write_size_dict(pth, rendered_sizes)

    time_log.log("export_to_goldendict()")
    export_to_goldendict(pth, dpd_data_list)

    time_log.log("goldendict_unzip_and_copy()")
    goldendict_unzip_and_copy(pth)

    if make_mdct is True:
        time_log.log("export_to_mdict()")
        export_to_mdict(dpd_data_list, pth)

    toc()
    time_log.log("exporter.py::main() return")


def export_to_goldendict(pth: ProjectPaths, data_list: ListProxy) -> None:
    """generate goldedict zip"""
    bip()

    print("[green]generating goldendict zip", end=" ")

    ifo = ifo_from_opts(
        {"bookname": "DPD",
            "author": "Bodhirasa",
            "description": "",
            "website": "https://digitalpalidictionary.github.io/", }
    )

    export_words_as_stardict_zip(data_list, ifo, pth.zip_path, pth.icon_path)

    # add bmp icon for android
    with zipfile.ZipFile(pth.zip_path, 'a') as zipf:
        source_path = pth.icon_bmp_path
        destination = 'dpd/android.bmp'
        zipf.write(source_path, destination)

    print(f"{bop():>29}")


def goldendict_unzip_and_copy(pth: ProjectPaths,) -> None:
    """unzip and copy to goldendict folder"""

    goldendict_path: (Path |str) = goldedict_path()

    bip()

    if (
        goldendict_path and 
        goldendict_path.exists()
        ):
        print(f"[green]unzipping and copying to [blue]{goldendict_path}")
        popen(
            f'unzip -o {pth.zip_path} -d "{goldendict_path}"')
    else:
        print("[red]local GoldenDict directory not found")

    print(f"{bop():>23}")

def sum_rendered_sizes(sizes: ListProxy) -> RenderedSizes:
    res = default_rendered_sizes()
    for i in sizes:
        for k, v in i.items():
            res[k] += v
    return res

def write_size_dict(pth: ProjectPaths, rendered_sizes: ListProxy):
    bip()
    print("[green]writing size_dict", end=" ")
    filename = pth.temp_dir.joinpath("size_dict.tsv")

    size_dict = sum_rendered_sizes(rendered_sizes)

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        for key, value in size_dict.items():
            writer.writerow([key, value])

    print(f"{bop():>38}")


def write_limited_datalist(combined_data_list):
    """A limited dataset for troubleshooting purposes"""

    limited_data_list = [
        item for item in combined_data_list if item["word"].startswith("ab")]

    with open("temp/limited_data_list", "wb") as file:
        pickle.dump(limited_data_list, file)


if __name__ == "__main__":
    main()
