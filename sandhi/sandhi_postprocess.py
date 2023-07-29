#!/usr/bin/env python3

"""Postprocess the results, find most likely candidates and save to database.
"""

import numpy as np
import pandas as pd
import pickle

from difflib import SequenceMatcher
from rich import print

from transliterate_sandhi import transliterate_sandhi

from db.get_db_session import get_db_session
from db.models import Sandhi
from tools.paths import ProjectPaths as PTH
from tools.tic_toc import tic, toc
from tools.configger import config_test

if config_test("deconstructor", "include_cloud", "yes"):
    ADD_DO = True
else:
    ADD_DO = False


def main():
    tic()
    print("[bright_yellow]post-processing sandhi-splitter")

    print(f"[green]add digital ocean {ADD_DO}")

    global db_session
    db_session = get_db_session(PTH.dpd_db_path)

    with open(PTH.neg_inflections_set_path, "rb") as f:
        neg_inflections_set = pickle.load(f)

    matches_df = process_matches(PTH, neg_inflections_set)
    top_five_dict = make_top_five_dict(matches_df)
    add_to_dpd_db(top_five_dict)
    transliterate_sandhi()
    make_rule_counts(PTH, matches_df)
    letter_counts(PTH, matches_df)
    toc()


def process_matches(PTH, neg_inflections_set):

    print("[green]processing matches")

    print("reading tsvs")
    matches_df = pd.read_csv(PTH.matches_path, dtype=str, sep="\t")

    if ADD_DO is True:
        matches_do_df = pd.read_csv(
            PTH.matches_do_path, dtype=str, sep="\t")
        matches_df = pd.concat([matches_df, matches_do_df], ignore_index=True)

    matches_df = matches_df.fillna("")

    print("adding manual")
    matches_df["manual"] = matches_df['process'].str.count("manual")

    print("adding splitcount")
    matches_df["splitcount"] = matches_df['split'].str.count(r' \+ ')

    print("adding lettercount")
    matches_df["lettercount"] = matches_df['split'].str.count('.')

    print("adding word count")
    matches_df['count'] = matches_df.groupby('word')['word'].transform('size')

    def calculate_ratio(original, split):
        split = split.replace(" + ", "")
        return SequenceMatcher(None, original, split).ratio()

    print("adding difference ratio")
    matches_df['ratio'] = np.vectorize(
        calculate_ratio)(matches_df['split'], matches_df['split'])

    print("adding neg_count")

    def neg_counter(row):
        neg_count = 0
        if " + " in row["split"]:
            word_list = row["split"].split(" + ")
            # doesn't matter if the first word is negative
            word_list.remove(word_list[0])
            for word in word_list:
                if word in neg_inflections_set:
                    neg_count += 1
        return neg_count

    matches_df['neg_count'] = matches_df.apply(neg_counter, axis=1)

    print("sorting df values")
    matches_df.sort_values(
        by=["manual", "splitcount", "lettercount", "ratio", "neg_count"],
        axis=0,
        ascending=[False, True, True, False, True],
        inplace=True,
        ignore_index=True
    )

    print("dropping duplicates")
    matches_df.drop_duplicates(
        subset=['word', 'split'],
        keep='first',
        inplace=True,
        ignore_index=True
    )

    print("saving to matches_sorted.tsv")
    matches_df.to_csv(PTH.matches_sorted, sep="\t", index=None)

    return matches_df


def make_top_five_dict(matches_df):
    print("[green]making top five dict", end=" ")
    top_five_dict = {}

    for index, i in matches_df.iterrows():

        if i.word not in top_five_dict:
            top_five_dict[i.word] = {
                "splits": [i.split],
                "splitcount": i.splitcount}
        else:
            if len(top_five_dict[i.word]["splits"]) < 5:
                if i.splitcount <= top_five_dict[i.word]["splitcount"]:
                    top_five_dict[i.word]["splits"].append(i.split)

    # print(top_five_dict["ārammaṇamūlakasappāyakārīsuttā"])

    # remove the splitcount
    for key, value in top_five_dict.items():
        top_five_dict[key] = value["splits"]

    print(len(top_five_dict))
    return top_five_dict


def add_to_dpd_db(top_five_dict):
    print("[green]adding to dpd_db", end=" ")

    db_session.execute(Sandhi.__table__.delete())
    db_session.commit()

    add_to_db = []
    for word, splits in top_five_dict.items():
        sandhi_split = Sandhi(
            sandhi=word,
            split=",".join(splits)
        )
        add_to_db.append(sandhi_split)

    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()

    print(f"{len(add_to_db)}")


def make_rule_counts(PTH, matches_df):
    print("[green]saving rule counts", end=" ")

    rules_list = matches_df[['rules']].values.tolist()
    rule_counts = {}

    for sublist in rules_list:
        for item in sublist[0].split(','):
            if item not in rule_counts:
                rule_counts[item] = 1
            else:
                rule_counts[item] += 1

    df = pd.DataFrame.from_dict(rule_counts, orient="index", columns=["count"])
    counts_df = df.value_counts()
    counts_df.to_csv(PTH.rule_counts_path, sep="\t")

    print("[white]ok")


def letter_counts(PTH, df):
    print("[green]saving letter counts", end=" ")
    df.drop_duplicates(subset=['word', 'split'],
                       keep='first', inplace=True, ignore_index=True)
    masterlist = []
    for row in range(len(df)):
        split = df.loc[row, "split"]
        if "<i>" not in split:
            words = split.split(" + ")
            for word in words:
                masterlist.append(word)
    masterlist = sorted(masterlist)

    letters = {}
    for i in range(1, 11):
        letters[i] = []

    for word in masterlist:
        if len(word) >= 10:
            letters[10].append(word)
        else:
            letters[len(word)].append(word)

    for i in range(1, 11):
        letters_df = pd.DataFrame(letters[i])
        letters_counts_sorted = letters_df.value_counts()
        letters_path = getattr(PTH, f"letters{i}")
        letters_counts_sorted.to_csv(letters_path, sep="\t", header=None)

    print("[white]ok")


if __name__ == "__main__":
    main()
