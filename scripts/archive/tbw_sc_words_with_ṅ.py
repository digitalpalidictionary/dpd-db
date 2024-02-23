#!/usr/bin/env python3

"""Find words in sutta central texts whcih contain the letter ṅ."""

from tools.cst_sc_text_sets import make_sc_text_set
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths

def main():
    pth = ProjectPaths()
    
    books = [
    "vin1", "vin2",
    "dn1", "dn2", "dn3",
    "mn1", "mn2", "mn3",
    "sn1", "sn2", "sn3", "sn4", "sn5",
    "an1", "an2", "an3", "an4", "an5",
    "an6", "an7", "an8",
    "an9", "an10", "an11",
    "kn1", "kn2", "kn3", "kn4", "kn5",
    "kn8", "kn9", 
    ]

    sc_text_set = make_sc_text_set(pth, books, niggahita="ṁ")

    ṅ_set = set()
    for i in sc_text_set:
        if "ṅ" in i:
            ṅ_set.add(i)
    
    ṅ_list = pali_list_sorter(ṅ_set)

    output_path = "temp/words_with_ṅ_in_sc_texts.txt"
    with open(output_path, "w") as f:
        f.write("words with ṅ in sutta central texts")
        for i in ṅ_list:
            f.write(f"{i}\n")

if __name__ == "__main__":
    main()
