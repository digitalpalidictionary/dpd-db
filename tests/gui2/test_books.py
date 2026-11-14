# -*- coding: utf-8 -*-
"""Tests that `SuttaCentralSource` builds its text index on first use rather
than at construction, so importing `gui2.books` stays off the startup path."""

from collections import defaultdict
from json import dumps
from pathlib import Path
from typing import Any, Callable, IO

import pytest

import gui2.books as books
from gui2.books import SuttaCentralSource

KHP_PALI = "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/kp"
KHP_ENGLISH = "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/kp"

needs_sc_data = pytest.mark.skipif(
    not Path(KHP_PALI).is_dir(),
    reason="sc-data submodule not checked out",
)


@pytest.fixture
def load_calls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Count `json.load` calls made through `gui2.books`."""
    real_load: Callable[..., Any] = books.load
    calls: list[str] = []

    def counting_load(fp: IO[str], *args: Any, **kwargs: Any) -> Any:
        calls.append(getattr(fp, "name", "?"))
        return real_load(fp, *args, **kwargs)

    monkeypatch.setattr(books, "load", counting_load)
    return calls


def make_source() -> SuttaCentralSource:
    return SuttaCentralSource(
        "khp", ["kn1"], KHP_PALI, KHP_ENGLISH, is_commentary=False
    )


@needs_sc_data
def test_construction_does_not_build_the_index(load_calls: list[str]) -> None:
    source = make_source()

    assert source.pali_file_list, "fixture book has no pali files to index"
    assert "segment_dict" not in vars(source)
    assert "word_dict" not in vars(source)
    assert load_calls == []


@needs_sc_data
def test_first_word_dict_access_builds_the_index(load_calls: list[str]) -> None:
    source = make_source()
    assert load_calls == []

    word_dict = source.word_dict

    assert load_calls, "reading word_dict did not read any source file"
    assert isinstance(word_dict, defaultdict)
    assert word_dict, "word index is empty"
    assert source.segment_dict, "segment index is empty"


@needs_sc_data
def test_index_is_built_only_once(load_calls: list[str]) -> None:
    source = make_source()
    first = source.word_dict
    calls_after_first = len(load_calls)

    second = source.word_dict

    assert second is first
    assert len(load_calls) == calls_after_first


def test_none_path_source_stays_lazy_and_empty(load_calls: list[str]) -> None:
    """The commentary sources constructed with None paths (kva, dhpa, jaa,
    dna) must build neither index and read no files."""
    source = SuttaCentralSource("kva", ["kva"], None, None, is_commentary=True)

    assert source.pali_file_list == []
    assert source.english_file_list == []
    assert source.word_dict == {}
    assert isinstance(source.word_dict, defaultdict)
    assert source.segment_dict == {}
    assert load_calls == []


@pytest.mark.parametrize(
    ("book", "expected"),
    [
        ("dna", True),
        ("mna", True),
        ("sna", True),
        ("ana", True),
        ("jaa", True),
        ("kva", True),
        ("ja-1", False),
        ("ja-5", False),
        ("mn", False),
        ("ps", False),
        ("mil", False),
        ("ne", False),
        ("pe", False),
    ],
)
def test_commentary_books_are_flagged(book: str, expected: bool) -> None:
    # "ja-1" is the Jātaka itself, not its commentary
    assert books.sutta_central_books[book].is_commentary is expected


def write_segments(folder: Path, name: str, segments: dict[str, str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(dumps(segments), encoding="utf-8")


def test_two_folders_load_as_one_book(tmp_path: Path) -> None:
    """A book can list several folders. Its files and words come from all of them."""
    first = tmp_path / "tha-ap"
    second = tmp_path / "thi-ap"
    write_segments(first, "tha-ap2.json", {"tha-ap2:1.1": "Therapadanam eka"})
    write_segments(first, "tha-ap10.json", {"tha-ap10:1.1": "Therapadanam dasa"})
    write_segments(second, "thi-ap1.json", {"thi-ap1:1.1": "Theripadanam eka"})

    source = SuttaCentralSource(
        "ap", ["kn10", "kn11"], [str(first), str(second)], None, is_commentary=False
    )

    assert [p.name for p in source.pali_file_list] == [
        "tha-ap2.json",
        "tha-ap10.json",
        "thi-ap1.json",
    ]
    assert set(source.word_dict) == {"therapadanam", "theripadanam", "eka", "dasa"}
    assert len(source.segment_dict) == 3


def test_single_folder_string_still_works(tmp_path: Path) -> None:
    write_segments(tmp_path, "kp1.json", {"kp1:1.1": "Namo tassa"})

    source = SuttaCentralSource(
        "khp", ["kn1"], str(tmp_path), None, is_commentary=False
    )

    assert [p.name for p in source.pali_file_list] == ["kp1.json"]
    assert set(source.word_dict) == {"namo", "tassa"}


@needs_sc_data
@pytest.mark.parametrize(
    ("book", "cst_books"),
    [
        ("tha-ap", ["kn10"]),
        ("thi-ap", ["kn11"]),
        ("mnd", ["kn15"]),
        ("cnd", ["kn16"]),
    ],
)
def test_real_split_books_read_their_own_folder(
    book: str, cst_books: list[str]
) -> None:
    source = books.sutta_central_books[book]

    assert {p.parent.name for p in source.pali_file_list} == {book}
    assert source.cst_books == cst_books
    assert "ap" not in books.sutta_central_books
    assert "nidd1&2" not in books.sutta_central_books


def test_story_range_keeps_only_the_files_inside_it(tmp_path: Path) -> None:
    for number in (1, 2, 10, 11, 100):
        write_segments(
            tmp_path, f"ja{number}_root-pli-ms.json", {f"ja{number}:1.1": "x"}
        )

    source = SuttaCentralSource(
        "ja-1",
        ["kn14"],
        str(tmp_path),
        None,
        is_commentary=False,
        story_range=range(2, 11),
    )

    assert [p.name for p in source.pali_file_list] == [
        "ja2_root-pli-ms.json",
        "ja10_root-pli-ms.json",
    ]


@needs_sc_data
def test_the_five_jataka_parts_read_every_story_once() -> None:
    parts = [books.sutta_central_books[f"ja-{i}"] for i in range(1, 6)]
    names = [p.name for part in parts for p in part.pali_file_list]

    assert len(names) == 547
    assert len(set(names)) == 547
    assert "ja" not in books.sutta_central_books
    assert [len(part.pali_file_list) for part in parts] == [350, 104, 42, 14, 37]


def test_bold_tags_do_not_split_words(tmp_path: Path) -> None:
    """SC bolds a quoted word and leaves the closing "ti" outside the tag."""
    write_segments(
        tmp_path,
        "ps1.json",
        {
            "ps1:1.1": "<b>agāran</b>ti vihāro.",
            "ps1:1.2": "<b>dvīhi balehī</b>ti dve balāni.",
        },
    )

    source = SuttaCentralSource(
        "ps", ["kn17"], str(tmp_path), None, is_commentary=False
    )

    assert set(source.word_dict) == {
        "agāranti",
        "vihāro",
        "dvīhi",
        "balehīti",
        "dve",
        "balāni",
    }
    assert "<b>" in source.segment_dict["ps1:1.1"].pali
