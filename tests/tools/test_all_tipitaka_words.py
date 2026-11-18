"""The combined word list holds the words of all four corpora."""

import json
from pathlib import Path

import pytest

import tools.all_tipitaka_words as module
from tools.paths import ProjectPaths

TOKENS = {
    "cst_wordlist": "cstword",
    "bjt_wordlist": "bjtword",
    "sya_wordlist": "syaword",
    "sc_wordlist": "scword",
}


def test_set_holds_one_word_from_each_corpus(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class PathsWithTinyLists(ProjectPaths):
        def __init__(self) -> None:
            super().__init__()
            for attribute, token in TOKENS.items():
                path = tmp_path / f"{attribute}.json"
                path.write_text(json.dumps([token]), encoding="utf-8")
                setattr(self, attribute, path)

    monkeypatch.setattr(module, "ProjectPaths", PathsWithTinyLists)
    assert module.make_all_tipitaka_word_set() == set(TOKENS.values())
