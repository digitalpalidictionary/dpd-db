#!/usr/bin/env python3

"""Generic MDict exporter."""

from functools import reduce
from rich import print
from tools.goldendict_exporter import DictInfo, DictVariables
from tools.tic_toc import bip, bop
from tools.utils import DictEntry
from tools.writemdict.writemdict import MDictWriter


def printer(message):
    print(f"{'':<5}[white]{message:<30}", end="")


def printer_ok():
    print(f"[blue]{'ok':<10}", end="")


def printer_no():
    print(f"[red]{'no':<10}", end="")


def printer_bop():
    print(f"{bop():>10}")


def make_synonyms(all_items, item):
    all_items.append((item['word'], item['definition_html']))
    for word in item['synonyms']:
        if word != item['word']:
            all_items.append((word, f"""@@@LINK={item["word"]}"""))
    return all_items


def add_css_js(dict_var: DictVariables) -> list:
    """Add CSS and JS and create a list with the format:
    (file_path, file_content_binary)"""
    
    assets = []

    for file in [dict_var.css_path, dict_var.js_path]:
        
        if (
            file
            and file.is_file()
        ):
            with open(file, "rb") as f:
                file_content = f.read()

            # mdd files expect the path to start with \ (windows) or /
            #  possible workaround (if this is a problem): <img src'../img.jpg'> and dont preppend a pathseparator
            file = f"\\{file.name}"
        
            # windows: goldendict will not display a linux path (path separator: /),
            #  but linux programs will display when path separator is \
            #  => transform all / to  \
            file = file.replace('/', r'\\')
        
            # Append the tuple to the list with either text or binary content
            assets.append((file, file_content))

    return assets


def export_to_mdict(
        dict_info: DictInfo,
        dict_var: DictVariables,
        dict_data: list[DictEntry],
        h3_header = True
) -> None:

    """Export to MDict"""

    print(f"[green]{'exporting to mdict'}")

    bip()
    printer("adding 'mdict' and h3 tag")
    if h3_header:
        for i in dict_data:
            i['definition_html'] = \
                i['definition_html'].replace("GoldenDict", "MDict")
            i['definition_html'] = \
                f"<h3>{i['word']}</h3>{i['definition_html']}"
        printer_ok()
    else:
        printer_no()    
    printer_bop()

    bip()
    printer("reducing synonyms")
    try:
        data = reduce(make_synonyms, dict_data, [])
        printer_ok()
    except Exception:
        printer_no()
    printer_bop()

    bip()
    printer("writing .mdx file")
    try:
        writer = MDictWriter(
            data,
            title=dict_info.bookname,
            description=dict_info.description)
        with open(dict_var.mdict_mdx_path, 'wb') as outfile:
            writer.write(outfile)
        printer_ok()
    except Exception:
        printer_no()
    printer_bop()

    bip()
    printer("compiling css and js assets")
    try:
        assets = add_css_js(dict_var)
        printer_ok()
    except Exception:
        printer_no()
    printer_bop()

    bip()
    printer("writing .mdd file")
    try:
        writer = MDictWriter(
            assets,
            title=dict_info.bookname,
            description=dict_info.description,
            is_mdd=True)
        with open(dict_var.mdict_mdd_path, "wb") as f:
            writer.write(f)
        printer_ok()
    except Exception:
        printer_no()
    printer_bop()

