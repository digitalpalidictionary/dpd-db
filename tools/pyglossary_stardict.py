# TODO Delete or rewrite
"""
"""

import re
import datetime

from typing import List, TypedDict, Optional
from pathlib import Path
from zipfile import ZipFile

import shutil
import struct
import idzip


SIMSAPA_DIR = Path("./")


class DictError(Exception):
    """Error in the dictionary."""


class WriteResult(TypedDict):
    idx_size: Optional[int]
    syn_count: Optional[int]


class StarDictIfo(TypedDict):
    """
    Available options:
    ```
    bookname=      // required
    wordcount=     // required
    synwordcount=  // required if ".syn" file exists.
    idxfilesize=   // required
    idxoffsetbits= // New in 3.0.0
    author=
    email=
    website=
    description= // You can use <br> for new line.
    date=
    sametypesequence= // very important.
    dicttype=
    ```
    sametypesequence=m The data should be a utf-8 string ending with '\\0'.
    sametypesequence=h Html
    Example contents of an .ifo file:
    ```
    StarDict's dict ifo file
    version=3.0.0
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
    ```
    """

    version: str
    bookname: str
    wordcount: str
    synwordcount: str
    idxfilesize: str
    idxoffsetbits: str
    author: str
    email: str
    website: str
    description: str
    date: str
    sametypesequence: str
    dicttype: str


class IdxEntry(TypedDict):
    # a utf-8 string, `\0` stripped
    word: str
    # word data's offset in .dict file
    offset_begin: int
    # word data's total size in .dict file
    data_size: int


class DictEntry(TypedDict):
    # a utf-8 string, `\0` stripped
    word: str
    definition_plain: str
    definition_html: str
    synonyms: List[str]


SynEntries = dict[
    # a utf-8 string, `\0` stripped
    str,
    # indices from the .idx
    List[int],
]


class StarDictPaths(TypedDict):
    zip_path: Path
    unzipped_dir: Path
    icon_path: Optional[Path]
    ifo_path: Optional[Path]
    idx_path: Optional[Path]
    dic_path: Optional[Path]
    syn_path: Optional[Path]


def ifo_from_opts(opts: dict[str, str]) -> StarDictIfo:
    ifo = StarDictIfo(
        version='',
        bookname='',
        wordcount='',
        synwordcount='',
        idxfilesize='',
        idxoffsetbits='',
        author='',
        email='',
        website='',
        description='',
        date='',
        sametypesequence='',
        dicttype='',
    )
    for k in opts.keys():
        if k in ifo.keys():
            ifo[k] = opts[k]

    return ifo


def new_stardict_paths(zip_path: Path):
    unzipped_dir: Path = SIMSAPA_DIR.joinpath("unzipped_stardict")
    return StarDictPaths(
        zip_path=zip_path,
        unzipped_dir=unzipped_dir,
        icon_path=None,
        ifo_path=None,
        idx_path=None,
        dic_path=None,
        syn_path=None,
    )


def write_ifo(ifo: StarDictIfo, paths: StarDictPaths):
    """Writes .ifo"""

    if paths['ifo_path'] is None:
        logger.error("ifo_path is required")
        return

    lines: List[str] = ["StarDict's dict ifo file"]

    required = ['bookname', 'wordcount', 'synwordcount',
                'idxfilesize', 'sametypesequence']
    missing = []
    for k in required:
        if k not in ifo.keys() and len(ifo[k]) > 0 and ifo[k] != 'None':
            missing.append(k)

    if len(missing) > 0:
        logger.error(f"Missing required keys: {missing}")
        return

    for k in ifo.keys():
        v = ifo[k]
        if len(v) > 0 and v != 'None':
            lines.append(f"{k}={v}")

    with open(paths['ifo_path'], 'w') as f:
        f.write("\n".join(lines))


def write_words(words: List[DictEntry], paths: StarDictPaths) -> WriteResult:
    """Writes .idx, .dict.dz, .syn.dz"""

    res = WriteResult(
        idx_size=None,
        syn_count=None
    )

    if paths['idx_path'] is None or paths['dic_path'] is None:
        logger.error("idx_path and dic_path are required")
        return res

    idx: List[IdxEntry] = []

    with idzip.IdzipFile(f"{paths['dic_path']}", "wb") as f:
        offset_begin = 0
        data_size = 0
        for w in words:
            d = bytes(w['definition_html'], 'utf-8')
            f.write(d)

            data_size = len(d)

            idx.append(IdxEntry(
                word=w['word'],
                offset_begin=offset_begin,
                data_size=data_size,
            ))

            offset_begin += data_size

    with open(paths['idx_path'], 'wb') as f:
        for i in idx:
            d = bytes(f"{i['word']}\0", "utf-8")
            f.write(d)
            d = struct.pack(">II", i['offset_begin'], i['data_size'])
            f.write(d)

    res['idx_size'] = paths['idx_path'].stat().st_size

    if paths['syn_path'] is not None:
        res['syn_count'] = 0

        with idzip.IdzipFile(f"{paths['syn_path']}", "wb") as f:
            for n, w in enumerate(words):

                if res['syn_count'] is not None:
                    res['syn_count'] += len(w['synonyms'])

                for s in w['synonyms']:
                    d = bytes(f"{s}\0", "utf-8")
                    f.write(d)
                    d = struct.pack(">I", n)
                    f.write(d)

    return res


def write_stardict_zip(paths: StarDictPaths):
    with ZipFile(paths['zip_path'], 'w') as z:
        a = [paths['ifo_path'],
             paths['idx_path'],
             paths['dic_path'],
             paths['syn_path'],
             paths['icon_path']]
        for p in a:
            if p is not None:
                # NOTE .parent to create a top level folder in .zip
                z.write(p, p.relative_to(paths['unzipped_dir'].parent))


def export_words_as_stardict_zip(
        words: List[DictEntry],
        ifo: StarDictIfo,
        zip_path: Path,
        icon_path: Optional[Path] = None) -> None:

    name = zip_path.name.replace('.zip', '')
    # No spaces in the filename and dict files.
    name = name.replace(' ', '-')

    # NOTE: A toplevel folder is created in the zip file, with the file name of the .zip file.
    # E.g. ncped.zip will contain ncped/ncped.ifo
    unzipped_dir: Path = SIMSAPA_DIR.joinpath("new_stardict").joinpath(name)
    if unzipped_dir.exists():
        shutil.rmtree(unzipped_dir)
    unzipped_dir.mkdir(parents=True)

    zip_icon_path = None

    if icon_path is not None and icon_path.exists():
        ext = icon_path.suffix
        zip_icon_path = unzipped_dir.joinpath(f"{name}{ext}")
        shutil.copy(icon_path, zip_icon_path)

    paths = StarDictPaths(
        zip_path=zip_path,
        unzipped_dir=unzipped_dir,
        icon_path=zip_icon_path,
        ifo_path=unzipped_dir.joinpath(f"{name}.ifo"),
        idx_path=unzipped_dir.joinpath(f"{name}.idx"),
        dic_path=unzipped_dir.joinpath(f"{name}.dict.dz"),
        syn_path=unzipped_dir.joinpath(f"{name}.syn.dz"),
    )

    ifo['version'] = '3.0.0'
    ifo['wordcount'] = f"{len(words)}"
    ifo['sametypesequence'] = 'h'
    ifo['date'] = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    res = write_words(words, paths)

    ifo['idxoffsetbits'] = "32"
    ifo['idxfilesize'] = f"{res['idx_size']}"
    ifo['synwordcount'] = f"{res['syn_count']}"

    write_ifo(ifo, paths)

    write_stardict_zip(paths)

    if unzipped_dir.exists():
        shutil.rmtree(unzipped_dir)
