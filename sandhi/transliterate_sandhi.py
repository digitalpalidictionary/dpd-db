#!/usr/bin/env python3

"""Transliterate deconstructor results using Aksharamukha and PathNirvana."""

import json

from rich import print
from typing import Dict
from aksharamukha import transliterate
from subprocess import check_output

from db.get_db_session import get_db_session
from db.models import Sandhi
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths as PTH

# !!! # only add new sandhi, leave the old ones alone


def main():
    tic()
    transliterate_sandhi()
    toc()


def transliterate_sandhi():
    print("[green]transliterating sandhi")

    db_session = get_db_session("dpd.db")
    sandhi_db = db_session.query(Sandhi).all()
    sandhi_translit_dict: Dict = {}

    # aksharamukha works much faster with large text files than smaller lists
    # sandhi_to_transliterate_string contains the words to translit,
    # and sandhi_index_dict contains the line numbers

    print("[green]creating string of sandhi to transliterate")
    sandhi_to_transliterate_string: str = ""
    sandhi_index_dict: dict = {}
    sandhi_for_json_dict: dict = {}
    counter: int = 0

    for counter, i in enumerate(sandhi_db):

        sandhi: str = i.sandhi
        sandhi_index_dict[counter] = i.sandhi
        sandhi_for_json_dict[i.sandhi] = {"sandhi": sandhi}
        sandhi_to_transliterate_string += f"{sandhi}\n"

    # saving json for path nirvana transliterator

    with open(PTH.sandhi_to_translit_path, "w") as f:
        f.write(json.dumps(
            sandhi_for_json_dict, ensure_ascii=False, indent=4))

    # transliterating with aksharamukha

    print("transliterating sinhala with aksharamukha")
    sinhala: str = transliterate.process(
        "IASTPali", "Sinhala", sandhi_to_transliterate_string,
        post_options=['SinhalaPali'])

    print("transliterating devanagari with aksharamukha")
    devanagari: str = transliterate.process(
        "IASTPali", "Devanagari", sandhi_to_transliterate_string)

    print("transliterating thai with aksharamukha")
    thai: str = transliterate.process(
        "IASTPali", "Thai", sandhi_to_transliterate_string)

    sinhala_lines: list = sinhala.split("\n")
    devanagari_lines: list = devanagari.split("\n")
    thai_lines: list = thai.split("\n")

    print("making sandhi dictionary")

    counter: int = 0
    for line in sinhala_lines[:-1]:
        headword: str = sandhi_index_dict[counter]
        sinhala_sandhi_set: set = set([line])
        sandhi_translit_dict[headword] = {
            "sinhala": sinhala_sandhi_set,
            "devanagari": set(), "thai": set()}
        counter += 1

    counter: int = 0
    for line in devanagari_lines[:-1]:
        headword: str = sandhi_index_dict[counter]
        devanagari_sandhi_set: set = set([line])
        sandhi_translit_dict[headword]["devanagari"] = devanagari_sandhi_set
        counter += 1

    counter: int = 0
    for line in thai_lines[:-1]:
        headword: str = sandhi_index_dict[counter]
        thai_sandhi_set: set = set([line])
        sandhi_translit_dict[headword]["thai"] = thai_sandhi_set
        counter += 1

    # path nirvana transliteration using node.js
    # pali-script.mjs produces different orthography from akshramusha

    print("running path nirvana node.js transliteration", end=" ")

    try:
        output = check_output([
            "node", "sandhi/transliterate_sandhi.mjs"])
        print(f"{output}")
    except Exception as e:
        print(f"[bright_red]{e}")

    # re-import path nirvana transliterations

    print("importing path nirvana translit", end=" ")

    with open(PTH.sandhi_from_translit_path, "r") as f:
        node_translit: dict = json.load(f)
        print(f"{len(node_translit)}")

    counter: int = 0

    for headword in node_translit:
        sandhi_translit_dict[headword]["sinhala"].update(
            set(node_translit[headword]["sinhala"]))

        sandhi_translit_dict[headword]["devanagari"].update(
            set(node_translit[headword]["devanagari"]))

        sandhi_translit_dict[headword]["thai"].update(
            set(node_translit[headword]["thai"]))
        counter += 1

    # write back into database

    print("writing to db")

    for i in sandhi_db:
        if i.sandhi in sandhi_translit_dict:

            i.sinhala = ",".join(
                list(sandhi_translit_dict[i.sandhi]["sinhala"]))

            i.devanagari = ",".join(
                list(sandhi_translit_dict[i.sandhi]["devanagari"]))

            i.thai = ",".join(
                list(sandhi_translit_dict[i.sandhi]["thai"]))

    db_session.commit()
    db_session.close()


if __name__ == "__main__":
    main()
