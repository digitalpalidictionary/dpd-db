#!/usr/bin/env python3

"""Find missing word families."""

import re
import pickle
import pyperclip

from rich import print
from rich.prompt import Prompt

from sqlalchemy.orm.session import Session

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.meaning_construction import make_meaning
from tools.paths import ProjectPaths


def main():
    print("[bright_yellow]finding word families")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()

    word_family_dict = build_word_family_dict(dpd_db)
    word_order = order_word_family_dict(word_family_dict)
    word_family_set = make_word_family_set(db_session)

    find_in_family_compound(pth, db_session, word_family_dict, word_order)
    find_in_construction(dpd_db, word_family_set)
    find_in_pali_1(dpd_db, word_family_set)

    db_session.close()


def build_word_family_dict(dpd_db):
    """build a dict of family_compound with
    1. no comp in gramnar
    2. no root
    {family_compound: [headword1, headword2, etc]}"""

    print("[green]building word_family_dict")
    word_family_dict: dict = {}

    for i in dpd_db:
        if (
            not i.family_word and
            i.family_compound and
            not re.findall(r"\bcomp\b", i.grammar) and
            not i.root_key and
            "idiom" not in i.pos and
            "sandhi" not in i.pos
                ):
            for cf in i.family_compound_key_list:
                if cf not in word_family_dict:
                    word_family_dict[cf] = [i.pali_1]
                else:
                    word_family_dict[cf] += [i.pali_1]

    # # remove single entries
    # for i in word_family_dict.copy():
    #     if len(word_family_dict[i]) == 1:
    #         del word_family_dict[i]

    return word_family_dict


def order_word_family_dict(word_family_dict):
    """Sort the word_family_dict by number of items."""
    print("[green]sorting word_family_dict")

    word_order = sorted(
        word_family_dict,
        key=lambda k: len(word_family_dict[k]), reverse=True)

    return word_order


def find_in_family_compound(pth: ProjectPaths, db_session: Session, word_family_dict, word_order):
    """Test if word is compound or word_family and add info to db. """
    print("[green]finding word families in family_compound")

    processed_words = []
    break_flag = False
    exceptions_list = open_exceptions_list(pth)

    for word in word_order:
        if break_flag:
            break

        print()
        print("[cyan](c)ompound")
        print("[cyan](w)ord_family")
        print("[cyan](a)dd word_family")
        print("[cyan](e)xception")
        print("[cyan](r)oot")
        print("[cyan](p)ass")
        print("[cyan](s)kip word")
        print("[cyan](b)reak")

        print(f"{word}: {[x for x in word_family_dict[word]]} {len(word_family_dict)}")
        print(f"/^({'|'.join(word_family_dict[word])})$/")
        for x in word_family_dict[word]:
            if x not in processed_words:
                headword = db_session.query(
                        PaliWord).filter(PaliWord.pali_1 == x).first()
                if headword is not None and headword.pali_1 not in exceptions_list:
                    meaning = make_meaning(headword)
                    query = Prompt.ask(f"{x}: [green]{headword.pos}. [light_green]{meaning} ")
                    if query == "c":
                        headword.grammar += ", comp"
                        processed_words += [x]
                    elif query == "w":
                        headword.family_word = word
                    elif query == "a":
                        enter_wf = Prompt.ask("[red]what is the word family? ")
                        headword.family_word = enter_wf
                    elif query == "e":
                        exceptions_list += [headword.pali_1]
                    elif query == "r":
                        enter_root = Prompt.ask("[red]what is the root? ")
                        headword.root_key = enter_root
                    elif query == "p":
                        continue
                    elif query == "s":
                        break
                    elif query == "b":
                        break_flag = True
                        break
                    else:
                        print("[red]not a valid option")
            db_session.commit()
        save_exceptions_list(pth, exceptions_list)
        del word_family_dict[word]


def open_exceptions_list(pth: ProjectPaths):
    """Load pickle of exceptions."""
    try:
        with open(pth.wf_exceptions_list, "rb") as f:
            exceptions_list = pickle.load(f)
            print("[green]exceptions file loaded", end=" ")
            print(exceptions_list)
            return exceptions_list
    except FileNotFoundError:
        print("[red]exceptions file not found")
        return []


def save_exceptions_list(pth: ProjectPaths, exceptions_list):
    """Save pickle of exceptions."""
    with open(pth.wf_exceptions_list, "wb") as f:
        pickle.dump(exceptions_list, f)
    print("[green]exceptions file saved")


def make_word_family_set(db_session):
    """Make a set of all family words without numbers."""
    print("[green]making word family set", end=" ")

    word_family_set = set()

    wf_db = db_session.query(PaliWord).all()

    for i in wf_db:
        try:
            word_family_set.add(re.sub(r"\d", "", i.family_word))
        except TypeError:
            print(i.pali_1)

    exceptions = [
        "", "ka", "na", "a", "vi"
    ]

    for e in exceptions:
        if e in word_family_set:
            word_family_set.remove(e)

    print(len(word_family_set))

    return word_family_set


def find_in_construction(dpd_db, word_family_set):
    """Find family_words in construction."""
    print("[green]finding word families in construction")

    exceptions = [
        "adhi",
        "ati",
        "anu",
        "pa",
        "saṃ",
        "ka",
        "vi",
        "pati",
        "ta",
        "ya",
        "upa",
        "ti",
        "ava",
        "na",
        "ku",
        "kasāya",
        "dhanvana",
        "dhanu",
        "soṇita",
        "sa",
        "soṇa",
        "ā",
        "saṅkha",
        "ud",
        "upa",
        "khāraka 2",
        "kururu",
        "no 1.1",
        "saṅkasāyati",
        "avadāniya",
        "upacāla",
        "sahali",
        "ussukkāpetvā",
        "upāti",
        "hisi",
        "hiti",
    ]

    # find all headwords where
    # 1. not compound
    # 2. word familiy is in construction
    # 3. root is empty

    for counter, wf in enumerate(word_family_set):
        wf_list = []
        for i in dpd_db:
            if (
                not re.findall(r"\bcomp\b", i.grammar) and
                not re.findall(r"\bdeno", i.grammar) and
                not re.findall("sandhi", i.pos) and
                not re.findall("idiom", i.pos) and
                not re.findall("prefix", i.pos) and
                re.findall(fr"\b{wf}\b", i.construction) and
                not i.family_word and
                not i.root_key):
                wf_list += [i.pali_1]
            for e in exceptions:
                if e in wf_list:
                    wf_list.remove(e)

        if len(wf_list) > 0:
            print(f"{counter}. {wf}: {wf_list}")
            regex = fr"/\b{wf}\b|^({'|'.join(wf_list)})$/"
            print(regex)
            pyperclip.copy(regex)
            input()

        if counter % 100 == 0:
            print(f"{counter}. {wf}: {wf_list}")


def find_in_pali_1(dpd_db, word_family_set):
    """Find clean headwords which match family_word."""
    print("[green]finding word families in pali_1")

    wf_dict = {}
    exceptions = [
        "addha 1.1",
        "assa 2.1",
        "assa 5.1",
        "āma 1.1",
        "ibha 1",
        "ela 2",
        "kora 1",
        "khīla 2.1",
        "pati 3.4",
        "sa 6.1",
        "sata 3.1",
        "sattu 1.1",
        "samma 2",
        "sāla 2.1"
    ]

    pos_exceptions = ["abbrev", "prefix", "suffix", "cs", "ve", "sandhi"]

    for i in dpd_db:
        if (i.pali_clean in word_family_set and
                i.pali_1 not in exceptions and
                not i.family_word and
                not i.root_key and
                i.pos not in pos_exceptions):
            if i.pali_clean not in wf_dict:
                wf_dict[i.pali_clean] = [i.pali_1]
            else:
                wf_dict[i.pali_clean] += [i.pali_1]

    for counter, wf in enumerate(wf_dict):
        print(f"{counter+1} / {len(wf_dict)}\t{wf}")
        regex = fr"/\b{wf}\b|^({'|'.join(wf_dict[wf])})$/"
        print(regex)
        pyperclip.copy(regex)
        input()


if __name__ == "__main__":
    main()
