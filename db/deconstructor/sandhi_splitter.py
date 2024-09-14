#!/usr/bin/env python3

"""Recursive algorithm to deconstruct compounds and split sandhi. """

import cProfile
import logging
import pandas as pd
import pickle
import re
import time

from rich import print
from typing import Optional, Set, TypedDict, Union, Self
from os import popen

from tools.pali_alphabet import vowels, double_consonants
from tools.tic_toc import tic, toc, bip, bop
from tools.paths import ProjectPaths
from tools.configger import config_test

# two word sandhi
#     ↓
#     ↓
#  three word sandhi
#     ↓
#     ↓
# recursive function < -------- < ---------- <
#     ↓                                      ↑
#     > -------- > na sa su dur ----- > -----↑
#     > -------- > two word --------- > -----↑
#     > -------- > front clean ------ > -----↑
#     > -------- > back clean ------- > -----↑
#     > -------- > front fuzzy ------ > -----↑
#     > -------- > back fuzzzy ------ > -----↑

# global dampers
global clean_list_max_length
global fuzzy_list_max_length
global clean_word_min_length
global fuzzy_word_min_length
global max_matches
global max_recursions
global profiler
global profiler_on
global max_word_length
clean_list_max_length = 3
fuzzy_list_max_length = 4
clean_word_min_length = 2
fuzzy_word_min_length = 1
max_matches = 20
max_recursions = 15
profiler_on = False
profiler: Optional[cProfile.Profile] = None
max_word_length = 1000


class Word:
    count_value: int = 0

    def __init__(self, word: str):
        Word.count_value += 1
        self.count = Word.count_value
        self.word: str = word
        self.tried: Set = set()
        self.matches = set()
        self.front = ""
        self.back = ""
        self.start_time = time.time()

    @property
    def comp(self):
        return self.front + self.word + self.back
    
    @property
    def overtime(self):
        return time.time() - self.start_time > 10

    def copy_class(self):
        word_copy = Word.__new__(Word)
        word_copy.__dict__.update(self.__dict__)
        word_copy.count = Word.count_value
        return word_copy
    

class DotDictInit(TypedDict):
    count: int
    comm: str
    init: str
    front: str
    word: str
    back: str
    rules_front: str
    rules_back: str
    tried: set
    matches: set
    path: str
    processes: int

def default_dot_dict_init(counter: int, word: str) -> DotDictInit:
    return DotDictInit(
        count = counter,
        comm = "start",
        init = word,
        front = "",
        word = word,
        back = "",
        rules_front = "",
        rules_back = "",
        tried = set(),
        matches =  set(),
        path = "start",
        processes = 0,
    )

class DotDict:
    count = 0
    comm = "start"
    init = ""
    front = ""
    back = ""
    rules_front = ""
    rules_back = ""
    word = ""
    tried = set()
    matches = set()
    path = "start"
    processes = 0

    def __init__(self, d: Union[DotDictInit, Self]):
        if isinstance(d, dict):
            for key in d:
                setattr(self, key, d[key])

        elif isinstance(d, DotDict):
            for key in d.__dict__:
                setattr(self, key, getattr(d, key))

        else:
            raise TypeError("Invalid argument type.")

def comp(d):
    return f"{d.front}{d.word}{d.back}"


def setup(pth: ProjectPaths):
    print("[green]importing assets")

    global rules
    rules = import_sandhi_rules(pth)

    global unmatched_set
    with open(pth.unmatched_set_path, "rb") as f:
        unmatched_set = pickle.load(f)

    global all_inflections_set
    with open(pth.all_inflections_set_path, "rb") as f:
        all_inflections_set = pickle.load(f)

    global all_inflections_nofirst
    global all_inflections_nolast

    (all_inflections_nofirst,
        all_inflections_nolast) = make_all_inflections_nfl_nll(
            all_inflections_set)

    # initalise matches.csv
    with open(pth.matches_path, "w") as f:
        f.write("")

    # initalise timer dict
    with open(pth.sandhi_timer_path, "w") as f:
        f.write("")


def import_sandhi_rules(pth: ProjectPaths):
    print("[green]importing sandhi rules", end=" ")

    sandhi_rules_df = pd.read_csv(
        pth.sandhi_rules_path, sep="\t", dtype=str)
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
        import_sandhi_rules(pth)
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
        import_sandhi_rules(pth)

    else:
        print("[white]ok")

    return sandhi_rules


def make_all_inflections_nfl_nll(all_inflections_set):
    """all inflections with no first letter, no last letter"""

    print("[green]making all inflections nfl & nll", end=" ")

    all_inflections_nofirst = set()
    all_inflections_nolast = set()

    for inflection in all_inflections_set:
        # no first letter
        all_inflections_nofirst.add(inflection[1:])
        # no last letter
        all_inflections_nolast.add(inflection[:-1])

    print(f"[white]{len(all_inflections_nofirst):,}")

    return all_inflections_nofirst, all_inflections_nolast


def main():
    tic()
    print("[bright_yellow]sandhi splitter")
    if not (
        config_test("exporter", "make_deconstructor", "yes") or 
        config_test("exporter", "make_tpr", "yes") or 
        config_test("exporter", "make_ebook", "yes") or 
        config_test("regenerate", "db_rebuild", "yes")
    ):
        print("[green]disabled in config.ini")
        toc()
        return

    global profiler
    if profiler_on:
        profiler = cProfile.Profile()
        profiler.enable()
    
    pth = ProjectPaths()

    # logging
    logging.basicConfig(
        filename=pth.sandhi_log_path, level=logging.INFO, 
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    # make globally accessible variables
    setup(pth)

    global matches_dict
    with open(pth.matches_dict_path, "rb") as f:
        matches_dict = pickle.load(f)

    time_dict = {}
    global unmatched_len_init
    unmatched_len_init = len(unmatched_set)

    print(f"[green]splitting sandhi [white]{unmatched_len_init:,}")

    for counter, word in enumerate(unmatched_set.copy()):

        bip()
        logging.info(word)

        global w
        w = Word(word)
        matches_dict[word] = []

        # d is a dictionary of data accessed using dot notation
        d = DotDict(default_dot_dict_init(counter, word))

        # two word sandhi
        d = two_word_sandhi(d)

        # iti + assa / assā
        if d.word.endswith(("tissa", "tissā")):
            d = remove_tissa(d)

        # three word sandhi
        if not w.matches:
            d = three_word_sandhi(d)

        # # recursive removal
        if not w.matches:
            recursive_removal(d)

        time_dict[word] = bop()

        if d.count % 1000 == 0:
            print(
                f"{d.count:>10,} / {unmatched_len_init:<10,}{d.word}")

            save_matches(pth, matches_dict)
            try:
                save_timer_dict(pth, time_dict)
            except KeyError:
                pass
            matches_dict = {}
            time_dict = {}     

    save_matches(pth, matches_dict)

    try:
        save_timer_dict(pth, time_dict)
    except KeyError as e:
        print(f"[red] {e}")

    summary(pth)
    toc()

    if profiler is not None:
        profiler.disable()
        profiler.dump_stats('profiler.prof')
        yes_no = input("open profiler? (y/n) ")
        if yes_no == "y":
            popen("tuna profiler.prof")


def save_matches(pth: ProjectPaths, matches_dict):

    with open(pth.matches_path, "a") as f:
        for word, data in matches_dict.items():
            for item in data:
                f.write(f"{word}\t")
                for column in item:
                    f.write(f"{column}\t")
                f.write("\n")


def save_timer_dict(pth: ProjectPaths, time_dict):
    df = pd.DataFrame.from_dict(time_dict, orient="index")
    df = df.sort_values(by=0, ascending=False)
    df.to_csv(
        pth.sandhi_timer_path, mode="a", header=False, sep="\t")


def recursive_removal(d: DotDict) -> None:

    if w.overtime:
        return

    d.processes += 1

    # global dampers
    if d.processes < max_recursions and len(w.matches) < max_matches:

        if comp(d) not in w.tried:
            w.tried.add(comp(d))
            d.tried.add(comp(d))

            if d.word in all_inflections_set:
                
                # add to matches
                if comp(d) not in w.matches:
                    matches_dict[d.init] += [(
                        comp(d), f"xword{d.comm}",
                        f"{comp_rules(d)}", d.path)]
                    w.matches.add(comp(d))
                    d.matches.add(comp(d))
                    unmatched_set.discard(d.init)

            else:
                # recursion
                if d.processes == 1:

                    # a na an nā
                    if d.word.startswith(("a", "na", "an", "nā")):
                        d = remove_neg(d)

                    # sa
                    if d.word.startswith("sa"):
                        d = remove_sa(d)

                    # su
                    if d.word.startswith("su"):
                        d = remove_su(d)

                    # dur
                    if d.word.startswith("du"):
                        d = remove_dur(d)

                    # ati
                    if d.word.startswith("ati"):
                        d = remove_ati(d)

                    # tā ttā
                    if d.word.endswith(("tā", "ttā", "tāya")):
                        d = remove_tta(d)

                    if d.word.endswith(("tissa", "tissā")):
                        d = remove_tissa(d)

                # two word sandhi
                if d.comm != "start":
                    d = two_word_sandhi(d)

                # ffc = lwff clean
                d = remove_lwff_clean(d)

                # fff = lwff fuzzy
                d = remove_lwff_fuzzy(d)

                # api eva iti
                if re.findall("(pi|va|ti)$", d.word) != []:
                    d = remove_apievaiti(d)

                # double consonants at the beginning
                dc_str = "|".join(double_consonants)
                if re.findall(f"^({dc_str})", d.word):
                    d = remove_double_consonants(d)

                if not w.matches:
                    # fbc = lwfb_clean
                    d = remove_lwfb_clean(d)

                    # fbf = lwfb fuzzy
                    d = remove_lwfb_fuzzy(d)


def remove_neg(d: DotDict) -> DotDict:
    """finds neg in front then
    1. finds match 2. recurses 3. passes through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches and len(d.word) > 2:
        d.path += " > neg"
        d.rules_front = "na,"
        d.front = f"na + {d.front}"

        if d.word.startswith("a"):
            if d.word[1] == d.word[2]:
                
                d.word = d.word[2:]
            else:
                d.word = d.word[1:]
            

        elif d.word.startswith("an"):
            d.word = d.word[2:]

        elif d.word.startswith("na"):
            if d.word[2] == d.word[3]:
                d.word = d.word[3:]
            else:
                d.word = d.word[2:]

        elif d.word.startswith("nā"):
            d.word = f"a{d.word[2:]}"

        if d.word in all_inflections_set:
            d.comm = f"match! = {comp(d)}"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [(
                    comp(d), "xword-na", "na", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing from na"
            recursive_removal(d)

        d = DotDict(d_orig)

    return d_orig


def remove_sa(d: DotDict) -> DotDict:
    """find sa in front then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches and len(d.word) > 3:
        d.path += " > sa"
        d.front = f"sa + {d.front}"
        d.rules_front = "sa,"

        if d.word[2] == d.word[3]:
            d.word = d.word[3:]

        else:
            d.word = d.word[2:]
        
        if d.word in all_inflections_set:
            d.comm = "sa"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-sa", "sa", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing sa"
            recursive_removal(d)

        d = DotDict(d_orig)

    return d_orig


def remove_su(d: DotDict) -> DotDict:
    """find su in front then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches and len(d.word) > 3:
        d.path += " > su"
        d.front = f"su + {d.front}"
        d.rules_front += "su,"
        if d.word[2] == d.word[3]:
            d.word = d.word[3:]
        else:
            d.word = d.word[2:]
        
        if d.word in all_inflections_set:
            d.comm = "su"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-su", "su", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing su"
            recursive_removal(d)

        d = DotDict(d_orig)

    return d_orig


def remove_dur(d: DotDict) -> DotDict:
    """find du(r) in front then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches and len(d.word) > 3:
        d.path += " > dur"
        d.rules_front = "dur,"
        d.front = f"dur + {d.front}"
        if d.word[2] == d.word[3]:
            d.word = d.word[3:]
        else:
            d.word = d.word[2:]
        
        if d.word in all_inflections_set:
            d.comm = "dur"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-dur", "dur", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing dur"
            recursive_removal(d)

        d = DotDict(d_orig)

    return d_orig


def remove_ati(d: DotDict) -> DotDict:
    """find ati in front then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches and len(d.word) > 3:
        d.path += " > ati"
        d.front = f"ati + {d.front}"
        d.rules_front += "ati,"

        if d.word[3] == d.word[4]:
            d.word = d.word[4:]
        else:
            d.word = d.word[3:]

        if d.word in all_inflections_set:
            d.comm = "ati"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-ati", "ati", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing ati"
            recursive_removal(d)

        d = DotDict(d_orig)

    return d_orig


def remove_tta(d: DotDict) -> DotDict:
    """find tā, ttā, tāya in back then
    1. match 2. recurse or 3. pass through.
    These are suffix which create abstract nouns,
    very common in the commentaries."""

    d_orig = DotDict(d)

    if comp(d) not in w.matches and len(d.word) > 3:
        d.path += " > tta"
        if d.word.endswith("ttā"):
            d.back = f"{d.back} + ttā"
            d.word = d.word[:-3]
            d.rules_back = f"ttā,{d.rules_back}"

        elif d.word.endswith("tā"):
            d.back = f"{d.back} + tā"
            d.word = d.word[:-2]
            d.rules_back = f"tā,{d.rules_back}"

        elif d.word.endswith("tāya"):
            d.back = f"{d.back} + tāya"
            d.word = d.word[:-4]
            d.rules_back = f"tāya,{d.rules_back}"

        if d.word in all_inflections_set:
            d.comm = "tta"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-tta", "tta", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing tta"
            recursive_removal(d)

        d = DotDict(d_orig)

    return d_orig


def remove_tissa(d: DotDict) -> DotDict:
    """find tissa or tissā in last place then
    1. match 2. recurse or 3. pass through.
    This fixes the problem of 'iti + assa / assā' being taken as tissa / tissā,
    very common in the commentaries."""

    d_orig = DotDict(d)

    if comp(d) not in w.matches and len(d.word) > 3:
        d.path += " > tissa"
        if d.word.endswith("tissa"):
            d.back = f"{d.back} + iti + assa"
            d.word = d.word[:-5]
            d.rules_back = f"tissa,{d.rules_back}"

        if d.word.endswith("tissā"):
            d.back = f"{d.back} + iti + assā"
            d.word = d.word[:-5]
            d.rules_back = f"tissa,{d.rules_back}"

        if d.word in all_inflections_set:
            d.comm = "tissa"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-tissa", "tissa", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing tissa"
            recursive_removal(d)

        d = DotDict(d_orig)

    return d_orig


def remove_double_consonants(d: DotDict) -> DotDict:
    """find double consontant at the start or end and remove
    1. match 2. recurse or 3. pass through.
    """

    d_orig = DotDict(d)

    if comp(d) not in w.matches and len(d.word) > 4:
        d.path += " > dc"
        if any(d.word.startswith(dc) for dc in double_consonants):
            d.word = d.word[1:]
            d.rules_front += "dc,"

        if d.word in all_inflections_set:
            d.comm = "dc"

            if comp(d) not in w.matches:
                matches_dict[d.init] += [
                    (comp(d), "xword-dc", "dc", d.path)]
                w.matches.add(comp(d))
                d.matches.add(comp(d))
                unmatched_set.discard(d.init)

        else:
            d.comm = "recursing dc"
            recursive_removal(d)

        d = DotDict(d_orig)

    return d_orig


def remove_apievaiti(d: DotDict) -> DotDict:
    """find api eva or iti using sandhi rules then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches:

        try:
            if d.word[-3] in vowels:
                wordA = d.word[:-3]
                wordB = d.word[-3:]

            else:
                wordA = d.word[:-2]
                wordB = d.word[-2:]

        except Exception:
            wordA = d.word[:-2]
            wordB = d.word[-2:]

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
                    d.word = d.word.replace(wordB, "")
                    d.word = d.word.replace(wordA, word1)
                    d.back = f" + {word2}{d.back}"
                    d.comm = "apievaiti"
                    d.rules_back = f"{rule+2},{d.rules_back}"
                    d.path += " > apievaiti"

                    if d.word in all_inflections_set:
                        d.comm = f"match! = {comp(d)}"

                        if comp(d) not in w.matches:
                            matches_dict[d.init] += [
                                (comp(d), "xword-pi", "apievaiti", d.path)]
                            w.matches.add(comp(d))
                            d.matches.add(comp(d))
                            unmatched_set.discard(d.init)

                    else:
                        recursive_removal(d)

                    d = DotDict(d_orig)

    return d_orig


def remove_lwff_clean(d: DotDict) -> DotDict:
    """make a list of the longest clean words from the front then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches:

        lwff_clean_list = []

        for i in range(len(d.word)):
            if d.word[:-i] in all_inflections_set:
                lwff_clean_list.append(d.word[:-i])

        lwff_clean_list = lwff_clean_list[:clean_list_max_length]

        for lwff_clean in lwff_clean_list:

            if len(lwff_clean) >= clean_word_min_length:
                d.path += " > front_clean"
                d.word = re.sub(f"^{lwff_clean}", "", d.word, count=1)
                d.front = f"{d.front}{lwff_clean} + "
                d.comm = f"lwff_clean [yellow]{lwff_clean}"
                d.rules_front += "0,"

                if d.word in all_inflections_set:

                    if comp(d) not in w.matches:
                        matches_dict[d.init] += [(
                            comp(d), "xword-lwff",
                            f"{comp_rules(d)}", d.path)]
                        w.matches.add(comp(d))
                        unmatched_set.discard(d.init)

                else:
                    d.comm = f"recursing lwff_clean [yellow]{comp(d)}"
                    recursive_removal(d)

                d = DotDict(d_orig)

    return d_orig


def remove_lwfb_clean(d: DotDict) -> DotDict:
    """make list of the longest clean words from the back then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches:

        lwfb_clean_list = []

        for i in range(len(d.word)):
            if d.word[i:] in all_inflections_set:
                lwfb_clean_list.append(d.word[i:])

        lwfb_clean_list = lwfb_clean_list[:clean_list_max_length]

        for lwfb_clean in lwfb_clean_list:

            if len(lwfb_clean) >= clean_word_min_length:
                d.path += " > back_clean"
                d.word = re.sub(f"{lwfb_clean}$", "", d.word, count=1)
                d.back = f" + {lwfb_clean}{d.back}"
                d.comm = f"lwfb_clean [yellow]{lwfb_clean}"
                d.rules_back = f"0,{d.rules_back}"

                if d.word in all_inflections_set:
                    if comp(d) not in w.matches:
                        matches_dict[d.init] += [(
                            comp(d), "xword-lwfb", f"{comp_rules(d)}", d.path)]
                        w.matches.add(comp(d))
                        d.matches.add(comp(d))
                        unmatched_set.discard(d.init)

                else:
                    d.comm = f"recursing lfwb_clean [yellow]{comp(d)}"
                    recursive_removal(d)

                d = DotDict(d_orig)

    return d_orig


def remove_lwff_fuzzy(d: DotDict) -> DotDict:
    """make a list of the longest fuzzy words from the front then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in d.matches:

        lwff_fuzzy_list = []

        if len(d.word) >= fuzzy_word_min_length:
            for i in range(len(d.word)):
                fuzzy_word = d.word[:-i]

                if (fuzzy_word in all_inflections_nolast or
                        fuzzy_word in all_inflections_set):
                    lwff_fuzzy_list.append(fuzzy_word)

        lwff_fuzzy_list = lwff_fuzzy_list[:fuzzy_list_max_length]

        for lwff_fuzzy in lwff_fuzzy_list:

            if len(lwff_fuzzy) >= fuzzy_word_min_length:

                wordA_fuzzy = lwff_fuzzy
                wordB_fuzzy = re.sub(f"^{wordA_fuzzy}", "", d.word, count=1)

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
                            d.path += " > front_fuzzy"
                            d.word = re.sub(
                                f"^{wordA_fuzzy}", "", d.word, count=1)
                            d.word = re.sub(
                                f"^{wordB_fuzzy}", word2, d.word, count=1)
                            d.front = f"{d.front}{word1} + "
                            d.comm = f"lwff_fuzzy [yellow]{word1} + {word2}"
                            d.rules_front += f"{rule+2},"

                            if d.word in all_inflections_set:
                                if comp(d) not in w.matches:
                                    matches_dict[d.init] += [(
                                        comp(d), "xword-fff",
                                        f"{comp_rules(d)}", d.path)]
                                    w.matches.add(comp(d))
                                    d.matches.add(comp(d))
                                    unmatched_set.discard(d.init)

                            else:
                                d.comm = f"recursing lwff_fuzzy {comp(d)}"
                                recursive_removal(d)

                            d = DotDict(d_orig)

    return d_orig


def remove_lwfb_fuzzy(d: DotDict) -> DotDict:
    """make a list of the longest fuzzy words from the back then
    1. match 2. recurse or 3. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches:

        lwfb_fuzzy_list = []

        if len(d.word) > 0:
            for i in range(len(d.word)):
                fuzzy_word = d.word[i:]

                if (fuzzy_word in all_inflections_nofirst or
                        fuzzy_word in all_inflections_set):
                    lwfb_fuzzy_list.append(fuzzy_word)

        lwfb_fuzzy_list = lwfb_fuzzy_list[:fuzzy_list_max_length]

        for lwfb_fuzzy in lwfb_fuzzy_list:

            if len(lwfb_fuzzy) >= fuzzy_word_min_length:
                wordA_fuzzy = re.sub(f"{lwfb_fuzzy}$", "", d.word, count=1)
                wordB_fuzzy = lwfb_fuzzy

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
                            d.path += " > back_fuzzy"
                            d.word = re.sub(
                                f"{wordB_fuzzy}$", "", d.word, count=1)
                            d.word = re.sub(
                                f"{wordA_fuzzy}$", word1, d.word, count=1)
                            # d.back = re.sub(
                            #     f"{wordB_fuzzy}$", word2, d.back, count=1)
                            d.back = f" + {word2}{d.back}"
                            d.comm = f"lwfb_fuzzy [yellow]{word1} + {word2}"
                            d.rules_back = f"{rule+2},{d.rules_back}"

                            if d.word in all_inflections_set:
                                if comp(d) not in w.matches:
                                    matches_dict[d.init] += [(
                                        comp(d), "xword-fbf",
                                        f"{comp_rules(d)}", d.path)]
                                    w.matches.add(comp(d))
                                    d.matches.add(comp(d))
                                    unmatched_set.discard(d.init)

                            else:
                                d.comm = f"recursing lwfb_fuzzy {comp(d)}"
                                recursive_removal(d)

                            d = DotDict(d_orig)

    return d_orig


def two_word_sandhi(d: DotDict) -> DotDict:
    """split into two words, apply sandhi rules then
    1. match or 2. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches:

        for x in range(0, len(d.word)-1):

            wordA = d.word[:-x-1]
            wordB = d.word[-1-x:]
            try:
                wordA_lastletter = wordA[len(wordA)-1]
            except Exception:
                wordA_lastletter = ""
            wordB_firstletter = wordB[0]

            # blah blah

            if (wordA in all_inflections_set and
                    wordB in all_inflections_set):
                d.front = f"{d.front}{wordA} + "
                d.word = wordB
                d.rules_front += "0,"
                d.path += " > 2.1"
                if d.comm == "start":
                    d.comm = "start2.1"
                else:
                    d.comm = "x2.1"

                if comp(d) not in d.matches:
                    matches_dict[d.init] += [(
                        f"{d.front}{wordB}{d.back}",
                        d.comm, comp_rules(d), d.path)]
                    w.matches.add(comp(d))
                    d.matches.add(comp(d))
                    unmatched_set.discard(d.init)

                d = DotDict(d_orig)

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
                        d.front = f"{d.front}{word1} + "
                        d.word = word2
                        d.rules_front += f"{rule+2},"
                        d.path += " > 2.2"
                        if d.comm == "start":
                            d.comm = "start2.2"
                        else:
                            d.comm = "x2.2"

                        if comp(d) not in w.matches:
                            matches_dict[d.init] += [
                                (comp(d), d.comm, f"{comp_rules(d)}", d.path)]
                            w.matches.add(comp(d))
                            d.matches.add(comp(d))
                            unmatched_set.discard(d.init)

                    d = DotDict(d_orig)

    return d_orig


def three_word_sandhi(d: DotDict) -> DotDict:
    """split into three words, apply sandhi rules then
    1. match or 2. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches:

        for x in range(0, len(d.word)-1):

            wordA = d.word[:-x-1]
            try:
                wordA_lastletter = wordA[len(wordA)-1]
            except Exception:
                wordA_lastletter = ""

            for y in range(0, len(d.word[-1-x:])-1):
                wordB = d.word[-1-x:-y-1]
                try:
                    wordB_firstletter = wordB[0]
                except Exception:
                    wordB_firstletter = ""
                try:
                    wordB_lastletter = wordB[len(wordB)-1]
                except Exception:
                    wordB_lastletter = ""

                wordC = d.word[-1-y:]
                wordC_firstletter = wordC[0]

                # blah blah blah

                if (wordA in all_inflections_set and
                    wordB in all_inflections_set and
                        wordC in all_inflections_set):

                    d.front = f"{d.front}{wordA} + "
                    d.word = wordB
                    d.back = f" + {wordC}{d.back}"
                    d.rules_front += "0,"
                    d.rules_back = f"0,{d.rules_back}"
                    d.path += " > 3.1"
                    if d.comm == "start":
                        d.comm = "start3.1"
                    else:
                        d.comm = "x3.1"

                    if comp(d) not in w.matches:
                        matches_dict[d.init] += [
                            (comp(d), d.comm, "0,0", d.path)]
                        w.matches.add(comp(d))
                        d.matches.add(comp(d))
                        unmatched_set.discard(d.init)

                    d = DotDict(d_orig)

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

                                d.front = f"{d.front}{wordA} + "
                                d.word = word2
                                d.back = f" + {word3}{d.back}"
                                d.rules_front += "0,"
                                d.rules_back = f"{rule+2},{d.rules_back}"
                                d.path += " > 3.2"
                                if d.comm == "start":
                                    d.comm = "start3.2"
                                else:
                                    d.comm = "x3.2"

                                if comp(d) not in w.matches:
                                    matches_dict[d.init] += [(
                                        comp(d), d.comm,
                                        f"{comp_rules(d)}", d.path)]
                                    w.matches.add(comp(d))
                                    d.matches.add(comp(d))
                                    unmatched_set.discard(d.init)

                                d = DotDict(d_orig)

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

                                d.front = f"{d.front}{word1} + "
                                d.word = word2
                                d.back = f" + {wordC}{d.back}"
                                d.rules_front += f"{rule+2},"
                                d.rules_back = f"0,{d.rules_back}"
                                d.path += " > 3.3"
                                if d.comm == "start":
                                    d.comm = "start3.3"
                                else:
                                    d.comm = "x3.3"

                                if comp(d) not in w.matches:
                                    matches_dict[d.init] += [(
                                        comp(d), d.comm,
                                        f"{comp_rules(d)}", d.path)]
                                    w.matches.add(comp(d))
                                    d.matches.add(comp(d))
                                    unmatched_set.discard(d.init)

                                d = DotDict(d_orig)

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

                                    d.front = f"{d.front}{word1} + "
                                    d.word = word2
                                    d.back = f" + {word3}{d.back}"
                                    d.rules_front += f"{rulex+2},"
                                    d.rules_back = f"{ruley+2},{d.rules_back}"
                                    d.path += " > 3.4"
                                    if d.comm == "start":
                                        d.comm = "start3.4"
                                    else:
                                        d.comm = "x3.4"

                                    if comp(d) not in w.matches:
                                        matches_dict[d.init] += [(
                                            comp(d), d.comm,
                                            f"{comp_rules(d)}", d.path)]
                                        w.matches.add(comp(d))
                                        d.matches.add(comp(d))
                                        unmatched_set.discard(d.init)

                                    d = DotDict(d_orig)

    return d_orig


def four_word_sandhi(d: DotDict) -> DotDict:

    """split into four words, apply sandhi rules, then
    1. match or 2. pass through"""

    d_orig = DotDict(d)

    if comp(d) not in w.matches:

        for x in range(0, len(d.word)-1):
            wordA = d.word[:-x-1]
            wordA_lastletter = wordA[len(wordA)-1]

            for y in range(0, len(d.word[-1-x:])-1):
                wordB = d.word[-1-x:-y-1]
                wordB_firstletter = wordB[0]
                wordB_lastletter = wordB[len(wordB)-1]
                wordC = d.word[-1-y:]
                wordC_firstletter = wordC[0]

                for z in range(0, len(d.word[-1-y:])-1):
                    wordC = d.word[-1-y:-z-1]
                    wordC_firstletter = wordC[0]
                    wordC_lastletter = wordC[len(wordC)-1]
                    wordD = d.word[-1-z:]
                    wordD_firstletter = wordD[0]

                    # bla* *la* *la* *lah

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

                                if wordB_lastletter == chAy and \
                                        wordC_firstletter == chBy:
                                    word2 = (ch2x + wordB[1:])[:-1] + ch1y
                                    word3 = ch2y + wordC[1:]

                                    for rulez in rules:
                                        chAz = rules[rulez]["chA"]
                                        chBz = rules[rulez]["chB"]
                                        ch1z = rules[rulez]["ch1"]
                                        ch2z = rules[rulez]["ch2"]

                                        if (wordC_lastletter == chAz and
                                                wordD_firstletter == chBz):
                                            word3 = (
                                                ch2y + wordC[1:])[:-1] + ch1z
                                            word4 = ch2z + wordD[1:]

                                            if (word1 in all_inflections_set
                                                and
                                                word2 in all_inflections_set
                                                and
                                                word3 in all_inflections_set
                                                and
                                                    word4 in all_inflections_set):
                                                d.front = f"{d.front}{word1} + {word2} + "
                                                d.word = word3
                                                d.back = f" + {word4}{d.back}"
                                                d.rules_front += f"{rulex+2},{ruley+2}"
                                                d.rules_back = f"{rulez+2},{d.rules_back}"
                                                d.path += " > 4"
                                                d.comm = "x4"

                                                if comp(d) not in w.matches:
                                                    matches_dict[d.init] += [(
                                                        comp(d), d.comm,
                                                        f"{comp_rules(d)}",
                                                        d.path)]
                                                    w.matches.add(comp(d))
                                                    d.matches.add(comp(d))
                                                    unmatched_set.discard(
                                                        d.init)

                                                d = DotDict(d_orig)

    return d_orig


def comp_rules(d: DotDict) -> str:
    return f"{d.rules_front}{d.rules_back}"


def dprint(d: DotDict) -> None:
    print(f"count:\t{d.count}")
    print(f"comm:\t{d.comm}")
    print(f"init:\t'{d.init}'")
    print(f"front:\t[blue]'{d.front}'")
    print(f"word:\t[blue]'{d.word}'")
    print(f"back:\t[blue]'{d.back}'")
    print(f"comp:\t[yellow]{comp(d)}")
    print(f"rules_front:\t{d.rules_front}")
    print(f"rules_back:\t{d.rules_back}")
    # print(f"tried:\t{d.tried}")
    # print(f"matches:\t{d.matches}")
    print(f"path:\t{d.path}")
    print(f"processes:\t{d.processes}")
    print()


def summary(pth: ProjectPaths):

    print("[green]writing unmatched set")

    with open(pth.unmatched_path, "w") as f:
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

    for __word__, matches in matches_dict.items():
        match_count += len(matches)

    match_average = match_count / word_count

    print(f"[green]match count:\t{match_count:,}")
    print(f"[green]match average:\t{match_average:.4f}")


if __name__ == "__main__":
    main()

# Pathavīkasiṇasamāpattintiādi
# dūteyyapahinagamanānuyogapabhedaṃ
# bhāvanārāmāriyavaṃsaṃ
# suttantabhājanīyaabhidhammabhājanīyapañhapucchakanayānaṃ
# anuttaradakkhiṇeyyatāuttamapūjanīyanamassanīyabhāvapūjananamassanakiriyāya
# dukkhānupassanāvisesoyeva
# sammāsambuddhantyādimāha
# vimissanavasena why na?

# include neg count in post process

# gosaddantassāvādesaṃ > sa + go + danta + assāvā + esaṃ
# !!! why sa first?
