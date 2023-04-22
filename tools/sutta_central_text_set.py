import os
import json
from rich import print
from tools.clean_machine import clean_machine
from tools.pali_text_files import sc_texts


def make_sc_text_set(books: list) -> set:
    """Make a set of words in Sutta Central texts based on a list of books."""

    # make a list of file names of included books
    sc_texts_list: list = []
    for i in books:
        try:
            if sc_texts[i]:
                sc_texts_list += sc_texts[i]
        except KeyError as e:
            print(f"[red]book does not exist: {e}")
            return set()

    # make set of words in those files
    path = "resources/sutta central/"
    sc_text_set: set = set()

    for root, dirs, files in sorted(os.walk(path)):
        for file in files:
            if file in sc_texts_list:
                with open(os.path.join(root, file)) as f:
                    # sc texts are json dictionaries
                    sc_text_dict: dict = json.load(f)
                    for title, text in sc_text_dict.items():
                        clean_text = clean_machine(text)
                        sc_text_set.update(clean_text.split())

    return sc_text_set


# usage
# sc_text_set = make_sutta_central_text_set(["abh7"])
