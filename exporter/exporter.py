#!/usr/bin/env python3.11

from os import popen
from rich import print

from sqlalchemy.orm import Session

from export_dpd import generate_dpd_html
from export_roots import generate_root_html
from export_epd import generate_epd_html
from export_sandhi import generate_sandhi_html
from export_help import generate_help_html

from helpers import get_paths, ResourcePaths
from helpers import make_roots_count_dict

from db.get_db_session import get_db_session
from tools.timeis import tic, toc, bip, bop
from tools.stardict_nu import export_words_as_stardict_zip, ifo_from_opts
from mdict_exporter import export_to_mdict

tic()
PTH: ResourcePaths = get_paths()
DB_SESSION: Session = get_db_session("dpd.db")


def main():
    print("[bright_yellow]exporting dpd")
    roots_count_dict = make_roots_count_dict(DB_SESSION)

    dpd_data_list: list = generate_dpd_html(DB_SESSION, PTH)
    root_data_list: list = generate_root_html(
        DB_SESSION, PTH, roots_count_dict)
    sandhi_data_list: list = generate_sandhi_html(DB_SESSION, PTH)
    epd_data_list: list = generate_epd_html(DB_SESSION, PTH)
    help_data_list: list = generate_help_html(DB_SESSION, PTH)

    combined_data_list: list = (
        dpd_data_list +
        root_data_list +
        sandhi_data_list +
        epd_data_list +
        help_data_list
    )

    export_to_goldendict(combined_data_list)
    goldendict_unzip_and_copy()
    export_to_mdict(combined_data_list, PTH)

    DB_SESSION.close()
    toc()


def export_to_goldendict(data_list: list) -> None:
    """generate goldedict zip"""
    bip()

    print("[green]generating goldendict zip", end=" ")

    zip_path = PTH.zip_path

    ifo = ifo_from_opts(
        {"bookname": "DPDv2",
            "author": "Bodhirasa",
            "description": "",
            "website": "https://digitalpalidictionary.github.io/", }
    )

    export_words_as_stardict_zip(data_list, ifo, zip_path)

    print(f"{bop():>29}")


def goldendict_unzip_and_copy() -> None:
    """unzip and copy to goldendict folder"""

    bip()
    print("[green]unipping and copying goldendict", end=" ")
    popen(
        f'unzip -o {PTH.zip_path} -d "/home/bhikkhu/Documents/Golden Dict"')

    print(f"{bop():>23}")


if __name__ == "__main__":
    main()
