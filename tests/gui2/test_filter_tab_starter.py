"""A contributor with no saved preset opens the DB tab on the starter preset."""

from unittest.mock import MagicMock

import pytest

from gui2.filter_tab_view import (
    CONTRIBUTOR_DATA_FILTERS,
    CONTRIBUTOR_DISPLAY_FILTERS,
    FilterTabView,
)
from gui2.main import App


@pytest.fixture(autouse=True)
def _stub_page(monkeypatch: pytest.MonkeyPatch) -> None:
    # Flet 1.0 raises on `.page` of an unmounted control.
    monkeypatch.setattr(FilterTabView, "page", MagicMock(), raising=False)


def _toolkit(*, not_primary: bool, first_preset: dict | None = None) -> MagicMock:
    toolkit = MagicMock()
    toolkit.username_manager.is_not_primary.return_value = not_primary
    toolkit.filter_presets_manager.get_first_preset.return_value = first_preset
    return toolkit


def _app(toolkit: MagicMock) -> App:
    app = App.__new__(App)
    app.page = MagicMock()  # pyright: ignore[reportAttributeAccessIssue]
    app.toolkit = toolkit  # pyright: ignore[reportAttributeAccessIssue]
    return app


def _checked(view: FilterTabView) -> set[str]:
    return {str(box.label) for box in view.column_checkboxes if box.value}


def test_the_starter_values_are_the_agreed_ones() -> None:
    assert CONTRIBUTOR_DATA_FILTERS == [("lemma_1", "")]
    assert CONTRIBUTOR_DISPLAY_FILTERS == [
        "id",
        "pos",
        "grammar",
        "meaning_1",
        "meaning_2",
        "meaning_lit",
    ]


def test_a_contributor_with_no_preset_gets_the_starter() -> None:
    view = _app(_toolkit(not_primary=True))._make_filter_tab()

    assert view.column_dropdowns[0].value == "lemma_1"
    assert view.regex_inputs[0].value == ""
    assert _checked(view) == set(CONTRIBUTOR_DISPLAY_FILTERS)


def test_the_primary_user_keeps_the_old_defaults() -> None:
    view = _app(_toolkit(not_primary=False))._make_filter_tab()

    assert view.column_dropdowns[0].value == "root_key"
    assert "root_key" in _checked(view)


def test_a_saved_preset_wins_over_the_starter() -> None:
    preset = {
        "data_filters": [["pos", "noun"]],
        "display_filters": ["id", "pos"],
        "limit": 50,
    }
    view = _app(_toolkit(not_primary=True, first_preset=preset))._make_filter_tab()

    assert view.column_dropdowns[0].value == "pos"
    assert _checked(view) == {"id", "pos"}


def test_reset_gives_the_starter_when_no_preset_is_saved() -> None:
    view = _app(_toolkit(not_primary=True))._make_filter_tab()
    view.column_dropdowns[0].value = "stem"

    view._reset_to_default_clicked(None)

    assert view.column_dropdowns[0].value == "lemma_1"
    assert _checked(view) == set(CONTRIBUTOR_DISPLAY_FILTERS)
