#!/usr/bin/env python3

"""Generic GoldenDict exporter using pyglossary."""

import shutil
import idzip
import os

from pathlib import Path
from pyglossary import Glossary
from subprocess import Popen
from typing import Optional
from zipfile import ZipFile, ZIP_DEFLATED

from tools.date_and_time import make_timestamp
from tools.goldendict_path import make_goldendict_path
from tools.printer import p_green_title, p_no, p_red, p_white, p_yes


class DictEntry():
    """Data for a single dictionary entry """
    def __init__(self, word, definition_html, definition_plain, synonyms) -> None:
        self.word: str = word
        self.definition_html: str = definition_html
        self.definition_plain: str = definition_plain
        self.synonyms: list[str] = synonyms


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
    """All relevant dictionary variables.
    Usage:
    dict_vars = DictVariables(
        css_path = css_path,
        js_paths = js_paths,
        gd_path = gd_path,
        md_path = md_path,
        dict_name = dict_name,
        icon_path = None,
        zip_up = False,
        delete_original = False,
    """
    
    def __init__(
            self,
            css_path: Optional[Path],
            js_paths: Optional[list[Path]],
            gd_path: Path,
            md_path: Path,
            dict_name: str,
            icon_path: Optional[Path],
            zip_up: bool = False,
            delete_original: bool = False,
    ) -> None:
        
        self.css_path: Optional[Path] = css_path
        self.js_paths: Optional[list[Path]] = js_paths
        
        self.gd_path: Path = gd_path.joinpath(dict_name)
        self.gd_name_name: Path = Path(dict_name).with_suffix(".ifo")
        self.gd_path_name: Path = self.gd_path \
                .joinpath(dict_name) \
                .with_suffix(".ifo")
        self.synfile: Path = self.gd_path_name.with_suffix(".syn")
        self.synfile_zip: Path = self.synfile.with_suffix(".syn.dz")

        self.slob_path_name: Path = gd_path \
            .joinpath(dict_name) \
            .with_suffix(".slob")
        
        self.mdict_mdx_path: Path = md_path \
                .joinpath(f"{dict_name}-mdict") \
                .with_suffix(".mdx")
        self.mdict_mdd_path: Path = md_path \
                .joinpath(f"{dict_name}-mdict") \
                .with_suffix(".mdd")
        self.icon_source_path: Optional[Path] = icon_path
        
        if icon_path:
            self.icon_target_path = self.gd_path_name.with_suffix(".ico")
        
        if zip_up:
            self.zip_up = zip_up
        else:
            self.zip_up = False
        
        if delete_original:
            self.delete_original = delete_original
        else:
            self.delete_original = False
        
        if gd_path.samefile(md_path):
            self.gd_zip_path = gd_path \
                .joinpath(f"{dict_name}-goldendict").with_suffix(".zip")
            self.md_zip_path = md_path \
                .joinpath(f"{dict_name}-mdict").with_suffix(".zip")
        else:
            self.gd_zip_path = gd_path \
                .joinpath(dict_name).with_suffix(".zip")
            self.md_zip_path = md_path \
                .joinpath(dict_name).with_suffix(".zip")


def export_to_goldendict_with_pyglossary(
    dict_info: DictInfo,
    dict_var: DictVariables,
    dict_data: list[DictEntry],
    zip_synonyms: bool = True,
    include_slob=False
) -> None:

    """Usage:
    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_var,
        dict_data,
        zip_synonyms = True,
        include_slob = False
    )
    """

    p_green_title("exporting to goldendict with pyglossary")
    glos = create_glossary(dict_info)
    glos = add_css(glos, dict_var)
    glos = add_js(glos, dict_var)
    glos = add_data(glos, dict_data)
    write_to_file(glos, dict_var)
    add_icon(dict_var)
    if zip_synonyms:
        zip_synfile(dict_var)
    copy_dir(dict_var)
    if dict_var.zip_up:
        zip_folder(dict_var)
    if dict_var.delete_original:
        delete_original(dict_var)
    if include_slob:
        write_to_slob(glos, dict_var)


def create_glossary(dict_info: DictInfo) -> Glossary:
    """Create Glossary."""
    
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
    
    p_white("adding css")
    if dict_var.css_path and dict_var.css_path.exists():
        with open(dict_var.css_path, "rb") as f:
            css = f.read()
            glos.addEntry(
                glos.newDataEntry(
                    dict_var.css_path.name, css)) #type:ignore
            p_yes("ok")
    else:
        p_yes("no")
    return glos


def add_js(glos: Glossary, dict_var: DictVariables) -> Glossary:
    """Add JS file."""
    
    p_white("adding js")
    if dict_var.js_paths:
        for js_path in dict_var.js_paths:
            if js_path and js_path.exists():
                with open(js_path, "rb") as f:
                    js = f.read()
                    glos.addEntry(
                        glos.newDataEntry(js_path.name, js)) #type:ignore
        p_yes("ok")
    else:
        p_yes("no")

    return glos


def add_data(glos: Glossary, dict_data: list[DictEntry]) -> Glossary:
    """Add dictionary data to glossary."""
    
    p_white("compiling data")
    for d in dict_data:
        glos.addEntry(
            glos.newEntry(
                word=[d.word] + d.synonyms,
                defi=d.definition_html,
                defiFormat="h")) #type:ignore
    
    p_yes("ok")
    return glos


def write_to_file(glos: Glossary, dict_var: DictVariables) -> None:
    """Write output files."""
    
    p_white("writing goldendict file")
    glos.write(
        filename=str(dict_var.gd_path_name),
        format="Stardict",
        dictzip=True,
        merge_syns=False,       # when True, include synonyms in compressed main file rather than *.syn
        sametypesequence="h",
        sqlite=False,           # when False, more RAM but faster 
    )
    p_yes("ok")


def write_to_slob(glos: Glossary, dict_var: DictVariables) -> None:
    """Write to slob format files."""
    
    p_white("writing slob file")
    glos.write(
        filename=str(dict_var.slob_path_name),
        format="Aard2Slob",
        compression="", # "", "bz2", "zlib", "lzma2"
        content_type="text/html; charset=utf-8",
        word_title=True
    )
    p_yes("ok")


def zip_synfile(dict_var: DictVariables) -> None:
    """ Compress .syn file into dictzip format """
    
    p_white("synzip")
    try:
        with open(dict_var.synfile, "rb") as input_f, open(dict_var.synfile_zip, 'wb') as output_f:
            input_info = os.fstat(input_f.fileno())
            idzip.compressor.compress( #type:ignore
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
    
    p_white("copying to GoldenDict dir")
    goldendict_pth: (Path |str) = make_goldendict_path()
    if goldendict_pth:
        if goldendict_pth.exists():
            try:
                Popen(
                    ["cp", "-r", v.gd_path, "-t", goldendict_pth])
                p_yes("ok")
            except Exception:
                p_no("error")
    else:
        p_yes("no")


def zip_folder(dict_var: DictVariables):
    """Zip up the gd and md files."""
    
    p_white("zipping directory")
    with ZipFile(dict_var.gd_zip_path, "w", ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dict_var.gd_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, dict_var.gd_path)
                zipf.write(file_path, relative_path)
    p_yes("ok")


def delete_original(dict_var: DictVariables):
    """Delete the original output folder"""

    p_white("deleting folder")
    try:
        shutil.rmtree(dict_var.gd_path)
        p_yes("ok")
    except Exception as e:
        p_no("error")
        p_red(e)
