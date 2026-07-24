import pytest

from db.models import DpdHeadword
import gui2.sandhi_find_replace_view as mod
from gui2.sandhi_find_replace_view import Data, SandhiFindReplaceView


@pytest.fixture
def data(monkeypatch: pytest.MonkeyPatch) -> Data:
    monkeypatch.setattr(mod, "get_db_session", lambda _: object())
    return Data()


@pytest.fixture
def view(monkeypatch: pytest.MonkeyPatch) -> SandhiFindReplaceView:
    monkeypatch.setattr(mod, "get_db_session", lambda _: object())
    v = SandhiFindReplaceView(page=None, toolkit=None)  # type: ignore[arg-type]
    v.update = lambda *a, **k: None  # type: ignore[assignment]
    return v


def _headword(**fields: str) -> DpdHeadword:
    hw = DpdHeadword()
    for name, value in fields.items():
        setattr(hw, name, value)
    return hw


class TestData:
    def test_columns_are_the_pali_fields(self, data: Data) -> None:
        assert data.columns == ["example_1", "example_2", "commentary"]

    def test_increment_walks_columns_then_next_row(self, data: Data) -> None:
        data.db_results = [_headword(), _headword()]

        seen = [(data.index, data.column_index)]
        for _ in range(6):
            data.increment()
            seen.append((data.index, data.column_index))

        assert seen == [
            (0, 0),
            (0, 1),
            (0, 2),
            (1, 0),
            (1, 1),
            (1, 2),
            (2, 0),
        ]

    def test_end_of_walk_sentinel(self, data: Data) -> None:
        data.db_results = [_headword()]
        for _ in range(3):
            data.increment()
        assert data.index >= len(data.db_results)

    def test_field_accessors(self, data: Data) -> None:
        data.db_results = [_headword(example_1="alpha", commentary="beta")]
        data.index = 0
        data.column_index = 0
        assert data.this_field_name == "example_1"
        assert data.this_field_text == "alpha"
        data.column_index = 2
        assert data.this_field_name == "commentary"
        assert data.this_field_text == "beta"


class TestHighlight:
    def test_literal_term_is_highlighted(self, view: SandhiFindReplaceView) -> None:
        view.find_me = "gacchati"
        view.replace_me = "gacchāmi"
        text = "so gacchati vana"

        view._highlight_found(text)
        highlighted = [s.text for s in view.found_field.spans if s.style is not None]

        assert highlighted == ["gacchati"]
