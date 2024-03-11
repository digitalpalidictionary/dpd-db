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
from typing import Dict, List, TypedDict

import psutil
from multiprocessing.managers import ListProxy
from multiprocessing import Process, Manager

from db.get_db_session import get_db_session
from db.models import DpdHeadwords

from tools.configger import config_test
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from tools.utils import list_into_batches


def _parse_batch(
    batch: List[DpdHeadwords],
    pth: ProjectPaths,
    changed_headwords: list,
    changed_templates: list,
    regenerate_all: bool,
    results_list: ListProxy,
    batch_idx: int,
):
    # aksharamukha works much faster with large text files than smaller lists
    # inflections_to_transliterate_string contains the inflections,
    # and inflections_index_dict contains the line numbers

    # print("[green]creating string of inflections to transliterate")

    translit_dict: Dict[str, WordInflections] = dict()

    inflections_to_transliterate_string: str = ""
    inflections_index_dict: Dict[int, str] = dict()
    inflections_for_json_dict: Dict[str, Dict[str, list]] = dict()
    counter: int = 0

    for counter, i in enumerate(batch):
        test1 = i.pattern in changed_templates
        test2 = i.lemma_1 in changed_headwords

        if test1 or test2 or regenerate_all:
            inflections: list = i.inflections_list
            inflections_index_dict[counter] = i.lemma_1
            inflections_for_json_dict[i.lemma_1] = {"inflections": inflections}

            # inflections_to_transliterate_string += (f"{i.lemma_1}\t")
            for inflection in inflections:
                inflections_to_transliterate_string += f"{inflection},"
            inflections_to_transliterate_string += "\n"

        else:
            inflections_index_dict[counter] = i.lemma_1
            inflections_to_transliterate_string += "\n"

    # saving json for path nirvana transliterator

    json_input_for_translit = pth.inflections_to_translit_json_path.with_suffix(
        f".batch_{batch_idx}_input.json"
    )
    json_output_from_translit = pth.inflections_from_translit_json_path.with_suffix(
        f".batch_{batch_idx}_output.json"
    )

    with open(json_input_for_translit, "w") as f:
        f.write(json.dumps(inflections_for_json_dict, ensure_ascii=False, indent=4))

    # transliterating with aksharamukha

    # print("[green]transliterating sinhala with aksharamukha")

    sinhala: str = transliterate.process(
        "IASTPali",
        "Sinhala",
        inflections_to_transliterate_string,
        post_options=["SinhalaPali"],
    )  # type:ignore

    # print("[green]transliterating devanagari with aksharamukha")

    devanagari: str = transliterate.process(
        "IASTPali",
        "Devanagari",
        inflections_to_transliterate_string,
    )  # type:ignore

    # print("[green]transliterating thai with aksharamukha")

    thai: str = transliterate.process(
        "IASTPali",
        "Thai",
        inflections_to_transliterate_string,
    )  # type:ignore

    sinhala_lines: list = sinhala.split("\n")
    devanagari_lines: list = devanagari.split("\n")
    thai_lines: list = thai.split("\n")

    # print("[green]making inflections dictionary")

    for counter, line in enumerate(sinhala_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            sinhala_inflections_set: set = set(line.split(","))
            sinhala_inflections_set.remove("")
            translit_dict[headword] = WordInflections(
                sinhala=sinhala_inflections_set,
                devanagari=set(),
                thai=set(),
            )

    for counter, line in enumerate(devanagari_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            devanagari_inflections_set: set = set(line.split(","))
            devanagari_inflections_set.remove("")
            translit_dict[headword]["devanagari"] = devanagari_inflections_set

    for counter, line in enumerate(thai_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            thai_inflections_set: set = set(line.split(","))
            thai_inflections_set.remove("")
            translit_dict[headword]["thai"] = thai_inflections_set

    # path nirvana transliteration using node.js
    # pali-script.mjs produces different orthography from akshramusha

    # print("[green]running path nirvana node.js transliteration", end=" ")

    try:
        _ = check_output(
            [
                "node",
                "db/inflections/transliterate inflections.mjs",
                json_input_for_translit,
                json_output_from_translit,
            ]
        )
        # print(f"[green]{output}")
    except Exception as e:
        print(f"[bright_red]{e}")

    # re-import path nirvana transliterations

    # print("[green]importing path nirvana inflections", end=" ")

    with open(json_output_from_translit, "r") as f:
        new_inflections: Dict[str, WordInflections] = json.load(f)
        # print(f"{len(new_inflections)}")

    for headword, values in new_inflections.items():
        if values["sinhala"]:
            translit_dict[headword]["sinhala"].update(
                set(new_inflections[headword]["sinhala"])
            )

            translit_dict[headword]["devanagari"].update(
                set(new_inflections[headword]["devanagari"])
            )

            translit_dict[headword]["thai"].update(
                set(new_inflections[headword]["thai"])
            )

    results_list.append(translit_dict)

    json_input_for_translit.unlink()
    json_output_from_translit.unlink()


class WordInflections(TypedDict):
    sinhala: set
    devanagari: set
    thai: set


def main():
    """It's the main function."""

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadwords).all()

    with open(pth.changed_headwords_path, "rb") as f:
        changed_headwords: list = pickle.load(f)

    with open(pth.template_changed_path, "rb") as f:
        changed_templates: list = pickle.load(f)

    tic()
    print("[bright_yellow]transliterating inflections")

    # check config
    if config_test("regenerate", "transliterations", "yes") or config_test(
        "regenerate", "db_rebuild", "yes"
    ):
        regenerate_all: bool = True
    else:
        regenerate_all: bool = False

    print(f"[green]{'regenerate all':<20}[white]{regenerate_all:>10}")

    num_logical_cores = psutil.cpu_count()
    batches: List[List[DpdHeadwords]] = list_into_batches(dpd_db, num_logical_cores)

    processes: List[Process] = []
    manager = Manager()
    results_list: ListProxy = manager.list()

    for batch_idx, batch in enumerate(batches):
        p = Process(
            target=_parse_batch,
            args=(
                batch,
                pth,
                changed_headwords,
                changed_templates,
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

    # write back into database
    print(f"[green]{'writing to db':<20}", end="")


    translit_counter = 0
    for i in dpd_db:
        if i.lemma_1 in translit_dict:
            i.inflections_sinhala = ",".join(list(translit_dict[i.lemma_1]["sinhala"]))
            i.inflections_devanagari = ",".join(
                list(translit_dict[i.lemma_1]["devanagari"])
            )
            i.inflections_thai = ",".join(list(translit_dict[i.lemma_1]["thai"]))
            translit_counter += 1

    print(f"{translit_counter:>10,}")

    db_session.commit()
    db_session.close()

    toc()


if __name__ == "__main__":
    main()
