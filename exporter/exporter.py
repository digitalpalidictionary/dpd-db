#!/usr/bin/env python3.10

from os import popen
from rich import print

from sqlalchemy.orm import Session

from export_dpd import generate_dpd_html
from export_roots import generate_root_html
from export_epd import generate_epd_html
from export_sandhi import generate_sandhi_html
from export_help import generate_help_html

from helpers import get_paths, ResourcePaths

from db.get_db_session import get_db_session
from tools.timeis import tic, toc, bip, bop
from tools.stardict_nu import export_words_as_stardict_zip, ifo_from_opts

tic()
PTH: ResourcePaths = get_paths()
DB_SESSION: Session = get_db_session("dpd.db")


def main():
    print("[bright_yellow]exporting dpd")
    dpd_data_list: list = generate_dpd_html(DB_SESSION, PTH)
    root_data_list: list = generate_root_html(DB_SESSION, PTH)
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

    golden_dict_gen(combined_data_list)
    unzip_and_copy()

    DB_SESSION.close()
    toc()


def golden_dict_gen(data_list: list) -> None:
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


def unzip_and_copy() -> None:
    """unzip and copy to goldendict folder"""

    bip()
    print("[green]unipping and copying goldendict", end=" ")
    popen(
        f'unzip -o {PTH.zip_path} -d "/home/bhikkhu/Documents/Golden Dict"')

    print(f"{bop():>23}")


if __name__ == "__main__":
    main()
