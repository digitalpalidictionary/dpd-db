#!/usr/bin/env python3.10

import pickle
import re
import pandas as pd
import cProfile

from rich import print
from typing import List
from os import popen
from copy import copy

from tools.pali_alphabet import vowels
from tools.timeis import tic, toc, bip, bop
from helpers import ResourcePaths, get_resource_paths


class Word:
    count_value: int = 0

    def __init__(self, word: str):
        Word.count_value += 1
        self.count = Word.count_value
        self.comm: str = "start"
        self.init: str = word
        self.front: str = ""
        self.word: str = word
        self.back: str = ""
        self.rfront: List = []
        self.rback: List = []
        self.tried: List = set()
        self.matches = set()
        self.path: List = ["start"]
        self.recursions = 0

    @property
    def comp(self):
        return self.front + self.word + self.back

    def copy_class(self):
        word_copy = Word.__new__(Word)
        word_copy.__dict__.update(self.__dict__)
        word_copy.count = Word.count_value
        return word_copy


def import_sandhi_rules():
    print("[green]importing sandhi rules", end=" ")

    sandhi_rules_df = pd.read_csv(
        pth["sandhi_rules_path"], sep="\t", dtype=str)
    sandhi_rules_df.fillna("", inplace=True)
    print(f"[white]{len(sandhi_rules_df):,}")
    sandhi_rules = sandhi_rules_df.to_dict('index')

    print("[green]testing sandhi rules for dupes", end=" ")
    dupes = sandhi_rules_df[sandhi_rules_df.duplicated(
        ["chA", "chB", "ch1", "ch2"], keep=False)]

    if len(dupes) != 0:
        print("\n[red]! duplicates found! please remove them and try again")
        print(f"\n[red]{dupes}")
        input("\n[white] press enter to continue")
        import_sandhi_rules()
    else:
        print("[white]ok")

    print("[green]testing sandhi rules for spaces", end=" ")

    if (
        sandhi_rules_df["chA"].str.contains(" ").any() or
        sandhi_rules_df["chB"].str.contains(" ").any() or
        sandhi_rules_df["ch1"].str.contains(" ").any() or
        sandhi_rules_df["ch2"].str.contains(" ").any()
    ):
        print("\n[red]! spaces found! please remove them and try again")
        input("[white]press enter to continue ")
        import_sandhi_rules()

    else:
        print("[white]ok")

    return sandhi_rules


def make_shortlist_set():

    print("[green]making shortlist set", end=" ")

    shortlist_df = pd.read_csv(
        pth["shortlist_path"], dtype=str, header=None, sep="\t")
    shortlist_df.fillna("", inplace=True)

    shortlist_set = set(shortlist_df[0].tolist())
    print(f"[white]{len(shortlist_set)}")

    return shortlist_set


def make_all_inflections_nfl_nll(all_inflections_set):
    """all inflections with no first letter, no last, no first three, no last three"""

    print("[green]making all inflections nfl & nll", end=" ")

    all_inflections_nofirst = set()
    all_inflections_nolast = set()
    all_inflections_first3 = set()
    all_inflections_last3 = set()

    for inflection in all_inflections_set:
        # no first letter
        all_inflections_nofirst.add(inflection[1:])
        # no last letter
        all_inflections_nolast.add(inflection[:-1])
        # leave first 3 letters
        all_inflections_first3.add(inflection[:3])
        # leave last 3 letters
        all_inflections_last3.add(inflection[-3:])

    print(f"[white]{len(all_inflections_nofirst):,}")

    return all_inflections_nofirst, all_inflections_nolast, all_inflections_first3, all_inflections_last3


def setup():
    print("[green]importing assets")
    global pth
    pth = get_resource_paths()

    global rules
    rules = import_sandhi_rules()

    global shortlist_set
    shortlist_set = make_shortlist_set()

    global unmatched_set
    with open(pth["unmatched_set_path"], "rb") as f:
        unmatched_set = pickle.load(f)

    global all_inflections_set
    with open(pth["all_inflections_set_path"], "rb") as f:
        all_inflections_set = pickle.load(f)

    global all_inflections_nofirst
    global all_inflections_nolast
    global all_inflections_first3
    global all_inflections_last3

    all_inflections_nofirst,\
        all_inflections_nolast,\
        all_inflections_first3,\
        all_inflections_last3\
        = make_all_inflections_nfl_nll(
            all_inflections_set)

    global matches_dict
    with open(pth["matches_dict_path"], "rb") as f:
        matches_dict = pickle.load(f)


def remove_neg(w):

    if w.comp not in w.matches and len(w.word) > 2:

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        if w.word.startswith("a"):
            if w.word[1] == w.word[2]:
                w.front = f"na + {w.front}"
                w.word = w.word[2:]
                w.comm = "na"
                w.rfront += ["na"]
            else:
                w.front = f"na + {w.front}"
                w.word = w.word[1:]
                w.comm = "na"
                w.rfront += ["na"]

        elif w.word.startswith("an"):
            w.front = f"na + {w.front}"
            w.word = w.word[2:]
            w.comm = "na"
            w.rfront += ["na"]

        elif w.word.startswith("na"):
            if w.word[1] == w.word[2]:
                w.front = f"na + {w.front}"
                w.word = w.word[3:]
                w.comm = "na"
                w.rfront += ["na"]
            else:
                w.front = f"na + {w.front}"
                w.word = w.word[2:]
                w.comm = "na"
                w.rfront += ["na"]

        elif w.word.startswith("nā"):
            w.front = f"na + {w.front}"
            w.word = f"a{w.word[2:]}"
            w.comm = "na"
            w.rfront += ["na"]

        if w.word in all_inflections_set:
            w.comm == f"match! = {w.comp}"

            if w.comp not in w.matches:
                matches_dict[w.init] += [(
                    w.comp, "xword-na", "na")]
                w.matches.add(w.comp)
                unmatched_set.discard(w.init)

        else:
            w.comm = "recursing na"
            w.path += ["na"]
            recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def remove_sa(w):

    if w.comp not in w.matches and len(w.word) >= 4:

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        if w.word[2] == w.word[3]:
            w.front = f"sa + {w.front}"
            w.word = w.word[3:]
            w.comm = "sa"
            w.rfront += ["sa"]

        else:
            w.front = f"sa + {w.front}"
            w.word = w.word[2:]
            w.comm = "sa"
            w.rfront += ["sa"]

        if w.word in all_inflections_set:

            if w.comp not in w.matches:
                matches_dict[w.init] += [
                    (w.comp, "xword-sa", "sa")]
                w.matches.add(w.comp)
                unmatched_set.discard(w.init)

        else:
            w.comm = "recursing sa"
            w.path += ["sa"]
            recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def remove_su(w):

    if w.comp not in w.matches and len(w.word) >= 4:

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        if w.word[2] == w.word[3]:
            w.front = f"su + {w.front}"
            w.word = w.word[3:]
            w.comm = "su"
            w.rfront += ["su"]

        else:
            w.front = f"su + {w.front}"
            w.word = w.word[2:]
            w.comm = "su"
            w.rfront += ["su"]

        if w.word in all_inflections_set:

            if w.comp not in w.matches:
                matches_dict[w.init] += [
                    (w.comp, "xword-su", "su")]
                w.matches.add(w.comp)
                unmatched_set.discard(w.init)

        else:
            w.comm = "recursing su"
            w.path += ["su"]
            recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def remove_dur(w):

    if w.comp not in w.matches and len(w.word) >= 4:

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        if w.word[2] == w.word[3]:
            w.front = f"dur + {w.front}"
            w.word = w.word[3:]
            w.comm = "dur"
            w.rfront += ["dur"]

        else:
            w.front = f"dur + {w.front}"
            w.word = w.word[2:]
            w.comm = "dur"
            w.rfront += ["dur"]

        if w.word in all_inflections_set:

            if w.comp not in w.matches:
                matches_dict[w.init] += [
                    (w.comp, "xword-dur", "dur")]
                w.matches.add(w.comp)
                unmatched_set.discard(w.init)

        else:
            w.comm = "recursing dur"
            w.path += ["dur"]
            recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def remove_apievaiti(w):

    if w.comp not in w.matches:

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)        # path_orig = copy(w.path)

        try:
            if w.word[-3] in vowels:
                wordA = w.word[:-3]
                wordB = w.word[-3:]

            else:
                wordA = w.word[:-2]
                wordB = w.word[-2:]

        except Exception:
            wordA = w.word[:-2]
            wordB = w.word[-2:]

        for rule in rules:
            chA = rules[rule]["chA"]
            chB = rules[rule]["chB"]
            ch1 = rules[rule]["ch1"]
            ch2 = rules[rule]["ch2"]

            try:
                wordA_lastletter = wordA[-1]
            except Exception:
                wordA_lastletter = wordA
            wordB_firstletter = wordB[0]

            if (wordA_lastletter == chA and
                    wordB_firstletter == chB):
                word1 = wordA[:-1] + ch1
                word2 = ch2 + wordB[1:]

                if word2 in ["api", "eva", "iti"]:
                    w.word = w.word.replace(wordB, "")
                    w.word = w.word.replace(wordA, word1)
                    w.back = f" + {word2}{back_orig}"
                    w.comm = "apievaiti"
                    w.rback = [rule+2] + rback_orig

                    if w.word in all_inflections_set:
                        w.comm == f"match! = {w.comp}"

                        if w.comp not in w.matches:
                            matches_dict[w.init] += [
                                (w.comp, "xword-pi", "apievaiti")]
                            w.matches.add(w.comp)
                            unmatched_set.discard(w.init)

                    else:
                        w.path += ["apievaiti"]
                        recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def remove_lwff_clean(w):

    if w.comp not in w.matches:

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        lwff_clean_list = []

        for i in range(len(w.word)):
            if w.word[:-i] in all_inflections_set:
                lwff_clean_list.append(w.word[:-i])

        for lwff_clean in lwff_clean_list:

            if len(lwff_clean) > 0:

                w.word = word_orig.replace(lwff_clean, "")
                w.front = f"{front_orig}{lwff_clean} + "
                w.comm = f"lwff_clean [yellow]{lwff_clean}"
                w.rfront = rfront_orig + [0]

                if w.word in all_inflections_set:

                    if w.comp not in w.matches:
                        matches_dict[w.init] += [
                            (w.comp, "xword-lwff", f"{comp_rules(w)}")]
                        w.matches.add(w.comp)
                        unmatched_set.discard(w.init)

                else:
                    w.comm = f"recursing lwff_clean [yellow]{w.comp}"
                    w.rfront = rfront_orig
                    w.path += ["lwff_clean"]
                    recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def remove_lwfb_clean(w):

    if w.comp not in w.matches:

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        lwfb_clean_list = []

        for i in range(len(w.word)):
            if w.word[i:] in all_inflections_set:
                lwfb_clean_list.append(w.word[i:])

        for lwfb_clean in lwfb_clean_list:

            if len(lwfb_clean) > 0:

                w.word = word_orig.replace(lwfb_clean, "")
                w.back = f" + {lwfb_clean}{back_orig}"
                w.comm = f"lwfb_clean [yellow]{lwfb_clean}"
                w.rback = [0] + rback_orig

                if w.word in all_inflections_set:
                    if w.comp not in w.matches:
                        matches_dict[w.init] += [
                            (w.comp, "xword-lwfb", f"{comp_rules(w)}")]
                        w.matches.add(w.comp)
                        unmatched_set.discard(w.init)

                else:
                    w.comm = f"recursing lfwb_clean [yellow]{w.comp}"
                    w.rback = rback_orig
                    w.path += ["lwfb_clean"]
                    recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def remove_lwff_fuzzy(w):

    if w.comp not in w.matches:

        lwff_fuzzy_list = []

        if len(w.word) >= 1:
            for i in range(len(w.word)):
                fuzzy_word = w.word[:-i]

                if fuzzy_word in all_inflections_nolast:
                    lwff_fuzzy_list.append(fuzzy_word)

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        for lwff_fuzzy in lwff_fuzzy_list:

            if len(lwff_fuzzy) >= 1:

                try:
                    if (lwff_fuzzy[-1]) in vowels:
                        wordA_fuzzy = (lwff_fuzzy[:-1])
                    else:
                        wordA_fuzzy = (lwff_fuzzy)
                except Exception:
                    wordA_fuzzy = (lwff_fuzzy)
                wordB_fuzzy = re.sub(f"^{wordA_fuzzy}", "", w.word)

                try:
                    wordA_lastletter = wordA_fuzzy[-1]
                except Exception:
                    wordA_lastletter = ""
                try:
                    wordB_firstletter = wordB_fuzzy[0]
                except Exception:
                    wordB_firstletter = ""

                for rule in rules:
                    chA = rules[rule]["chA"]
                    chB = rules[rule]["chB"]
                    ch1 = rules[rule]["ch1"]
                    ch2 = rules[rule]["ch2"]

                    if (wordA_lastletter == chA and
                            wordB_firstletter == chB):
                        word1 = wordA_fuzzy[:-1] + ch1
                        word2 = ch2 + wordB_fuzzy[1:]

                        if word1 in all_inflections_set:

                            w.word = re.sub(f"^{wordA_fuzzy}", "", w.word)
                            w.word = re.sub(f"^{wordB_fuzzy}", word2, w.word)
                            w.front = f"{front_orig}{word1} + "
                            w.comm = f"lwff_fuzzy [yellow]{word1} + {word2}"
                            w.rfront = rfront_orig + [rule+2]

                            if w.word in all_inflections_set:
                                if w.comp not in w.matches:
                                    matches_dict[w.init] += [
                                        (w.comp, "xword-fff", f"{comp_rules(w)}")]
                                    w.matches.add(w.comp)
                                    unmatched_set.discard(w.init)

                            else:
                                w.comm = f"recursing lwff_fuzzy [yellow]{w.comp}"
                                w.rfront = rfront_orig
                                w.path += ["lwff_fuzzy"]
                                recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def remove_lwfb_fuzzy(w):
    "find fuzzy list of longest words fuzzy from the back and recurse"

    if w.comp not in w.matches:

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        lwfb_fuzzy_list = []

        if len(w.word) >= 1:
            for i in range(len(w.word)):
                fuzzy_word = w.word[i:]

                if fuzzy_word in all_inflections_nofirst:
                    lwfb_fuzzy_list.append(fuzzy_word)

        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        for lwfb_fuzzy in lwfb_fuzzy_list:

            if len(lwfb_fuzzy) >= 1:
                wordA_fuzzy = re.sub(f"{lwfb_fuzzy}$", "", w.word)
                wordB_fuzzy = (lwfb_fuzzy)

                try:
                    wordA_lastletter = wordA_fuzzy[-1]
                except Exception:
                    wordA_lastletter = ""
                try:
                    wordB_firstletter = wordB_fuzzy[0]
                except Exception:
                    wordB_firstletter = ""

                for rule in rules:
                    chA = rules[rule]["chA"]
                    chB = rules[rule]["chB"]
                    ch1 = rules[rule]["ch1"]
                    ch2 = rules[rule]["ch2"]

                    if (wordA_lastletter == chA and
                            wordB_firstletter == chB):
                        word1 = wordA_fuzzy[:-1] + ch1
                        word2 = ch2 + wordB_fuzzy[1:]

                        if word2 in all_inflections_set:

                            w.word = re.sub(f"{wordB_fuzzy}$", "", w.word)
                            w.word = re.sub(f"{wordA_fuzzy}$", word1, w.word)
                            w.back = f" + {word2}{back_orig}"
                            w.comm = f"lwfb_fuzzy [yellow]{word1} + {word2}"
                            w.rback = [rule+2] + rback_orig

                            if w.word in all_inflections_set:
                                if w.comp not in w.matches:
                                    matches_dict[w.init] += [
                                        (w.comp, "xword-fbf", f"{comp_rules(w)}")]
                                    w.matches.add(w.comp)
                                    unmatched_set.discard(w.init)

                            else:
                                w.comm = f"recursing lwfb_fuzzy [yellow]{w.comp}"
                                w.rback = rback_orig
                                w.path += ["lwfb_fuzzy"]
                                recursive_removal(w)

        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def two_word_sandhi(w):

    if w.comp not in w.matches:

        comm_orig = copy(w.comm)
        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        for x in range(0, len(w.word)-1):
            wordA = w.word[:-x-1]
            wordB = w.word[-1-x:]
            try:
                wordA_lastletter = wordA[len(wordA)-1]
            except Exception:
                wordA_lastletter = ""
            wordB_firstletter = wordB[0]

            # blah blah

            if (wordA in all_inflections_set and
                    wordB in all_inflections_set):
                w.front = f"{front_orig}{wordA} + "
                w.word = wordB
                w.comm = "two word sandhi"
                w.rfront = rfront_orig + [0]

                if w.comp not in w.matches:
                    matches_dict[w.init] += [
                        (f"{w.front}{wordB}{w.back}", "xword-2.1", "0")]
                    w.matches.add(w.comp)
                    unmatched_set.discard(w.init)
                    w.path += ["two_word"]

            # bla* *lah

            for rule in rules:
                chA = rules[rule]["chA"]
                chB = rules[rule]["chB"]
                ch1 = rules[rule]["ch1"]
                ch2 = rules[rule]["ch2"]

                if (wordA_lastletter == chA and
                        wordB_firstletter == chB):
                    word1 = wordA[:-1] + ch1
                    word2 = ch2 + wordB[1:]

                    if (word1 in all_inflections_set and
                            word2 in all_inflections_set):
                        w.front = f"{front_orig}{word1} + "
                        w.word = word2
                        w.comm = "two word sandhi 2.2"
                        w.rfront = rfront_orig + [rule+2]

                        if w.comp not in w.matches:
                            matches_dict[w.init] += [
                                (w.comp, "xword-2.2",  f"{comp_rules(w)}")]
                            w.matches.add(w.comp)
                            unmatched_set.discard(w.init)
                            w.path += ["two_word"]

        w.comm = comm_orig
        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def three_word_sandhi(w):

    if w.comp not in w.matches:

        comm_orig = copy(w.comm)
        front_orig = copy(w.front)
        word_orig = copy(w.word)
        back_orig = copy(w.back)
        rfront_orig = copy(w.rfront)
        rback_orig = copy(w.rback)

        for x in range(0, len(w.word)-1):
            wordA = w.word[:-x-1]
            try:
                wordA_lastletter = wordA[len(wordA)-1]
            except Exception:
                wordA_lastletter = ""

            for y in range(0, len(w.word[-1-x:])-1):
                wordB = w.word[-1-x:-y-1]
                try:
                    wordB_firstletter = wordB[0]
                except Exception:
                    wordB_firstletter = ""
                try:
                    wordB_lastletter = wordB[len(wordB)-1]
                except Exception:
                    wordB_lastletter = ""

                wordC = w.word[-1-y:]
                wordC_firstletter = wordC[0]

                # blah blah blah

                if (wordA in all_inflections_set and
                    wordB in all_inflections_set and
                        wordC in all_inflections_set):

                    w.front = f"{front_orig}{wordA} + "
                    w.word = wordB
                    w.back = f" + {wordC}{back_orig}"

                    if w.comp not in w.matches:
                        matches_dict[w.init] += [
                            (w.comp, "three word", "0,0")]
                        w.matches.add(w.comp)
                        unmatched_set.discard(w.init)
                        w.path += ["three_word"]

                # blah bla* *lah

                if wordA in all_inflections_set:

                    for rule in rules:
                        chA = rules[rule]["chA"]
                        chB = rules[rule]["chB"]
                        ch1 = rules[rule]["ch1"]
                        ch2 = rules[rule]["ch2"]

                        if (wordB_lastletter == chA and
                                wordC_firstletter == chB):
                            word2 = wordB[:-1] + ch1
                            word3 = ch2 + wordC[1:]

                            if (wordA in all_inflections_set and
                                word2 in all_inflections_set and
                                    word3 in all_inflections_set):

                                w.front = f"{front_orig}{wordA} + "
                                w.word = word2
                                w.back = f" + {word3}{back_orig}"
                                w.rfront += [0]
                                w.rback += [rule+2]

                                if w.comp not in w.matches:
                                    matches_dict[w.init] += [
                                        (w.comp, "three word", f"{comp_rules(w)}")]
                                    w.matches.add(w.comp)
                                    unmatched_set.discard(w.init)
                                    w.path += ["three_word"]

                # bla* *lah blah

                if wordC in all_inflections_set:

                    for rule in rules:
                        chA = rules[rule]["chA"]
                        chB = rules[rule]["chB"]
                        ch1 = rules[rule]["ch1"]
                        ch2 = rules[rule]["ch2"]

                        if (wordA_lastletter == chA and
                                wordB_firstletter == chB):
                            word1 = wordA[:-1] + ch1
                            word2 = ch2 + wordB[1:]

                            if (word1 in all_inflections_set and
                                word2 in all_inflections_set and
                                    wordC in all_inflections_set):

                                w.front = f"{front_orig}{word1} + "
                                w.word = word2
                                w.back = f" + {wordC}{back_orig}"
                                w.rfront = rfront_orig + [rule+2]
                                w.rback = [0] + rback_orig

                                if w.comp not in w.matches:
                                    matches_dict[w.init] += [
                                        (w.comp, "three word", f"{comp_rules(w)}")]
                                    w.matches.add(w.comp)
                                    unmatched_set.discard(w.init)
                                    w.path += ["three_word"]

                # bla* *la* *lah

                for rulex in rules:
                    chAx = rules[rulex]["chA"]
                    chBx = rules[rulex]["chB"]
                    ch1x = rules[rulex]["ch1"]
                    ch2x = rules[rulex]["ch2"]

                    if (wordA_lastletter == chAx and
                            wordB_firstletter == chBx):
                        word1 = wordA[:-1] + ch1x
                        word2 = ch2x + wordB[1:]

                        for ruley in rules:
                            chAy = rules[ruley]["chA"]
                            chBy = rules[ruley]["chB"]
                            ch1y = rules[ruley]["ch1"]
                            ch2y = rules[ruley]["ch2"]

                            if (wordB_lastletter == chAy and
                                    wordC_firstletter == chBy):
                                word2 = (ch2x + wordB[1:])[:-1] + ch1y
                                word3 = ch2y + wordC[1:]

                                if (word1 in all_inflections_set and
                                        word2 in all_inflections_set and
                                        word3 in all_inflections_set):

                                    w.front = f"{front_orig}{word1} + "
                                    w.word = word2
                                    w.back = f" + {word3}{back_orig}"
                                    w.rfront = rfront_orig + [rulex+2]
                                    w.rback = [ruley+2] + rback_orig

                                    if w.comp not in w.matches:
                                        matches_dict[w.init] += [
                                            (w.comp, "three word", f"{comp_rules(w)}")]
                                        w.matches.add(w.comp)
                                        unmatched_set.discard(w.init)
                                        w.path += ["three_word"]

        w.comm = comm_orig
        w.front = front_orig
        w.word = word_orig
        w.back = back_orig
        w.rfront = rfront_orig
        w.rback = rback_orig

    return w


def comp_rules(w):
    rules_list = w.rfront + w.rback
    rules_string = ""

    for rule in rules_list:
        rules_string += f"{rule},"
    return rules_string


def comp_path(w):
    path_string = ""
    for p in w.path:
        path_string += f"{p} > "
    return path_string


def dprint(w):
    print(f"count:\t{w.count}")
    print(f"comm:\t{w.comm}")
    print(f"init:\t'{w.init}'")
    print(f"front:\t[blue]'{w.front}'")
    print(f"word:\t[blue]'{w.word}'")
    print(f"back:\t[blue]'{w.back}'")
    print(f"comp:\t[yellow]{w.comp}")
    print(f"rfront:\t{w.rfront}")
    print(f"rback:\t{w.rback}")
    print(f"tried:\t{w.tried}")
    print(f"matches:\t{w.matches}")
    print(f"path:\t{w.path}")
    print(f"recursions:\t{w.recursions}")
    print()


def summary():

    with open("sandhi/output/unmatched.csv", "w") as f:
        for item in unmatched_set:
            f.write(f"{item}\n")

    unmatched = len(unmatched_set)
    umatched_perc = (unmatched/unmatched_len_init)*100
    matched = unmatched_len_init-len(unmatched_set)
    matched_perc = (matched/unmatched_len_init)*100

    print(
        f"[green]unmatched:\t{unmatched:,} / {unmatched_len_init:,}\t[white]{umatched_perc:.2f}%")
    print(
        f"[green]matched:\t{matched:,} / {unmatched_len_init:,}\t[white]{matched_perc:.2f}%")

    word_count = len(matches_dict)
    match_count = 0

    for word, matches in matches_dict.items():
        match_count += len(matches)

    match_average = match_count / word_count

    print(f"[green]match count:\t{match_count}")
    print(f"[green]match average:\t{match_average:.4f}")


def recursive_removal(w):

    w.recursions += 1

    if w.recursions < 15:

        # add to matches

        if w.comp not in w.tried:
            w.tried.add(w.comp)

            if w.word in all_inflections_set:
                if w.comp not in w.matches:
                    matches_dict[w.init] += [
                        (w.comp, f"xword{w.comm}", f"{comp_rules(w)}")]
                    w.matches.add(w.comp)
                    unmatched_set.discard(w.init)

            else:
                # recursion

                if w.recursions == 1:

                    # negatives
                    if w.word.startswith(("a", "na", "an", "nā")):
                        na = w.copy_class()
                        w = remove_neg(na)

                    # sa
                    elif w.word.startswith("sa"):
                        sa = w.copy_class()
                        w = remove_sa(sa)

                    # su
                    elif w.word.startswith("su"):
                        su = w.copy_class()
                        w = remove_su(su)

                    # dur
                    elif w.word.startswith("du"):
                        dur = w.copy_class()
                        w = remove_dur(dur)

                # api eva iti
                if re.findall("(pi|va|ti)$", w.word) != []:
                    pi = w.copy_class()
                    w = remove_apievaiti(pi)

                # two word sandhi
                if w.comm != "start":
                    w2 = w.copy_class()
                    w2.comm = "two word sandhi"
                    w = two_word_sandhi(w2)

                    if not w2.matches:

                        # three word sandhi
                        w3 = w.copy_class()
                        w3.comm = "three word sandhi"
                        w = three_word_sandhi(w3)

                    # ffc = lwff clean
                    ffc = w.copy_class()
                    w = remove_lwff_clean(ffc)

                    # fbc = lwfb_clean
                    fbc = w.copy_class()
                    w = remove_lwfb_clean(fbc)

                    # fff = lwff fuzzy
                    fff = w.copy_class()
                    w = remove_lwff_fuzzy(fff)

                    # fbf = lwfb fuzzy
                    fbf = w.copy_class()
                    w = remove_lwfb_fuzzy(fbf)


def main():
    tic()

    print("[bright_yellow]sandhi splitter")

    profiler_on = False

    if profiler_on is True:
        profiler = cProfile.Profile()
        profiler.enable()

    # make globally accessable vaiables
    setup()

    time_dict = {}
    global unmatched_len_init
    unmatched_len_init = len(unmatched_set)

    print(f"[green]splitting sandhi [white]{unmatched_len_init:,}")

    for word in unmatched_set.copy():
        bip()
        w = Word(word)
        matches_dict[w.init] = []

        if w.count % 1000 == 0:
            print(
                f"\t{w.count:,} / {unmatched_len_init:,}\t{w.word}")

        # two word sandhi
        w2 = w.copy_class()
        w2.comm = "two word sandhi"
        w = two_word_sandhi(w2)

        if matches_dict[word] != []:
            w.matches.add(w.comp)
            unmatched_set.discard(word)
            time_dict[word] = bop()

        else:
            # three word sandhi
            w3 = w.copy_class()
            w3.comm = "three word sandhi"
            w = three_word_sandhi(w3)

            if matches_dict[word] != []:
                w.matches.add(w.comp)
                unmatched_set.discard(word)
                time_dict[word] = bop()

        # recursive removal
        if w.matches == set():
            recursive_removal(w)
            time_dict[word] = bop()

    summary()

    # save matches
    with open(pth["matches_path"], "w") as f:
        for word, data in matches_dict.items():
            for item in data:
                f.write(f"{word}\t")
                for column in item:
                    f.write(f"{column}\t")
                f.write("\n")

    # save timer_dict
    df = pd.DataFrame.from_dict(time_dict, orient="index")
    df = df.sort_values(by=0, ascending=False)
    df.to_csv("sandhi/output/timer.csv", sep="\t")

    if profiler_on:
        profiler.disable()
        profiler.dump_stats('profiler.prof')
        yes_no = input("open profiler? (y/n) ")
        if yes_no == "y":
            popen("tuna profiler.prof")

    toc()


if __name__ == "__main__":
    main()


# two word three word sandhi use comment when writing to dict
# in lwff lwffb, don't use the whole lists
# fix rules
# add ttā and its inflections to all inflections
# think of some sanity tests

# csv > tsv

# iṭṭhārammaṇānubhavanārahe iṭṭhārammaṇa + anu + bhavanā
# dakkhiṇadisābhāgo   dakkhiṇadisābhi + āgo

# why are some words taking so long?
# too many clean and fuzzy words getting recursed

# guṇavaṇṇābhāvena
# must show negative

# khayasundarābhirūpaabbhanumodanādīsu

# dibbacakkhuñāṇavipassanāñāṇamaggañāṇaphalañāṇapaccavekkhaṇañāṇānametaṃ
# end etaṃ is getting lost!

# only add words to matches that aren't already there.

# unmatched:      2627 / 51972    5.05%
# matched:        49345 / 51972   94.95%
# ----------------------------------------
# 0:48:24.987711
# = 5.387516355 hours

# include neg count in post process
