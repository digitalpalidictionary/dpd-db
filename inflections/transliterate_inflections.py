#!/usr/bin/env python3
# coding: utf-8

"""Transliterate all inflections into Sinhala, Devanagari and Thai.
- Regenerate from scratch OR
- Update if stem & pattern has changed or inflection template has changed.
Save into database.
"""


import json
import pickle

from aksharamukha import transliterate
from rich import print
from subprocess import check_output
from typing import Dict

from db.get_db_session import get_db_session
from db.models import PaliWord, DerivedData

from tools.configger import config_test, config_update
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths as PTH


db_session = get_db_session(PTH.dpd_db_path)
dpd_db = db_session.query(PaliWord).all()
dd1 = db_session.query(DerivedData).first()

with open(PTH.changed_headwords_path, "rb") as f:
    changed_headwords: list = pickle.load(f)

with open(PTH.template_changed_path, "rb") as f:
    changed_templates: list = pickle.load(f)

translit_dict: Dict = {}


def main():
    """It's the main function."""

    tic()
    print("[bright_yellow]transliterating inflections")

    # check config
    if config_test("regenerate", "transliterations", "yes"):
        regenerate_all: bool = True
    else:
        regenerate_all: bool = False

    print(f"[green]regenerate all [white]{regenerate_all}")

    # aksharamukha works much faster with large text files than smaller lists
    # inflections_to_transliterate_string contains the inflections,
    # and inflections_index_dict contains the line numbers

    print("[green]creating string of inflections to transliterate")
    inflections_to_transliterate_string: str = ""
    inflections_index_dict: dict = {}
    inflections_for_json_dict: dict = {}
    counter: int = 0

    for counter, i in enumerate(dpd_db):
        test1 = i.pattern in changed_templates
        test2 = i.pali_1 in changed_headwords
        test3 = regenerate_all

        if test1 or test2 or test3:
            inflections: list = i.dd.inflections_list
            inflections_index_dict[counter] = i.pali_1
            inflections_for_json_dict[i.pali_1] = {"inflections": inflections}

            # inflections_to_transliterate_string += (f"{i.pali_1}\t")
            for inflection in inflections:
                inflections_to_transliterate_string += f"{inflection},"
            inflections_to_transliterate_string += "\n"

        else:
            inflections_index_dict[counter] = i.pali_1
            inflections_to_transliterate_string += "\n"

    # saving json for path nirvana transliterator

    with open(PTH.inflections_to_translit_json_path, "w") as f:
        f.write(json.dumps(
            inflections_for_json_dict, ensure_ascii=False, indent=4))

    # transliterating with aksharamukha

    print("[green]transliterating sinhala with aksharamukha")
    sinhala: str = transliterate.process(
        "IASTPali",
        "Sinhala",
        inflections_to_transliterate_string,
        post_options=['SinhalaPali'],
    )

    print("[green]transliterating devanagari with aksharamukha")
    devanagari: str = transliterate.process(
        "IASTPali",
        "Devanagari",
        inflections_to_transliterate_string,
    )

    print("[green]transliterating thai with aksharamukha")
    thai: str = transliterate.process(
        "IASTPali",
        "Thai",
        inflections_to_transliterate_string,
    )

    sinhala_lines: list = sinhala.split("\n")
    devanagari_lines: list = devanagari.split("\n")
    thai_lines: list = thai.split("\n")

    print("[green]making inflections dictionary")

    for counter, line in enumerate(sinhala_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            sinhala_inflections_set: set = set(line.split(","))
            sinhala_inflections_set.remove('')
            translit_dict[headword] = {
                "sinhala": sinhala_inflections_set,
                "devanagari": set(), "thai": set()}

    for counter, line in enumerate(devanagari_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            devanagari_inflections_set: set = set(line.split(","))
            devanagari_inflections_set.remove('')
            translit_dict[headword]["devanagari"] = devanagari_inflections_set

    for counter, line in enumerate(thai_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            thai_inflections_set: set = set(line.split(","))
            thai_inflections_set.remove('')
            translit_dict[headword]["thai"] = thai_inflections_set

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

    with open(PTH.inflections_from_translit_json_path, "r") as f:
        new_inflections: dict = json.load(f)
        print(f"{len(new_inflections)}")

    for headword, values in new_inflections.items():
        if values["sinhala"]:

            translit_dict[headword]["sinhala"].update(
                set(new_inflections[headword]["sinhala"]))

            translit_dict[headword]["devanagari"].update(
                set(new_inflections[headword]["devanagari"]))

            translit_dict[headword]["thai"].update(
                set(new_inflections[headword]["thai"]))

    # write back into database
    print("[green]writing to db")

    for i in dpd_db:
        if i.pali_1 in translit_dict:

            i.dd.sinhala = ",".join(
                list(translit_dict[i.pali_1]["sinhala"]))
            i.dd.devanagari = ",".join(
                list(translit_dict[i.pali_1]["devanagari"]))
            i.dd.thai = ",".join(
                list(translit_dict[i.pali_1]["thai"]))

    db_session.commit()
    db_session.close()

    # config update
    config_update("regenerate", "transliterations", "no")

    toc()


if __name__ == "__main__":
    main()
