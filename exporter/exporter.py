#!/usr/bin/env python3

"""Export DPD for GoldenDict and MDict."""

import argparse
import contextlib
import csv
import pickle
import zipfile

from os import popen
from rich import print
from sqlalchemy.orm import Session
from typing import ContextManager, Dict, Type

from export_dpd import generate_dpd_html
from export_epd import generate_epd_html
from export_help import generate_help_html
from export_roots import generate_root_html
from export_variant_spelling import generate_variant_spelling_html
from pyglossary_exporter import export_stardict_zip, Info

from helpers import make_roots_count_dict
from mdict_exporter import export_to_mdict

from db.get_db_session import get_db_session
from tools.paths import ProjectPaths as PTH
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.stop_watch import StopWatch, Tic, close_line
from tools.profiler import Profiler

db_session: Session = get_db_session(PTH.dpd_db_path)
SANDHI_CONTRACTIONS: dict = make_sandhi_contraction_dict(db_session)


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Exporter')
    parser.add_argument(
        '--profiling',
        required=False,
        action='store_true',
        help='Collect and print memory usage information in cost of execution time')
    return parser.parse_args()


def main() -> None:
    timer = StopWatch()

    print("[bright_yellow]exporting dpd")
    size_dict: Dict[str, int] = {}

    roots_count_dict = make_roots_count_dict(
        db_session)
    dpd_data_list, size_dict = generate_dpd_html(
        db_session, PTH, SANDHI_CONTRACTIONS, size_dict)
    root_data_list, size_dict = generate_root_html(
        db_session, PTH, roots_count_dict, size_dict)
    variant_spelling_data_list, size_dict = generate_variant_spelling_html(
        PTH, size_dict)
    epd_data_list, size_dict = generate_epd_html(
        db_session, PTH, size_dict)
    help_data_list, size_dict = generate_help_html(
        db_session, PTH, size_dict)
    db_session.close()

    # FIXME Some synonyms are empty str, is it OK?
    combined_data_list: list = (
        dpd_data_list +
        root_data_list +
        variant_spelling_data_list +
        epd_data_list +
        help_data_list
    )

    write_limited_datalist(combined_data_list)
    write_size_dict(size_dict)
    export_to_goldendict(combined_data_list)
    export_to_goldendict_orig(combined_data_list)
    goldendict_unzip_and_copy()
    export_to_mdict(combined_data_list, PTH)  # TODO Try to optimize

    close_line(timer)


# TODO Deprecate
def export_to_goldendict_orig(data_list: list) -> None:
    """generate goldedict zip"""
    tic = Tic('generating goldendict zip')

    ifo = ifo_from_opts(
        {"bookname": "DPD",
            "author": "Bodhirasa",
            "description": "",
            "website": "https://digitalpalidictionary.github.io/", }
    )

    export_words_as_stardict_zip(data_list, ifo, PTH.zip_path, PTH.icon_path)

    # add bmp icon for android
    with zipfile.ZipFile(PTH.zip_path, 'a') as zipf:
        source_path = PTH.icon_bmp_path
        destination = 'dpd/android.bmp'
        zipf.write(source_path, destination)

    tic.toc()


def export_to_goldendict(data_list: list) -> None:
    """generate goldedict zip"""

    info = Info(
        bookname='DPD',
        author='Bodhirasa',
        description='Digital Pāḷi Dictionary is a feature-rich Pāḷi dictionary',
        website='https://digitalpalidictionary.github.io/')

    with Tic('generating goldendict zip'):
        # FIXME
        dst = PTH.zip_path.with_stem('dpd_new')
        export_stardict_zip(
            data_list,
            destination=dst,
            info=info,
            icon_path=PTH.icon_path,
            android_icon_path=PTH.icon_bmp_path)


def goldendict_unzip_and_copy() -> None:
    """unzip and copy to goldendict folder"""

    with Tic('unipping and copying goldendict'):
        try:
            popen(f'unzip -o {PTH.zip_path} -d "/home/bhikkhu/Documents/Golden Dict"')
        except Exception as e:
            print(f"[red]{e}")


def write_size_dict(size_dict):
    tic = Tic("writing size_dict")
    filename = PTH.temp_dir.joinpath("size_dict.tsv")

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        for key, value in size_dict.items():
            writer.writerow([key, value])

    tic.toc()


def write_limited_datalist(combined_data_list):
    """A limited dataset for troubleshooting purposes"""

    limited_data_list = [
        item for item in combined_data_list if item["word"].startswith("ab")]

    with open("temp/limited_data_list", "wb") as file:
        pickle.dump(limited_data_list, file)


if __name__ == "__main__":
    args = get_args()

    Context: Type[ContextManager] = contextlib.nullcontext
    if args.profiling:
        Context = Profiler

    with Context():
        main()
