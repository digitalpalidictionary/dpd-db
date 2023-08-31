#!/usr/bin/env python3

# TODO Make testcases
# TODO Switch to pyglossary_stardict

"""Export DPD for GoldenDict and MDict."""

import csv
import pickle
import pyglossary
import zipfile

from os import popen
from rich import print
from sqlalchemy.orm import Session

from export_dpd import generate_dpd_html
from export_roots import generate_root_html
from export_epd import generate_epd_html
from export_variant_spelling import generate_variant_spelling_html
from export_help import generate_help_html

from helpers import make_roots_count_dict
from mdict_exporter import export_to_mdict

from db.get_db_session import get_db_session
from tools.tic_toc import tic, toc
from tools.stop_watch import StopWatch
from tools.stardict import export_words_as_stardict_zip, ifo_from_opts
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.paths import ProjectPaths as PTH

tic()
db_session: Session = get_db_session(PTH.dpd_db_path)
SANDHI_CONTRACTIONS: dict = make_sandhi_contraction_dict(db_session)


def main() -> None:
    print("[bright_yellow]exporting dpd")
    size_dict = {}

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

    combined_data_list: list = (
        dpd_data_list +
        root_data_list +
        variant_spelling_data_list +
        epd_data_list +
        help_data_list
    )

    ## FIXME delete
    import yaml

    ## FIXME delete
    #with open('data.yaml', 'w') as f:
    #    yaml.dump(combined_data_list[0:100], stream=f)

    ## FIXME delete
    #with open('data.yaml', 'r') as f:
    #    combined_data_list = yaml.safe_load(f)

    write_limited_datalist(combined_data_list)
    write_size_dict(size_dict)
    export_to_goldendict(combined_data_list)
    goldendict_unzip_and_copy()
    export_to_mdict(combined_data_list, PTH)
    toc()


def export_to_goldendict(data_list: list) -> None:
    """generate goldedict zip"""

    with StopWatch() as timer:
        print("[green]generating goldendict zip", end=" ")

        # TODO Try empty fields for self-documentatnion
        """
        bookname=Digital Pāli Dictionary
        wordcount=36893
        synwordcount=1727042
        idxfilesize=747969
        idxoffsetbits=32
        author=Digital Pāli Tools <digitalpalitools@gmail.com>
        website=https://github.com/digitalpalitools
        description=The next generation comprehensive Digital Pāli Dictionary.
        date=2021-10-31T08:56:25Z
        sametypesequence=h
        """

        info = {
            "bookname": "DPD",
            "author": "Bodhirasa",
            "description": "",
            "website": "https://digitalpalidictionary.github.io/",
        }

        pyglossary.Glossary.init()
        glossary = pyglossary.Glossary(info=info)

        for word in data_list:
            entry = glossary.newEntry(
                word=word['synonyms'],
                defi=word['definition_html'],
                defiFormat='h')
            glossary.addEntryObj(entry)

        glossary.write(filename=str(PTH.zip_path), format='Stardict')

        # TODO Speed comparizon 51 sec
        # TODO Size comparizon
        # TODO Icon
        # TODO Zip
        # TODO Purge tools/*stardict.py
        # TODO README dictd for dictzip
        # FIXME Giant syn file

        #export_words_as_stardict_zip(data_list, ifo, PTH.zip_path, PTH.icon_path)

        # add bmp icon for android
        #with zipfile.ZipFile(PTH.zip_path, 'a') as zipf:
        #    source_path = PTH.icon_bmp_path
        #    destination = 'dpd/android.bmp'
        #    zipf.write(source_path, destination)

    print(f"{timer:>29}")


def goldendict_unzip_and_copy() -> None:
    """unzip and copy to goldendict folder"""

    with StopWatch() as timer:
        print("[green]unipping and copying goldendict", end=" ")
        try:
            popen(
                f'unzip -o {PTH.zip_path} '
                '-d "/home/bhikkhu/Documents/Golden Dict"')
        except Exception as e:
            print(f"[red]{e}")

    print(f"{timer:>23}")


def write_size_dict(size_dict):
    with StopWatch() as timer:
        print("[green]writing size_dict", end=" ")
        filename = PTH.temp_dir.joinpath("size_dict.tsv")

        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter='\t')
            for key, value in size_dict.items():
                writer.writerow([key, value])

    print(f"{timer:>38}")


def write_limited_datalist(combined_data_list):
    """A limited dataset for troubleshooting purposes"""

    limited_data_list = [
        item for item in combined_data_list if item["word"].startswith("ab")]

    with open("temp/limited_data_list", "wb") as file:
        pickle.dump(limited_data_list, file)


if __name__ == "__main__":
    main()
