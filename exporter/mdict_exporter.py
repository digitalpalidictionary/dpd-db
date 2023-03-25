#!/usr/bin/env python3
# coding: utf-8

import sys
from functools import reduce
from rich import print
from pathlib import Path
from typing import List, Dict
from tools.timeis import bip, bop
sys.path.insert(1, 'tools/writemdict')
from writemdict import MDictWriter


def synonyms(all_items, item):
    all_items.append((item['word'], item['definition_html']))
    for word in item['synonyms']:
        if word != item['word']:
            all_items.append((word, f"""@@@LINK={item["word"]}"""))
    return all_items


def export_to_mdict(data_list: List[Dict], PTH: Path) -> None:
    print("[green]converting to mdict")

    bip()
    print("[white]adding 'mdict' and h3 tag", end=" ")
    for i in data_list:
        i['definition_html'] = i['definition_html'].replace(
            "GoldenDict", "MDict")
        i['definition_html'] = f"<h3>{i['word']}</h3>{i['definition_html']}"
    print(bop())

    bip()
    print("[white]reducing synonyms", end=" ")
    dpd_data = reduce(synonyms, data_list, [])
    del data_list
    print(bop())

    print("[white]writing mdict", end=" ")

    description = """<p>Digital Pāḷi Dictionary by Bodhirasa</p>
<p>For more infortmation, please visit
<a href=\"https://digitalpalidictionary.github.io\">
Digital Pāḷi Dictionary</a></p>"""

    writer = MDictWriter(
        dpd_data,
        title="Digital Pāḷi Dictionary",
        description=description)
    print(bop())

    print("[white]copying mdx file", end=" ")
    outfile = open(PTH.mdict_mdx_path, 'wb')
    writer.write(outfile)
    outfile.close()
    print(bop())
