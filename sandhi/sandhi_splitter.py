#!/usr/bin/env python3.10

import pickle
import re
import pandas as pd
import cProfile

from rich import print
from typing import List
from os import popen

from tools.pali_alphabet import vowels
from tools.timeis import tic, toc, bip, bop, line
from sandhi_setup import import_sandhi_rules, make_shortlist_set, make_all_inflections_nfl_nll
from helpers import ResourcePaths, get_resource_paths


class Word:
    count_value: int = 0
    tried: List = []
    matches: List = []

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
        self.tried: List = []
        self.mactches: List = []

    def copy_class(self):
        word_copy = Word.__new__(Word)
        word_copy.__dict__.update(self.__dict__)
        word_copy.count = Word.count_value
        return word_copy


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

    all_inflections_nofirst, all_inflections_nolast, all_inflections_first3, all_inflections_last3 = make_all_inflections_nfl_nll(
        all_inflections_set)

    global matches_dict
    with open(pth["matches_dict_path"], "rb") as f:
        matches_dict = pickle.load(f)


def negative_in_front(w):
    if len(w.word) > 2:

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

        if w.word.startswith("an"):
            w.front = f"na + {w.front}"
            w.word = w.word[2:]
            w.comm = "na"
            w.rfront += ["na"]

        if w.word.startswith("na"):
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

        if w.word.startswith("nā"):
            w.front = f"na + {w.front}"
            w.word = f"a{w.word[2:]}"
            w.comm = "na"
            w.rfront += ["na"]

        if w.word in all_inflections_set:
            w.comm == f"match! = {w.front}{w.word}{w.back}"

            # if f"na + {w.word}" not in w.matches:
            #     w.matches += [f"na + {w.word}"]
            matches_dict[w.init] += [
                (f"na + {w.word}", "xword-na", "na")]
            unmatched_set.discard(w.init)

            if debug:
                dprint(w)
                print("[yellow]match found!")
                input(f"{w.init} {matches_dict[w.init]}\n")

        else:
            w.comm = "recursing na"

            if debug:
                dprint(w)

            recursive_removal(w)


def sa_in_front(w):

    if w.word[2] == w.word[3]:
        w.front += ["sa"]
        w.word = w.word[3:]
        w.comm = "sa"
        w.rfront = w.rfront.append("sa")

    else:
        w.front += ["sa"]
        w.word = w.word[2:]
        w.comm = "sa"
        w.rfront = w.rfront.append("sa")

    if w.word in all_inflections_set:

        # if f"sa + {w.word}" not in w.matches:
        #     w.matches += [f"sa + {w.word}"]
        matches_dict[w.init] += [
            (f"sa + {w.word}", "xword-sa", "sa")]
        unmatched_set.discard(w.init)

        if debug:
            print("[yellow]match found!")
            input(f"{w.init} {matches_dict[w.init]}\n")

    else:
        w.comm = "recursing sa"

        if debug:
            dprint(w)

        recursive_removal(w)


def su_in_front(w):

    if w.word[2] == w.word[3]:
        w.front += ["su"]
        w.word = w.word[3:]
        w.comm = "su"
        w.rfront = w.rfront.append("su")

    else:
        w.front += ["su"]
        w.word = w.word[2:]
        w.comm = "su"
        w.rfront = w.rfront.append("su")

    if w.word in all_inflections_set:

        # if f"su + {w.word}" not in w.matches:
        #     w.matches += [f"su + {w.word}"]
        matches_dict[w.init] += [
            (f"su + {w.word}", "xword-su", "su")]
        unmatched_set.discard(w.init)

        if debug:
            print("[yellow]match found!")
            input(f"{w.init} {matches_dict[w.init]}\n")

    else:
        w.comm = "recursing su"

        if debug:
            dprint(w)

        recursive_removal(w)


def dur_in_front(w):

    if w.word[2] == w.word[3]:
        w.front += ["dur"]
        w.word = w.word[3:]
        w.comm = "dur"
        w.rfront = w.rfront.append("dur")

    else:
        w.front += ["dur"]
        w.word = w.word[2:]
        w.comm = "dur"
        w.rfront = w.rfront.append("dur")

    if w.word in all_inflections_set:

        # if f"dur + {w.word}" not in w.matches:
        #     w.matches += [f"dur + {w.word}"]
        matches_dict[w.init] += [
            (f"dur + {w.word}", "xword-dur", "dur")]
        unmatched_set.discard(w.init)

        if debug:
            print("[yellow]match found!")
            input(f"{w.init} {matches_dict[w.init]}\n")

    else:
        w.comm = "recursing dur"

        if debug:
            dprint(w)

        recursive_removal(w)


def remove_apievaiti(w):
    pi_rback_orig = w.rback

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

    if debug:
        print(f"api eva iti: {wordA} + {wordB}")

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
                w.back = f" + {word2}{w.back}"
                w.comm = "api eva iti"
                w.rback = [rule+2] + pi_rback_orig

                if w.word in all_inflections_set:
                    w.comm == f"match! = {w.front}{w.word}{w.back}"

                    # if f"{w.front}{w.word}{w.back}" not in w.matches:
                    #     w.matches += [f"{w.front}{w.word}{w.back}"]
                    matches_dict[w.init] += [
                        (f"{w.front}{w.word}{w.back}", "xword-pi", "api eva iti")]
                    unmatched_set.discard(w.init)

                    if debug:
                        dprint(w)
                        print("[yellow]match found!")
                        input(f"{w.init} {matches_dict[w.init]}\n")

                else:
                    w.rback = pi_rback_orig

                    if debug:
                        dprint(w)

                    recursive_removal(w)


def lwff_clean(w):
    """1. make list of longest words from the front
2. test if in inflections
3. recurse"""

    word_orig = w.word
    front_orig = w.front
    rfront_orig = w.rfront

    lwff_clean_list = []

    for i in range(len(w.word)):
        if w.word[:-i] in all_inflections_set:
            lwff_clean_list.append(w.word[:-i])

    if debug:
        input(f"lwff_clean_list\n{lwff_clean_list}\n")

    for lwff_clean in lwff_clean_list:

        w.word = word_orig.replace(lwff_clean, "")
        w.front = f"{front_orig}{lwff_clean} + "
        w.comm = f"lwff_clean [yellow]{lwff_clean}"
        rfront_orig += [0]
        w.rfront = rfront_orig

        if debug:
            dprint(w)

        if w.word in all_inflections_set:

            # if f"{w.front}{w.word}{w.back}" not in w.matches:
            #     w.matches += [f"{w.front}{w.word}{w.back}"]
            matches_dict[w.init] += [
                (f"{w.front}{w.word}{w.back}", "xword-lwff", f"{comp_rules(w)}")]

            unmatched_set.discard(w.init)

            if debug:
                print("[yellow]match found!")
                input(f"{w.init}: {matches_dict[w.init]}")

        else:
            w.rfront = rfront_orig
            w.comm = f"recursing lwff_clean [yellow]{w.front}{w.word}{w.back}"

            if debug:
                dprint(w)

            recursive_removal(w)


def lwfb_clean(w):
    "find clean list of longest words from the back"

    word_orig = w.word
    back_orig = w.back
    rback_orig = w.rback

    lwfb_clean_list = []

    for i in range(len(w.word)):
        if w.word[i:] in all_inflections_set:
            lwfb_clean_list.append(w.word[i:])

    if debug:
        input(f"lwfb_clean_list\n{lwfb_clean_list}\n")
        dprint(w)

    for lwfb_clean in lwfb_clean_list:

        w.word = word_orig.replace(lwfb_clean, "")
        w.back = f" + {lwfb_clean}{back_orig}"
        w.comm = f"lwfb_clean [yellow]{lwfb_clean}"
        w.rback = [0] + rback_orig

        if debug:
            dprint(w)

        if w.word in all_inflections_set:
            # if f"{w.front}{w.word}{w.back}" not in w.matches:
            #     w.matches += [f"{w.front}{w.word}{w.back}"]
            matches_dict[w.init] += [
                (f"{w.front}{w.word}{w.back}", "xword-lwfb", f"{comp_rules(w)}")]

            unmatched_set.discard(w.init)

            if debug:
                print("[yellow] macth found")
                input(f"{w.init}: {matches_dict[w.init]}")

        else:
            w.rback = rback_orig
            w.comm = f"recursing lfwb_clean [yellow]{w.front}{w.word}{w.back}"

            if debug:
                dprint(w)

            recursive_removal(w)


def lwff_fuzzy(w):
    "find fuzzy list of longest words from the front and recurse"

    lwff_fuzzy_list = []

    if len(w.word) > 2:
        for i in range(len(w.word)):
            fuzzy_word = w.word[:-i]

            if fuzzy_word in all_inflections_nolast:
                lwff_fuzzy_list.append(fuzzy_word)

    previous_lwff_fuzzy = None
    rfront_orig = w.rfront

    for lwff_fuzzy in lwff_fuzzy_list:

        if len(lwff_fuzzy) > 2:

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

            if debug:
                print(
                    f"wordA-wordB: {wordA_fuzzy}-{wordB_fuzzy}")
                print(
                    f"wordA-wordB_firstletter: {wordA_lastletter}-{wordB_firstletter}")
                input()

            for rule in rules:
                chA = rules[rule]["chA"]
                chB = rules[rule]["chB"]
                ch1 = rules[rule]["ch1"]
                ch2 = rules[rule]["ch2"]

                if (wordA_lastletter == chA and
                        wordB_firstletter == chB):
                    word1 = wordA_fuzzy[:-1] + ch1
                    word2 = ch2 + wordB_fuzzy[1:]

                    if debug:
                        print(f"lwff_fuzzy: [green]{word1}-[blue]{word2}")
                        input()

                    if (word1 in all_inflections_set and
                            word2[:3] in all_inflections_first3):

                        if w.front == "":
                            w.word = w.word.replace(wordA_fuzzy, "")
                            w.word = w.word.replace(wordB_fuzzy, word2)
                            w.front = f"{word1} + "

                        else:
                            if previous_lwff_fuzzy:
                                w.word = (
                                    previous_lwff_fuzzy).replace(lwff_fuzzy, "")
                                w.front = re.sub(previous_lwff_fuzzy, word1, w.front)

                            else:
                                w.word = w.word.replace(wordA_fuzzy, "")
                                w.word = w.word.replace(wordB_fuzzy, word2)
                                w.front = f"{w.front}{word1} + "

                        w.comm = f"lwff_fuzzy [yellow]{word1} + {word2}"
                        rfront_orig += [rule+2]
                        w.rfront = rfront_orig

                        if debug:
                            dprint(w)

                        if w.word in all_inflections_set:
                            # if f"{w.front}{w.word}{w.back}" not in w.matches:
                            #     w.matches += [f"{w.front}{w.word}{w.back}"]
                            matches_dict[w.init] += [
                                (f"{w.front}{w.word}{w.back}", "xword-fff", f"{comp_rules(w)}")]
                            unmatched_set.discard(w.init)

                            if debug:
                                print("[yellow]match found!")
                                input(
                                    f"{w.init}: {matches_dict[w.init]}")

                        else:
                            w.comm = f"recursing lwff_fuzzy [yellow]{w.front}{w.word}{w.back}"
                            w.rfront = rfront_orig

                            if debug:
                                dprint(w)

                            recursive_removal(w)

                        previous_lwff_fuzzy = lwff_fuzzy

    if debug:
        input(f"lwff_fuzzy_list\n{lwff_fuzzy_list}\n")

    return lwff_fuzzy_list


def two_word_sandhi(w):
    front_orig = w.front
    rfront_orig = w.rfront
    rback_orig = w.rback

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

            # if f"{w.front}{wordB}{w.back}" not in w.matches:
            # w.matches += [f"{w.front}{wordB}{w.back}"]

            rfront_orig += [0]
            w.rfront = rfront_orig
            matches_dict[w.init] += [
                (f"{w.front}{wordB}{w.back}", "xword-2.1", "0")]
            unmatched_set.discard(w.init)
            
            if debug:
                print("[yellow]match found!")
                input(f"{w.init} {matches_dict[w.init]}")

            else:
                w.rfront = rfront_orig
                w.rback = rback_orig

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
                    rfront_orig += [rule+2]
                    w.rfront = rfront_orig

                    # if f"{w.front}{w.word}{w.back}" not in w.matches:
                    #     w.matches += [f"{w.front}{w.word}{w.back}"]
                    matches_dict[w.init] += [
                        (f"{w.front}{w.word}{w.back}", "xword-2.2",  f"{comp_rules(w)}")]
                    unmatched_set.discard(w.init)

                    if debug:
                        print("[yellow]match found!")
                        input(f"{w.init} {matches_dict[w.init]}\n")

                else:
                    w.rfront = rfront_orig
                    w.rback = rback_orig


def three_word_sandhi(w):

    front_orig = w.front
    back_orig = w.back
    rfront_orig = w.rfront
    rback_orig = w.rback

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

                matches_dict[w.init] += [
                    (f"{w.front}{w.word}{w.back}", "three word", "0,0")]
                unmatched_set.discard(w.init)

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
                            rfront_orig += []
                            rback_orig += [rule+2]
                            w.rback = rback_orig

                            matches_dict[w.init] += [
                                (f"{w.front}{w.word}{w.back}", "three word", f"{comp_rules(w)}")]
                            unmatched_set.discard(w.init)

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
                            rfront_orig += [rule+2]
                            w.rfront = rfront_orig
                            rback_orig += [0]
                            w.rback = rback_orig

                            matches_dict[w.init] += [
                                (f"{w.front}{w.word}{w.back}", "three word", f"{comp_rules(w)}")]
                            unmatched_set.discard(w.init)

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
                                rfront_orig += [rulex+2]
                                w.rfront = rfront_orig
                                rback_orig += [ruley+2]
                                w.rback = rback_orig

                                matches_dict[w.init] += [
                                    (f"{w.front}{w.word}{w.back}", "three word", f"{comp_rules(w)}")]
                                unmatched_set.discard(w.init)


def comp_rules(w):
    rules_list = w.rfront + w.rback
    rules_string = ""

    for rule in rules_list:
        rules_string += f"{rule},"
    return rules_string


def dprint(w):
    print(f"count:\t{w.count}")
    print(f"comm:\t{w.comm}")
    print(f"init:\t'{w.init}'")
    print(f"front:\t[blue]'{w.front}'")
    print(f"word:\t[blue]'{w.word}'")
    print(f"back:\t[blue]'{w.back}'")
    print(f"rfront:\t{w.rfront}")
    print(f"rback:\t{w.rback}")
    print(f"tried:\t{w.tried}")
    input()


def recursive_removal(w):

    if f"{w.front}{w.word}{w.back}" in w.tried:
        if debug:
            print(f"[red]{w.front}{w.word}{w.back} [white]tried already\n")
            input()

    else:
        if w.word in all_inflections_set:
            # if f"{w.front}{w.word}{w.back}" not in w.matches:
                # w.matches += [f"{w.front}{w.word}{w.back}"]
            matches_dict[w.init] += [
                (f"{w.front}{w.word}{w.back}", f"xword{w.comm}", f"{comp_rules(w)}")]
            unmatched_set.discard(w.init)

            if debug:
                print("[yellow] match found!!!!")
                dprint(w)
                input(f"{w.init} {matches_dict[w.init]}\n")

        else:
            w.tried += [f"{w.front}{w.word}{w.back}"]

        # negatives

        if (w.comm == "start" and
                w.word.startswith(("a", "na", "an", "nā"))):
            na = w.copy_class()
            na = negative_in_front(na)

        # sa

        elif (w.comm == ["start"] and
                w.word.startswith("sa")):
            sa = w.copy_class()
            sa_in_front(sa)

        # su

        elif (w.comm == ["start"] and
                w.word.startswith("su")):
            su = w.copy_class()
            su_in_front(su)

        # dur

        elif (w.comm == ["start"] and
                w.word.startswith("du")):
            dur = w.copy_class()
            dur_in_front(dur)

        # api eva iti

        apievaiti = re.findall("(pi|va|ti)$", w.word)
        if apievaiti != []:
            pi = w.copy_class()
            remove_apievaiti(pi)

        # two word sandhi
        if w.comm != "start":
            w2 = w.copy_class()
            w2.comm = "two word sandhi"

            if debug:
                dprint(w2)

            two_word_sandhi(w2)

            if matches_dict[w2.init] == []:

                # three word sandhi
                w3 = w.copy_class()
                w3.comm = "three word sandhi"
                three_word_sandhi(w3)

        # ffc = lwff clean

        ffc = w.copy_class()
        lwff_clean(ffc)

        # fbc = lwfb_clean

        fbc = w.copy_class()
        lwfb_clean(fbc)

        # fff = lwff fuzzy

        fff = w.copy_class()
        lwff_fuzzy(fff)


def summary():

    with open("sandhi/output/unmatched.csv", "w") as f:
        for item in unmatched_set:
            f.write(f"{item}\n")

    unmatched = len(unmatched_set)
    umatched_perc = (unmatched/unmatched_len_init)*100
    matched = unmatched_len_init-len(unmatched_set)
    matched_perc = (matched/unmatched_len_init)*100

    # perc_macthed = (100 - ((len(unmatched_set) / unmatched_len_init)*100))
    # perc_all = (100 - ((len(unmatched_set) / len(text_set))*100))
    # perc_unmatched = (unmatched_len_init-len(unmatched_set)/{unmatched_len_init})*100

    print(
        f"[green]unmatched:\t{unmatched} / {unmatched_len_init}\t[white]{umatched_perc:.2f}%")
    print(
        f"[green]matched:\t{matched} / {unmatched_len_init}\t[white]{matched_perc:.2f}%")


def main():
    tic()
    print("[yellow]sandhi splitter")

    global debug
    debug = False
    profiler_on = False

    if profiler_on is True:
        profiler = cProfile.Profile()
        profiler.enable()

    # make globally accessable vaiables
    setup()

    time_dict = {}
    global unmatched_len_init
    unmatched_len_init = len(unmatched_set)

    print(f"[green]splitting sandhi [white]{unmatched_len_init}")

    for word in unmatched_set.copy():
        bip()
        w = Word(word)
        matches_dict[w.init] = []

        if debug:
            dprint(w)

        if w.count % 1000 == 0:
            print(f"\t{w.count}/{unmatched_len_init}\t{w.word}")

        # two word sandhi
        w2 = w.copy_class()
        w2.comm = "two word sandhi"
        two_word_sandhi(w2)

        if matches_dict[word] != []:
            unmatched_set.discard(word)
            time_dict[word] = bop()

        else:
            # three word sandhi
            w3 = w.copy_class()
            w3.comm = "three word sandhi"
            three_word_sandhi(w3)

            if matches_dict[word] != []:
                unmatched_set.discard(word)
                time_dict[word] = bop()

            else:
                # recursive removal
                exlcuded = [
                    "kusalākusalasāvajjānavajjasevitabbāsevitabbahīnapaṇītakaṇhasukkasappaṭibhāgānaṃ",
                    "attahitaparahitaubhayahitasabbalokahitameva",
                    "kusalākusalasāvajjānavajjasevitabbāsevitabbahīna",
                ]

                if word not in exlcuded:
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

# w.tried not working properly

# two word three word sandhi use comment when writing to dict
# use na sa api in the beginning before two word sandhi

# in lwff lwffb, don't use the whole lists
# better startegy original_front, original_back
# stop more than 10 recursions
# fix rules

# postprocess
# write splits into db
# make goldendict etc

# add ttā and its inflections to all inflections
# test for su dur
# 2word only if comm != "start"

# think of some sanity tests

# ask subhuti to run in cloud with full text set

# aṭṭhicammamattameva
# aṭṭhi + camma + mattaṃ + eva + eva + eva + eva + eva

# 91000 took 1 hour 30 min
# 350 000 will take 5 hours
