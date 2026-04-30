#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# coding: utf-8

"""Transliterate all Lookup table keys into Sinhala, Devanagari and Thai.
Either regenerate from scratch OR update missing entries.
Save into database.
"""

import json
from multiprocessing import Manager, Process
from multiprocessing.managers import ListProxy
from subprocess import check_output
from typing import TypedDict

import psutil
from aksharamukha import transliterate

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.configger import config_test, config_update
from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sinhala_tools import translit_ro_to_si
from tools.utils import list_into_batches


def _parse_batch(
    batch: list[Lookup],
    pth: ProjectPaths,
    regenerate_all: bool,
    results_list: ListProxy,
    batch_idx: int,
):
    # aksharamukha works much faster with large text files than smaller lists
    # lookup_to_transliterate_string contains the lookup_key,
    # and translit_index_dict contains the line numbers

    translit_dict: dict[str, WordInflections] = dict()

    lookup_to_transliterate_string: str = ""
    translit_index_dict: dict[int, str] = dict()
    lookup_for_json_dict: dict[str, dict[str, list[str]]] = dict()
    counter: int = 0

    for counter, i in enumerate(batch):
        if (
            not i.sinhala
            or regenerate_all
            and not is_another_value(i, "epd")  # dont transliterate pure english words
        ):
            lookup_key: str = i.lookup_key
            translit_index_dict[counter] = lookup_key
            if lookup_key:
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
            key: str = translit_index_dict[counter]
            sinhala_translit_set: set = set(line.split(","))
            # sinhala_translit_set.remove("")
            translit_dict[key] = WordInflections(
                sinhala=sinhala_translit_set,
                devanagari=set(),
                thai=set(),
            )

    for counter, line in enumerate(devanagari_lines[:-1]):
        if line:
            key: str = translit_index_dict[counter]
            devanagari_translit_set: set = set(line.split(","))
            # devanagari_translit_set.remove("")
            translit_dict[key]["devanagari"] = devanagari_translit_set

    for counter, line in enumerate(thai_lines[:-1]):
        if line:
            key: str = translit_index_dict[counter]
            thai_translit_set: set = set(line.split(","))
            # thai_translit_set.remove("")
            translit_dict[key]["thai"] = thai_translit_set

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
        pr.red(str(e))

    # re-import path nirvana transliterations

    with open(json_output_from_translit, "r") as f:
        new_translit: dict[str, WordInflections] = json.load(f)

    for key, values in new_translit.items():
        try:
            if values["sinhala"]:
                translit_dict[key]["sinhala"].update(set(new_translit[key]["sinhala"]))

                translit_dict[key]["devanagari"].update(
                    set(new_translit[key]["devanagari"])
                )

                translit_dict[key]["thai"].update(set(new_translit[key]["thai"]))
        except KeyError as error:
            pr.red(f"headword: {key}")
            pr.red(f"values: {values}")
            pr.red(f"error: {error}")

    results_list.append(translit_dict)

    json_input_for_translit.unlink()
    json_output_from_translit.unlink()


class WordInflections(TypedDict):
    sinhala: set
    devanagari: set
    thai: set


def main():
    pr.tic()
    pr.yellow_title("transliterating lookup table")
    pr.green_tmr("setting up db")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    lookup_db = db_session.query(Lookup).all()

    pr.yes("")
    pr.green_tmr("regenerate all")

    # check config
    if config_test("regenerate", "transliterations", "yes") or config_test(
        "regenerate", "db_rebuild", "yes"
    ):
        regenerate_all: bool = True
    else:
        regenerate_all: bool = False

    pr.yes(str(regenerate_all))

    pr.green_tmr("processing batches")

    num_logical_cores = psutil.cpu_count() or 1
    batches: list[list[Lookup]] = list_into_batches(lookup_db, num_logical_cores)

    processes: list[Process] = []
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

    results_translit_dict: list[dict[str, WordInflections]] = list(results_list)

    translit_dict: dict[str, WordInflections] = dict()

    for i in results_translit_dict:
        for k, v in i.items():
            translit_dict[k] = v

    pr.yes(len(translit_dict))

    # write back into database
    pr.green_tmr("writing to db")

    translit_counter = 0
    for i in lookup_db:
        if i.lookup_key in translit_dict:
            i.sinhala_pack(list(translit_dict[i.lookup_key]["sinhala"]))
            i.devanagari_pack(list(translit_dict[i.lookup_key]["devanagari"]))
            i.thai_pack(list(translit_dict[i.lookup_key]["thai"]))
            translit_counter += 1

    db_session.commit()
    db_session.close()

    pr.yes(translit_counter)

    # config update
    if regenerate_all:
        config_update("regenerate", "transliterations", "no")

    pr.toc()


if __name__ == "__main__":
    main()
