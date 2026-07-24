import re

import pytest

from db.models import DpdHeadword
import gui2.spelling_find_replace_view as mod
from gui2.spelling_find_replace_view import Data, SpellingFindReplaceView


@pytest.fixture
def data(monkeypatch: pytest.MonkeyPatch) -> Data:
    monkeypatch.setattr(mod, "get_db_session", lambda _: object())
    return Data()


@pytest.fixture
def view(monkeypatch: pytest.MonkeyPatch) -> SpellingFindReplaceView:
    monkeypatch.setattr(mod, "get_db_session", lambda _: object())
    v = SpellingFindReplaceView(page=None, toolkit=None)  # type: ignore[arg-type]
    v.update = lambda *a, **k: None  # type: ignore[assignment]
    return v


def _headword(**fields: str) -> DpdHeadword:
    hw = DpdHeadword()
    for name, value in fields.items():
        setattr(hw, name, value)
    return hw


class TestData:
    def test_columns_are_the_english_prose_fields(self, data: Data) -> None:
        assert data.columns == ["meaning_1", "meaning_2", "meaning_lit", "notes"]

    def test_increment_walks_columns_then_next_row(self, data: Data) -> None:
        data.db_results = [_headword(), _headword()]

        seen = [(data.index, data.column_index)]
        for _ in range(8):
            data.increment()
            seen.append((data.index, data.column_index))

        assert seen == [
            (0, 0),
            (0, 1),
            (0, 2),
            (0, 3),
            (1, 0),
            (1, 1),
            (1, 2),
            (1, 3),
            (2, 0),
        ]

    def test_end_of_walk_sentinel(self, data: Data) -> None:
        data.db_results = [_headword()]
        for _ in range(4):
            data.increment()
        assert data.index >= len(data.db_results)

    def test_field_accessors(self, data: Data) -> None:
        data.db_results = [_headword(meaning_1="alpha", notes="")]
        data.index = 0
        data.column_index = 0
        assert data.this_field_name == "meaning_1"
        assert data.this_field_text == "alpha"
        data.column_index = 3
        assert data.this_field_name == "notes"
        assert data.this_field_text == ""


class TestTransforms:
    def test_raw_regex_word_boundary_replaces_whole_word_only(
        self, view: SpellingFindReplaceView
    ) -> None:
        view.find_me = r"\bcognise\b"
        view.replace_me = "cognize"
        text = "recognise then cognise now"

        view._highlight_replaced(text)
        full = "".join(s.text or "" for s in view.replaced_field.spans)
        highlighted = [s.text for s in view.replaced_field.spans if s.style is not None]

        assert full == re.sub(view.find_me, view.replace_me, text)
        assert full == "recognise then cognize now"
        assert highlighted == ["cognize"]

    def test_found_highlights_matches_only(self, view: SpellingFindReplaceView) -> None:
        view.find_me = r"\bcognise\b"
        view.replace_me = "cognize"
        text = "recognise then cognise now"

        view._highlight_found(text)
        highlighted = [s.text for s in view.found_field.spans if s.style is not None]

        assert highlighted == ["cognise"]

    def test_backreference_replacement(self, view: SpellingFindReplaceView) -> None:
        view.find_me = r"(\w+?)ise\b"
        view.replace_me = r"\1ize"
        text = "to realise and to organise"

        view._highlight_replaced(text)
        full = "".join(s.text or "" for s in view.replaced_field.spans)

        assert full == "to realize and to organize"
