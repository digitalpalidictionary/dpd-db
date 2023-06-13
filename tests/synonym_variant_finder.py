#!/usr/bin/env python3.11
import re
import pickle
import pyperclip

from rich import print
from rich.prompt import Prompt

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.db_search_string import db_search_string
from tools.pali_sort_key import pali_list_sorter, pali_sort_key
from tools.paths import ProjectPaths as PTH
from tools.tic_toc import tic, toc

nouns = ["masc", "fem", "nt"]


def main():
    tic()
    print("[bright_yellow]finding synonyms and variants")

    db_session = get_db_session("dpd.db")
    dpd_db = db_session.query(PaliWord).all()

    exceptions = load_exceptions()

    identical_meaning_dict = find_identical_meanings(
        dpd_db, exceptions)

    add_identical_meanings(
        identical_meaning_dict, db_session, exceptions)

    single_meaning_dict = find_single_meanings(
        dpd_db, exceptions)

    add_single_meanings(
        single_meaning_dict, db_session, exceptions)

    toc()


def load_exceptions():
    """Load exceptions pickle file."""
    try:
        with open(PTH.syn_var_exceptions_path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []


def find_identical_meanings(dpd_db, exceptions):
    """Find words with the same pos and identical clean meanings."""
    print(f"[green]{'finding identical meanings'}", end=" ")

    identical_meaning_dict: dict = {}

    for counter, i in enumerate(dpd_db):
        if i.meaning_1:
            meaning = clean_meaning(i.meaning_1)

            if i.pos in nouns:
                pos_meaning = f"[noun] {meaning}"
            else:
                pos_meaning = f"[{i.pos}] {meaning}"

            if (
                i.pos != "pron" and
                meaning and
                pos_meaning not in exceptions and
                # no cases in grammar
                not re.findall(
                    r"\b(nom|acc|instr|dat|abl|gen|loc|voc)\b", i.grammar)
            ):
                if pos_meaning not in identical_meaning_dict:
                    identical_meaning_dict[pos_meaning] = [i.pali_1]
                else:
                    identical_meaning_dict[pos_meaning] += [i.pali_1]

    # remove single entries
    for k, v in identical_meaning_dict.copy().items():
        if len(v) < 2:
            del identical_meaning_dict[k]

    print(f"{len(identical_meaning_dict)}")
    return identical_meaning_dict


def clean_meaning(text):
    """Return text having removed
    1. all brackets and their contents
    2. proceeding or following spaces
    3. commentary meaning."""
    text = re.sub(r"\(comm\).*$", "", text)
    text = re.sub(r" \(.*?\) | \(.*?\)|\(.*?\) ", "", text)
    return text


def add_identical_meanings(
        identical_meaning_dict, db_session, exceptions):
    """Process identical meanings and add to db."""
    print("[green]adding identical meanings to db")

    count = 0
    for meaning, headwords in identical_meaning_dict.items():
        if len(headwords) > 1:

            db = db_session.query(
                PaliWord).filter(PaliWord.pali_1.in_(headwords)).all()

            # sorted lists of clean headwords, synonyms and variants
            db = sorted(db, key=lambda x: pali_sort_key(x.pali_1))
            clean_headwords = pali_list_sorter([i.pali_clean for i in db])

            synonyms = pali_list_sorter(
                [syn for i in db for syn in i.synonym_list if syn])

            variants = pali_list_sorter(
                [var for i in db for var in i.variant_list if var])

            if (
                set(clean_headwords) != set(synonyms) and
                not set(clean_headwords).issubset(set(synonyms)) and
                set(clean_headwords) != set(variants) and
                not set(clean_headwords).issubset(set(variants))
            ):
                print(f"\n{count} / {len(identical_meaning_dict)}")

                for i in db:
                    print(f"[yellow]{i.pali_1:<20}[blue]{i.pos:10}[green]{i.meaning_1:<30} [cyan]{i.synonym_list} [violet]{i.variant_list}")
                print(f"[cyan]{synonyms}")
                print(f"[violet]{variants}")

                # the options are:
                # 1. add list of synomyms minus the headword
                # 2. add a list of variants minus the headword
                # 3. edit it manually if it's complicated
                # 4. add an exception
                # 5. pass
                # 6. break

                question = "[white](s)ynonym, (v)ariant, (m)anual (e)xception (p)ass (b)reak"
                choice = Prompt.ask(question)
                search_string = db_search_string(headwords)
                pyperclip.copy(search_string)

                if choice == "s":
                    for i in db:
                        synonyms = set(clean_headwords) | set(synonyms)
                        synonyms = synonyms - set([i.pali_clean])
                        synonyms = synonyms - set(i.variant_list)
                        synonyms = pali_list_sorter(synonyms)
                        i.synonym = ", ".join(synonyms)

                    print(search_string)
                    db_session.commit()

                elif choice == "v":
                    for i in db:
                        variants = set(clean_headwords) | set(variants)
                        variants = variants - set([i.pali_clean])
                        variants = variants - set(i.synonym_list)
                        variants = pali_list_sorter(variants)
                        i.variant = ", ".join(variants)

                    print(search_string)
                    db_session.commit()

                elif choice == "m":
                    print(search_string)
                    print(', '.join(clean_headwords))

                elif choice == "e":
                    exceptions += [meaning]
                    with open(PTH.syn_var_exceptions_path, "wb") as f:
                        pickle.dump(exceptions, f)
                    print(exceptions)

                elif choice == "p":
                    continue

                elif choice == "b":
                    break

        count += 1


def find_single_meanings(dpd_db, exceptions):
    """Find words with the same pos and identical single meaning."""
    print(f"[green]{'finding single meanings'}", end=" ")

    # make a single_meanings_dict
    # iterate thru db
    # clean the meanings of brackets
    # split into a list
    # add each pos_meaning : headwords

    single_meanings_dict = {}

    for i in dpd_db:
        for meaning in i.meaning_1.split("; "):
            meaning = clean_meaning(meaning)

            if meaning:

                pos_meaning = f"{i.pos}:{meaning}"

                if (
                    i.pos != "pron" and
                    pos_meaning not in exceptions and
                    # no cases in grammar
                    not re.findall(
                        r"\b(nom|acc|instr|dat|abl|gen|loc|voc|3rd|2nd|1st|reflx)\b", i.grammar)
                ):
                    if pos_meaning not in single_meanings_dict:
                        single_meanings_dict[pos_meaning] = set([i.pali_1])
                    else:
                        # dont include same headword with different numbers
                        if not re.findall(
                            fr"{i.pali_clean} \d.*",
                                ", ".join(single_meanings_dict[pos_meaning])):
                            single_meanings_dict[pos_meaning].add(i.pali_1)

    # remove meanings with single words
    for (k, v) in (single_meanings_dict.copy().items()):
        if len(v) < 2:
            del single_meanings_dict[k]
    print(len(single_meanings_dict))

    assert ', ' not in single_meanings_dict

    return single_meanings_dict


def add_single_meanings(
        single_meaning_dict, db_session, exceptions):
    """Process single meanings and add to db
    if 2 or more corresponding headwords."""
    print("[green]adding single meanings to db")

    break_flag = False

    for counter, (key1, values1) in enumerate(single_meaning_dict.items()):

        if break_flag is True:
            break

        pos1, meaning1 = key1.split(":")
        first_pass = set()
        identical_meanings = set()
        syn_count = 0

        for headword in values1:

            for key2, values2 in single_meaning_dict.items():

                if break_flag is True:
                    break

                pos2, meaning2 = key2.split(":")
                if (
                    key1 != key2 and
                    headword in values2 and
                    pos1 == pos2 and
                    f"{key1} {key2}" not in exceptions
                ):
                    intersect = values1.intersection(values2)
                    if len(intersect) > 1:
                        if syn_count == 0:
                            first_pass.update(intersect)
                        if syn_count > 0:
                            identical_meanings.update(
                                first_pass.intersection(intersect))

                        syn_count += 1

                        if (
                            len(identical_meanings) > 1 and
                            syn_count > 1
                        ):

                            db = db_session.query(
                                PaliWord).filter(
                                    PaliWord.pali_1.in_(
                                        identical_meanings)).all()

                            # sorted lists of clean headwords, synonyms and variants
                            db = sorted(db, key=lambda x: pali_sort_key(x.pali_1))
                            clean_headwords = pali_list_sorter([i.pali_clean for i in db])

                            synonyms = pali_list_sorter(
                                set([syn for i in db for syn in i.synonym_list if syn]))

                            variants = pali_list_sorter(
                                set([var for i in db for var in i.variant_list if var]))

                            if (
                                set(clean_headwords) != set(synonyms) and
                                not set(clean_headwords).issubset(set(synonyms)) and
                                set(clean_headwords) != set(variants) and
                                not set(clean_headwords).issubset(set(variants))
                            ):
                                print(f"\n{counter}. {pos1}. {meaning1} / {meaning2}")

                                for i in db:
                                    print(f"[yellow]{i.pali_1:<20}[blue]{i.pos:10}[green]{i.meaning_1:<30} [cyan]{i.synonym_list} [violet]{i.variant_list}")
                                print(f"[cyan]{synonyms}")
                                print(f"[violet]{variants}")

                                # the options are:
                                # 1. add list of synomyms minus the headword
                                # 2. add a list of variants minus the headword
                                # 3. edit it manually if it's complicated
                                # 4. add an exception
                                # 5. pass
                                # 6. break

                                question = "[white](s)ynonym, (v)ariant, (m)anual (e)xception (p)ass (b)reak"
                                choice = Prompt.ask(question)
                                search_string = db_search_string(identical_meanings)
                                pyperclip.copy(search_string)

                                if choice == "s":
                                    for i in db:
                                        synonyms = set(clean_headwords) | set(i.synonym_list)
                                        synonyms = synonyms - set([i.pali_clean])
                                        synonyms = synonyms - set(i.variant_list)
                                        if "" in synonyms:
                                            synonyms.remove("")
                                        synonyms = pali_list_sorter(synonyms)
                                        i.synonym = ", ".join(synonyms)

                                    print(search_string)
                                    db_session.commit()

                                elif choice == "v":
                                    for i in db:
                                        variants = set(clean_headwords) | set(i.variant_list)
                                        variants = variants - set([i.pali_clean])
                                        variants = variants - set(i.synonym_list)
                                        if "" in variants:
                                            variants.remove("")
                                        variants = pali_list_sorter(variants)
                                        i.variant = ", ".join(variants)

                                    print(search_string)
                                    db_session.commit()

                                elif choice == "m":
                                    print(search_string)
                                    print(', '.join(clean_headwords))

                                elif choice == "e":
                                    exceptions += [f"{key1} {key2}"]
                                    with open(PTH.syn_var_exceptions_path, "wb") as f:
                                        pickle.dump(exceptions, f)
                                    print(exceptions)

                                elif choice == "p":
                                    continue

                                elif choice == "b":
                                    break_flag = True
                                    break

                            first_pass = set()
                            identical_meanings = set()
                            syn_count = 0

        # if counter % 100 == 0:
        #     print(f"{counter:>10} / {len(single_meaning_dict):<10} {headword}")


if __name__ == "__main__":
    main()
