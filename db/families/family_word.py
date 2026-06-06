#!/usr/bin/env python3

"""Create an html table of all words belonging to the same family."""

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyWord
from exporter.anki.anki_updater import family_updater
from tools.configger import config_test
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.superscripter import superscripter_uni


def main() -> None:
    pr.tic()
    pr.yellow_title("word families generator")

    if not (
        config_test("exporter", "make_dpd", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
        or config_test("exporter", "make_tpr", "yes")
        or config_test("exporter", "make_ebook", "yes")
    ):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    wf_db = db_session.query(DpdHeadword).filter(DpdHeadword.family_word != "").all()
    wf_db = sorted(wf_db, key=lambda x: pali_sort_key(x.lemma_1))

    wf_dict = make_word_fam_dict(wf_db)
    wf_dict = compile_wf_html(wf_db, wf_dict)
    errors_list = add_wf_to_db(db_session, wf_dict)
    print_errors_list(errors_list)
    db_session.close()

    if config_test("anki", "update", "yes"):
        # word families
        anki_data_list = make_anki_data(wf_dict)
        deck = ["Family Word"]
        family_updater(anki_data_list, deck)

    pr.toc()


def make_word_fam_dict(wf_db: list[DpdHeadword]) -> dict[str, dict]:
    pr.green_tmr("extracting word families")

    # create a dict of all word families
    # word: {headwords: [], html: "", }

    wf_dict: dict[str, dict] = {}

    for i in wf_db:
        wf = i.family_word

        if " " in wf:
            pr.red("ERROR: spaces found please remove!")

        if wf in wf_dict:
            wf_dict[wf]["headwords"] += [i.lemma_1]
        else:
            wf_dict[wf] = {
                "headwords": [i.lemma_1],
                "html": "",
                "data": [],
            }

    pr.yes(len(wf_dict))
    return wf_dict


def compile_wf_html(
    wf_db: list[DpdHeadword], wf_dict: dict[str, dict]
) -> dict[str, dict]:
    pr.green_tmr("compiling html")

    for i in wf_db:
        wf = i.family_word
        if not wf_dict[wf]["html"]:
            html_string = "<table class='family'>"
        else:
            html_string = wf_dict[wf]["html"]

        html_string += "<tr>"
        html_string += f"<th>{superscripter_uni(i.lemma_1)}</th>"
        html_string += f"<td><b>{i.pos}</b></td>"
        html_string += f"<td>{i.meaning_combo}</td>"
        html_string += f"<td>{i.degree_of_completion_html}</td>"
        html_string += "</tr>"

        wf_dict[wf]["html"] = html_string

        wf_dict[wf]["data"].append(
            (i.lemma_1, i.pos, i.meaning_combo, i.degree_of_completion)
        )

    for i in wf_dict:
        wf_dict[i]["html"] += "</table>"

    pr.yes(len(wf_dict))
    return wf_dict


def add_wf_to_db(db_session: Session, wf_dict: dict[str, dict]) -> list[str]:
    pr.green_tmr("adding to db")

    add_to_db = []
    errors_list = []

    for wf in wf_dict:
        if len(wf_dict[wf]["headwords"]) < 2:
            errors_list += [wf]

        wf_data = FamilyWord(
            word_family=wf,
            html=wf_dict[wf]["html"],
            count=len(wf_dict[wf]["headwords"]),
        )
        wf_data.data_pack(wf_dict[wf]["data"])
        add_to_db.append(wf_data)

    db_session.query(FamilyWord).delete()
    db_session.add_all(add_to_db)
    db_session.commit()
    pr.yes("ok")

    return errors_list


def print_errors_list(errors_list: list[str]) -> None:
    if len(errors_list) > 0:
        pr.red("ERROR: only 1 word in family:")
    for error in errors_list:
        pr.red(f"{error}")
    pr.red("")


def make_anki_data(wf_dict: dict[str, dict]) -> list[tuple[str, str]]:
    """Save to TSV for anki."""

    anki_data_list = []

    for i in wf_dict:
        html = "<table><tbody>"
        for row in wf_dict[i]["data"]:
            headword, pos, meaning, degree = row
            html += "<tr valign='top'>"
            html += "<div style='color: #FFB380'>"
            html += f"<td>{headword}</td>"
            html += f"<td><div style='color: #FF6600'>{pos}</div></td>"
            html += f"<td><div style='color: #FFB380'>{meaning}</td>"
            html += f"<td><div style='color: #FF6600'>{degree}</div></td></tr>"

        html += "</tbody></table>"
        if len(html) > 131072:
            pr.red(f"{i} longer than 131072 characters")
        else:
            anki_data_list += [(i, html)]

    return anki_data_list


if __name__ == "__main__":
    main()
