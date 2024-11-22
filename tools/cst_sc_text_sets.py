"""Make sets of clean words in Chaṭṭha Saṅgāyana and Sutta Central texts.
Optionally change the niggahita character.
How to use: feed in a list of books and get a set in return.
    cst_test_set = make_cst_text_set(["an1", "an2"])
    sc_text_set = make_sc_text_set(["abh7"])
    sc_text_set = make_sc_text_set(["an1"], niggahita="ṁ")
"""

import json
import os
import re

from rich import print
from typing import Optional, Set, List

from tools.clean_machine import clean_machine
from tools.pali_text_files import sc_texts, cst_texts, bjt_texts
from tools.pali_text_files import mula_books, all_books
from tools.paths import ProjectPaths
from tools.printer import p_green, p_yes, p_red


def make_cst_text_set(
        pth: ProjectPaths,
        books: List[str], 
        niggahita="ṃ", 
        add_hyphenated_parts=True,
    ) -> Set[str]:
    
    """
    Make a set of words in CST texts from a list of books.
    - Use when keeping the word order is *not* important.
    - Optionally change the niggahita character (niggahita="ṃ" or niggahita="ṁ")
    - Optionally add the parts of hyphenated word (add_hyphenated_parts=True)
    - Return a disordered set.
    """
    p_green("making cst text set")
    cst_texts_list: List[str] = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    words_list: List[str] = []


    for book in cst_texts_list:
        with open(pth.cst_txt_dir.joinpath(book), "r") as f:
            text_string = f.read()
            if add_hyphenated_parts:
                # dont remove the hyphen, deal with it later
                text_string = clean_machine(
                    text_string, niggahita=niggahita, remove_hyphen=False)
            else:
                # remove the hyphen immediately
                text_string = clean_machine(
                    text_string, niggahita=niggahita, remove_hyphen=True)

            words_list.extend(text_string.split())
    
    words_list = list(set(words_list))
    
    if add_hyphenated_parts:
        words_list = hyphenated_parts_adder(words_list)
    
    p_yes(len(set(words_list)))
    return set(words_list)


def hyphenated_parts_adder(words_list: list[str]) -> list[str]:
    for index, word in enumerate(words_list):
        if "-" in word:
            # remove the dash and add the clean word back into the list
            words_list[index] = word.replace("-", "")

            # split on dashes and add each split back into the list
            # in the correct order
            hyphenated_words = word.split("-")
            for h_word in hyphenated_words.__reversed__():
                words_list.insert(index + 1, h_word)
    return words_list


def make_cst_text_list(
        pth: ProjectPaths, 
        books: List[str], 
        niggahita="ṃ",
        dedupe=True,
        add_hyphenated_parts=True,
    ) -> List[str]:
    
    """
    Make a list of words in CST texts from a list of books.
    - Use when keeping the order *is* important.
    - Optionally change the niggahita character (niggahita="ṁ").
    - Optionally dedupe the list (dedupe=True).
    Usage:
    - word_list = make_cst_text_list(pth, ["kn8"], niggahita="ŋ")
    - word_list = make_cst_text_list(pth, ["kn8", "kn9"], dedupe=False)
    - word_list = make_cst_text_list(pth, ["kn8", "kn9"], add_hyphenated_parts=True)
    """

    cst_texts_list: List[str] = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    words_list: List[str] = []

    for book in cst_texts_list:
        with open(pth.cst_txt_dir.joinpath(book), "r") as f:
            text_string = f.read()
            # remove all brackets
            text_string = re.sub(r"\(.+?\)", "", text_string)
            
            if add_hyphenated_parts:
                # dont remove the hyphen, deal with it later
                text_string = clean_machine(
                    text_string, niggahita=niggahita, remove_hyphen=False)
            else:
                # remove the hyphen immediately
                text_string = clean_machine(
                    text_string, niggahita=niggahita, remove_hyphen=True)
            
            words_list.extend(text_string.split())

    if add_hyphenated_parts:
        for index, word in enumerate(words_list):
            if "-" in word:
                # remove the dash and add the clean word back into the list
                words_list[index] = word.replace("-", "")

                # split on dashes and add each split back into the list
                # in the correct order
                hyphenated_words = word.split("-")
                for h_word in hyphenated_words.__reversed__():
                    words_list.insert(index + 1, h_word)

    if dedupe == True:
        exists = []
        reduced_list = []
        for word in words_list:
            if word not in exists:
                exists += [word]
                reduced_list += [word]
        return reduced_list
    else:
        return words_list


def extract_sutta_from_file(sutta_name: str, text_string: str, books: List[str]) -> Optional[str]:
    # Read the file content

    print(f"sutta_name : {sutta_name}")
    
    print(f"text_string : {len(text_string)}")
    print(f"book : {books}")

    # Search for the beginning of the sutta using the sutta_name
    start_index = text_string.find(sutta_name)
    
    # If sutta_name is not found in the text_string, return None
    if start_index == -1:
        print(f"'{sutta_name}' not found in the text_string.")
        return None
    print(f"Start index of sutta: {start_index}")  # Debugging print

    # Adjust end pattern based on the file's name
    if books[0].startswith(("dn", "mn")):
        end_pattern = f"{sutta_name} niṭṭhitaṃ"
    elif books[0].startswith(("sn", "an", "kd")):
        end_pattern = "suttaṃ"
    else:
        print(f"Unknown file name pattern: {text_string}")
        return None
    
    # Search for the end of the sutta using the end_pattern
    end_index = text_string.find(end_pattern, start_index + len(sutta_name))

    
    # If the end pattern is not found after the start index, return None
    if end_index == -1:
        print(f"End pattern '{end_pattern}' not found in the text_string after '{sutta_name}'.")
        return None
    print(f"End index of sutta: {end_index}")  # Debugging print

    # Extract the sutta from the text_string using the start and end indices
    sutta = text_string[start_index:end_index + len(end_pattern)]

    print(f"sutta : {sutta}")
    print("sutta_end")

    return sutta


def make_cst_text_set_sutta(
        pth: ProjectPaths,
        sutta_name: str,
        books: List[str],
        niggahita="ṃ"
) -> Set[str]:
    
    """Make a list of words in CST texts from a list of books.
    Optionally change the niggahita character.
    Return a list or a set."""

    cst_texts_list = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    words_list: list = []

    for book in cst_texts_list:
        with open(pth.cst_txt_dir.joinpath(book), "r") as f:
            text_string = f.read()
            sutta_string = extract_sutta_from_file(sutta_name, text_string, books)
            if sutta_string is not None:
                sutta_string = clean_machine(sutta_string, niggahita=niggahita)
                words_list.extend(sutta_string.split())

    return set(words_list)


def make_cst_text_list_sutta(
        pth: ProjectPaths,
        sutta_name: str,
        books: List[str],
        niggahita="ṃ",
        dedupe=True,
        add_hyphenated_parts=True,
) -> List[str]:
    
    """Make a list of words in CST texts from a list of books.
    - Use when keeping the order *is* important.
    - Optionally change the niggahita character (niggahita="ṁ").
    - Optionally dedupe the list (dedupe=True).
    Return a list or a set."""

    cst_texts_list = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    words_list: list = []

    for book in cst_texts_list:
        with open(pth.cst_txt_dir.joinpath(book), "r") as f:
            text_string = f.read()
            sutta_string = extract_sutta_from_file(sutta_name, text_string, books)
            if sutta_string is not None:
                # remove all brackets
                sutta_string = re.sub(r"\(.+?\)", "", sutta_string)
                if add_hyphenated_parts:
                    # dont remove the hyphen, deal with it later
                    sutta_string = clean_machine(
                        sutta_string, niggahita=niggahita, remove_hyphen=False)
                else:
                    # remove the hyphen immediately
                    sutta_string = clean_machine(
                        sutta_string, niggahita=niggahita, remove_hyphen=True)                
                words_list.extend(sutta_string.split())

    if add_hyphenated_parts:
        for index, word in enumerate(words_list):
            if "-" in word:
                # remove the dash and add the clean word back into the list
                words_list[index] = word.replace("-", "")

                # split on dashes and add each split back into the list
                # in the correct order
                hyphenated_words = word.split("-")
                for h_word in hyphenated_words.__reversed__():
                    words_list.insert(index + 1, h_word)

    if dedupe == True:
        exists = []
        reduced_list = []
        for word in words_list:
            if word not in exists:
                exists += [word]
                reduced_list += [word]
        return reduced_list
    else:
        return words_list


def make_cst_text_set_from_file(
        dpspth,
        niggahita="ṃ"
) -> Set[str]:

    """Make a list of words in CST texts from a list of books.
    Optionally change the niggahita character.
    Return a list or a set."""

    words_list: List[str] = []

    if dpspth.text_to_add_path:
        try:
            with open(dpspth.text_to_add_path, "r") as f:
                text_string = f.read()
                text_string = clean_machine(text_string, niggahita=niggahita)
                words_list.extend(text_string.split())
        except FileNotFoundError:
            print(f"[red]file {dpspth.text_to_add_path } does not exist")
            return set()

    return set(words_list)


def make_cst_text_list_from_file(
        dpspth,
        niggahita="ṃ",
        dedupe=True,
        add_hyphenated_parts=True,
) -> List[str]:

    """Make a list of words in CST texts from a list of books.
    - Use when keeping the order *is* important.
    - Optionally change the niggahita character (niggahita="ṁ").
    - Optionally dedupe the list (dedupe=True).
    Return a list or a set."""

    words_list: List[str] = []

    if dpspth.text_to_add_path:
        try:
            with open(dpspth.text_to_add_path, "r") as f:
                text_string = f.read()
                # remove all brackets
                text_string = re.sub(r"\(.+?\)", "", text_string)
                if add_hyphenated_parts:
                    # dont remove the hyphen, deal with it later
                    text_string = clean_machine(
                        text_string, niggahita=niggahita, remove_hyphen=False)
                else:
                    # remove the hyphen immediately
                    text_string = clean_machine(
                        text_string, niggahita=niggahita, remove_hyphen=True)
                
                words_list.extend(text_string.split())
        except FileNotFoundError:
            print(f"[red]file {dpspth.text_to_add_path } does not exist")
            return words_list

    if add_hyphenated_parts:
        for index, word in enumerate(words_list):
            if "-" in word:
                # remove the dash and add the clean word back into the list
                words_list[index] = word.replace("-", "")

                # split on dashes and add each split back into the list
                # in the correct order
                hyphenated_words = word.split("-")
                for h_word in hyphenated_words.__reversed__():
                    words_list.insert(index + 1, h_word)

    if dedupe == True:
        exists = []
        reduced_list = []
        for word in words_list:
            if word not in exists:
                exists += [word]
                reduced_list += [word]
        return reduced_list
    else:
        return words_list


def make_sc_text_set(
        pth: ProjectPaths, 
        books: List[str], 
        niggahita="ṃ",
        add_hyphenated_parts=True
) -> Set[str]:
    
    """Make a list of words in Sutta Central texts from a list of books.
    Optionally change the niggahita character.
    Return a list or a set."""

    p_green("making sc text set")

    # make a list of file names of included books
    sc_texts_list: List[str] = []
    for i in books:
        try:
            if sc_texts[i]:
                sc_texts_list += sc_texts[i]
        except KeyError as e:
            p_red(f"book does not exist: {e}")
            return set()

    words_list: List[str] = []

    for root, __dirs__, files in sorted(os.walk(pth.sc_data_dir)):
        for file in files:
            if file in sc_texts_list:
                with open(os.path.join(root, file)) as f:
                    # Sutta Cental texts are json dictionaries
                    sc_text_dict: dict = json.load(f)
                    for __title__, text_string in sc_text_dict.items():
                        if add_hyphenated_parts:
                            # dont remove the hyphen, deal with it later
                            text_string = clean_machine(
                                text_string, niggahita=niggahita, remove_hyphen=False)
                        else:
                            # remove the hyphen immediately
                            text_string = clean_machine(
                                text_string, niggahita=niggahita, remove_hyphen=True)
                            
                        words_list.extend(text_string.split())
    
    if add_hyphenated_parts:
        words_list = hyphenated_parts_adder(words_list)
    
    p_yes(len(set(words_list)))
    return set(words_list)


def make_sc_text_list(
        pth: ProjectPaths,
        books: List[str],
        niggahita="ṃ",
        deduped=True
) -> List[str]:
    
    """
    Make a list of words in Sutta Central texts from a list of books.
    - optionally change the niggahita character 
    - optionally dedupe.
    Return a list."""

    # make a list of file names of included books
    sc_texts_list: List[str] = []
    for i in books:
        try:
            if sc_texts[i]:
                sc_texts_list += sc_texts[i]
        except KeyError as e:
            p_red(f"book does not exist: {e}")
            return []

    words_list: List[str] = []

    for root, __dirs__, files in sorted(os.walk(pth.sc_data_dir)):
        for file in files:
            if file in sc_texts_list:
                with open(os.path.join(root, file)) as f:
                    # Sutta Cental texts are json dictionaries
                    sc_text_dict: dict = json.load(f)
                    for __title__, text in sc_text_dict.items():
                        clean_text = clean_machine(text, niggahita=niggahita)
                        words_list.extend(clean_text.split())
    
    if deduped == False:
        return words_list
    else:
        exists = []
        deduped_list = []
        for word in words_list:
            if word not in exists:
                exists += [word]
                deduped_list += [word]
        return deduped_list


# def make_bjt_text_set(
#         pth: ProjectPaths,
#         include: List[str]
# ) -> Set[str]:
    
#     """This is not currently used."""

#     p_green("make bjt text set")
#     bjt_texts_list: List[str] = []
#     for i in include:
#         if bjt_texts[i]:
#             bjt_texts_list += bjt_texts[i]

#     bjt_text_string = ""

#     for bjt_text in bjt_texts_list:
#         with open(pth.bjt_text_path.joinpath(bjt_text), "r") as f:
#             bjt_text_string += f.read()

#     bjt_text_string = clean_machine(bjt_text_string)
#     bjt_text_set = set(bjt_text_string.split())

#     p_yes(len(bjt_text_set))
#     return bjt_text_set


def make_mula_words_set(pth: ProjectPaths) -> Set[str]:
    """Returns a set of all words in CST & Sutta Cental mūla texts.
    Usage: mula_word_set = make_mula_words_set()"""
    
    cst_word_set = make_cst_text_set(pth, mula_books)
    sc_word_set = make_sc_text_set(pth, mula_books)
    mula_word_set = cst_word_set | sc_word_set
    return mula_word_set


def make_all_words_set(pth: ProjectPaths) -> Set[str]:
    """Returns a set of all words in CST & Sutta Cental texts.
    Usage: all_words_set = make_all_words_set()"""
    
    cst_word_set = make_cst_text_set(pth, all_books)
    sc_word_set = make_sc_text_set(pth, all_books)
    all_words_set = cst_word_set | sc_word_set
    return all_words_set


def make_other_pali_texts_set(pth: ProjectPaths) -> Set[str]:
    """Compile a set of all words in other pali texts, chanting books, etc."""

    p_green("making set of other pali texts")
    other_pali_texts_set: Set[str] = set()

    dir_path = pth.other_pali_texts_dir
    if dir_path.exists():
        file_list = [file for file in dir_path.iterdir() if file.is_file()]
        for file_path in file_list:
            with open(file_path, "r") as f:
                text_string = f.read()
                text_string = clean_machine(text_string)
                other_pali_texts_set.update(text_string.split())

    p_yes(len(other_pali_texts_set))
    return other_pali_texts_set


if __name__ == "__main__":
    pth = ProjectPaths()
    # TODO why does it need a path!?

    cst_test_set = make_cst_text_list(
        pth,
        ["mna"],
        dedupe=False,
        add_hyphenated_parts=True)
    print(type(cst_test_set))
    print(len(cst_test_set))
    print(cst_test_set[:10])

    from collections import Counter
    
    c = Counter(cst_test_set)
    most_common = c.most_common(100)
    print(most_common)