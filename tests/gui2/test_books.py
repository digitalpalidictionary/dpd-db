# -*- coding: utf-8 -*-
"""Tests that `SuttaCentralSource` builds its text index on first use rather
than at construction, so importing `gui2.books` stays off the startup path."""

from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, IO

import pytest

import gui2.books as books
from gui2.books import SuttaCentralSource

KHP_PALI = "resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/kp"
KHP_ENGLISH = "resources/sc-data/sc_bilara_data/translation/en/sujato/sutta/kn/kp"

pytestmark = pytest.mark.skipif(
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
    return SuttaCentralSource("khp", ["kn1"], KHP_PALI, KHP_ENGLISH)


def test_construction_does_not_build_the_index(load_calls: list[str]) -> None:
    source = make_source()

    assert source.pali_file_list, "fixture book has no pali files to index"
    assert "segment_dict" not in vars(source)
    assert "word_dict" not in vars(source)
    assert load_calls == []


def test_first_word_dict_access_builds_the_index(load_calls: list[str]) -> None:
    source = make_source()
    assert load_calls == []

    word_dict = source.word_dict

    assert load_calls, "reading word_dict did not read any source file"
    assert isinstance(word_dict, defaultdict)
    assert word_dict, "word index is empty"
    assert source.segment_dict, "segment index is empty"


def test_index_is_built_only_once(load_calls: list[str]) -> None:
    source = make_source()
    first = source.word_dict
    calls_after_first = len(load_calls)

    second = source.word_dict

    assert second is first
    assert len(load_calls) == calls_after_first


def test_none_path_source_stays_lazy_and_empty(load_calls: list[str]) -> None:
    """The four sources constructed with None paths (nidd1&2, kva, dhpa,
    jaa) must build neither index and read no files."""
    source = SuttaCentralSource("kva", ["kva"], None, None)

    assert source.pali_file_list == []
    assert source.english_file_list == []
    assert source.word_dict == {}
    assert isinstance(source.word_dict, defaultdict)
    assert source.segment_dict == {}
    assert load_calls == []
