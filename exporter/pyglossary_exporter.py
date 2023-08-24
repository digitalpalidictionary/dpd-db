import dataclasses
import datetime
import pyglossary
import shutil
import tempfile

import rich

from pathlib import Path
from typing import Any, Dict, List, Optional

DataType = List[Dict[str, str]]


def get_date_string() -> str:
    tzinfo = datetime.timezone.utc
    now = datetime.datetime.now(tzinfo)
    return now.isoformat()


@dataclasses.dataclass
class Info:
    bookname: str
    author: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    date: str = dataclasses.field(default=get_date_string())

    def get(self) -> Dict[str, str]:
        dic = dataclasses.asdict(self)
        return {key: val for key, val in dic.items() if val is not None}


def _export(
        data_list: DataType,
        destination: Path,
        info: Info,
        format_name: str,
        format_options: Dict[str, Any]) -> None:
    # TODO Try empty fields for self-documentatnion

    pyglossary.Glossary.init()
    glossary = pyglossary.Glossary(info=info.get())

    for word in data_list:
        entry = glossary.newEntry(
            word=word['synonyms'],
            defi=word['definition_html'],
            defiFormat='h')
        glossary.addEntryObj(entry)

    with tempfile.TemporaryDirectory() as unzipped_path:
        glos_path = Path(unzipped_path) / destination.name
        glossary.write(
            filename=str(glos_path),
            format=format_name,
            **format_options)
        # TODO Conditional zipping
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copytree(unzipped_path, destination, dirs_exist_ok=True)


def export_stardict_zip(data_list: DataType, destination: Path, info: Info) -> None:
    dictzip = shutil.which('dictzip')
    if not dictzip:
        rich.print('[yellow bold]WARINING: missing dictzip in $PATH, skipping StarDict compression')
    dst = destination.parent / 'dpd1'  # FIXME
    # Avaliable options can be explored with pyglossary UI, with
    # glos.writeOptions or in pyglossary.plugins.* source files
    fmt_opt = {
        'large_file': False,
        'dictzip': True,
        'stardict_client': True,
        'merge_syns': False,
        'sqlite': False
    }

    _export(data_list, destination=dst, info=info, format_name='Stardict', format_options=fmt_opt)
    # TODO Speed comparizon 51 sec
    # TODO Icon
    # TODO Zip
    # TODO Purge tools/*stardict.py
    # TODO README dictd for dictzip
    # TODO dictzip check
    # TODO Info arg
    # TODO Compress .syn

    # TODO Slob, make class?
