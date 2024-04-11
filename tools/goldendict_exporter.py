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
            output_path: Path,
            dict_name: str,
            icon_path: Optional[Path],
    ) -> None:
        
        """icon_path can be a .ico or .bmp"""
        
        self.css_path: Optional[Path] = css_path
        self.output_path: Path = \
            output_path.joinpath(dict_name)
        self.output_name: Path = \
            Path(dict_name).with_suffix(".ifo")
        self.output_path_name: Path = \
            self.output_path \
                .joinpath(dict_name) \
                .with_suffix(".ifo")
        self.synfile: Path = \
            self.output_path_name.with_suffix(".syn")
        self.synfile_zip: Path = \
            self.synfile.with_suffix(".syn.dz")
        self.icon_source_path: Optional[Path] = icon_path
        if icon_path:
            self.icon_target_path = self.output_path_name.with_suffix(".ico")


class DictEntry():
    """Data for an individual dictionary entry."""
    def __init__(
            self,
            word,
            definition_html,
            definition_plain,
            synonyms,
    ) -> None:
        self.word: str = word
        self.definition_html: str = definition_html
        self.definition_plain: str = definition_plain
        self.synonyms: list[str] = synonyms
        if definition_html:
            self.format: str = "h"
        else:
            self.format: str = "m"


def export_to_goldendict_pyglossary(
    i: DictInfo,
    v: DictVariables,
    data_list: list[DictEntry]
) -> None:
    
    """Export to GoldenDict using Pyglossary."""
    
    bip()
    print(f"[green]{'exporting goldendict with pyglossary':<40}")
    
    Glossary.init()
    glos = Glossary(info={
        "bookname": i.bookname,
        "author": i.author,
        "description": i.description,
        "website": i.website,
        "sourceLang": i.source_lang,
        "targetLang": i.target_lang,
        "date": i.date,
    })


    # add css
    bip()
    print(f"[white]    {'adding css':<40}", end="")
    if v.css_path and v.css_path.exists():
        with open(v.css_path, "rb") as f:
            css = f.read()
            glos.addEntry(glos.newDataEntry(v.css_path.name, css))
    print(f"{bop():>10}")

    # add data
    bip()
    print(f"[white]    {'compiling data':<40}", end="")
    for d in data_list:
        new_word = glos.newEntry(
            word=[d.word] + d.synonyms, # type: ignore
            defi=d.definition_html,
            defiFormat=d.format)
        glos.addEntry(new_word)
    print(f"{bop():>10}")

    # write file
    bip()
    print(f"[white]    {'writing goldendict file':<40}", end="")
    glos.write(
        filename=str(v.output_path_name),
        format="Stardict",
        dictzip=True,
        merge_syns=False,       # when True, include synonyms in compressed main file rather than *.syn
        sametypesequence="h",
        sqlite=False,           # when False, more RAM but faster 
    )
    print(f"{bop():>10}")

    # dictzip the .syn file
    dictzip(v)

    # copy the .ico file
    copy_icon(v)

    # copy to goldendict folder
    goldendict_copy_dir(v)


def dictzip(v: DictVariables) -> None:
    """ Compress .syn file into dictzip format """

    print(f"[white]    {'zipping synonyms':<40}", end="")

    with open(v.synfile, "rb") as input_f, open(v.synfile_zip, 'wb') as output_f:
        input_info = fstat(input_f.fileno())
        idzip.compressor.compress(
            input_f,
            input_info.st_size,
            output_f,
            v.synfile.name,
            int(input_info.st_mtime))

    v.synfile.unlink()
    print(f"{bop():>10}")


def copy_icon(v: DictVariables) -> None:
    """Copy the icon if provided."""
    
    bip()
    
    if v.icon_source_path is not None and v.icon_source_path.exists():
        print(f"[white]    {'copying icon':<30}", end="")
        try:
            Popen(
                ["cp", v.icon_source_path, v.icon_target_path])
            print(f"[blue]{'ok':<10}", end="")
        except Exception:
            print(f"[red]{'failed':<10}", end="")
        print(f"{bop():>10}")


def goldendict_copy_dir(v: DictVariables) -> None:
    "Copy to Goldendict dir "

    bip()
    goldendict_pth: (Path |str) = make_goldendict_path()
    if goldendict_pth and goldendict_pth.exists():
        print(f"[white]    {'copying to GoldenDict dir':<30}", end="")
        try:
            Popen(
                ["cp", "-r", v.output_path, "-t", goldendict_pth])
            print(f"[blue]{'ok':<10}", end="")
            print(f"{bop():>10}")
        except Exception:
            print(f"[red]{'failed':<10}", end="")
            print(f"{bop():>10}")


if __name__ == "__main__":
    i = DictInfo(
        bookname="test",
        author="test",
        description="a test dictionary",
        website="no website",
        source_lang="en",
        target_lang="en"
    )

    v = DictVariables(
        css_path=None,
        output_path=Path("exporter/share"),
        dict_name="tester",
        icon_path=None
    )

    d = [
        DictEntry(
        word="hello",
        definition_html="well <b>hello</b> there!",
        definition_plain="",
        synonyms=["hello", "well", "there"]
    )]

    export_to_goldendict_pyglossary(i, v, d)
    
    # TODO make separate functions for every action