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
from tools.printer import printer as pr


class DictEntry:
    """Data for a single dictionary entry"""

    def __init__(self, word, definition_html, definition_plain, synonyms) -> None:
        self.word: str = word
        self.definition_html: str = definition_html
        self.definition_plain: str = definition_plain
        self.synonyms: list[str] = synonyms


class DictInfo:
    """Dictionary Information"""

    def __init__(
        self, bookname, author, description, website, source_lang, target_lang
    ) -> None:
        self.bookname: str = bookname
        self.author: str = author
        self.description: str = description
        self.website: str = website
        self.source_lang: str = source_lang
        self.target_lang: str = target_lang
        self.date = make_timestamp()


class DictVariables:
    """All relevant dictionary variables.
    Usage:
    dict_vars = DictVariables(
        css_path = css_path,
        js_paths = js_paths,
        gd_path = gd_path,
        md_path = md_path,
        dict_name = dict_name,
        icon_path = None,
        font_path = None
        zip_up = False,
        delete_original = False,
    """

    def __init__(
        self,
        css_paths: Optional[list[Path]],
        js_paths: Optional[list[Path]],
        gd_path: Path,
        md_path: Path,
        dict_name: str,
        icon_path: Optional[Path],
        font_path: Optional[Path] = None,
        zip_up: bool = False,
        delete_original: bool = False,
    ) -> None:
        self.css_paths: Optional[list[Path]] = css_paths
        self.js_paths: Optional[list[Path]] = js_paths

        self.gd_path: Path = gd_path.joinpath(dict_name)
        self.gd_name_name: Path = Path(dict_name).with_suffix(".ifo")
        self.gd_path_name: Path = self.gd_path.joinpath(dict_name).with_suffix(".ifo")
        self.synfile: Path = self.gd_path_name.with_suffix(".syn")
        self.synfile_zip: Path = self.synfile.with_suffix(".syn.dz")

        self.slob_path_name: Path = gd_path.joinpath(dict_name).with_suffix(".slob")

        self.mdict_mdx_path: Path = md_path.joinpath(f"{dict_name}-mdict").with_suffix(
            ".mdx"
        )
        self.mdict_mdd_path: Path = md_path.joinpath(f"{dict_name}-mdict").with_suffix(
            ".mdd"
        )
        self.icon_source_path: Optional[Path] = icon_path

        if icon_path:
            self.icon_target_path = self.gd_path_name.with_suffix(".ico")

        self.font_source_path = font_path
        if self.font_source_path:
            self.font_target_dir = self.gd_path_name

        if zip_up:
            self.zip_up = zip_up
        else:
            self.zip_up = False

        if delete_original:
            self.delete_original = delete_original
        else:
            self.delete_original = False

        if gd_path.samefile(md_path):
            self.gd_zip_path = gd_path.joinpath(f"{dict_name}-goldendict").with_suffix(
                ".zip"
            )
            self.md_zip_path = md_path.joinpath(f"{dict_name}-mdict").with_suffix(
                ".zip"
            )
        else:
            self.gd_zip_path = gd_path.joinpath(dict_name).with_suffix(".zip")
            self.md_zip_path = md_path.joinpath(dict_name).with_suffix(".zip")


def export_to_goldendict_with_pyglossary(
    dict_info: DictInfo,
    dict_var: DictVariables,
    dict_data: list[DictEntry],
    include_slob=False,
) -> None:
    """Usage:
    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_var,
        dict_data,
        include_slob = False,
    )
    """

    pr.green_title("exporting to goldendict with pyglossary")
    glos = create_glossary(dict_info)
    glos = add_css(glos, dict_var)
    glos = add_js(glos, dict_var)
    glos = add_fonts(glos, dict_var)
    glos = add_data(glos, dict_data)
    write_to_file(glos, dict_var)
    add_icon(dict_var)
    copy_dir(dict_var)
    if dict_var.zip_up:
        zip_folder(dict_var)
    if dict_var.delete_original:
        delete_original(dict_var)
    if include_slob:
        write_to_slob(glos, dict_var)


def create_glossary(dict_info: DictInfo) -> Glossary:
    """Create Glossary."""

    pr.white("creating glossary")
    Glossary.init()
    glos = Glossary(
        info={
            "bookname": dict_info.bookname,
            "author": dict_info.author,
            "description": dict_info.description,
            "website": dict_info.website,
            "sourceLang": dict_info.source_lang,
            "targetLang": dict_info.target_lang,
            "date": dict_info.date,
        }
    )

    pr.yes("ok")
    return glos


def add_css(glos: Glossary, dict_var: DictVariables) -> Glossary:
    """Add CSS file."""

    pr.white("adding css")
    if dict_var.css_paths:
        for css_path in dict_var.css_paths:
            if css_path and css_path.exists():
                css = css_path.read_bytes()
                glos.addEntry(glos.newDataEntry(css_path.name, css))
        pr.yes("ok")
    else:
        pr.yes("no")
    return glos


def add_js(glos: Glossary, dict_var: DictVariables) -> Glossary:
    """Add JS file."""

    pr.white("adding js")
    if dict_var.js_paths:
        for js_path in dict_var.js_paths:
            if js_path and js_path.exists():
                js = js_path.read_bytes()
                glos.addEntry(glos.newDataEntry(js_path.name, js))
        pr.yes("ok")
    else:
        pr.yes("no")

    return glos


def add_fonts(glos: Glossary, dict_var: DictVariables) -> Glossary:
    """Add the fonts."""

    pr.white("adding fonts")
    if dict_var.font_source_path:
        for font_path in dict_var.font_source_path.iterdir():
            # Check if the file exists and has a valid font extension
            if (
                font_path
                and font_path.exists()
                and font_path.suffix.lower() in [".ttf", ".otf"]  # <-- Added check
            ):
                font_file = font_path.read_bytes()
                glos.addEntry(glos.newDataEntry(font_path.name, font_file))
        pr.yes("ok")
    else:
        pr.yes("no")

    return glos


def add_data(glos: Glossary, dict_data: list[DictEntry]) -> Glossary:
    """Add dictionary data to glossary."""

    pr.white("compiling data")
    for d in dict_data:
        glos.addEntry(
            glos.newEntry(
                word=[d.word] + d.synonyms, defi=d.definition_html, defiFormat="h"
            )  # type:ignore
        )

    pr.yes("ok")
    return glos


def write_to_file(glos: Glossary, dict_var: DictVariables) -> None:
    """Write output files."""

    pr.white("writing goldendict file")
    glos.write(
        filename=str(dict_var.gd_path_name),
        format="Stardict",
        # dictzip=True,
        dictzip=True,
        # merge_syns=False,  # when True, include synonyms in compressed main file rather than *.syn
        sametypesequence="h",
        sqlite=False,  # when False, more RAM but faster
    )
    pr.yes("ok")


def write_to_slob(glos: Glossary, dict_var: DictVariables) -> None:
    """Write to slob format files."""

    pr.white("writing slob file")
    glos.write(
        filename=str(dict_var.slob_path_name),
        format="Aard2Slob",
        compression="",  # "", "bz2", "zlib", "lzma2"
        content_type="text/html; charset=utf-8",
        word_title=True,
    )
    pr.yes("ok")


def zip_synfile(dict_var: DictVariables) -> None:
    """Compress .syn file into dictzip format"""

    pr.white("synzip")
    try:
        with (
            open(dict_var.synfile, "rb") as input_f,
            open(dict_var.synfile_zip, "wb") as output_f,
        ):
            input_info = os.fstat(input_f.fileno())
            idzip.compressor.compress(  # type:ignore
                input_f,
                input_info.st_size,
                output_f,
                dict_var.synfile.name,
                int(input_info.st_mtime),
            )
            dict_var.synfile.unlink()
            pr.yes("ok")
    except FileNotFoundError:
        pr.no("no")


def add_icon(v: DictVariables) -> None:
    """Copy the icon if provided."""

    pr.white("copying icon")
    if v.icon_source_path is not None:
        if v.icon_source_path.exists():
            try:
                Popen(["cp", v.icon_source_path, v.icon_target_path])
                pr.yes("ok")
            except Exception:
                pr.no("error")
    else:
        pr.yes("no")


def copy_dir(v: DictVariables) -> None:
    "Copy to Goldendict dir"

    pr.white("copying to GoldenDict dir")
    goldendict_pth: Path | str = make_goldendict_path()
    if goldendict_pth:
        if goldendict_pth.exists():
            try:
                Popen(["cp", "-r", v.gd_path, "-t", goldendict_pth])
                pr.yes("ok")
            except Exception:
                pr.no("error")
    else:
        pr.yes("no")


def zip_folder(dict_var: DictVariables):
    """Zip up the gd and md files."""

    pr.white("zipping directory")
    with ZipFile(dict_var.gd_zip_path, "w", ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dict_var.gd_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, dict_var.gd_path)
                zipf.write(file_path, relative_path)
    pr.yes("ok")


def delete_original(dict_var: DictVariables):
    """Delete the original output folder"""

    pr.white("deleting folder")
    try:
        shutil.rmtree(dict_var.gd_path)
        pr.yes("ok")
    except Exception as e:
        pr.no("error")
        pr.red(str(e))
