import re
import csv
from rich import print
from json import loads
from db.models import DerivedData
from db.get_db_session import get_db_session

from functions.get_paths import get_paths, ResourcePaths
from tools.pali_text_files import cst_texts, sc_texts
from tools.clean_machine import clean_machine


def make_words_to_add_list(window, book: str) -> list:
    pth = get_paths()
    text_list = make_text_list(window, pth, book)
    sp_mistakes_list = make_sp_mistakes_list(pth)
    variant_list = make_variant_list(pth)
    sandhi_ok_list = make_sandhi_ok_list(pth)
    all_inflections_set = make_all_inflections_set()

    text_set = set(text_list) - set(sandhi_ok_list)
    text_set = text_set - set(sp_mistakes_list)
    text_set = text_set - set(variant_list)
    text_set = text_set - all_inflections_set
    text_list = sorted(text_set, key=text_list.index)
    print(f"words_to_add: {len(text_list)}")

    return text_list


def make_text_list(window, pth: ResourcePaths, book: str) -> list:
    text_list = []

    if book in cst_texts and book in sc_texts:
        for b in cst_texts[book]:
            filepath = pth.cst_texts_dir.joinpath(b)
            with open(filepath) as f:
                text_read = f.read()
                text_clean = clean_machine(text_read)
                text_list += text_clean.split()

        for b in sc_texts[book]:
            filepath = pth.sc_texts_dir.joinpath(b)
            with open(filepath) as f:
                text_read = f.read()
                text_read = re.sub("var P_HTM.+", "", text_read)
                text_read = re.sub("""P_HTM\\[\\d+\\]="\\*""", "", text_read)
                text_read = re.sub("""\\*\\*.+;""", "", text_read)
                text_read = re.sub("\n", " ", text_read)
                text_read = text_read.lower()
                text_clean = clean_machine(text_read)
                text_list += text_clean.split()

    else:
        window["messages"].update(
            f"{book} not found", text_color="red")

    print(f"text list: {len(text_list)}")
    return text_list


def make_sp_mistakes_list(pth):

    with open(pth.spelling_mistakes_path) as f:
        reader = csv.reader(f, delimiter="\t")
        sp_mistakes_list = [row[0] for row in reader]

    print(f"sp_mistakes_list: {len(sp_mistakes_list)}")
    return sp_mistakes_list


def make_variant_list(pth):
    with open(pth.variant_path) as f:
        reader = csv.reader(f, delimiter="\t")
        variant_list = [row[0] for row in reader]

    print(f"variant_list: {len(variant_list)}")
    return variant_list


def make_sandhi_ok_list(pth):
    with open(pth.sandhi_ok_path) as f:
        reader = csv.reader(f, delimiter="\t")
        sandhi_ok_list = [row[0] for row in reader]

    print(f"sandhi_ok_list: {len(sandhi_ok_list)}")
    return sandhi_ok_list


def make_all_inflections_set():

    db_session = get_db_session("dpd.db")

    inflections_db = db_session.query(
        DerivedData.inflections
    ).all()

    all_inflections_set = set()
    for i in inflections_db:
        all_inflections_set.update(loads(i.inflections))

    print(f"all_inflections_set: {len(all_inflections_set)}")
    return all_inflections_set
