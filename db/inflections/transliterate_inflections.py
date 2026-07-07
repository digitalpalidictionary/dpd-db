#!/usr/bin/env python3
"""
Transliterate all inflections into Sinhala, Devanagari and Thai.
- Regenerate from scratch OR
- Update if stem & pattern has changed or inflection template has changed.
Save into database.
"""

import json
import pickle
from multiprocessing import Manager, Process
from multiprocessing.managers import ListProxy
from subprocess import check_output
from typing import TypedDict

import psutil
from aksharamukha import transliterate
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.sinhala_tools import translit_ro_to_si
from tools.utils import list_into_batches


class WordInflections(TypedDict):
    sinhala: set[str]
    devanagari: set[str]
    thai: set[str]


def _parse_batch(
    batch: list[DpdHeadword],
    pth: ProjectPaths,
    changed_headwords: list[str],
    changed_templates: list[str],
    regenerate_all: bool,
    results_list: ListProxy,
    batch_idx: int,
) -> None:
    """Transliterate one batch of headwords and append results to results_list."""
    # aksharamukha works much faster with large text files than smaller lists
    # inflections_to_transliterate_string contains the inflections,
    # and inflections_index_dict contains the line numbers

    translit_dict: dict[str, WordInflections] = dict()

    inflections_to_transliterate_string: str = ""
    inflections_index_dict: dict[int, str] = dict()
    inflections_for_json_dict: dict[str, dict[str, list[str]]] = dict()

    for counter, i in enumerate(batch):
        test1 = i.pattern in changed_templates
        test2 = i.lemma_1 in changed_headwords

        if test1 or test2 or regenerate_all:
            inflections: list[str] = i.inflections_list_all  # include api ca eva iti
            inflections_index_dict[counter] = i.lemma_1
            inflections_for_json_dict[i.lemma_1] = {"inflections": inflections}

            inflections_to_transliterate_string += (
                "".join(f"{inflection}," for inflection in inflections) + "\n"
            )

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

    with json_input_for_translit.open("w", encoding="utf-8") as f:
        json.dump(inflections_for_json_dict, f, ensure_ascii=False, indent=4)

    # transliterating with aksharamukha

    sinhala: str = translit_ro_to_si(inflections_to_transliterate_string)

    devanagari: str = transliterate.process(
        "IASTPali",
        "Devanagari",
        inflections_to_transliterate_string,
    )  # type:ignore

    thai: str = transliterate.process(
        "IASTPali",
        "Thai",
        inflections_to_transliterate_string,
    )  # type:ignore

    sinhala_lines: list[str] = sinhala.split("\n")
    devanagari_lines: list[str] = devanagari.split("\n")
    thai_lines: list[str] = thai.split("\n")

    for counter, line in enumerate(sinhala_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            sinhala_inflections_set: set[str] = set(line.split(","))
            sinhala_inflections_set.discard("")
            translit_dict[headword] = WordInflections(
                sinhala=sinhala_inflections_set,
                devanagari=set(),
                thai=set(),
            )

    for counter, line in enumerate(devanagari_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            devanagari_inflections_set: set[str] = set(line.split(","))
            devanagari_inflections_set.discard("")
            translit_dict[headword]["devanagari"] = devanagari_inflections_set

    for counter, line in enumerate(thai_lines[:-1]):
        if line:
            headword: str = inflections_index_dict[counter]
            thai_inflections_set: set[str] = set(line.split(","))
            thai_inflections_set.discard("")
            translit_dict[headword]["thai"] = thai_inflections_set

    # path nirvana transliteration using node.js
    # pali-script.mjs produces different orthography from akshramusha

    try:
        _ = check_output(
            [
                "node",
                "db/inflections/transliterate inflections.mjs",
                json_input_for_translit,
                json_output_from_translit,
            ]
        )
    except Exception as e:
        pr.red(str(e))

    # re-import path nirvana transliterations

    with json_output_from_translit.open(encoding="utf-8") as f:
        new_inflections: dict[str, WordInflections] = json.load(f)

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


def _write_translit_to_db(
    db_session: Session,
    dpd_db: list[DpdHeadword],
    translit_dict: dict[str, WordInflections],
) -> int:
    """Raw SQL executemany write-back, replacing the per-row ORM mutation loop."""
    rows: list[tuple[str, str, str, int]] = [
        (
            ",".join(translit_dict[i.lemma_1]["sinhala"]),
            ",".join(translit_dict[i.lemma_1]["devanagari"]),
            ",".join(translit_dict[i.lemma_1]["thai"]),
            i.id,
        )
        for i in dpd_db
        if i.lemma_1 in translit_dict
    ]
    if rows:
        db_session.connection().exec_driver_sql(
            "UPDATE dpd_headwords "
            "SET inflections_sinhala = ?, inflections_devanagari = ?, inflections_thai = ? "
            "WHERE id = ?",
            rows,
        )
    db_session.commit()
    return len(rows)


def main() -> None:
    """It's the main function."""

    pr.tic()
    pr.yellow_title("transliterating inflections")
    pr.green_tmr("setting up db")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()

    with pth.changed_headwords_path.open("rb") as f:
        changed_headwords: list[str] = pickle.load(f)

    with pth.template_changed_path.open("rb") as f:
        changed_templates: list[str] = pickle.load(f)

    pr.yes(len(dpd_db))

    pr.green_tmr("regenerate all")

    # check config
    if config_test("regenerate", "transliterations", "yes") or config_test(
        "regenerate", "db_rebuild", "yes"
    ):
        regenerate_all: bool = True
    else:
        regenerate_all: bool = False
    pr.yes(str(regenerate_all))

    pr.green_tmr("transliterating")

    num_logical_cores = psutil.cpu_count() or 1
    batches: list[list[DpdHeadword]] = list_into_batches(dpd_db, num_logical_cores)

    processes: list[Process] = []
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

    results_translit_dict: list[dict[str, WordInflections]] = list(results_list)

    translit_dict: dict[str, WordInflections] = dict()

    for i in results_translit_dict:
        for k, v in i.items():
            translit_dict[k] = v
    pr.yes(len(translit_dict))

    # write back into database
    pr.green_tmr("writing to db")

    translit_counter = _write_translit_to_db(db_session, dpd_db, translit_dict)
    db_session.close()
    pr.yes(translit_counter)

    pr.toc()


if __name__ == "__main__":
    main()
