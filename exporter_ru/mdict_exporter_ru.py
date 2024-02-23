#!/usr/bin/env python3

"""Prepare ru data and export to MDict."""

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


def export_ru_to_mdict(data_list: List[Dict], dpspth) -> None:
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
    dpd_data = reduce(mdict_synonyms, data_list, [])
    del data_list
    print(bop())

    print("[white]writing mdict", end=" ")

    description = """<p>Электронный Пали Словарь Дост. Бодхирасв</p>
<p>For more infortmation, please visit
<a href=\"https://digitalpalidictionary.github.io\">
the Digital Pāḷi Dictionary website</a></p>"""

    bip()
    writer = MDictWriter(
        dpd_data,
        title="Электронный Пали Словарь",
        description=description)
    print(bop())

    bip()
    print("[white]copying mdx file", end=" ")
    outfile = open(dpspth.mdict_mdx_path, 'wb')
    writer.write(outfile)
    outfile.close()
    print(bop())
