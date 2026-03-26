#!/usr/bin/env python3

"""Compile sets save to database."""

import re

from natsort import natsorted

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilySet
from tools.configger import config_test
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.superscripter import superscripter_uni

SORT_STRATEGIES: dict[str, list[str]] = {
    "natsort_prefixes": [
        "suttas of ",
        "vaggas of ",
        "books of the ",
        "chapters of ",
        "collections of ",
        "parts of ",
    ],
    "natsort_exact": [
        "previous Buddhas",
    ],
    "bracket_number": [
        "ordinal numbers",
        "cardinal numbers",
    ],
    "day_order": [
        "days of the week",
    ],
}

DAY_ORDER: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _get_sort_strategy(set_name: str) -> str | None:
    """Return the sort strategy for a set name, or None for default Pāḷi sort."""
    for prefix in SORT_STRATEGIES["natsort_prefixes"]:
        if set_name.startswith(prefix):
            return "natsort"
    if set_name in SORT_STRATEGIES["natsort_exact"]:
        return "natsort"
    if set_name in SORT_STRATEGIES["bracket_number"]:
        return "bracket_number"
    if set_name in SORT_STRATEGIES["day_order"]:
        return "day_order"
    return None


def _extract_bracket_number(meaning_1: str) -> float:
    """Extract number from brackets in meaning_1.
    E.g. '(48th)' → 48, '(38)' → 38, '(800 000)' → 800000.
    """
    match = re.search(r"\(([0-9 ]+)", meaning_1)
    if match:
        return float(match.group(1).replace(" ", ""))
    return float("inf")


def _day_sort_key(meaning_1: str) -> int:
    """Sort by day of the week order."""
    return DAY_ORDER.get(meaning_1.strip().lower(), 99)


def main():
    pr.tic()
    pr.yellow_title("sets generator")

    if not (
        config_test("exporter", "make_dpd", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
        or config_test("exporter", "make_tpr", "yes")
        or config_test("exporter", "make_ebook", "yes")
    ):
        pr.green_tmr("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    sets_db = db_session.query(DpdHeadword).filter(DpdHeadword.family_set != "").all()
    sets_db = sorted(sets_db, key=lambda x: pali_sort_key(x.lemma_1))

    sets_dict = make_sets_dict(sets_db)
    sets_dict = compile_sf_html(sets_db, sets_dict)
    errors_list = add_sf_to_db(db_session, sets_dict)
    print_errors_list(errors_list)
    pr.toc()


def make_sets_dict(sets_db):
    pr.green_tmr("extracting set names")

    # create a dict of all sets
    # set: {headwords: [], html: "", data:, []}

    sets_dict: dict = {}

    for __counter__, i in enumerate(sets_db):
        for fs in i.family_set_list:
            if fs == " ":
                pr.red("ERROR: spaces found please remove!")
            elif not fs:
                pr.red("ERROR: '' found please remove!")
            elif fs == "+":
                pr.red("ERROR: + found please remove!")

            if i.meaning_1:
                if fs in sets_dict:
                    sets_dict[fs]["headwords"] += [i.lemma_1]
                else:
                    sets_dict[fs] = {
                        "headwords": [i.lemma_1],
                        "html": "",
                        "data": [],
                    }

    pr.yes(len(sets_dict))
    return sets_dict


def compile_sf_html(sets_db: list[DpdHeadword], sets_dict):
    pr.green_tmr("compiling html")

    for i in sets_db:
        for sf in i.family_set_list:
            if sf in sets_dict:
                if i.lemma_1 in sets_dict[sf]["headwords"]:
                    sets_dict[sf].setdefault("items", []).append(i)

    for sf, sf_data in sets_dict.items():
        items = sf_data.get("items", [])
        strategy = _get_sort_strategy(sf)

        if strategy == "natsort":
            items = natsorted(items, key=lambda x: x.meaning_1)
        elif strategy == "bracket_number":
            items = sorted(items, key=lambda x: _extract_bracket_number(x.meaning_1))
        elif strategy == "day_order":
            items = sorted(items, key=lambda x: _day_sort_key(x.meaning_1))

        html_string = "<table class='family'>"
        for i in items:
            html_string += "<tr>"
            html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
            html_string += f"<td><b>{i.pos}</b></td>"
            html_string += f"<td>{i.meaning_combo}</td>"
            html_string += f"<td>{i.degree_of_completion_html}</td>"
            html_string += "</tr>"

            sf_data["data"].append(
                (
                    i.lemma_1,
                    i.pos,
                    i.meaning_combo,
                    i.degree_of_completion,
                )
            )
        html_string += "</table>"
        sf_data["html"] = html_string

    pr.yes(len(sets_dict))
    return sets_dict


def add_sf_to_db(db_session, sets_dict):
    pr.green_tmr("adding to db")

    add_to_db = []
    errors_list = []

    for __counter__, sf in enumerate(sets_dict):
        count = len(sets_dict[sf]["headwords"])

        sf_data = FamilySet(
            set=sf,
            html=sets_dict[sf]["html"],
            count=count,
        )
        sf_data.data_pack(sets_dict[sf]["data"])

        add_to_db.append(sf_data)

        if count < 3:
            errors_list += [sf]

    db_session.execute(FamilySet.__table__.delete())  # type: ignore
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    pr.yes("ok")

    return errors_list


def print_errors_list(errors_list):
    if errors_list != []:
        pr.red("ERROR: less than 3 names in set: ")
        for error in sorted(errors_list):
            pr.red(f"{error}")


if __name__ == "__main__":
    main()
