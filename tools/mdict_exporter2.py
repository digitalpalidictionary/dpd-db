#!/usr/bin/env python3

"""Generic MDict exporter."""

from functools import reduce
from pathlib import Path
from tools.goldendict_exporter import DictEntry
from tools.goldendict_exporter import DictInfo
from tools.goldendict_exporter import DictVariables
from tools.printer import p_green_title, p_white, p_yes, p_no
from tools.tic_toc import bip, bop
from tools.writemdict.writemdict import MDictWriter




def make_synonyms(all_items, item: DictEntry):
    all_items.append((item.word, item.definition_html))
    for word in item.synonyms:
        if word != item.word:
            all_items.append((word, f"""@@@LINK={item.word}"""))
    return all_items


def add_css_js(dict_var: DictVariables) -> list:
    """Add CSS and JS and create a list with the format:
    (file_path, file_content_binary)"""
    
    assets = []
    file_list = [dict_var.css_path] if dict_var.css_path else []
    file_list += dict_var.js_paths if dict_var.js_paths else []
    
    for file in file_list:
        
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

    p_green_title("exporting to mdict")

    bip()
    p_white("adding 'mdict' and h3 tag")
    if h3_header:
        for i in dict_data:
            i.definition_html = \
                i.definition_html.replace("GoldenDict", "MDict")
            i.definition_html = \
                f"<h3>{i.word}</h3>{i.definition_html}"
        p_yes("ok")
    else:
        p_no("error")
    
    bip()
    p_white("reducing synonyms")
    try:
        data = reduce(make_synonyms, dict_data, [])
        p_yes("ok")
    except Exception:
        p_no("error")


    bip()
    p_white("writing .mdx file")
    try:
        writer = MDictWriter(
            data,
            title=dict_info.bookname,
            description=dict_info.description)
        with open(dict_var.mdict_mdx_path, 'wb') as outfile:
            writer.write(outfile)
        p_yes("ok")
    except Exception:
        p_no("error")

    bip()
    p_white("compiling css and js assets")
    try:
        assets = add_css_js(dict_var)
        p_yes("ok")
    except Exception:
        p_no("error")

    bip()
    p_white("writing .mdd file")
    try:
        writer = MDictWriter(
            assets,
            title=dict_info.bookname,
            description=dict_info.description,
            is_mdd=True)
        with open(dict_var.mdict_mdd_path, "wb") as f:
            writer.write(f)
        p_yes("ok")
    except Exception:
        p_no("error")
