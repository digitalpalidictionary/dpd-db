"""Tests for exporter/goldendict/export_variant_spelling.py."""

import csv
from pathlib import Path
from unittest.mock import MagicMock


from exporter.goldendict.export_variant_spelling import (
    test_and_make_see_dict as _make_see_dict,
    test_and_make_spelling_dict as _make_spelling_dict,
    test_and_make_variant_dict as _make_variant_dict,
)


def _write_tsv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


class TestTestAndMakeSeeDict:
    def test_valid_pairs(self, tmp_path: Path) -> None:
        tsv = tmp_path / "see.tsv"
        _write_tsv(
            tsv,
            ["see", "headword"],
            [
                {"see": "kamma", "headword": "kamma 1"},
                {"see": "dhamma", "headword": "dhamma 1"},
            ],
        )
        pth = MagicMock()
        pth.see_path = tsv
        assert _make_see_dict(pth) == {"kamma": "kamma 1", "dhamma": "dhamma 1"}

    def test_duplicate_keeps_first(self, tmp_path: Path) -> None:
        tsv = tmp_path / "see.tsv"
        _write_tsv(
            tsv,
            ["see", "headword"],
            [
                {"see": "kamma", "headword": "kamma 1"},
                {"see": "kamma", "headword": "kamma 2"},
            ],
        )
        pth = MagicMock()
        pth.see_path = tsv
        assert _make_see_dict(pth) == {"kamma": "kamma 1"}

    def test_self_reference_is_added(self, tmp_path: Path) -> None:
        tsv = tmp_path / "see.tsv"
        _write_tsv(
            tsv,
            ["see", "headword"],
            [
                {"see": "kamma", "headword": "kamma"},
            ],
        )
        pth = MagicMock()
        pth.see_path = tsv
        assert _make_see_dict(pth) == {"kamma": "kamma"}

    def test_empty_file(self, tmp_path: Path) -> None:
        tsv = tmp_path / "see.tsv"
        _write_tsv(tsv, ["see", "headword"], [])
        pth = MagicMock()
        pth.see_path = tsv
        assert _make_see_dict(pth) == {}


class TestTestAndMakeVariantDict:
    def test_valid_pairs(self, tmp_path: Path) -> None:
        tsv = tmp_path / "variants.tsv"
        _write_tsv(
            tsv,
            ["variant", "main"],
            [
                {"variant": "nibbāna", "main": "nibbāna 1"},
                {"variant": "āvuso", "main": "āvuso 1"},
            ],
        )
        pth = MagicMock()
        pth.variant_readings_path = tsv
        assert _make_variant_dict(pth) == {
            "nibbāna": "nibbāna 1",
            "āvuso": "āvuso 1",
        }

    def test_duplicate_keeps_first(self, tmp_path: Path) -> None:
        tsv = tmp_path / "variants.tsv"
        _write_tsv(
            tsv,
            ["variant", "main"],
            [
                {"variant": "nibbāna", "main": "nibbāna 1"},
                {"variant": "nibbāna", "main": "nibbāna 2"},
            ],
        )
        pth = MagicMock()
        pth.variant_readings_path = tsv
        assert _make_variant_dict(pth) == {"nibbāna": "nibbāna 1"}

    def test_self_reference_is_added(self, tmp_path: Path) -> None:
        tsv = tmp_path / "variants.tsv"
        _write_tsv(
            tsv,
            ["variant", "main"],
            [
                {"variant": "nibbāna", "main": "nibbāna"},
            ],
        )
        pth = MagicMock()
        pth.variant_readings_path = tsv
        assert _make_variant_dict(pth) == {"nibbāna": "nibbāna"}


class TestTestAndMakeSpellingDict:
    def test_valid_pairs(self, tmp_path: Path) -> None:
        tsv = tmp_path / "spelling.tsv"
        _write_tsv(
            tsv,
            ["mistake", "correction"],
            [
                {"mistake": "nibbana", "correction": "nibbāna 1"},
                {"mistake": "avuso", "correction": "āvuso 1"},
            ],
        )
        pth = MagicMock()
        pth.spelling_mistakes_path = tsv
        assert _make_spelling_dict(pth) == {
            "nibbana": "nibbāna 1",
            "avuso": "āvuso 1",
        }

    def test_duplicate_keeps_first(self, tmp_path: Path) -> None:
        tsv = tmp_path / "spelling.tsv"
        _write_tsv(
            tsv,
            ["mistake", "correction"],
            [
                {"mistake": "nibbana", "correction": "nibbāna 1"},
                {"mistake": "nibbana", "correction": "nibbāna 2"},
            ],
        )
        pth = MagicMock()
        pth.spelling_mistakes_path = tsv
        assert _make_spelling_dict(pth) == {"nibbana": "nibbāna 1"}

    def test_self_reference_is_added(self, tmp_path: Path) -> None:
        tsv = tmp_path / "spelling.tsv"
        _write_tsv(
            tsv,
            ["mistake", "correction"],
            [
                {"mistake": "nibbana", "correction": "nibbana"},
            ],
        )
        pth = MagicMock()
        pth.spelling_mistakes_path = tsv
        assert _make_spelling_dict(pth) == {"nibbana": "nibbana"}
