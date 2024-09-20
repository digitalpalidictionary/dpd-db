#!/usr/bin/env python3

"""Setup for compound deconstruction."""

import json
import pandas as pd
import pickle
import re

from typing import Dict, List, Set, Tuple
from sqlalchemy.orm.session import Session

from books_to_include import limited_texts, all_texts

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.all_words_in_dpd import make_all_words_in_dpd_set
from tools.bjt import make_bjt_text_list
from tools.configger import config_test
from tools.cst_sc_text_sets import make_cst_text_set
from tools.cst_sc_text_sets import make_other_pali_texts_set
from tools.cst_sc_text_sets import make_sc_text_set
from tools.paths import ProjectPaths
from tools.printer import p_title, p_green_title, p_green, p_yes, p_red
from tools.tic_toc import tic, toc


def setup_deconstructor():
    """Prepare all the necessary parts for deconstructor locally
    or in the cloud."""

    tic()
    p_title("setting up deconstructor")
    if not (
        config_test("exporter", "make_deconstructor", "yes")
        or config_test("exporter", "make_tpr", "yes")
        or config_test("exporter", "make_ebook", "yes")
        or config_test("regenerate", "db_rebuild", "yes")
    ):
        p_green_title("disabled in config.ini")
        toc()

    # Read configurations from config.ini
    if config_test("deconstructor", "run_on_cloud", "yes"):
        p_green_title("setting up to run [cyan]on cloud")
    else:
        p_green_title("setting up to run [cyan]locally")

    if config_test("deconstructor", "all_texts", "yes"):
        texts_to_include = all_texts
        p_green_title("including [cyan]all texts")

    elif config_test("deconstructor", "all_texts", "no"):
        texts_to_include = limited_texts
        p_green_title("including [cyan]limited texts")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    cst_text_set = make_cst_text_set(pth, texts_to_include)
    sc_text_set = make_sc_text_set(pth, texts_to_include)
    other_pali_text_set = make_other_pali_texts_set(pth)
    dpd_text_set = make_all_words_in_dpd_set(db_session)

    # bjt_text_set = make_bjt_text_set(include)
    (spelling_mistakes_set, spelling_corrections_set) = make_spelling_mistakes_set(pth)
    (variant_readings_set, variant_corrections_set) = make_variant_readings_set(pth)
    abbreviations_set = make_abbreviations_set(db_session)
    (manual_corrections_set, manual_corrections_dict) = make_manual_corrections_set(pth)
    sandhi_exceptions_set = make_exceptions_set(pth)
    all_inflections_set = make_all_inflections_set(db_session, sandhi_exceptions_set)
    neg_inflections_set = make_neg_inflections_set(db_session, sandhi_exceptions_set)

    def make_unmatched_set() -> Tuple[Set[str], Set[str]]:
        p_green("making text set")

        text_set = cst_text_set | sc_text_set
        # text_set = text_set | bjt_text_set
        text_set = text_set | other_pali_text_set
        text_set = text_set | dpd_text_set
        text_set = text_set | spelling_corrections_set
        text_set = text_set | variant_corrections_set
        text_set = text_set - spelling_mistakes_set
        text_set = text_set - variant_readings_set
        text_set = text_set - abbreviations_set
        text_set = text_set - manual_corrections_set
        text_set.update(["tā", "ttā"])
        if "" in text_set:
            text_set.remove("")
        p_yes(len(text_set))

        p_green("making unmatched set")
        unmatched_set = text_set - all_inflections_set
        unmatched_set = unmatched_set - sandhi_exceptions_set
        p_yes(len(unmatched_set))

        return text_set, unmatched_set

    text_set, unmatched_set = make_unmatched_set()

    def save_assets(pth: ProjectPaths) -> None:
        p_green("saving assets")

        with open(pth.unmatched_set_path, "wb") as f:
            pickle.dump(unmatched_set, f)
        with open("db/deconstructor/assets/unmatched_set.json", "w") as f:
            json.dump(list(unmatched_set), f, ensure_ascii=False, indent=0)

        with open(pth.all_inflections_set_path, "wb") as f:
            pickle.dump(all_inflections_set, f)
        with open("db/deconstructor/assets/all_inflections_set.json", "w") as f:
            json.dump(list(all_inflections_set), f, ensure_ascii=False, indent=0)

        with open(pth.text_set_path, "wb") as f:
            pickle.dump(text_set, f)
        with open("db/deconstructor/assets/text_set.json", "w") as f:
            json.dump(list(text_set), f, ensure_ascii=False, indent=0)

        with open(pth.neg_inflections_set_path, "wb") as f:
            pickle.dump(neg_inflections_set, f)
        with open("db/deconstructor/assets/neg_inflections_set.json", "w") as f:
            json.dump(list(neg_inflections_set), f, ensure_ascii=False, indent=0)

        p_yes("ok")

    save_assets(pth)

    def make_matches_dict(pth: ProjectPaths) -> None:
        p_green("saving matches_dict")
        matches_dict = {}
        matches_dict["word"] = [("split", "process", "rules", "path")]
        matches_dict.update(manual_corrections_dict)

        with open(pth.matches_dict_path, "wb") as f:
            pickle.dump(matches_dict, f)
        with open("db/deconstructor/assets/matches_dict.json", "w") as f:
            json.dump(matches_dict, f, ensure_ascii=False, indent=0)

        p_yes("ok")

    make_matches_dict(pth)

    toc()


def make_spelling_mistakes_set(pth: ProjectPaths) -> Tuple[Set[str], Set[str]]:
    p_green("making spelling mistakes set")

    sp_mistakes_df = pd.read_csv(
        pth.spelling_mistakes_path, dtype=str, header=None, sep="\t"
    )
    sp_mistakes_df.fillna("", inplace=True)

    spelling_mistakes_set: Set[str] = set(sp_mistakes_df[0].tolist())
    p_yes(len(spelling_mistakes_set))

    filtered = sp_mistakes_df[0] == sp_mistakes_df[1]
    dupes_df = sp_mistakes_df[filtered]
    dupes_list = dupes_df[0].to_list()
    if dupes_list != []:
        p_red(f"! dupes found {dupes_list}")

    p_green("making spelling corrections set")
    spelling_corrections_set: Set[str] = set(sp_mistakes_df[1].tolist())
    remove_me = set()
    add_me = set()

    for word in spelling_corrections_set:
        if re.findall(".+ .+", word):
            remove_me.add(word)
            single_words = word.split(" ")
            for single_word in single_words:
                add_me.add(single_word)

    spelling_corrections_set = spelling_corrections_set - remove_me
    spelling_corrections_set = spelling_corrections_set | add_me

    p_yes(len(spelling_corrections_set))
    return (spelling_mistakes_set, spelling_corrections_set)


def make_variant_readings_set(pth: ProjectPaths) -> Tuple[Set[str], Set[str]]:
    p_green("making variant readings set")

    variant_reading_df = pd.read_csv(
        pth.variant_readings_path, dtype=str, header=None, sep="\t"
    )
    variant_reading_df.fillna("", inplace=True)

    variant_readings_set: Set[str] = set(variant_reading_df[0].tolist())
    p_yes(len(variant_readings_set))

    filter = variant_reading_df[0] == variant_reading_df[1]
    dupes_df = variant_reading_df[filter]
    dupes_list = dupes_df[0].to_list()
    if dupes_list != []:
        p_red(f"! dupes found {dupes_list}")

    p_green("making variant corrections set")
    variant_corrections_set: Set[str] = set(variant_reading_df[1].tolist())
    remove_me = set()
    add_me = set()

    for word in variant_corrections_set:
        if re.findall(".+ .+", word):
            remove_me.add(word)
            single_words = word.split(" ")
            for single_word in single_words:
                add_me.add(single_word)

    variant_corrections_set = variant_corrections_set - remove_me
    variant_corrections_set = variant_corrections_set | add_me
    p_yes(len(variant_corrections_set))

    return variant_readings_set, variant_corrections_set


def make_abbreviations_set(db_session: Session) -> Set[str]:
    p_green("making abbreviations set")
    abbreviations_set: Set[str] = set()

    abbreviations_db = db_session.query(DpdHeadword).filter(
        DpdHeadword.pos == "abbrev"
    )

    for i in abbreviations_db:
        lemma_1_clean = re.sub(r" \d.*", "", i.lemma_1)
        abbreviations_set.add(lemma_1_clean)

    p_yes(len(abbreviations_set))
    return abbreviations_set


def make_manual_corrections_set(pth: ProjectPaths) -> Tuple[Set[str], Dict]:
    p_green("making manual corrections set")

    manual_corrections_df = pd.read_csv(
        pth.decon_manual_corrections, dtype=str, header=None, sep="\t"
    )
    manual_corrections_df.fillna("", inplace=True)

    manual_corrections_set: Set[str] = set(manual_corrections_df[0].tolist())
    p_yes(len(manual_corrections_set))

    manual_corrections_list: List[str] = manual_corrections_df[1].tolist()

    for word in manual_corrections_list:
        if not re.findall("\\+", word):
            p_red(f"! no plus sign {word}")
        if re.findall("(\\S\\+|\\+\\S)", word):
            p_red(f"! needs space {word}")

    p_green("making manual corrections dict")
    manual_corrections_dict = {}

    for row in range(len(manual_corrections_df)):
        sandhi = manual_corrections_df.loc[row, 0]
        split = manual_corrections_df.loc[row, 1]

        if sandhi in manual_corrections_dict:
            manual_corrections_dict[sandhi] += [(split, "manual", "m", "-")]
        else:
            manual_corrections_dict[sandhi] = [(split, "manual", "m", "-")]
    p_yes(len(manual_corrections_dict))

    return manual_corrections_set, manual_corrections_dict


def make_exceptions_set(pth: ProjectPaths) -> Set[str]:
    p_green("making exceptions set")

    sandhi_exceptions_df = pd.read_csv(pth.decon_exceptions, header=None)
    sandhi_exceptions_set: Set[str] = set(sandhi_exceptions_df[0].tolist())

    p_yes(len(sandhi_exceptions_set))

    return sandhi_exceptions_set


def make_all_inflections_set(
    db_session: Session, sandhi_exceptions_set: Set[str]
) -> Set[str]:
    p_green("making all inflections set")
    all_inflections_set: Set[str] = set()

    exceptions_list = set(
        ["abbrev", "cs", "idiom", "letter", "prefix", "root", "sandhi", "suffix", "ve"]
    )

    no_exceptions = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.pos.notin_(exceptions_list))
        .all()
    )

    all_headwords = [i.id for i in no_exceptions]

    all_inflections_db = (
        db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(all_headwords)).all()
    )

    for i in all_inflections_db:
        inflections = i.inflections_list
        all_inflections_set.update(inflections)

    all_inflections_set = all_inflections_set - sandhi_exceptions_set

    if "" in all_inflections_set:
        all_inflections_set.remove("")

    p_yes(len(all_inflections_set))

    return all_inflections_set


def make_neg_inflections_set(
    db_session: Session, sandhi_exceptions_set: Set[str]
) -> Set[str]:
    p_green("making neg inflections set")
    neg_inflections_set: Set[str] = set()

    exceptions_list = set(
        ["abbrev", "cs", "idiom", "letter", "prefix", "root", "sandhi", "suffix", "ve"]
    )

    neg_headwords_db = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.pos.notin_(exceptions_list))
        .filter(DpdHeadword.neg == "neg")
        .all()
    )

    neg_headwords = [i.id for i in neg_headwords_db]

    neg_inflections_db = (
        db_session.query(DpdHeadword).filter(DpdHeadword.id.in_(neg_headwords)).all()
    )

    for i in neg_inflections_db:
        inflections = i.inflections_list
        neg_inflections_set.update(inflections)

    neg_inflections_set = neg_inflections_set - sandhi_exceptions_set

    if "" in neg_inflections_set:
        neg_inflections_set.remove("")

    p_yes(len(neg_inflections_set))

    return neg_inflections_set

if __name__ == "__main__":
    setup_deconstructor()
