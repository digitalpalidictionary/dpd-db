#!/usr/bin/env python3

"""Setup for compound deconstruction."""

from typing import Dict, List, Set, Tuple
import pandas as pd
import pickle
import re

from rich import print

from books_to_include import limited_texts, all_texts

from sqlalchemy.orm.session import Session

from db.models import DpdHeadwords
from db.get_db_session import get_db_session
from tools.cst_sc_text_sets import make_cst_text_set
from tools.cst_sc_text_sets import make_sc_text_set
from tools.cst_sc_text_sets import make_other_pali_texts_set
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from tools.configger import config_test


def setup_deconstructor():
    """Prepare all the necessary parts for deconstructor locally
    or in the cloud."""

    # Read configurations from config.ini
    if config_test("deconstructor", "run_on_cloud", "yes"):
        print("[green]setting up to run [cyan]on cloud")
    else:
        print("[green]setting up to run [cyan]locally")
    
    if config_test("deconstructor", "all_texts", "yes"):
        texts_to_include = all_texts
        print("[green]including [cyan]all texts")
    
    elif config_test("deconstructor", "all_texts", "no"):
        texts_to_include = limited_texts
        print("[green]including [cyan]limited texts")
    
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    print(f"[green]{'making cst text set':<35}", end="")
    cst_text_set = make_cst_text_set(pth, texts_to_include)
    print(f"[white]{len(cst_text_set):>10,}")

    print(f"[green]{'making sc text set':<35}", end="")
    sc_text_set = make_sc_text_set(pth, texts_to_include)
    print(f"[white]{len(sc_text_set):>10,}")

    print(f"[green]{'making other pali texts set':<35}", end="")
    other_pali_text_set = make_other_pali_texts_set(pth)
    print(f"[white]{len(other_pali_text_set):>10,}")

    # bjt_text_set = make_bjt_text_set(include)
    (spelling_mistakes_set,
        spelling_corrections_set) = make_spelling_mistakes_set(pth)
    (variant_readings_set,
        variant_corrections_set) = make_variant_readings_set(pth)
    abbreviations_set = make_abbreviations_set(db_session)
    (manual_corrections_set,
        manual_corrections_dict) = make_manual_corrections_set(pth)
    sandhi_exceptions_set = make_exceptions_set(pth)
    all_inflections_set = make_all_inflections_set(db_session, sandhi_exceptions_set)
    neg_inflections_set = make_neg_inflections_set(db_session, sandhi_exceptions_set)

    def make_unmatched_set() -> Tuple[Set[str], Set[str]]:
        print(f"[green]{'making text set':<35}", end="")

        text_set = cst_text_set | sc_text_set
        # text_set = text_set | bjt_text_set
        text_set = text_set | other_pali_text_set
        text_set = text_set | spelling_corrections_set
        text_set = text_set | variant_corrections_set
        text_set = text_set - spelling_mistakes_set
        text_set = text_set - variant_readings_set
        text_set = text_set - abbreviations_set
        text_set = text_set - manual_corrections_set
        text_set.update(["tā", "ttā"])
        if "" in text_set:
            text_set.remove("")

        print(f"[white]{len(text_set):>10,}")

        print(f"[green]{'making unmatched set':<35}", end="")

        unmatched_set = text_set - all_inflections_set
        unmatched_set = unmatched_set - sandhi_exceptions_set

        print(f"[white]{len(unmatched_set):>10,}")

        return text_set, unmatched_set

    text_set, unmatched_set = make_unmatched_set()

    def save_assets(pth: ProjectPaths) -> None:
        print(f"[green]{'saving assets':<35}", end="")

        with open(pth.unmatched_set_path, "wb") as f:
            pickle.dump(unmatched_set, f)

        with open(pth.all_inflections_set_path, "wb") as f:
            pickle.dump(all_inflections_set, f)

        with open(pth.text_set_path, "wb") as f:
            pickle.dump(text_set, f)

        with open(pth.neg_inflections_set_path, "wb") as f:
            pickle.dump(neg_inflections_set, f)

        print(f"[white]{'ok':>10}")

    save_assets(pth)

    def make_matches_dict(pth: ProjectPaths) -> None:
        print(f"[green]{'saving matches_dict':<35}", end="")
        matches_dict = {}
        matches_dict["word"] = [
            ("split", "process", "rules", "path")]
        matches_dict.update(manual_corrections_dict)

        with open(pth.matches_dict_path, "wb") as f:
            pickle.dump(matches_dict, f)

        print(f"[white]{'ok':>10}")

    make_matches_dict(pth)


def make_spelling_mistakes_set(pth: ProjectPaths) -> Tuple[Set[str], Set[str]]:
    print(f"[green]{'making spelling mistakes set':<35}", end="")

    sp_mistakes_df = pd.read_csv(
        pth.spelling_mistakes_path, dtype=str, header=None, sep="\t")
    sp_mistakes_df.fillna("", inplace=True)

    spelling_mistakes_set: Set[str] = set(sp_mistakes_df[0].tolist())
    print(f"[white]{len(spelling_mistakes_set):>10,}")

    filtered = sp_mistakes_df[0] == sp_mistakes_df[1]
    dupes_df = sp_mistakes_df[filtered]
    dupes_list = dupes_df[0].to_list()
    if dupes_list != []:
        print(f"[bright_red]! dupes found {dupes_list}")

    print(f"[green]{'making spelling corrections set':<35}", end="")
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
    print(f"[white]{len(spelling_corrections_set):>10,}")

    return (
        spelling_mistakes_set,
        spelling_corrections_set)


def make_variant_readings_set(pth: ProjectPaths) -> Tuple[Set[str], Set[str]]:
    print(f"[green]{'making variant readings set':<35}", end="")

    variant_reading_df = pd.read_csv(
        pth.variant_readings_path, dtype=str, header=None, sep="\t")
    variant_reading_df.fillna("", inplace=True)

    variant_readings_set: Set[str] = set(variant_reading_df[0].tolist())
    print(f"[white]{len(variant_readings_set):>10,}")

    filter = variant_reading_df[0] == variant_reading_df[1]
    dupes_df = variant_reading_df[filter]
    dupes_list = dupes_df[0].to_list()
    if dupes_list != []:
        print(f"[bright_red]! dupes found {dupes_list}")

    print(f"[green]{'making variant corrections set':<35}", end="")
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
    print(f"[white]{len(variant_corrections_set):>10,}")

    return variant_readings_set, variant_corrections_set


def make_abbreviations_set(db_session: Session) -> Set[str]:

    print(f"[green]{'making abbreviations set':<35}", end="")

    abbreviations_set: Set[str] = set()

    abbreviations_db = db_session.query(DpdHeadwords).filter(
        DpdHeadwords.pos == "abbrev"
    )

    for i in abbreviations_db:
        lemma_1_clean = re.sub(r" \d.*", "", i.lemma_1)
        abbreviations_set.add(lemma_1_clean)

    print(f"[white]{len(abbreviations_set):>10,}")

    return abbreviations_set


def make_manual_corrections_set(pth: ProjectPaths) -> Tuple[Set[str], Dict]:

    print(f"[green]{'making manual corrections set':<35}", end="")

    manual_corrections_df = pd.read_csv(
        pth.manual_corrections_path, dtype=str, header=None, sep="\t")
    manual_corrections_df.fillna("", inplace=True)

    manual_corrections_set: Set[str] = set(manual_corrections_df[0].tolist())
    print(f"[white]{len(manual_corrections_set):>10,}")

    manual_corrections_list: List[str] = manual_corrections_df[1].tolist()

    for word in manual_corrections_list:
        if not re.findall("\\+", word):
            print(f"[bright_red]! no plus sign {word}")
        if re.findall("(\\S\\+|\\+\\S)", word):
            print(f"[bright_red]! needs space {word}")

    manual_corrections_dict = {}

    for row in range(len(manual_corrections_df)):
        sandhi = manual_corrections_df.loc[row, 0]
        split = manual_corrections_df.loc[row, 1]

        if sandhi in manual_corrections_dict:
            manual_corrections_dict[sandhi] += [
                (split, "manual", "m", "-")]
        else:
            manual_corrections_dict[sandhi] = [
                (split, "manual", "m", "-")]

    return manual_corrections_set, manual_corrections_dict


def make_exceptions_set(pth: ProjectPaths) -> Set[str]:
    print(f"[green]{'making exceptions set':<35}", end="")

    sandhi_exceptions_df = pd.read_csv(
        pth.sandhi_exceptions_path, header=None)
    sandhi_exceptions_set: Set[str] = set(sandhi_exceptions_df[0].tolist())

    print(f"[white]{len(sandhi_exceptions_set):>10,}")

    return sandhi_exceptions_set


def make_all_inflections_set(db_session: Session, sandhi_exceptions_set: Set[str]) -> Set[str]:
    print(f"[green]{'making all inflections set':<35}", end="")
    all_inflections_set: Set[str] = set()

    exceptions_list = set(
        ["abbrev", "cs", "idiom", "letter", "prefix", "root", "sandhi",
            "suffix", "ve"])

    no_exceptions = db_session.query(DpdHeadwords).filter(
        DpdHeadwords.pos.notin_(exceptions_list)).all()

    all_headwords = [i.id for i in no_exceptions]

    all_inflections_db = db_session.query(DpdHeadwords).filter(
        DpdHeadwords.id.in_(all_headwords)).all()

    for i in all_inflections_db:
        inflections = i.inflections_list
        all_inflections_set.update(inflections)

    all_inflections_set = all_inflections_set - sandhi_exceptions_set

    if "" in all_inflections_set:
        all_inflections_set.remove("")

    print(f"[white]{len(all_inflections_set):>10,}")

    return all_inflections_set


def make_neg_inflections_set(db_session: Session, sandhi_exceptions_set: Set[str]) -> Set[str]:
    print(f"[green]{'making neg inflections set':<35}", end="")
    neg_inflections_set: Set[str] = set()

    exceptions_list = set(
        ["abbrev", "cs", "idiom", "letter", "prefix", "root", "sandhi",
            "suffix", "ve"])

    neg_headwords_db = db_session.query(DpdHeadwords).filter(
        DpdHeadwords.pos.notin_(exceptions_list)).filter(
        DpdHeadwords.neg == "neg").all()

    neg_headwords = [i.id for i in neg_headwords_db]

    neg_inflections_db = db_session.query(DpdHeadwords).filter(
        DpdHeadwords.id.in_(neg_headwords)).all()

    for i in neg_inflections_db:
        inflections = i.inflections_list
        neg_inflections_set.update(inflections)

    neg_inflections_set = neg_inflections_set - sandhi_exceptions_set

    if "" in neg_inflections_set:
        neg_inflections_set.remove("")

    print(f"[white]{len(neg_inflections_set):>10,}")

    return neg_inflections_set


if __name__ == "__main__":
    tic()
    print("[bright_yellow]setting up for sandhi splitting")
    if (
        config_test("exporter", "make_deconstructor", "yes") or 
        config_test("exporter", "make_tpr", "yes") or 
        config_test("exporter", "make_ebook", "yes") or 
        config_test("regenerate", "db_rebuild", "yes")
    ):
        setup_deconstructor()
    else:
        print("generating is disabled in the config")
    toc()