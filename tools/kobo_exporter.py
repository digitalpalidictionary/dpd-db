#!/usr/bin/env python3

"""Generic Kobo exporter."""

import shutil

from pathlib import Path

from tools.printer import p_green_title, p_white, p_yes
from tools.goldendict_exporter import DictEntry
from tools.goldendict_exporter import DictInfo
from tools.goldendict_exporter import create_glossary
from tools.goldendict_exporter import add_data

class DictVariablesKobo():
    """All relevant dictionary variables for Kobo."""
    def __init__(
            self,
            kobo_path: Path,
    ) -> None:
        
        self.kobo_path = kobo_path
        self.kobo_folder = kobo_path.joinpath("kobo")
        self.kobo_zip = kobo_path.joinpath("dicthtml-pi-en")


def write_kobo_file(glos, dict_var: DictVariablesKobo):
    p_white("writing kobo file")
    glos.write(
        filename=str(dict_var.kobo_folder),
        format="Kobo",
    )
    p_yes("ok")


def archive_folder(dict_var: DictVariablesKobo) -> None:
    p_white("archiving folder")
    shutil.make_archive(
        str(dict_var.kobo_zip), 
        'zip', 
        dict_var.kobo_folder,
        base_dir=None
    )
    p_yes("ok")


def export_to_kobo_with_pyglossary(
    dict_info: DictInfo,
    dict_var: DictVariablesKobo,
    dict_data: list[DictEntry],
) -> None:
    
    """Export to Kobo using Pyglossary."""

    p_green_title("exporting to kobo with pyglossary")
    glos = create_glossary(dict_info)
    glos = add_data(glos, dict_data)
    write_kobo_file(glos, dict_var)
    archive_folder(dict_var)
