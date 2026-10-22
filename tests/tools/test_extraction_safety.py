"""Archive extraction must stay inside its folder (issue #268)."""

import io
import tarfile
import zipfile
from importlib import import_module
from pathlib import Path

import pytest

from tools.paths import ProjectPaths
from tools.tarballer import extract_tarball


def make_tar(path: Path, members: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))


def test_tar_with_normal_files_extracts(tmp_path: Path) -> None:
    make_tar(tmp_path / "ok.tar.gz", {"a.txt": b"hello"})
    extract_tarball(tmp_path / "ok.tar.gz", tmp_path / "out")
    assert (tmp_path / "out" / "a.txt").read_bytes() == b"hello"


def test_tar_member_outside_the_folder_is_refused(tmp_path: Path) -> None:
    make_tar(tmp_path / "evil.tar.gz", {"../evil.txt": b"x"})
    with pytest.raises(tarfile.TarError):
        extract_tarball(tmp_path / "evil.tar.gz", tmp_path / "out")
    assert not (tmp_path / "evil.txt").exists()


def downloader():
    try:
        return import_module("resources.tipitaka_translation_db.download_and_unzip_db")
    except ModuleNotFoundError:
        pytest.skip("resources submodule not checked out")


def test_unzip_extracts_only_the_database_file(tmp_path: Path) -> None:
    db_name = ProjectPaths().tipitaka_translation_db_path.name
    with zipfile.ZipFile(tmp_path / "t.zip", "w") as z:
        z.writestr(db_name, b"db")
        z.writestr("download_and_unzip_db.py", b"print('pwned')")
    downloader().unzip_file(tmp_path / "t.zip", tmp_path / "out")
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [db_name]


def test_unzip_refuses_a_zip_without_the_database(tmp_path: Path) -> None:
    with zipfile.ZipFile(tmp_path / "t.zip", "w") as z:
        z.writestr("download_and_unzip_db.py", b"print('pwned')")
    with pytest.raises(ValueError):
        downloader().unzip_file(tmp_path / "t.zip", tmp_path / "out")
    assert not (tmp_path / "out" / "download_and_unzip_db.py").exists()
