import pyglossary
import tempfile
import shutil

from pathlib import Path
from typing import Any, Dict, List

DataType = List[Dict[str, str]]


def _export(
        data_list: DataType,
        destination: Path,
        format_name: str,
        format_options: Dict[str, Any]) -> None:
    # TODO Try empty fields for self-documentatnion
    """
    bookname=Digital Pāli Dictionary
    wordcount=36893
    synwordcount=1727042
    idxfilesize=747969
    idxoffsetbits=32
    author=Digital Pāli Tools <digitalpalitools@gmail.com>
    website=https://github.com/digitalpalitools
    description=The next generation comprehensive Digital Pāli Dictionary.
    date=2021-10-31T08:56:25Z
    sametypesequence=h
    """

    info = {
        "bookname": "DPD",
        "author": "Bodhirasa",
        "description": "",
        "website": "https://digitalpalidictionary.github.io/",
    }

    pyglossary.Glossary.init()
    glossary = pyglossary.Glossary(info=info)

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
        print(f'===> {glos_path.exists()}')
        # TODO Conditional zipping
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copytree(unzipped_path, destination, dirs_exist_ok=True)


def export_stardict_zip(data_list: DataType, destination: Path) -> None:
    dst = destination.parent / 'dpd1'
    # Avaliable options can be listed with pyglossary UI or with glos.writeOptions
    fmt_opt = {
        'large_file': True,
        'dictzip': True,
        'stardict_client': True,
        'merge_syns': False,
        'sqlite': False
    }

    _export(data_list, destination=dst, format_name='Stardict', format_options=fmt_opt)
    # TODO Speed comparizon 51 sec
    # TODO Icon
    # TODO Zip
    # TODO Purge tools/*stardict.py
    # TODO README dictd for dictzip
    # TODO dictzip check
    # TODO Info arg

    # TODO Slob, make class?
