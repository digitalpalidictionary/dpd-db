#!/usr/bin/env python3

"""Search for text string in a given BJT book, and return 
source code, sutta name and sentence example."""

import re

from rich import print
from tools.bjt import get_bjt_file_names, get_bjt_json, replace_footnotes
from tools.clean_machine import clean_machine

def start_sutta_counter(book: str) -> int:
    """Start the sutta counter in the correct place
    according to the book."""

    sutta_counter = 0
    if book == "mn1":
        sutta_counter = 0
    elif book == "mn2":
        sutta_counter = 50
    elif book == "mn3":
        sutta_counter = 100
    elif book == "dn1":
        sutta_counter = 0
    elif book == "dn2":
        sutta_counter = 13
    elif book == "dn3":
        sutta_counter = 23
    return sutta_counter


def find_bjt_source_sutta_example(
        book: str,
        search_string: str
) -> list[tuple[str, str, str]]:

    """Take a book and search term, 
    and return tuples of (source, sutta, example).
    
    Usage example:
    `find_bjt_source_sutta_example("vin1", "dāyak`)
    """

    source_sutta_examples = []
    bjt_file_names: list[str] = get_bjt_file_names([book])
    bjt_dicts: list[dict] = get_bjt_json(bjt_file_names)

    book_code = re.sub(r"\d", "", book).upper()
    sutta_counter: int = start_sutta_counter(book)

    for bjt_dict in bjt_dicts:
        file_name = bjt_dict["filename"]
        pages = bjt_dict["pages"]
        sutta_number = ""

        for page in pages:
            page_num = page["pageNum"]
            entries =  page["pali"]["entries"]
            footnotes = page["pali"]["footnotes"]

            for i in range(len(entries)):
                entry = entries[i]

                if (
                    entry["type"] == "centered"
                    and entry.get("level")
                    and (
                        entry["level"] == 1
                        or entry["level"] == 2
                        or entry["level"] == 3
                        )
                    and re.findall(r"^\d", entry["text"])
                ):
                    sutta_number = entry["text"]
                    sutta_number = sutta_number.replace(" ", "")
                
                if (
                    entry["type"] == "heading"
                    and (
                        entry["level"] == 1
                        or entry["level"] == 2
                        or entry["level"] == 3
                        or entry["level"] == 4
                    )
                    and (
                        "sutta" in entry["text"]
                        or "nipāto" in entry["text"]
                        )
                ):
                    sutta_name = entry["text"]
                    sutta_counter += 1
                    sutta_subname = ""

                if (
                    entry["type"] == "centered"
                    and entry.get("level")
                    and (
                        entry["level"] == 1
                        or entry["level"] == 2
                        or entry["level"] == 3
                        )
                    and not re.findall(r"^\d", entry["text"])
                    and not re.findall(r"^\w", entry["text"])
                ):
                    sutta_subname = entry["text"]
                    sutta_subname = re.sub(r"\[|\]|\(|\)", "", sutta_subname)
                
                if (
                    entry["type"] == "paragraph"
                    or entry["type"] == "gatha"
                ):
                    if search_string in clean_machine(entry["text"]):
                        
                        example: str = entry["text"]
                        example = replace_footnotes(
                            example, footnotes, file_name, page_num
                        )

                        source = f"{book_code}{sutta_counter}"
                        if sutta_name:
                            sutta = f"{sutta_number} {sutta_name}"
                        else:
                            sutta = f"{sutta_number}"
                        if sutta_subname:
                            sutta += f", {sutta_subname}"
                        
                        source_sutta_examples.append((
                            source,
                            sutta,
                            example
                        ))
        
    return source_sutta_examples


if __name__ == "__main__":
    book = "mn3"
    search_term = "aggatthik"
    source_sutta_examples = find_bjt_source_sutta_example(
        book,
        search_term)

    for i in source_sutta_examples:
        source, sutta, example = i
        example = example.replace(search_term, f"[green]{search_term}[/green]")
        print(f"[green]{source}")
        print(f"[cyan]{sutta}")
        print(f"{example}")
        print()


# TODO vagga counter for samyutta nikāya
# TODO sutta counter for anguttara nikāya