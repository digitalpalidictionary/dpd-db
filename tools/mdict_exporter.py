#!/usr/bin/env python3

"""Generic MDict exporter."""

from functools import reduce
from rich import print
from typing import List, Dict
from tools.tic_toc import bip, bop
from tools.writemdict.writemdict import MDictWriter


def mdict_synonyms(all_items, item):
    all_items.append((item['word'], item['definition_html']))
    for word in item['synonyms']:
        if word != item['word']:
            all_items.append((word, f"""@@@LINK={item["word"]}"""))
    return all_items

def printer(message):
    print(f"{'':<5}[white]{message:20}", end="")


def export_to_mdict(
        data_list: List[Dict], 
        output_file: str,
        title: str,
        description: str,
        h3_header=True
    ) -> None:
    """
    1. data_list {
            headword: str,
            definition_html: str,
            definition_plain: str,
            synonyms: list
        }
    2. output file name
    3. title of the dictionary
    4. descritpion of the dictionary
    5. (h3_header=bool)
    """

    if h3_header:
        bip()
        printer("adding h3 tag")
        for i in data_list:
            i['definition_html'] = f"<h3>{i['word']}</h3>{i['definition_html']}"
        print(f"{bop():>10}")

    bip()
    printer("reducing synonyms")
    data = reduce(mdict_synonyms, data_list, [])
    print(f"{bop():>10}")

    bip()
    printer("writing mdict")
    writer = MDictWriter(
        data,
        title=title,
        description=description)
    print(f"{bop():>10}")

    bip()
    printer("copying mdx file")
    with open(output_file, 'wb') as outfile:
        writer.write(outfile)
    print(f"{bop():>10}")
