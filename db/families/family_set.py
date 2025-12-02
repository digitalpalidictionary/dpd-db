#!/usr/bin/env python3

"""Compile sets save to database."""

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilySet
from tools.configger import config_test
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.superscripter import superscripter_uni


def main():
    pr.tic()
    pr.title("sets generator")

    if not (
        config_test("exporter", "make_dpd", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
        or config_test("exporter", "make_tpr", "yes")
        or config_test("exporter", "make_ebook", "yes")
    ):
        pr.green("disabled in config.ini")
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
    pr.green("extracting set names")

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
    pr.green("compiling html")

    for __counter__, i in enumerate(sets_db):
        for sf in i.family_set_list:
            if sf in sets_dict:
                if i.lemma_1 in sets_dict[sf]["headwords"]:
                    if not sets_dict[sf]["html"]:
                        html_string = "<table class='family'>"
                    else:
                        html_string = sets_dict[sf]["html"]

                    html_string += "<tr>"
                    html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
                    html_string += f"<td><b>{i.pos}</b></td>"
                    html_string += f"<td>{i.meaning_combo}</td>"
                    html_string += f"<td>{i.degree_of_completion_html}</td>"
                    html_string += "</tr>"

                    sets_dict[sf]["html"] = html_string

                    # data
                    sets_dict[sf]["data"].append(
                        (
                            i.lemma_1,
                            i.pos,
                            i.meaning_combo,
                            i.degree_of_completion,
                        )
                    )

    for i in sets_dict:
        sets_dict[i]["html"] += "</table>"

    pr.yes(len(sets_dict))
    return sets_dict


def add_sf_to_db(db_session, sets_dict):
    pr.green("adding to db")

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
