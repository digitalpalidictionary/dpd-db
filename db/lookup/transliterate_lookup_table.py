#!/usr/bin/env python3
# coding: utf-8

"""Transliterate all Lookup table keys into Sinhala, Devanagari and Thai.
Either regenerate from scratch OR update missing entries.
Save into database.
"""


import json

from aksharamukha import transliterate
from subprocess import check_output
from typing import Dict, List, TypedDict

import psutil
from multiprocessing.managers import ListProxy
from multiprocessing import Process, Manager

from db.db_helpers import get_db_session
from db.models import Lookup

from tools.lookup_is_another_value import is_another_value 
from tools.configger import config_test, config_update
from tools.printer import p_green, p_red, p_title, p_yes
from tools.sinhala_tools import translit_ro_to_si
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from tools.utils import list_into_batches


def _parse_batch(
    batch: List[Lookup],
    pth: ProjectPaths,
    regenerate_all: bool,
    results_list: ListProxy,
    batch_idx: int,
):
    # aksharamukha works much faster with large text files than smaller lists
    # lookup_to_transliterate_string contains the lookup_key,
    # and translit_index_dict contains the line numbers

    translit_dict: Dict[str, WordInflections] = dict()

    lookup_to_transliterate_string: str = ""
    translit_index_dict: Dict[int, str] = dict()
    lookup_for_json_dict: dict[str, dict[str, list[str]]]= dict()
    counter: int = 0

    for counter, i in enumerate(batch):

        if (
            not i.sinhala
            or regenerate_all
            and not is_another_value(i, "epd")  # dont transliterate pure english words
        ):
            lookup_key: str = i.lookup_key
            translit_index_dict[counter] = lookup_key
            lookup_for_json_dict[lookup_key] = {"inflections": [lookup_key]}

            # lookup_to_transliterate_string += (f"{i.lemma_1}\t")
            # for inflection in lookup_key:
            lookup_to_transliterate_string += f"{lookup_key}\n"

        else:
            translit_index_dict[counter] = i.lookup_key
            lookup_to_transliterate_string += "\n"

    # saving json for path nirvana transliterator

    json_input_for_translit = pth.lookup_to_translit_path.with_suffix(
        f".batch_{batch_idx}_input.json"
    )
    json_output_from_translit = pth.lookup_from_translit_path.with_suffix(
        f".batch_{batch_idx}_output.json"
    )

    with open(json_input_for_translit, "w") as f:
        f.write(json.dumps(lookup_for_json_dict, ensure_ascii=False, indent=4))

    # transliterating with aksharamukha

    sinhala: str = translit_ro_to_si(lookup_to_transliterate_string)

    devanagari: str = transliterate.process(
        "IASTPali",
        "Devanagari",
        lookup_to_transliterate_string,
    )  # type:ignore

    thai: str = transliterate.process(
        "IASTPali",
        "Thai",
        lookup_to_transliterate_string,
    )  # type:ignore

    sinhala_lines: list = sinhala.split("\n")
    devanagari_lines: list = devanagari.split("\n")
    thai_lines: list = thai.split("\n")

    for counter, line in enumerate(sinhala_lines[:-1]):
        if line:
            headword: str = translit_index_dict[counter]
            sinhala_translit_set: set = set(line.split(","))
            # sinhala_translit_set.remove("")
            translit_dict[headword] = WordInflections(
                sinhala=sinhala_translit_set,
                devanagari=set(),
                thai=set(),
            )

    for counter, line in enumerate(devanagari_lines[:-1]):
        if line:
            headword: str = translit_index_dict[counter]
            devanagari_translit_set: set = set(line.split(","))
            # devanagari_translit_set.remove("")
            translit_dict[headword]["devanagari"] = devanagari_translit_set

    for counter, line in enumerate(thai_lines[:-1]):
        if line:
            headword: str = translit_index_dict[counter]
            thai_translit_set: set = set(line.split(","))
            # thai_translit_set.remove("")
            translit_dict[headword]["thai"] = thai_translit_set

    # path nirvana transliteration using node.js
    # pali-script.mjs produces different orthography from aksharamukha

    try:
        _ = check_output(
            [
                "node",
                "db/lookup/transliterate_lookup.mjs",
                json_input_for_translit,
                json_output_from_translit,
            ]
        )
    except Exception as e:
        p_red(e)

    # re-import path nirvana transliterations

    with open(json_output_from_translit, "r") as f:
        new_translit: Dict[str, WordInflections] = json.load(f)

    for headword, values in new_translit.items():
        try:
            if values["sinhala"]:
                translit_dict[headword]["sinhala"].update(
                    set(new_translit[headword]["sinhala"])
                )

                translit_dict[headword]["devanagari"].update(
                    set(new_translit[headword]["devanagari"])
                )

                translit_dict[headword]["thai"].update(
                    set(new_translit[headword]["thai"])
                )
        except KeyError as error:
            p_red(f"headword: {headword}")
            p_red(f"values: {values}")
            p_red(f"error: {error}")

    results_list.append(translit_dict)

    json_input_for_translit.unlink()
    json_output_from_translit.unlink()


class WordInflections(TypedDict):
    sinhala: set
    devanagari: set
    thai: set


def main():
    tic()
    p_title("transliterating lookup table")
    p_green("setting up db")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    lookup_db = db_session.query(Lookup).all()

    p_yes("")
    p_green("regenerate all")

    # check config
    if config_test("regenerate", "transliterations", "yes") or config_test(
        "regenerate", "db_rebuild", "yes"
    ):
        regenerate_all: bool = True
    else:
        regenerate_all: bool = False

    p_yes(str(regenerate_all))
    
    p_green("processing batches")

    num_logical_cores = psutil.cpu_count()
    batches: List[List[Lookup]] = list_into_batches(lookup_db, num_logical_cores)

    processes: List[Process] = []
    manager = Manager()
    results_list: ListProxy = manager.list()

    for batch_idx, batch in enumerate(batches):
        p = Process(
            target=_parse_batch,
            args=(
                batch,
                pth,
                regenerate_all,
                results_list,
                batch_idx,
            ),
        )

        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    results_translit_dict: List[Dict[str, WordInflections]] = list(results_list)

    translit_dict: Dict[str, WordInflections] = dict()
    

    for i in results_translit_dict:
        for k, v in i.items():
            translit_dict[k] = v

    p_yes(len(translit_dict))

    # write back into database
    p_green("writing to db")

    translit_counter = 0
    for i in lookup_db:
        if i.lookup_key in translit_dict:
            i.sinhala_pack(
                list(translit_dict[i.lookup_key]["sinhala"]))
            i.devanagari_pack(
                list(translit_dict[i.lookup_key]["devanagari"]))
            i.thai_pack(
                list(translit_dict[i.lookup_key]["thai"]))
            translit_counter += 1

    db_session.commit()
    db_session.close()

    p_yes(translit_counter)

    # config update
    if regenerate_all:
        config_update("regenerate", "transliterations", "no")

    toc()


if __name__ == "__main__":
    main()
