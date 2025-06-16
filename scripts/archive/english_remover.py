#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Quick starter template for getting a database session and iterating thru."""

import re

from rich import print
from tools.pali_alphabet import pali_alphabet

def main():
    pali_alphabet_string = "".join(pali_alphabet)
    diacritics_list = remove_english_letters(pali_alphabet_string)
    diacritics_str = "".join(diacritics_list)
    print(diacritics_str)

    files = [
        "resources/other_pali_texts/anandajoti_daily_chanting_pe.txt",
        "resources/other_pali_texts/anandajoti_safeguard_recitals_pe.txt"
    ]
    
    for file in files:
        with open(file, "r") as f:
            text = f.read()

        paragraphs = text.split('\n\n')
        for i, paragraph in enumerate(paragraphs):
            if paragraph:
                if not contains_diacritcs(diacritics_str, paragraph):
                    # print(i+1)
                    print(f"[red]{paragraph}")
                    input()
                else:
                    print(f"[white]{paragraph}")
                input()

def remove_english_letters(pali_alphabet_string):
    return [char for char in pali_alphabet_string if not char.isalpha() or not char.isascii()]

def contains_diacritcs(diacritics_str, text):
    diacritics_pattern = re.compile(f"[{diacritics_str}]")
    return re.findall(diacritics_pattern, text)

if __name__ == "__main__":
    main()