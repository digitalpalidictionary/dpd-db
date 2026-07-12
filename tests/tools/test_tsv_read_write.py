"""Tests for tools/tsv_read_write.py TSV reading and writing helpers.

All reads and writes go through pytest's tmp_path fixture so nothing ever
touches files in the repo.
"""

from pathlib import Path

import pytest

from tools.tsv_read_write import (
    read_tsv,
    read_tsv_2col_to_dict,
    read_tsv_as_dict,
    read_tsv_dict,
    read_tsv_dot_dict,
    read_tsv_single_column,
    write_tsv_2col_from_dict,
    write_tsv_dot_dict,
    write_tsv_list,
)


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_read_tsv_functions_parse_same_file(tmp_path: Path) -> None:
    tsv = _write(tmp_path / "in.tsv", "col1\tcol2\na\t1\nb\t2\n")

    assert read_tsv(tsv) == [["col1", "col2"], ["a", "1"], ["b", "2"]]
    assert read_tsv_single_column(tsv) == ["col1", "a", "b"]
    assert read_tsv_dict(tsv) == [
        {"col1": "a", "col2": "1"},
        {"col1": "b", "col2": "2"},
    ]

    rows = read_tsv_dot_dict(tsv)
    assert rows[0].col1 == "a"
    assert rows[1].col2 == "2"
    assert rows[0].missing_key is None


def test_write_tsv_dot_dict_round_trips(tmp_path: Path) -> None:
    out = tmp_path / "out.tsv"
    write_tsv_dot_dict(out, [{"col1": "a", "col2": "1"}, {"col1": "b", "col2": "2"}])

    assert read_tsv(out) == [["col1", "col2"], ["a", "1"], ["b", "2"]]


def test_write_tsv_list_skips_rows_with_blank_first_column(tmp_path: Path) -> None:
    out = tmp_path / "out.tsv"
    write_tsv_list(
        str(out),
        ["col1", "col2"],
        [["a", "1"], ["", "2"], ["b", "3"]],
    )

    assert read_tsv(out) == [["col1", "col2"], ["a", "1"], ["b", "3"]]


def test_read_tsv_as_dict_skips_blank_keys(tmp_path: Path) -> None:
    tsv = _write(
        tmp_path / "in.tsv",
        "col1\tcol2\tcol3\nx\t1\t2\n\t9\t9\n",
    )

    assert read_tsv_as_dict(tsv) == {"x": {"col2": "1", "col3": "2"}}


def test_read_tsv_2col_to_dict_happy_path_and_missing_file(tmp_path: Path) -> None:
    tsv = _write(tmp_path / "in.tsv", "k\tv\na\t1\nb\t2\n")

    result = read_tsv_2col_to_dict(tsv)
    assert result.headers == ["k", "v"]
    assert result.data == {"a": "1", "b": "2"}

    missing = read_tsv_2col_to_dict(tmp_path / "does_not_exist.tsv")
    assert missing.data == {}
    assert missing.headers == []


def test_write_tsv_2col_from_dict_validates_header_length_and_writes(
    tmp_path: Path,
) -> None:
    out = tmp_path / "nested" / "out.tsv"

    with pytest.raises(ValueError):
        write_tsv_2col_from_dict(out, {"a": "1"}, headers=["only_one"])

    write_tsv_2col_from_dict(out, {"a": "1", "b": "2"}, headers=["k", "v"])

    assert read_tsv(out) == [["k", "v"], ["a", "1"], ["b", "2"]]
