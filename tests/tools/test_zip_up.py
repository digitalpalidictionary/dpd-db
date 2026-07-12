"""Tests for tools/zip_up.py zip/unzip helpers.

All zip and directory operations run against pytest's tmp_path fixture so
nothing is ever written into the repo.
"""

import zipfile
from pathlib import Path

import pytest

from tools.zip_up import (
    recompress_apkg,
    unzip_file,
    zip_up_directory,
    zip_up_file,
)


def test_zip_up_file_creates_zip_with_basename_arcname(tmp_path: Path) -> None:
    input_file = tmp_path / "sub" / "data.txt"
    input_file.parent.mkdir()
    input_file.write_text("hello", encoding="utf-8")
    output_file = tmp_path / "out" / "data.zip"

    zip_up_file(input_file, output_file)

    assert output_file.exists()
    with zipfile.ZipFile(output_file) as zf:
        assert zf.namelist() == ["data.txt"]
        assert zf.read("data.txt") == b"hello"
    assert input_file.exists()


def test_zip_up_file_delete_original_removes_input(tmp_path: Path) -> None:
    input_file = tmp_path / "data.txt"
    input_file.write_text("hello", encoding="utf-8")
    output_file = tmp_path / "data.zip"

    zip_up_file(input_file, output_file, delete_original=True)

    assert output_file.exists()
    assert not input_file.exists()


def test_zip_up_file_missing_input_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        zip_up_file(tmp_path / "missing.txt", tmp_path / "out.zip")


def test_zip_up_directory_creates_zip_next_to_dir_with_relative_names(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "mydir"
    (input_dir / "nested").mkdir(parents=True)
    (input_dir / "a.txt").write_text("a", encoding="utf-8")
    (input_dir / "nested" / "b.txt").write_text("b", encoding="utf-8")

    zip_up_directory(input_dir)

    output_file = tmp_path / "mydir.zip"
    assert output_file.exists()
    with zipfile.ZipFile(output_file) as zf:
        assert sorted(zf.namelist()) == [
            "mydir/a.txt",
            "mydir/nested/b.txt",
        ]
    assert input_dir.exists()


def test_zip_up_directory_missing_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        zip_up_directory(tmp_path / "no_such_dir")


def test_unzip_file_extracts_contents(tmp_path: Path) -> None:
    zip_path = tmp_path / "archive.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("hello.txt", "world")

    destination = tmp_path / "extracted"
    unzip_file(zip_path, destination)

    assert (destination / "hello.txt").read_text(encoding="utf-8") == "world"


def test_unzip_file_missing_zip_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        unzip_file(tmp_path / "missing.zip", tmp_path / "dest")


def test_recompress_apkg_preserves_entries_and_content(tmp_path: Path) -> None:
    apkg_path = tmp_path / "deck.apkg"
    with zipfile.ZipFile(apkg_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("collection.anki2", "sqlite-bytes")
        zf.writestr("media", "{}")

    recompress_apkg(apkg_path)

    assert apkg_path.exists()
    with zipfile.ZipFile(apkg_path) as zf:
        assert sorted(zf.namelist()) == ["collection.anki2", "media"]
        assert zf.read("collection.anki2") == b"sqlite-bytes"
        assert zf.read("media") == b"{}"
        info = zf.getinfo("collection.anki2")
        assert info.compress_type == zipfile.ZIP_DEFLATED


def test_recompress_apkg_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        recompress_apkg(tmp_path / "missing.apkg")
