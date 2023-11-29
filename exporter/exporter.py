#!/usr/bin/env python3

"""Export DPD for GoldenDict and MDict."""

from typing import List
import zipfile
import csv
import pickle

from subprocess import Popen, PIPE
from pathlib import Path
from rich import print
from sqlalchemy.orm import Session

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
from tools.utils import RenderedSizes, sum_rendered_sizes
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

    rendered_sizes: List[RenderedSizes] = []

    # check config
    if config_test("dictionary", "make_mdict", "yes"):
        make_mdct: bool = True
    else:
        make_mdct: bool = False

    time_log.log("make_roots_count_dict()")
    roots_count_dict = make_roots_count_dict(db_session)

    time_log.log("generate_dpd_html()")
    dpd_data_list, sizes = generate_dpd_html(db_session, pth, sandhi_contractions, cf_set)
    rendered_sizes.append(sizes)

    time_log.log("generate_root_html()")
    root_data_list, sizes = generate_root_html(db_session, pth, roots_count_dict)
    rendered_sizes.append(sizes)

    time_log.log("generate_variant_spelling_html()")
    variant_spelling_data_list, sizes = generate_variant_spelling_html(pth)
    rendered_sizes.append(sizes)

    time_log.log("generate_epd_html()")
    epd_data_list, sizes = generate_epd_html(db_session, pth)
    rendered_sizes.append(sizes)

    time_log.log("generate_help_html()")
    help_data_list, sizes = generate_help_html(db_session, pth)
    rendered_sizes.append(sizes)

    db_session.close()

    combined_data_list: list = (
        dpd_data_list +
        root_data_list +
        variant_spelling_data_list +
        epd_data_list +
        help_data_list
    )

    time_log.log("write_limited_datalist()")
    write_limited_datalist(combined_data_list)

    time_log.log("write_size_dict()")
    write_size_dict(pth, sum_rendered_sizes(rendered_sizes))

    time_log.log("export_to_goldendict()")
    export_to_goldendict(pth, combined_data_list)

    time_log.log("goldendict_unzip_and_copy()")
    goldendict_unzip_and_copy(pth)

    if make_mdct is True:
        time_log.log("export_to_mdict()")
        export_to_mdict(combined_data_list, pth)

    toc()
    time_log.log("exporter.py::main() return")


def export_to_goldendict(pth: ProjectPaths, data_list: list) -> None:
    """generate goldedict zip"""
    bip()

    print("[green]generating goldendict zip", end=" ")

    ifo = ifo_from_opts(
        {"bookname": "DPD",
            "author": "Bodhirasa",
            "description": "",
            "website": "https://digitalpalidictionary.github.io/", }
    )

    export_words_as_stardict_zip(data_list, ifo, pth.dpd_zip_path, pth.icon_path)

    # add bmp icon for android
    with zipfile.ZipFile(pth.dpd_zip_path, 'a') as zipf:
        source_path = pth.icon_bmp_path
        destination = 'dpd/android.bmp'
        zipf.write(source_path, destination)

    print(f"{bop():>29}")


def goldendict_unzip_and_copy(pth: ProjectPaths) -> None:
    """unzip and copy to goldendict folder"""

    goldendict_path: (Path |str) = goldedict_path()

    bip()

    if goldendict_path and goldendict_path.exists():
        try:
            with Popen(f'unzip -o {pth.dpd_zip_path} -d "{goldendict_path}"', shell=True, stdout=PIPE, stderr=PIPE) as process:
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    print(f"[green]Unzipping and copying to [blue]{goldendict_path} [green]successful")
                else:
                    print("[red]Error during unzip and copy:")
                    print(f"Exit Code: {process.returncode}")
                    print(f"Standard Output: {stdout.decode('utf-8')}")
                    print(f"Standard Error: {stderr.decode('utf-8')}")
        except Exception as e:
            print(f"[red]Error during unzip and copy: {e}")
    else:
        print("[red]local GoldenDict directory not found")

    print(f"{bop():>23}")


def write_size_dict(pth: ProjectPaths, size_dict):
    bip()
    print("[green]writing size_dict", end=" ")
    filename = pth.temp_dir.joinpath("size_dict.tsv")

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
