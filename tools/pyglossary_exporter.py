import pyglossary
import tempfile
import shutil

from pathlib import Path
from typing import Dict, List


def export(data_list: List[Dict[str, str]], destination: Path, format='Stardict') -> None:
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
        glossary.write(filename=unzipped_path, format=format)
        # TODO Conditional zipping
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copytree(unzipped_path, destination, dirs_exist_ok=True)


    # TODO Speed comparizon 51 sec
    # TODO Size comparizon
    # TODO Icon
    # TODO Zip
    # TODO Purge tools/*stardict.py
    # TODO README dictd for dictzip
    # FIXME Giant syn file
