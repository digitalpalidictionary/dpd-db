#!/usr/bin/env python3

"""Generic Kobo exporter."""

from pathlib import Path
from pyglossary import Glossary


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
            dict_name: str,
    ) -> None:
        
        self.kobo_path = kobo_path
        self.kobo_path_name: Path = self.kobo_path \
                .joinpath(dict_name)
        self.kobo_dict_file_name: Path = self.kobo_path \
                .joinpath(dict_name) \
                .with_suffix(".df")


def export_to_kobo_with_pyglossary(
    dict_info: DictInfo,
    dict_var: DictVariablesKobo,
    dict_data: list[DictEntry],
) -> None:
    
    """Export to Kobo using Pyglossary."""
    p_green_title("exporting to kobo with pyglossary")

    glos = create_glossary(dict_info)
    glos = add_data(glos, dict_data)

    p_white("writing kobo file")
    glos.write(
        filename=str(dict_var.kobo_path_name),
        format="Kobo",
    )
    p_yes("ok")

    p_white("writing dictfile file")    
    glos.write(
        filename=str(dict_var.kobo_dict_file_name),
        format="Dictfile",
    )
    p_yes("ok")
