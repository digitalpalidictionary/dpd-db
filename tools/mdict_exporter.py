#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Generic MDict exporter."""

from functools import reduce
from zipfile import ZIP_DEFLATED, ZipFile
from tools.goldendict_exporter import DictEntry
from tools.goldendict_exporter import DictInfo
from tools.goldendict_exporter import DictVariables
from tools.printer import printer as pr
from tools.writemdict.writemdict import MDictWriter


class ProgData:
    def __init__(
        self,
        dict_info: DictInfo,
        dict_var: DictVariables,
        dict_data: list[DictEntry],
        h3_header: bool,
    ) -> None:
        self.dict_info: DictInfo = dict_info
        self.dict_var: DictVariables = dict_var
        self.dict_data: list[DictEntry] = dict_data
        self.reduced_data: list
        self.needs_h3_header: bool = h3_header
        self.assets: list


def export_to_mdict(
    dict_info: DictInfo,
    dict_var: DictVariables,
    dict_data: list[DictEntry],
    h3_header=True,
) -> None:
    """Export to MDict"""

    pr.green_title("exporting to mdict")
    g = ProgData(dict_info, dict_var, dict_data, h3_header)

    replace_goldendict(g)

    if h3_header:
        add_h3_header(g)

    reduce_synonyms(g)
    write_mdx_file(g)
    compile_css_js_assets(g)
    write_mdd_file(g)

    if dict_var.zip_up:
        zip_files(g)

    if dict_var.delete_original:
        delete_original(g)


def replace_goldendict(g: ProgData) -> None:
    pr.white("adding 'mdict'")
    for i in g.dict_data:
        i.definition_html = i.definition_html.replace("GoldenDict", "MDict")
    pr.yes("ok")


def add_h3_header(g: ProgData) -> None:
    pr.white("adding h3 tag")
    for i in g.dict_data:
        i.definition_html = f"<h3>{i.word}</h3>{i.definition_html}"
    pr.yes("ok")


def reduce_synonyms(g: ProgData) -> None:
    pr.white("reducing synonyms")
    try:
        g.reduced_data = reduce(make_synonyms, g.dict_data, [])
        pr.yes("ok")
    except Exception as e:
        pr.no("error")
        pr.red(e)


def make_synonyms(all_items, item: DictEntry):
    all_items.append((item.word, item.definition_html))
    for word in item.synonyms:
        if word != item.word:
            all_items.append((word, f"""@@@LINK={item.word}"""))
    return all_items


def write_mdx_file(g: ProgData) -> None:
    pr.white("writing .mdx file")
    try:
        writer = MDictWriter(
            g.reduced_data,
            title=g.dict_info.bookname,
            description=g.dict_info.description,
        )
        with open(g.dict_var.mdict_mdx_path, "wb") as outfile:
            writer.write(outfile)
        pr.yes("ok")
    except Exception as e:
        pr.no("error")
        pr.red(e)


def compile_css_js_assets(g: ProgData) -> None:
    """Add CSS and JS and create a list with the format:
    (file_path, file_content_binary)"""

    pr.white("compiling css and js assets")

    try:
        g.assets = []
        file_list = g.dict_var.css_paths if g.dict_var.css_paths else []
        file_list += g.dict_var.js_paths if g.dict_var.js_paths else []

        for file in file_list:
            if file and file.is_file():
                with open(file, "rb") as f:
                    file_content = f.read()

                # mdd files expect the path to start with \ (windows) or /
                #  possible workaround (if this is a problem): <img src'../img.jpg'> and dont preppend a pathseparator
                file = f"\\{file.name}"

                # windows: goldendict will not display a linux path (path separator: /),
                #  but linux programs will display when path separator is \
                #  => transform all / to  \
                file = file.replace("/", r"\\")

                # Append the tuple to the list with either text or binary content
                g.assets.append((file, file_content))
        pr.yes("ok")

    except Exception as e:
        pr.no("error")
        pr.red(e)


def write_mdd_file(g: ProgData) -> None:
    pr.white("writing .mdd file")
    try:
        writer = MDictWriter(
            g.assets,
            title=g.dict_info.bookname,
            description=g.dict_info.description,
            is_mdd=True,
        )
        with open(g.dict_var.mdict_mdd_path, "wb") as f:
            writer.write(f)
        pr.yes("ok")

    except Exception as e:
        pr.no("error")
        pr.red(e)


def zip_files(g: ProgData) -> None:
    pr.white("zipping mdict files")
    try:
        with ZipFile(g.dict_var.md_zip_path, "w", ZIP_DEFLATED) as zipf:
            for file_path in [g.dict_var.mdict_mdd_path, g.dict_var.mdict_mdx_path]:
                zipf.write(file_path, file_path.name)
        pr.yes("ok")

    except Exception as e:
        pr.no("error")
        pr.red(e)


def delete_original(g: ProgData) -> None:
    """Delete the original output folder"""

    pr.white("deleting original files")
    try:
        g.dict_var.mdict_mdd_path.unlink()
        g.dict_var.mdict_mdx_path.unlink()
        pr.yes("ok")

    except Exception as e:
        pr.no("error")
        pr.red(e)
