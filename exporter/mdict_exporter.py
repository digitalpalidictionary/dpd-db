#!/usr/bin/env python3

"""Prepare data and export to MDict."""

from functools import reduce
from multiprocessing.managers import ListProxy
from rich import print
from tools.tic_toc import bip, bop
from tools.writemdict.writemdict import MDictWriter
from tools.paths import ProjectPaths


def mdict_synonyms(all_items, item):
    all_items.append((item['word'], item['definition_html']))
    for word in item['synonyms']:
        if word != item['word']:
            all_items.append((word, f"""@@@LINK={item["word"]}"""))
    return all_items


def export_to_mdict(data_list: ListProxy, PTH: ProjectPaths) -> None:
    print("[green]converting to mdict")

    bip()
    print("[white]adding 'mdict' and h3 tag", end=" ")
    for i in data_list:
        # i: RenderResult
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

    description = """<p>Digital Pāḷi Dictionary by Bodhirasa</p>
<p>For more infortmation, please visit
<a href=\"https://digitalpalidictionary.github.io\">
the Digital Pāḷi Dictionary website</a></p>"""

    bip()
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
