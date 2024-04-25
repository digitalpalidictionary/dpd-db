#!/usr/bin/env python3

"""Generic GoldenDict exporter using pyglossary."""

import idzip

from os import fstat
from pathlib import Path
from pyglossary import Glossary
from subprocess import Popen
from typing import Optional


from tools.date_and_time import make_timestamp
from tools.goldendict_path import make_goldendict_path
from tools.printer import p_green, p_no, p_white, p_yes
from tools.tic_toc import bip
from tools.utils import DictEntry


class DictInfo():
    """Dictionary Information"""
    def __init__(
            self,
            bookname,
            author,
            description,
            website,
            source_lang,
            target_lang
    ) -> None:
        self.bookname: str = bookname
        self.author: str = author
        self.description: str = description
        self.website: str = website
        self.source_lang: str = source_lang
        self.target_lang: str = target_lang
        self.date = make_timestamp()


class DictVariables():
    """All relevant dictionary variables."""
    def __init__(
            self,
            css_path: Optional[Path],
            js_path: Optional[Path],
            output_path: Path,
            dict_name: str,
            icon_path: Optional[Path],
    ) -> None:
        
        """icon_path can be a .ico or .bmp"""
        
        self.css_path: Optional[Path] = css_path
        self.js_path: Optional[Path] = js_path
        self.output_path: Path = \
            output_path.joinpath(dict_name)
        self.output_name: Path = \
            Path(dict_name).with_suffix(".ifo")
        self.output_path_name: Path = \
            self.output_path \
                .joinpath(dict_name) \
                .with_suffix(".ifo")
        self.mdict_mdx_path: Path = \
            self.output_path \
                .with_stem(f"{dict_name}-mdict") \
                .with_suffix(".mdx")
        self.mdict_mdd_path: Path = \
            self.output_path \
                .with_stem(f"{dict_name}-mdict") \
                .with_suffix(".mdd")
        self.synfile: Path = \
            self.output_path_name.with_suffix(".syn")
        self.synfile_zip: Path = \
            self.synfile.with_suffix(".syn.dz")
        self.icon_source_path: Optional[Path] = icon_path
        if icon_path:
            self.icon_target_path = self.output_path_name.with_suffix(".ico")
        

def export_to_goldendict_with_pyglossary(
    dict_info: DictInfo,
    dict_var: DictVariables,
    dict_data: list[DictEntry],
    zip_synonyms: bool = True
) -> None:
    
    """Export to GoldenDict using Pyglossary."""
    
    p_green("exporting to goldendict with pyglossary")

    glos = create_glossary(dict_info)
    glos = add_css(glos, dict_var)
    glos = add_js(glos, dict_var)
    glos = add_data(glos, dict_data)
    write_to_file(glos, dict_var)
    add_icon(dict_var)
    if zip_synonyms:
        zip_synfile(dict_var)
    copy_dir(dict_var)
    

def create_glossary(dict_info: DictInfo) -> Glossary:
    """Create Glossary."""

    bip()
    p_white("creating glossary")

    Glossary.init()
    glos = Glossary(info={
        "bookname": dict_info.bookname,
        "author": dict_info.author,
        "description": dict_info.description,
        "website": dict_info.website,
        "sourceLang": dict_info.source_lang,
        "targetLang": dict_info.target_lang,
        "date": dict_info.date})
    
    p_yes("ok")
    return glos


def add_css(glos: Glossary, dict_var: DictVariables) -> Glossary:
    """Add CSS file."""

    bip()
    p_white("adding css")
    
    if dict_var.css_path and dict_var.css_path.exists():
        with open(dict_var.css_path, "rb") as f:
            css = f.read()
            glos.addEntry(
                glos.newDataEntry(
                    dict_var.css_path.name, css))
            p_yes("ok")
    else:
        p_yes("no")
    return glos


def add_js(glos: Glossary, dict_var: DictVariables) -> Glossary:
    """Add JS file."""
    
    bip()
    p_white("adding js")
    
    if dict_var.js_path and dict_var.js_path.exists():
        with open(dict_var.js_path, "rb") as f:
            js = f.read()
            glos.addEntry(
                glos.newDataEntry(
                    dict_var.js_path.name, js))
            p_yes("ok")
    else:
        p_yes("no")

    return glos


def add_data(glos: Glossary, dict_data: list[DictEntry]) -> Glossary:
    """Add dictionary data to glossary."""
    
    bip()
    p_white("compiling data")
    
    for d in dict_data:
        glos.addEntry(
            glos.newEntry(
                word=[d["word"]] + d["synonyms"],
                defi=d["definition_html"],
                defiFormat="h"))
    
    p_yes("ok")
    return glos


def write_to_file(glos: Glossary, dict_var: DictVariables) -> None:
    """Write output files."""

    bip()
    p_white("writing goldendict file")
    
    glos.write(
        filename=str(dict_var.output_path_name),
        format="Stardict",
        dictzip=True,
        merge_syns=False,       # when True, include synonyms in compressed main file rather than *.syn
        sametypesequence="h",
        sqlite=False,           # when False, more RAM but faster 
    )
    p_yes("ok")


def zip_synfile(dict_var: DictVariables) -> None:
    """ Compress .syn file into dictzip format """
    
    bip()
    p_white("zipping synonyms")
    try:
        with open(dict_var.synfile, "rb") as input_f, open(dict_var.synfile_zip, 'wb') as output_f:
            input_info = fstat(input_f.fileno())
            idzip.compressor.compress(
                input_f,
                input_info.st_size,
                output_f,
                dict_var.synfile.name,
                int(input_info.st_mtime))
            dict_var.synfile.unlink()
            p_yes("ok")
    except FileNotFoundError:
        p_no("no")



def add_icon(v: DictVariables) -> None:
    """Copy the icon if provided."""
    
    bip()
    p_white("copying icon")
    
    if v.icon_source_path is not None:
        if v.icon_source_path.exists():
            try:
                Popen(
                    ["cp", v.icon_source_path, v.icon_target_path])
                p_yes("ok")
            except Exception:
                p_no("error")
    else:
        p_yes("no")


def copy_dir(v: DictVariables) -> None:
    "Copy to Goldendict dir "

    bip()
    p_white("copying to GoldenDict dir")

    goldendict_pth: (Path |str) = make_goldendict_path()
    if goldendict_pth:
        if goldendict_pth.exists():
            try:
                Popen(
                    ["cp", "-r", v.output_path, "-t", goldendict_pth])
                p_yes("ok")
            except Exception:
                p_no("error")
    else:
        p_yes("no")
