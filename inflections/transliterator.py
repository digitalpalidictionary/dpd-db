#!/usr/bin/env python3.10
# coding: utf-8

import re
import sqlite3
import json
import pickle
import csv

from rich import print
from sorter import sort_key
from tqdm import tqdm
from db.db_helpers import get_db_session
from db.models import PaliWord, PaliRoot
from typing import Tuple, List, Dict
from pathlib import Path
from aksharamukha import transliterate
from subprocess import check_output

regenerate_all = False

dpd_db_path = Path("dpd.db")
db_session = get_db_session(dpd_db_path)
dpd_db = db_session.query(PaliWord).all()

with open("share/changed_headwords", "rb") as f:
    changed_headwords: list = pickle.load(f)

with open("share/changed_patterns", "rb") as f:
    changed_patterns:list = pickle.load(f)

translit_dict: Dict = {}

# !!!!!!!!!!!!!!!!!!!!!!!!!
# add sandhi dict too
# !!!!!!!!!!!!!!!!!!!!!!!!!

def main():
    print("[yellow] transliterating inflections")

    # aksharamukha works much faster with large text files than smaller lists
    # inflections_to_transliterate_string contains the inflections,
    # and inflections_key_dict contains the line numbers

    print("[green] creating string of inflections to transliterate")
    inflections_to_transliterate_string: str = ""
    inflections_key_dict: dict = {}
    inflections_for_json_dict: dict = {}
    counter: int = 0
    
    for i in tqdm(dpd_db):
        test1 = i.pattern in changed_patterns
        test2 = i.pali_1 in changed_headwords
        test3 = regenerate_all == True

        if test1 or test2 or test3 :
            inflections:list = json.loads(i.inflections)
            inflections_key_dict[counter] = i.pali_1
            inflections_for_json_dict[i.pali_1] = {"inflections": inflections}

            # inflections_to_transliterate_string += (f"{i.pali_1}\t")
            for inflection in inflections:
                inflections_to_transliterate_string += f"{inflection},"
            inflections_to_transliterate_string += f"\n"
            counter += 1
    
    # saving json for path nirvana transliterator
    
    with open("share/inflections_to_translit.json", "w") as f:
        f.write(json.dumps(
        inflections_for_json_dict, ensure_ascii=False, indent=4))

    # transliterating with aksharamukha

    print("[green] translitering sinhala with aksharamukha")
    sinhala : str = transliterate.process(
        "IASTPali", "Sinhala", inflections_to_transliterate_string, post_options=['SinhalaPali'])
    
    print("[green] translitering devanagari with aksharamukha")
    devanagari : str = transliterate.process(
        "IASTPali", "Devanagari", inflections_to_transliterate_string)

    print("[green] translitering thai with aksharamukha")
    thai: str = transliterate.process(
        "IASTPali", "Thai", inflections_to_transliterate_string)
    
    sinhala_lines: list = sinhala.split("\n")
    devanagari_lines: list = devanagari.split("\n")
    thai_lines: list = thai.split("\n")

    print("[green] making inflections dictionary")

    counter: int = 0
    for line in sinhala_lines[:-1]:
        headword:str = inflections_key_dict[counter]
        sinhala_inflections_set: set = set(line.split(","))
        sinhala_inflections_set.remove('')
        translit_dict[headword] = {
            "sinhala": sinhala_inflections_set, "devanagari": set(), "thai": set()}
        counter += 1

    counter: int = 0
    for line in devanagari_lines[:-1]:
        headword: str = inflections_key_dict[counter]
        devanagari_inflections_set: set = set(line.split(","))
        devanagari_inflections_set.remove('')
        translit_dict[headword]["devanagari"] = devanagari_inflections_set
        counter += 1

    counter: int = 0
    for line in thai_lines[:-1]:
        headword: str = inflections_key_dict[counter]
        thai_inflections_set: set = set(line.split(","))
        thai_inflections_set.remove('')
        translit_dict[headword]["thai"] = thai_inflections_set
        counter += 1
    

    # path nirvana transliteration using node.js
    # pali-script.mjs produces different orthography from akshramusha

    print(f"[green]running path nirvana node.js transliteration", end=" ")

    try:
        output = check_output(["node", "inflections/transliterate inflections.mjs"])
        print(f"[green]{output}")
    except Exception as e:
        print(f"[red]{e}")

    # re-import path nirvana transliterations
    
    print(f"[green]importing path nirvana inflections", end=" ")

    with open("share/inflections_from_translit.json", "r") as f:
            new_inflections: dict = json.load(f)
            print(f"{len(new_inflections)}")

    counter: int = 0
    sinhala_count: int = 0
    devanagari_count = 0
    thai_count: int = 0
    length: int = len(new_inflections)

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

    print("[green] writing to database")

    for i in dpd_db:
        if i.pali_1 in translit_dict:
            
            i.inflections_sinhala = json.dumps(
                list(translit_dict[i.pali_1]["sinhala"]), ensure_ascii=False)
            i.inflections_devanagari = json.dumps(
                list(translit_dict[i.pali_1]["devanagari"]), ensure_ascii=False)
            i.inflections_thai = json.dumps(
                list(translit_dict[i.pali_1]["thai"]), ensure_ascii=False)

    db_session.commit()
    db_session.close()

if __name__ == "__main__":
    main()
