#!/usr/bin/env python3

"""Prepare data and export to MDict."""

from functools import reduce
from rich import print
from typing import List, Dict
from tools.paths import ProjectPaths
from tools.tic_toc import bip, bop
from tools.writemdict.writemdict import MDictWriter
from pathlib import Path



def get_all_files(directory):
    """ recursively get all files and create a list with the format (file_path, file_content_binary)"""
    files_list = []
    # Create a Path object for the directory
    base_path = Path(directory)
    # Iterate over all files in the directory recursively
    for file_path in base_path.rglob('*'):
        if file_path.is_file():  # Make sure it's a file
            # Read the content of the file as bytes
            with open(file_path, 'rb') as file:
                file_content = file.read()

            # Get the relative file path (relative to the base directory)
            relative_file_path = file_path.relative_to(base_path)
            # mdd files expect the path to start with \ (windows) or /
            #  possible workaround (if this is a problem): <img src'../img.jpg'> and dont preppend a pathseparator
            file = '\\'+str(relative_file_path)
            # windows: goldendict will not display a linux path (path separator: /),
            #  but linux programms will display when path separator is \
            #  => transform all / to  \
            file = file.replace('/', r'\\')
            # Append the tuple to the list with either text or binary content
            files_list.append((file, file_content))

    return files_list

def mdict_synonyms(all_items, item):
    all_items.append((item['word'], item['definition_html']))
    for word in item['synonyms']:
        if word != item['word']:
            all_items.append((word, f"""@@@LINK={item["word"]}"""))
    return all_items


def export_to_mdict(
        data_list: List[Dict],
        pth: ProjectPaths,
        description,
        title,
        external_css = False
    ) -> None:
    
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

    bip()
    print("[white]writing mdx file", end=" ")

    writer = MDictWriter(
        dpd_data,
        title=title,
        description=description)

    with  open(pth.mdict_mdx_path, 'wb') as outfile:
        writer.write(outfile)
        outfile.close()
    
    print(bop())

    if external_css is True:
        bip()
        print("[white]writing mdd file", end=" ")

        # create assets mdd file, adding all files in the folder 'assets/' (recursively)
        assets = get_all_files('exporter/goldendict/css/')
        assets += get_all_files('exporter/goldendict/javascript/')
        assets += get_all_files('exporter/goldendict/icon/')

        writer = MDictWriter(
            assets,
            title=title,
            description=description,
            is_mdd=True)
    
        # write the assets .mdd file
        with open(pth.mdict_mdd_path, "wb") as outfile:
            writer.write(outfile)
        
        print(bop())

