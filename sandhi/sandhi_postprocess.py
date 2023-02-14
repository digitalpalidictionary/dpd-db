#!/usr/bin/env python3.10

import pandas as pd
import os
import warnings
import random
import json
import pickle
import re
import time

from rich import print
from tools.timeis import tic, toc
from helpers import ResourcePaths, get_resource_paths
from tools.clean_machine import clean_machine
from timeis import timeis, blue, green, yellow, line, white, red, tic, toc
from pathlib import Path
from difflib import SequenceMatcher
from simsapa.app.stardict import export_words_as_stardict_zip, ifo_from_opts, DictEntry


global pth
pth = get_resource_paths()


def process_matches():

    print(f"[green]combining matches df's", end=" ")

    matches_df = pd.read_csv(pth["matches_path"], dtype=str, sep="\t")
    matches_df = matches_df.fillna("")

    # add splitcount and lettercount and count

    matches_df["splitcount"] = matches_df['split'].str.count(r' \+ ')
    matches_df["lettercount"] = matches_df['split'].str.count('.')
    matches_df['count'] = matches_df.groupby('word')['word'].transform('size')

    # add difference ratio

    for row in range(len(matches_df)):
        original = matches_df.iloc[row, 0]
        split = matches_df.iloc[row, 1]
        split = split.replace(" + ", "")
        matches_df.loc[row, 'ratio'] = SequenceMatcher(
            None, original, split).ratio()

    matches_df.sort_values(
        by=["splitcount","ratio", "lettercount"],
        axis=0,
        ascending=[True, False, True],
        inplace=True,
        ignore_index=True
    )

    matches_df.drop_duplicates(
        subset=['word', 'split'],
        keep='first',
        inplace=True,
        ignore_index=True
    )

    matches_df.to_csv(pth["matches_sorted"], sep="\t", index=None)

    print("[white]ok")

# def make_sandhi_dict(neg_inflections_set):

#     print(f"[green]making sandhi dict")
#     sandhi_dict = {}
#     sandhi_dict_clean = {}

#     with open("sandhi/sandhi.css", "r") as f:
#         sandhi_css = f.read()

#     matches_df_length = len(matches_df)

#     for row in range(matches_df_length):  # matches_df_length
#         word = matches_df.loc[row, 'word']

#         if row % 1000 == 0:
#             print(f"[white]{row}/{matches_df_length} {word}")

#         if word not in sandhi_dict.keys():

#             filter = matches_df['word'] == word
#             word_df = matches_df[filter]
#             word_df.reset_index(drop=True, inplace=True)

#             length = len(word_df)
#             if len(word_df) > 5:
#                 length = 5

#             html_string = ""
#             html_string_clean = ""
#             html_string += sandhi_css
#             html_string += f"<body><div class='sandhi'><p class='sandhi'>"

#             for rowx in range(length):
#                 word = word_df.loc[rowx, 'word']
#                 split = word_df.loc[rowx, 'split']
#                 split = re.sub("-", " + ", split)
#                 split_words = split.split(" + ")
#                 rulez = str(word_df.loc[rowx, 'rules'])
#                 rulez = re.sub(" ", "", rulez)
#                 ratio = word_df.loc[rowx, 'ratio']

#                 # exclude negatives prefixed with a-
#                 # include double negatives

#                 neg_count = 0
#                 add = True

#                 for split_word in split_words:
#                     if split_word in neg_inflections_set:
#                         neg_count += 1
#                         if re.findall(f"(>| ){split_word[1:]}(<| )", html_string):
#                             add = False

#                 if add == True or \
#                         neg_count > 1:
#                     html_string += f"{split} <span class='sandhi'> ({rulez}) ({ratio: .4f})</span>"
#                     html_string_clean += split

#                     if rowx != length-1:
#                         html_string += f"<br>"
#                         html_string_clean += f"<br>"
#                     else:
#                         html_string += f"</p></div></body>"

#             sandhi_dict.update({word: html_string})
#             sandhi_dict_clean.update({word: html_string_clean})

#     with open("output/sandhi dict", "wb") as pf:
#         pickle.dump(sandhi_dict_clean, pf)

#     sandhi_dict_df = pd.DataFrame(sandhi_dict.items())
#     sandhi_dict_df.rename({0: "word", 1: "split"},
#                           axis='columns', inplace=True)
#     sandhi_dict_df.to_csv(
#         "output/sandhi/sandhi_dict_df.csv", index=None, sep="\t")


# def make_golden_dict():

#     print(f"[green]generating goldendict", end=" ")

#     df = pd.read_csv("output/sandhi/sandhi_dict_df.csv", sep="\t", dtype=str)
#     df = df.fillna("")
#     df.insert(2, "definition_plain", "")
#     df.insert(3, "synonyms", "")
#     df.rename({"word": "word", "split": "definition_html"},
#               axis='columns', inplace=True)

#     df.to_json("output/sandhi/matches.json",
#                force_ascii=False, orient="records", indent=5)

#     zip_path = Path("./output/sandhi/padavibhāga.zip")

#     with open("output/sandhi/matches.json", "r") as gd_data:
#         data_read = json.load(gd_data)

#     def item_to_word(x):
#         return DictEntry(
#             word=x["word"],
#             definition_html=x["definition_html"],
#             definition_plain=x["definition_plain"],
#             synonyms=x["synonyms"],)

#     words = list(map(item_to_word, data_read))

#     ifo = ifo_from_opts(
#         {"bookname": "padavibhāga",
#             "author": "Bodhirasa",
#             "description": "",
#             "website": "", }
#     )

#     export_words_as_stardict_zip(words, ifo, zip_path)

#     print(f"[white]ok")


# def unzip_and_copy():

#     print(f"[green]unipping and copying goldendict", end=" ")

#     os.popen(
#         'unzip -o "output/sandhi/padavibhāga" -d "/home/bhikkhu/Documents/Golden Dict"')

#     print(f"[white]ok")
#     print(f"[green]{line}")


# def value_counts():

#     print(f"[green]saving value counts", end=" ")
#     matches_df = pd.read_csv("output/sandhi/matches.csv", sep="\t")

#     rules_string = ""

#     for row in range(len(matches_df)):
#         rulez = matches_df.loc[row, 'rules']
#         rulez = re.sub("'", "", rulez)
#         rulez = re.sub(r"\[|\]", "", rulez)
#         rules_string = rules_string + rulez + ","

#     rules_df = pd.DataFrame(rules_string.split(","))
#     # print(rules_df)

#     counts = rules_df.value_counts()
#     counts.to_csv(f"output/sandhi/counts", sep="\t")

#     print(f"[white]ok")


# def word_counts():

#     print(f"[green]saving word counts", end=" ")

#     df = pd.read_csv("output/sandhi/matches.csv", sep="\t", dtype=str)
#     df.drop_duplicates(subset=['word', 'split'],
#                        keep='first', inplace=True, ignore_index=True)

#     masterlist = []

#     for row in range(len(df)):
#         split = df.loc[row, "split"]
#         words = re.findall("[^ + |-]+", split)
#         for word in words:
#             masterlist.append(word)

#     letters1 = []
#     letters2 = []
#     letters3 = []
#     letters4 = []
#     letters5 = []
#     letters6 = []
#     letters7 = []
#     letters8 = []
#     letters9 = []
#     letters10plus = []

#     for word in masterlist:
#         if len(word) == 1:
#             letters1.append(word)
#         if len(word) == 2:
#             letters2.append(word)
#         if len(word) == 3:
#             letters3.append(word)
#         if len(word) == 4:
#             letters4.append(word)
#         if len(word) == 5:
#             letters5.append(word)
#         if len(word) == 6:
#             letters6.append(word)
#         if len(word) == 7:
#             letters7.append(word)
#         if len(word) == 8:
#             letters8.append(word)
#         if len(word) == 9:
#             letters9.append(word)
#         if len(word) >= 10:
#             letters10plus.append(word)

#     masterlist = sorted(masterlist)

#     letters_df = pd.DataFrame(masterlist)
#     letters_counts = letters_df.value_counts(sort=False)
#     letters_counts.to_csv(f"output/sandhi/letters", sep="\t", header=None)
#     letters_counts_sorted = letters_df.value_counts()
#     letters_counts_sorted.to_csv(
#         f"output/sandhi/letters sorted", sep="\t", header=None)

#     letters1_df = pd.DataFrame(letters1)
#     letters1_counts = letters1_df.value_counts(sort=False)
#     letters1_counts.to_csv(f"output/sandhi/letters1", sep="\t", header=None)
#     letters1_counts_sorted = letters1_df.value_counts()
#     letters1_counts_sorted.to_csv(
#         f"output/sandhi/letters1sorted", sep="\t", header=None)

#     letters2_df = pd.DataFrame(letters2)
#     letters2_counts = letters2_df.value_counts(sort=False)
#     letters2_counts.to_csv(f"output/sandhi/letters2", sep="\t", header=None)
#     letters2_counts_sorted = letters2_df.value_counts()
#     letters2_counts_sorted.to_csv(
#         f"output/sandhi/letters2sorted", sep="\t", header=None)

#     letters3_df = pd.DataFrame(letters3)
#     letters3_counts = letters3_df.value_counts(sort=False)
#     letters3_counts.to_csv(f"output/sandhi/letters3", sep="\t", header=None)
#     letters3_counts_sorted = letters3_df.value_counts()
#     letters3_counts_sorted.to_csv(
#         f"output/sandhi/letters3sorted", sep="\t", header=None)

#     letters4_df = pd.DataFrame(letters4)
#     letters4_counts = letters4_df.value_counts(sort=False)
#     letters4_counts.to_csv(f"output/sandhi/letters4", sep="\t", header=None)
#     letters4_counts_sorted = letters4_df.value_counts()
#     letters4_counts_sorted.to_csv(
#         f"output/sandhi/letters4sorted", sep="\t", header=None)

#     letters5_df = pd.DataFrame(letters5)
#     letters5_counts = letters5_df.value_counts(sort=False)
#     letters5_counts.to_csv(f"output/sandhi/letters5", sep="\t", header=None)
#     letters5_counts_sorted = letters5_df.value_counts()
#     letters5_counts_sorted.to_csv(
#         f"output/sandhi/letters5sorted", sep="\t", header=None)

#     letters6_df = pd.DataFrame(letters6)
#     letters6_counts = letters6_df.value_counts(sort=False)
#     letters6_counts.to_csv(f"output/sandhi/letters6", sep="\t", header=None)
#     letters6_counts_sorted = letters6_df.value_counts()
#     letters6_counts_sorted.to_csv(
#         f"output/sandhi/letters6sorted", sep="\t", header=None)

#     letters7_df = pd.DataFrame(letters7)
#     letters7_counts = letters7_df.value_counts(sort=False)
#     letters7_counts.to_csv(f"output/sandhi/letters7", sep="\t", header=None)
#     letters7_counts_sorted = letters7_df.value_counts()
#     letters7_counts_sorted.to_csv(
#         f"output/sandhi/letters7sorted", sep="\t", header=None)

#     letters8_df = pd.DataFrame(letters8)
#     letters8_counts = letters8_df.value_counts(sort=False)
#     letters8_counts.to_csv(f"output/sandhi/letters8", sep="\t", header=None)
#     letters8_counts_sorted = letters8_df.value_counts()
#     letters8_counts_sorted.to_csv(
#         f"output/sandhi/letters8sorted", sep="\t", header=None)

#     letters9_df = pd.DataFrame(letters9)
#     letters9_counts = letters9_df.value_counts(sort=False)
#     letters9_counts.to_csv(f"output/sandhi/letters9", sep="\t", header=None)
#     letters9_counts_sorted = letters9_df.value_counts()
#     letters9_counts_sorted.to_csv(
#         f"output/sandhi/letters9sorted", sep="\t", header=None)

#     letters10plus_df = pd.DataFrame(letters10plus)
#     letters10plus_counts = letters10plus_df.value_counts(sort=False)
#     letters10plus_counts.to_csv(
#         f"output/sandhi/letters10+", sep="\t", header=None)
#     letters10plus_counts_sorted = letters10plus_df.value_counts()
#     letters10plus_counts_sorted.to_csv(
#         f"output/sandhi/letters10+sorted", sep="\t", header=None)

#     print(f"[white]ok")


# def test_me():

#     print(f"[green]random test [white]10")
#     print(f"[green][green]{line}")
#     for x in range(10):
#         print(f"[white]{random.choice(list(unmatched_set))}")


def main():
    tic()
    print("[yellow]postprocessing sandhi splits")
    process_matches()
    # make_sandhi_dict(neg_inflections_set)
    # make_golden_dict()
    # unzip_and_copy()
    # value_counts()
    # word_counts()
    # test_me()
    toc()

if __name__ == "__main__":
    main()
