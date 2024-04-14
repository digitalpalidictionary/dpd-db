#!/usr/bin/env python3

"""Generic GoldenDict exporter using pyglossary."""

import idzip

from os import fstat
from pathlib import Path
from pyglossary import Glossary
from rich import print
from subprocess import Popen
from typing import Optional


from tools.date_and_time import make_timestamp
from tools.goldendict_path import make_goldendict_path
from tools.tic_toc import bip, bop
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
    dict_data: list[DictEntry]
) -> None:
    
    """Export to GoldenDict using Pyglossary."""
    
    print(f"[green]{'exporting to goldendict with pyglossary':<40}")

    glos = create_glossary(dict_info)
    glos = add_css(glos, dict_var)
    glos = add_js(glos, dict_var)
    glos = add_data(glos, dict_data)
    write_to_file(glos, dict_var)
    add_icon(dict_var)
    zip_synfile(dict_var)
    copy_dir(dict_var)
    

def create_glossary(dict_info: DictInfo) -> Glossary:
    """Create Glossary."""

    bip()
    print(f"[white]{'':<5}{'creating glossary':<40}", end="")

    Glossary.init()
    glos = Glossary(info={
        "bookname": dict_info.bookname,
        "author": dict_info.author,
        "description": dict_info.description,
        "website": dict_info.website,
        "sourceLang": dict_info.source_lang,
        "targetLang": dict_info.target_lang,
        "date": dict_info.date})
    
    print(f"{bop():>10}")
    return glos


def add_css(glos: Glossary, dict_var: DictVariables) -> Glossary:
    """Add CSS file."""

    bip()
    print(f"[white]{'':<5}{'adding css':<30}", end="")
    
    if dict_var.css_path and dict_var.css_path.exists():
        with open(dict_var.css_path, "rb") as f:
            css = f.read()
            glos.addEntry(
                glos.newDataEntry(
                    dict_var.css_path.name, css))
            print(f"[blue]{'ok':<10}", end="")
    else:
        print(f"[red]{'no':<10}", end="")
    
    print(f"{bop():>10}")
    return glos


def add_js(glos: Glossary, dict_var: DictVariables) -> Glossary:
    """Add JS file."""
    
    bip()
    print(f"[white]{'':<5}{'adding js':<30}", end="")
    
    if dict_var.js_path and dict_var.js_path.exists():
        with open(dict_var.js_path, "rb") as f:
            js = f.read()
            glos.addEntry(
                glos.newDataEntry(
                    dict_var.js_path.name, js))
            print(f"[blue]{'ok':<10}", end="")
    else:
        print(f"[red]{'no':<10}")
    
    print(f"{bop():>10}")
    return glos


def add_data(glos: Glossary, dict_data: list[DictEntry]) -> Glossary:
    """Add dictionary data to glossary."""
    
    bip()
    print(f"[white]{'':<5}{'compiling data':<40}", end="")
    
    for d in dict_data:
        glos.addEntry(
            glos.newEntry(
                word=[d["word"]] + d["synonyms"],
                defi=d["definition_html"],
                defiFormat="h"))
    
    print(f"{bop():>10}")
    return glos


def write_to_file(glos: Glossary, dict_var: DictVariables) -> None:
    """Write output files."""

    bip()
    print(f"[white]{'':<5}{'writing goldendict file':<40}", end="")
    
    glos.write(
        filename=str(dict_var.output_path_name),
        format="Stardict",
        dictzip=True,
        merge_syns=False,       # when True, include synonyms in compressed main file rather than *.syn
        sametypesequence="h",
        sqlite=False,           # when False, more RAM but faster 
    )
    
    print(f"{bop():>10}")


def zip_synfile(dict_var: DictVariables) -> None:
    """ Compress .syn file into dictzip format """
    
    bip()
    print(f"[white]{'':<5}{'zipping synonyms':<30}", end="")
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
            print(f"[blue]{'ok':<10}", end="")
    except FileNotFoundError:
        print(f"[red]{'error':<10}")
    print(f"{bop():>10}")



def add_icon(v: DictVariables) -> None:
    """Copy the icon if provided."""
    
    bip()
    print(f"[white]{'':<5}{'copying icon':<30}", end="")
    
    if v.icon_source_path is not None and v.icon_source_path.exists():
        try:
            Popen(
                ["cp", v.icon_source_path, v.icon_target_path])
            print(f"[blue]{'ok':<10}", end="")
        except Exception:
            print(f"[red]{'no':<10}", end="")
    
    print(f"{bop():>10}")


def copy_dir(v: DictVariables) -> None:
    "Copy to Goldendict dir "

    bip()
    print(f"[white]{'':<5}{'copying to GoldenDict dir':<30}", end="")

    goldendict_pth: (Path |str) = make_goldendict_path()
    if goldendict_pth and goldendict_pth.exists():
        try:
            Popen(
                ["cp", "-r", v.output_path, "-t", goldendict_pth])
            print(f"[blue]{'ok':<10}", end="")
        except Exception:
            print(f"[red]{'no':<10}", end="")
    
    print(f"{bop():>10}")

