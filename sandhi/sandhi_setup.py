#!/usr/bin/env python3.11
import shutil
import re
import pandas as pd
import pickle

from json import loads
from rich import print

from db.models import PaliWord, DerivedData
from db.get_db_session import get_db_session
from helpers import get_resource_paths
from tools.clean_machine import clean_machine
from tools.pali_text_files import cst_texts, bjt_texts
from tools.make_cst_sc_text_sets import make_sc_text_set
from tools.timeis import tic, toc
from books_to_include import include

# prepare all the necessary parts for local and cloud


def make_cst_text_set(include):

    print(f"[green]{'making cst text set':<35}", end="")

    cst_texts_list = []

    for i in include:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    cst_text_string = ""

    for text in cst_texts_list:
        with open(pth['cst_text_path'].joinpath(text), "r") as f:
            cst_text_string += f.read()

    cst_text_string = clean_machine(cst_text_string)
    cst_text_set = set(cst_text_string.split())

    print(f"[white]{len(cst_text_set):>10,}")
    return cst_text_set


def make_bjt_text_set(include):

    print(f"[green]{'making buddhajayanti text set':<35}", end="")

    bjt_texts_list = []
    for i in include:
        if bjt_texts[i]:
            bjt_texts_list += bjt_texts[i]

    bjt_text_string = ""

    for bjt_text in bjt_texts_list:
        with open(pth["bjt_text_path"].joinpath(bjt_text), "r") as f:
            bjt_text_string += f.read()

    bjt_text_string = clean_machine(bjt_text_string)
    bjt_text_set = set(bjt_text_string.split())

    print(f"[white]{len(bjt_text_set):>10,}")
    return bjt_text_set


def make_spelling_mistakes_set():
    print(f"[green]{'making spelling mistakes set':<35}", end="")

    sp_mistakes_df = pd.read_csv(
        pth["sp_mistakes_path"], dtype=str, header=None, sep="\t")
    sp_mistakes_df.fillna("", inplace=True)

    spelling_mistakes_set = set(sp_mistakes_df[0].tolist())
    print(f"[white]{len(spelling_mistakes_set):>10,}")

    filtered = sp_mistakes_df[0] == sp_mistakes_df[1]
    dupes_df = sp_mistakes_df[filtered]
    dupes_list = dupes_df[0].to_list()
    if dupes_list != []:
        print(f"[bright_red]! dupes found {dupes_list}")

    print(f"[green]{'making spelling corrections set':<35}", end="")
    spelling_corrections_set = set(sp_mistakes_df[1].tolist())
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

    spelling_mistakes_dict = {}

    for row in range(len(sp_mistakes_df)):
        mistake = sp_mistakes_df.loc[row, 0]
        correction = sp_mistakes_df.loc[row, 1]

        if mistake in spelling_mistakes_dict:
            spelling_mistakes_dict[mistake] += [(
                f"incorrect spelling of <i>{correction}</i>",
                "spelling", "sp", "-")]
        else:
            spelling_mistakes_dict[mistake] = [(
                f"incorrect spelling of <i>{correction}</i>",
                "spelling", "sp", "-")]

    return (
        spelling_mistakes_set,
        spelling_corrections_set,
        spelling_mistakes_dict)


def make_variant_readings_set():
    print(f"[green]{'making variant readings set':<35}", end="")

    variant_reading_df = pd.read_csv(
        pth["variant_readings_path"], dtype=str, header=None, sep="\t")
    variant_reading_df.fillna("", inplace=True)

    variant_readings_set = set(variant_reading_df[0].tolist())
    print(f"[white]{len(variant_readings_set):>10,}")

    filter = variant_reading_df[0] == variant_reading_df[1]
    dupes_df = variant_reading_df[filter]
    dupes_list = dupes_df[0].to_list()
    if dupes_list != []:
        print(f"[bright_red]! dupes found {dupes_list}")

    print(f"[green]{'making variant corrections set':<35}", end="")
    variant_corrections_set = set(variant_reading_df[1].tolist())
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

    variant_dict = {}

    for row in range(len(variant_reading_df)):
        variant = variant_reading_df.loc[row, 0]
        correction = variant_reading_df.loc[row, 1]

        if variant in variant_dict:
            variant_dict[variant] += [(
                f"variant reading of <i>{correction}</i>",
                "variant", "var", "-")]
        else:
            variant_dict[variant] = [(
                f"variant reading of <i>{correction}</i>",
                "variant", "var", "-")
            ]

    return variant_readings_set, variant_corrections_set, variant_dict


def make_abbreviations_set():

    print(f"[green]{'making abbreviations set':<35}", end="")

    abbreviations_set = set()

    abbreviations_db = db_session.query(PaliWord).filter(
        PaliWord.pos == "abbrev"
    )

    for i in abbreviations_db:
        pali_1_clean = re.sub(r" \d.*", "", i.pali_1)
        abbreviations_set.add(pali_1_clean)

    print(f"[white]{len(abbreviations_set):>10,}")

    return abbreviations_set


def make_manual_corrections_set():

    print(f"[green]{'making manual corrections set':<35}", end="")

    manual_corrections_df = pd.read_csv(
        pth["manual_corrections_path"], dtype=str, header=None, sep="\t")
    manual_corrections_df.fillna("", inplace=True)

    manual_corrections_set = set(manual_corrections_df[0].tolist())
    print(f"[white]{len(manual_corrections_set):>10,}")

    manual_corrections_list = manual_corrections_df[1].tolist()

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


def make_exceptions_set():
    print(f"[green]{'making exceptions set':<35}", end="")

    sandhi_exceptions_df = pd.read_csv(
        pth["sandhi_exceptions_path"], header=None)
    sandhi_exceptions_set = set(sandhi_exceptions_df[0].tolist())

    print(f"[white]{len(sandhi_exceptions_set):>10,}")

    return sandhi_exceptions_set


def make_all_inflections_set(sandhi_exceptions_set):
    print(f"[green]{'making all inflections set':<35}", end="")
    all_inflections_set = set()

    exceptions_list = set(
        ["abbrev", "cs", "idiom", "letter", "prefix", "root", "sandhi",
            "sandhix", "suffix", "ve"]
    )

    no_exceptions = db_session.query(PaliWord).filter(
        PaliWord.pos.notin_(exceptions_list)).all()

    all_headwords = [i.id for i in no_exceptions]

    all_inflections_db = db_session.query(DerivedData).filter(
        DerivedData.id.in_(all_headwords)).all()

    for i in all_inflections_db:
        inflections = loads(i.inflections)
        all_inflections_set.update(inflections)

    all_inflections_set = all_inflections_set - sandhi_exceptions_set

    if "" in all_inflections_set:
        all_inflections_set.remove("")

    print(f"[white]{len(all_inflections_set):>10,}")

    return all_inflections_set


def make_neg_inflections_set(sandhi_exceptions_set):
    print(f"[green]{'making neg inflections set':<35}", end="")
    neg_inflections_set = set()

    exceptions_list = set(
        ["abbrev", "cs", "idiom", "letter", "prefix", "root", "sandhi",
            "sandhix", "suffix", "ve"]
    )

    neg_headwords_db = db_session.query(PaliWord).filter(
        PaliWord.pos.notin_(exceptions_list)).filter(
        PaliWord.neg == "neg").all()

    neg_headwords = [i.id for i in neg_headwords_db]

    neg_inflections_db = db_session.query(DerivedData).filter(
        DerivedData.id.in_(neg_headwords)).all()

    for i in neg_inflections_db:
        inflections = loads(i.inflections)
        neg_inflections_set.update(inflections)

    neg_inflections_set = neg_inflections_set - sandhi_exceptions_set

    if "" in neg_inflections_set:
        neg_inflections_set.remove("")

    print(f"[white]{len(neg_inflections_set):>10,}")

    return neg_inflections_set


def copy_sandhi_related_dir():
    print(f"[green]{'copying sandhi related dir':<35}", end="")
    try:
        shutil.rmtree(pth["sandhi_related_dest_dir"])
    except Exception as e:
        print(f"[bright_red]{e}")

    shutil.copytree(pth[
        "sandhi_related_source_dir"],
        pth["sandhi_related_dest_dir"])

    print(f"[white]{'ok':>10}")


def main():
    tic()
    print("[bright_yellow]setting up for sandhi splitting")

    global pth
    pth = get_resource_paths()

    global db_session
    db_session = get_db_session(pth["dpd_db_path"])

    cst_text_set = make_cst_text_set(include)
    sc_text_set = make_sc_text_set(include)
    # bjt_text_set = make_bjt_text_set(include)
    spelling_mistakes_set,\
        spelling_corrections_set,\
        spelling_mistakes_dict\
        = make_spelling_mistakes_set()
    variant_readings_set, \
        variant_corrections_set, \
        variant_dict\
        = make_variant_readings_set()
    abbreviations_set = make_abbreviations_set()
    manual_corrections_set,\
        manual_corrections_dict \
        = make_manual_corrections_set()
    sandhi_exceptions_set = make_exceptions_set()
    all_inflections_set = make_all_inflections_set(sandhi_exceptions_set)
    neg_inflections_set = make_neg_inflections_set(sandhi_exceptions_set)

    def make_unmatched_set():
        print(f"[green]{'making text set':<35}", end="")

        text_set = cst_text_set | sc_text_set
        # text_set = text_set | bjt_text_set
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

    def save_assets():
        print(f"[green]{'saving assets':<35}", end="")

        with open(pth["unmatched_set_path"], "wb") as f:
            pickle.dump(unmatched_set, f)

        with open(pth["all_inflections_set_path"], "wb") as f:
            pickle.dump(all_inflections_set, f)

        with open(pth["text_set_path"], "wb") as f:
            pickle.dump(text_set, f)

        with open(pth["neg_inflections_set_path"], "wb") as f:
            pickle.dump(neg_inflections_set, f)

        print(f"[white]{'ok':>10}")

    save_assets()

    def make_matches_dict():
        print(f"[green]{'saving matches_dict':<35}", end="")
        matches_dict = {}
        matches_dict["word"] = [
            ("split", "process", "rules", "path")]
        matches_dict.update(spelling_mistakes_dict)
        matches_dict.update(variant_dict)
        matches_dict.update(manual_corrections_dict)

        with open(pth["matches_dict_path"], "wb") as f:
            pickle.dump(matches_dict, f)

        print(f"[white]{'ok':>10}")

    make_matches_dict()

    toc()


if __name__ == "__main__":
    main()
