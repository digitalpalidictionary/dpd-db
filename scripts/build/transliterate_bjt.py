#!/usr/bin/env python3

"""
Transliterate tipitaka.lk texts from Sinhala to Roman script.
Save as json and text as well as complete books.
"""

import json
from os import walk
import os
from tools.bjt import get_bjt_file_names, get_bjt_json, process_single_bjt_file
from tools.pali_text_files import bjt_texts
from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green, p_title, p_yes
from tools.sinhala_tools import translit_si_to_ro
from tools.tic_toc import tic, toc

pth = ProjectPaths()
sinhala_dir = pth.bjt_sinhala_dir
roman_dir = pth.bjt_roman_json_dir

def transliterate_json():
    tic()
    p_title("transliterating tipitaka.lk json files")

    for root, dirs, files in walk(sinhala_dir):
        for counter, file in enumerate(files, 1):
            p_counter(counter, 285, file)
            in_path = sinhala_dir.joinpath(file)
            out_path = roman_dir.joinpath(file)
            
            with open(in_path) as f:
                sinhala = f.read()
            
            roman = translit_si_to_ro(sinhala)
            
            with open(out_path, "w") as f:
                f.write(roman)
    
    toc()


def get_file_names():
    p_green("get actual file names")
    file_list = []
    for root, dirs, files in walk(sinhala_dir):
        for counter, file in enumerate(files, 1):
            file_list.append(file)
    file_list = sorted(file_list)
    p_yes(len(file_list))
    return file_list


def test_file_names():
    p_title("test file names")

    file_names = get_file_names()

    p_green("get dict file names")

    counter = 0
    bjt_files = []
    for book in bjt_texts:
        for file_name in bjt_texts[book]:
            bjt_files.append(file_name)
            counter += 1
    p_yes(counter)

    p_green("difference 1")
    x = set(bjt_files).symmetric_difference(set(file_names))
    p_yes(f"{x}")
    p_green("difference 2")
    x = set(file_names).symmetric_difference(set(bjt_files))
    p_yes(f"{x}")


def make_index():
    """Make an index of 
    ```
    {collection: {"book_id": 12, "filenames": [ ... ]}}
    ```
    """
    
    p_title("making index")
    pth = ProjectPaths()
    file_names = get_file_names()
    json_dicts = get_bjt_json(file_names)
    index_dict = {"mula": {}, "atta": {}}
    
    for jd in json_dicts:
        file_name = jd["filename"]
        book_id = jd["bookId"]
        collection = jd.get("collection", "mula")

        if not index_dict[collection].get(book_id):
            index_dict[collection][book_id] = []

        index_dict[collection][book_id].append(file_name)

    list_of_tuples = []
    for collection, data in index_dict.items():
        for id, filenames in data.items():
            list_of_tuples.append((collection, id, filenames))

    list_of_tuples = sorted(list_of_tuples, key=lambda x: x[2])
    list_of_tuples = sorted(list_of_tuples, key=lambda x: x[1])
    list_of_tuples = sorted(list_of_tuples, key=lambda x: x[0], reverse=True)

    save_path = pth.bjt_dir.joinpath("index.json")
    with open(save_path, "w") as f:
        json.dump(list_of_tuples, f, ensure_ascii=False, indent=1)


def save_books():
    """Save each book in BJT to a text file."""

    tic()

    p_title("saving BJT books")
    file_dir = pth.bjt_books_dir

    for counter, book in enumerate(bjt_texts):
        p_counter(counter, len(bjt_texts), book)
        bjt_file_names = get_bjt_file_names([book])
        json_dicts = get_bjt_json(bjt_file_names)
        bjt_text = ""
        for json_dict in json_dicts:
            bjt_text += process_single_bjt_file(
                json_dict,
                convert_bold_tags = False,
                footnotes_inline = False,
                show_page_numbers = True,
                show_metadata = True)

        file_path = file_dir \
            .joinpath(book) \
            .with_suffix(".txt") 
        with open(file_path, "w") as f:
            f.write(bjt_text)
    toc()


def save_text_files() -> None:
    "Save all BJT json to text files"
    
    tic()
    p_title("saving BJT to text files")

    counter = 1
    for root, dirs, files in os.walk(pth.bjt_roman_json_dir):
        for file in files:
            bjt_dicts = get_bjt_json([file])
            bjt_text = ""
            for bjt_dict in bjt_dicts:
                bjt_text += process_single_bjt_file(bjt_dict)
            file_path = pth.bjt_roman_txt_dir.joinpath(f"{file}.txt")
            with open(file_path, "w") as f:
                f.write(bjt_text)
            p_counter(counter, 285, file)
            counter += 1
    toc()


if __name__ == "__main__":
    transliterate_json()
    save_books()
    save_text_files()
    