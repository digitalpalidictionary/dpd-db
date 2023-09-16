import dataclasses
import datetime
import idzip
import logging
import os
import pyglossary
import tempfile
import zipfile

from pathlib import Path
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)
DataType = List[Dict[str, str]]
pyglossary.Glossary.init()


class PyGlossaryExporterError(RuntimeError):
    ...


# TODO Subject to move to tools/paths.py
def path_append_suffix(path: Path, suffix: str) -> Path:
    """ Add additional suffix to filename """
    return Path(path.parent/(f'{path.name}.{suffix.lstrip(".")}'))


def dictzip(filename: Path) -> None:
    """ Compress file into dictzip format """
    with open(filename, 'rb') as file:
        inputinfo = os.fstat(file.fileno())
        destination = path_append_suffix(filename, '.dz')
        LOGGER.info('compressing %s to %s', filename, destination)
        output = open(destination, 'wb')
        idzip.compressor.compress(
            file,
            inputinfo.st_size,
            output,
            filename.name,
            int(inputinfo.st_mtime))
    filename.unlink()


def get_date_string() -> str:
    """ Make current time iso-formatted UTC datetime string """
    now = datetime.datetime.utcnow().replace(microsecond=0)
    return now.isoformat()


@dataclasses.dataclass
class Info:
    bookname: str
    author: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    date: str = get_date_string()

    def get(self) -> Dict[str, str]:
        dic = dataclasses.asdict(self)
        return {key: val for key, val in dic.items() if val is not None}


def _export(
        data_list: DataType,
        destination: Path,
        info: Info,
        format_name: str,
        format_options: Dict[str, Any]) -> None:
    glossary = pyglossary.Glossary(info=info.get())

    for word_data in data_list:
        if (synonyms := word_data['synonyms']):
            assert isinstance(synonyms, list)
            word = [word_data['word']] + synonyms
        else:
            word = word_data['word']

        if (definition := word_data['definition_html']):
            definition_format = 'h'
        else:
            definition = word_data['definition_plain']
            definition_format = 'm'

        entry = glossary.newEntry(word=word, defi=definition, defiFormat=definition_format)

        glossary.addEntry(entry)

    if destination.exists():
        backup_dst = destination.parent / (destination.name + '~')
        destination.rename(backup_dst)

    destination.parent.mkdir(parents=True, exist_ok=True)

    glossary.write(filename=str(destination), format=format_name, **format_options)


def export_stardict_zip(
        data_list: DataType,
        destination: Path,
        info: Info,
        icon_path: Optional[Path] = None,
        android_icon_path: Optional[Path] = None) -> None:
    """ Create zipped stardict dictionary

    :data_list: List of entries in form of {'word': 'value', definition_html: 'value', 'synonyms': []}
    :destination: Resulting filename in form of 'dir/name.zip'
    :info: Metadata special dict
    :icon_path: Path of *.ico image file to include into resulting file
    TODO Check if android.bmp used anywhere
    :android_icon_path: Path of image to include into resulting file for GoldenDict Mobile (?)
    """

    if destination.suffix != '.zip':
        LOGGER.warning('[yellow bold]Resulting zip file supposed to have a "zip" suffix')
    if icon_path and not icon_path.is_file():
        raise PyGlossaryExporterError(f'{icon_path} is not existing file')
    if android_icon_path and not android_icon_path.is_file():
        raise PyGlossaryExporterError(f'{android_icon_path} is not existing file')

    # Avaliable options can be explored with pyglossary UI, with
    # glos.writeOptions or in pyglossary.plugins.* source files
    fmt_opt = {
        'large_file': False,  # 64-bit headers
        # While pyglossary depends on dictzip bin and does not compress syn compression will be done here
        'dictzip': False,
        'sametypesequence': 'h',  # Mark all definitions in one format
        'stardict_client': False,  # "Modify html entries for StarDict 3.0"
        'merge_syns': False,  # No separate syn file
        'sqlite': False,
    }

    relative_destination = Path(destination.stem)

    # Unzipped dictionary will be created into a temporary destination (usually in /tmp/)
    with tempfile.TemporaryDirectory() as unzipped_path:
        name = destination.stem
        # To get properly named dir with StarDict files to zip
        tmp_destination = Path(unzipped_path)/name/name
        LOGGER.info(f'export_stardict_zip temporary directory is {tmp_destination}')
        _export(
            data_list,
            destination=tmp_destination,
            info=info,
            format_name='Stardict',
            format_options=fmt_opt)

        dictzip(path_append_suffix(tmp_destination, '.syn'))
        dictzip(path_append_suffix(tmp_destination, '.dict'))

        with zipfile.ZipFile(destination, mode='w', compression=zipfile.ZIP_STORED) as archive:
            for file in tmp_destination.parent.glob('*'):
                archive.write(file, relative_destination/file.name)

            if icon_path:
                icon_dst = relative_destination/icon_path.with_stem(destination.stem).name
                archive.write(icon_path, icon_dst)

            if android_icon_path:
                android_icon_dst = relative_destination/android_icon_path.with_stem('android').name
                archive.write(android_icon_path, android_icon_dst)


def export_slob_zip(
        data_list: DataType,
        destination: Path,
        info: Info) -> None:
    """ Create zipped slob dictionary

    :data_list: List of entries in form of {'word': 'value', definition_html: 'value', 'synonyms': []}
    :destination: Resulting filename in form of 'dir/name.slob.zip'
    :info: Metadata special dict
    :icon_path: Path of *.ico image file to include into resulting file
    TODO Check if android.bmp used anywhere
    :android_icon_path: Path of image to include into resulting file for GoldenDict Mobile (?)
    """
    # zlib and bz2 compressions are close in compression time and ration.
    # lzma2 is ~1.3 times slower but gives ~1.18x better ration.
    fmt_opt = {
        'compression': 'zlib',  # bz2, zlib, lzma2
        'content_type': 'text/html; charset=utf-8',
        'separate_alternates': False,
        'word_title': False,  # "Add headwords title to beginning of definition"
    }
    with tempfile.TemporaryDirectory() as unzipped_path:
        tmp_destination = Path(unzipped_path)/destination.stem
        _export(
            data_list,
            destination=tmp_destination,
            info=info,
            format_name='Aard2Slob',
            format_options=fmt_opt)

        with zipfile.ZipFile(destination, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(tmp_destination, tmp_destination.name)


# TODO Reserved for next pyglossary release since QuickDic6 is only in master of v4.6.1
def export_quickdic(
        data_list: DataType,
        destination: Path,
        info: Info,
        target_lang='English') -> None:
    fmt_opt = {
        'normalizer_rules': '',  # "ICU normalizer rules to use for index sorting"
        'source_lang': 'Pali',
        'target_lang': target_lang,
    }
    _export(
        data_list,
        destination=destination,
        info=info,
        format_name='QuickDic6',
        format_options=fmt_opt)
