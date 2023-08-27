import dataclasses
import datetime
import logging
import pyglossary
import shutil
import tempfile
import zipfile

from pathlib import Path
from pyglossary.os_utils import runDictzip
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger(__name__)
DataType = List[Dict[str, str]]


class PyGlossaryExporterError(RuntimeError):
    ...


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
    date: str = dataclasses.field(default=get_date_string())  # TODO No field?

    def get(self) -> Dict[str, str]:
        dic = dataclasses.asdict(self)
        return {key: val for key, val in dic.items() if val is not None}


def _export(
        data_list: DataType,
        destination: Path,
        info: Info,
        format_name: str,
        format_options: Dict[str, Any]) -> None:
    pyglossary.Glossary.init()
    glossary = pyglossary.Glossary(info=info.get())

    for word in data_list:
        entry = glossary.newEntry(
            word=word['synonyms'],
            defi=word['definition_html'],
            defiFormat='h')
        glossary.addEntryObj(entry)

    destination.mkdir(parents=True, exist_ok=True)
    glossary.write(
        filename=str(destination),
        format=format_name,
        **format_options)


def export_stardict_zip(
        data_list: DataType,
        destination: Path,
        info: Info,
        icon_path: Optional[Path] = None,
        android_icon_path: Optional[Path] = None) -> None:
    """ Create zipped stardict dictionary

    :data_list: List of entries in form of {'word': 'value', definition_html: 'value', 'synonyms': []}
    :destination: Directory to save result, will be created if not exists
    :info: Metadata special dict
    :icon_path: Path of ico-image to include into resulting file
    TODO Check if android.bmp used anywhere
    :android_icon_path: Path of image to include into resulting file for GoldenDict Mobile (?)
    """

    dictzip = shutil.which('dictzip')
    if not dictzip:
        LOGGER.warning('[yellow bold]missing dictzip in $PATH, skipping StarDict compression')
    if icon_path and not icon_path.is_file():
        raise PyGlossaryExporterError(f'{icon_path} is not existing file')
    if android_icon_path and not android_icon_path.is_file():
        raise PyGlossaryExporterError(f'{android_icon_path} is not existing file')

    # Avaliable options can be explored with pyglossary UI, with
    # glos.writeOptions or in pyglossary.plugins.* source files
    fmt_opt = {
        'large_file': False,
        'dictzip': True,
        'sametypesequence': ['h'],
        'stardict_client': True,
        'merge_syns': False,
        'sqlite': False
    }

    # Unzipped dictionary will be created into a temporary destination (usually in /tmp/)
    with tempfile.TemporaryDirectory() as unzipped_path:
        tmp_destination = Path(unzipped_path) / destination.stem
        LOGGER.info(f'export_stardict_zip temporary directory is {tmp_destination}')
        _export(
            data_list,
            destination=tmp_destination,
            info=info,
            format_name='Stardict',
            format_options=fmt_opt)

        # dz-compress syn file while PyGlossary skip it
        if fmt_opt.get('dictzip'):
            syn_path = str(tmp_destination/tmp_destination.name) + '.syn'
            runDictzip(syn_path)
            #with zipfile.ZipFile('./dpd.zip', mode='w', compression=zipfile.ZIP_LZMA) as arch:

        if icon_path:
            icon_dst = tmp_destination / icon_path.with_stem(destination.name).name
            shutil.copy(icon_path, icon_dst)

        if android_icon_path:
            android_icon_dst = tmp_destination / android_icon_path.with_stem('android').name
            shutil.copy(android_icon_path, android_icon_dst)

        # TODO ZIP
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copytree(tmp_destination, destination, dirs_exist_ok=True)


def export_slob_zip() -> None:
    # TODO
    ...
