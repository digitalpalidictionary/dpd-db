#!/usr/bin/env python3

"""Process Buddha Jayanti Triptitaka files from tipitaka.lk."""

import json
import re
from rich import print

from tools.clean_machine import clean_machine
from tools.list_deduper import dedupe_list
from tools.pali_text_files import bjt_texts
from tools.paths import ProjectPaths


def get_bjt_file_names(
        books: list[str]
) -> list[str]:
    
    bjt_file_list = []
    if books == []:
        for book, file_list in bjt_texts.items():
           bjt_file_list.extend(file_list)
    else:
        for book in books:
            if book in bjt_texts:
                bjt_file_list.extend(bjt_texts[book])
    return bjt_file_list


def get_bjt_json(bjt_file_names: list[str]) -> list[dict]:
    
    """Take the list of file names and 
    return a list of json dicts."""

    pth = ProjectPaths()
    roman_dir = pth.bjt_roman_dir
    json_dicts = []

    for file_name in bjt_file_names:
        file_path = roman_dir.joinpath(file_name)
        with open(file_path) as f:
            json_dict: dict = json.load(f)
        json_dicts.append(json_dict)
       
    return json_dicts


def convert_json_to_text(json_dicts: list[dict]) -> str:
    
    """Take the json dicts and compile a single text string."""
    
    bjt_text = ""
    for json_dict in json_dicts:
        bjt_text += process_single_bjt_file(json_dict)
    return bjt_text


def process_single_bjt_file(
        dict: dict,
        convert_bold_tags=False,
        footnotes_inline=False,
        show_page_numbers=False,
        show_metadata=False
    ) -> str:
    
    """
    Return Pāḷi text for a single BJT file.
    Optionally include 
    1. footnotes inline
    2. show page numbers
    3. show file metadata
    """
    
    main_text = []
    file_name = dict['filename']
    book_id = dict['bookId']
    
    if show_metadata:
        main_text.append(f"filename: {file_name}")
        main_text.append(f"bookId  : {book_id}") 

    pages = dict["pages"]
    for page in pages:
        page_number = page["pageNum"]
        if show_page_numbers:
            main_text.append(f"page {page_number}.")

        pali = page["pali"]
        entries = pali["entries"]
        footnotes = pali["footnotes"]

        for entry in entries:
            text = entry["text"]
            
            # replace ** with bold tags
            if convert_bold_tags:
                text = re.sub(
                    r"""
                    (\*\*)              # find **   
                    (.+?)               # capture whats in-between  
                    (\*\*)              # find **   
                    """, 
                    "<b>\\2</b>",       # replace with bold + capture
                    text, 
                    flags=re.VERBOSE
                )

            # put footnotes inline
            if footnotes_inline and footnotes:

                text = replace_footnotes(
                    text, footnotes, file_name, page_number
                )

            
            # TODO add {*} footnotes

            main_text.append(text.strip())
        
        if not footnotes_inline:
            if footnotes:
                for footnote in footnotes:
                    text = footnote["text"]
                    main_text.append(text)

    if show_metadata:
        main_text.append(f"filename: {dict['filename']}")
        main_text.append(f"bookId  : {dict['bookId']}") 

    return "\n".join(main_text)


def replace_footnotes(text, footnotes, file_name, page_number):
    footnote_links = re.findall(
        r"""\{(\d*)\}""", text)
    for fl in footnote_links:
        num = int(fl)
        try:
            footnote_num = footnotes[num-1]["text"]
        except IndexError:
            print(f"[red]{file_name} page {page_number} footnote {num}")
        text = re.sub(
            fr"""\{{{num}\}}""",
            fr" [{footnote_num}]",
            text, flags=re.DOTALL)
    return text

def make_bjt_text_list(
        books: list[str],
        return_type="list",
) -> set[str] | list[str]:
    
    """
    Make a set of words in BJT texts from a list of books.
    
    Use an empty list `[]` to include all books.
    
    Returns a full list of all words by default.   
    Other options are
    return_type = "list" or "list_deduped" or "set"

    Usage examples:

    `make_bjt_text_list([], "set")`

    `make_bjt_text_list(["vin1"], "list_deduped")`

    """

    bjt_file_names = get_bjt_file_names(books)
    bjt_dicts = get_bjt_json(bjt_file_names)
    bjt_text = convert_json_to_text(bjt_dicts)
    bjt_text_clean = clean_machine(bjt_text)
    bjt_text_list = bjt_text_clean.split()

    if return_type == "set":
        return set(bjt_text_list)
    elif return_type == "list_deduped":
        return dedupe_list(bjt_text_list)
    else:
        return bjt_text_list 

if __name__ == "__main__":
    bjt_list = make_bjt_text_list(["vin1"], "list_deduped")
    print(bjt_list)
    print(len(bjt_list))


