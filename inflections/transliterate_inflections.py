#!/usr/bin/env python3.10
# coding: utf-8

import json
import pickle

from rich import print
from rich.progress import track
from typing import Dict
from pathlib import Path
from aksharamukha import transliterate
from subprocess import check_output

from db.db_helpers import get_db_session
from db.models import PaliWord, DerivedInflections
from tools.timeis import tic, toc

regenerate_all = True

dpd_db_path = Path("dpd.db")
db_session = get_db_session(dpd_db_path)
dpd_db = db_session.query(PaliWord).all()
derived_db = db_session.query(DerivedInflections).all()

with open("share/changed_headwords", "rb") as f:
    changed_headwords: list = pickle.load(f)

with open("share/changed_patterns", "rb") as f:
    changed_patterns: list = pickle.load(f)

translit_dict: Dict = {}


def main():
    tic()
    print("[bright_yellow]transliterating inflections")

    # aksharamukha works much faster with large text files than smaller lists
    # inflections_to_transliterate_string contains the inflections,
    # and inflections_index_dict contains the line numbers

    print("[green]creating string of inflections to transliterate")
    inflections_to_transliterate_string: str = ""
    inflections_index_dict: dict = {}
    inflections_for_json_dict: dict = {}
    counter: int = 0

    for i in track(dpd_db, description=""):
        test1 = i.pattern in changed_patterns
        test2 = i.pali_1 in changed_headwords
        test3 = regenerate_all

        if test1 or test2 or test3:
            find = db_session.query(DerivedInflections).filter(
                    DerivedInflections.pali_1 == i.pali_1).first()
            if not find:
                print(f"\t[red]{i.pali_1} not found")
            inflections: list = json.loads(find.inflections)
            inflections_index_dict[counter] = i.pali_1
            inflections_for_json_dict[i.pali_1] = {"inflections": inflections}

            # inflections_to_transliterate_string += (f"{i.pali_1}\t")
            for inflection in inflections:
                inflections_to_transliterate_string += f"{inflection},"
            inflections_to_transliterate_string += "\n"
            counter += 1

    # saving json for path nirvana transliterator

    with open("share/inflections_to_translit.json", "w") as f:
        f.write(json.dumps(
            inflections_for_json_dict, ensure_ascii=False, indent=4))

    # transliterating with aksharamukha

    print("[green]transliterating sinhala with aksharamukha")
    sinhala: str = transliterate.process(
        "IASTPali", "Sinhala", inflections_to_transliterate_string,
        post_options=['SinhalaPali'])

    print("[green]transliterating devanagari with aksharamukha")
    devanagari: str = transliterate.process(
        "IASTPali", "Devanagari", inflections_to_transliterate_string)

    print("[green]transliterating thai with aksharamukha")
    thai: str = transliterate.process(
        "IASTPali", "Thai", inflections_to_transliterate_string)

    sinhala_lines: list = sinhala.split("\n")
    devanagari_lines: list = devanagari.split("\n")
    thai_lines: list = thai.split("\n")

    print("[green]making inflections dictionary")

    counter: int = 0
    for line in sinhala_lines[:-1]:
        headword: str = inflections_index_dict[counter]
        sinhala_inflections_set: set = set(line.split(","))
        sinhala_inflections_set.remove('')
        translit_dict[headword] = {
            "sinhala": sinhala_inflections_set,
            "devanagari": set(), "thai": set()}
        counter += 1

    counter: int = 0
    for line in devanagari_lines[:-1]:
        headword: str = inflections_index_dict[counter]
        devanagari_inflections_set: set = set(line.split(","))
        devanagari_inflections_set.remove('')
        translit_dict[headword]["devanagari"] = devanagari_inflections_set
        counter += 1

    counter: int = 0
    for line in thai_lines[:-1]:
        headword: str = inflections_index_dict[counter]
        thai_inflections_set: set = set(line.split(","))
        thai_inflections_set.remove('')
        translit_dict[headword]["thai"] = thai_inflections_set
        counter += 1

    # path nirvana transliteration using node.js
    # pali-script.mjs produces different orthography from akshramusha

    print("[green]running path nirvana node.js transliteration", end=" ")

    try:
        output = check_output([
            "node", "inflections/transliterate inflections.mjs"])
        print(f"[green]{output}")
    except Exception as e:
        print(f"[bright_red]{e}")

    # re-import path nirvana transliterations

    print("[green]importing path nirvana inflections", end=" ")

    with open("share/inflections_from_translit.json", "r") as f:
        new_inflections: dict = json.load(f)
        print(f"{len(new_inflections)}")

    counter: int = 0
    # !!!!!!!!!!!!!!!!!!!!!!!
    # can delete these
    # !!!!!!!!!!!!!!!!!!!!!!!

    sinhala_count: int = 0
    devanagari_count = 0
    thai_count: int = 0

    for headword in new_inflections:
        translit_dict[headword]["sinhala"].update(
            set(new_inflections[headword]["sinhala"]))
        sinhala_count += 1

        translit_dict[headword]["devanagari"].update(
            set(new_inflections[headword]["devanagari"]))
        devanagari_count += 1

        translit_dict[headword]["thai"].update(
            set(new_inflections[headword]["thai"]))
        thai_count += 1
        counter += 1

    print(f"[green]sinhala: {sinhala_count}")
    print(f"[green]devanagari: {devanagari_count}")
    print(f"[green]thai: {thai_count}")

    # write back into database

    print("[green]writing to db")

    for i in derived_db:
        if i.pali_1 in translit_dict:

            i.sinhala = json.dumps(
                list(translit_dict[i.pali_1]["sinhala"]), ensure_ascii=False)
            i.devanagari = json.dumps(
                list(translit_dict[i.pali_1]["devanagari"]),
                ensure_ascii=False)
            i.thai = json.dumps(
                list(translit_dict[i.pali_1]["thai"]), ensure_ascii=False)

    db_session.commit()
    db_session.close()
    toc()


if __name__ == "__main__":
    main()
