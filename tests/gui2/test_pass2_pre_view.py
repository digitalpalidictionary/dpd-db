# -*- coding: utf-8 -*-
"""Tests for the Pass2Pre examples search in gui2.pass2_pre_view: while the
"eng" switch is on, the search also matches each CST example's English."""

from types import SimpleNamespace

import pytest

from gui2.pass2_pre_view import Pass2PreProcessView
from tools.cst_source.models import CstSourceSuttaExample

EXAMPLE = CstSourceSuttaExample(
    "DNa1",
    "brahmajālasuttavaṇṇanā",
    "paṭhamamahāsaṅgīti nāma cesā kiñcāpi vinayapiṭake tantimārūḷhā",
)
OTHER_EXAMPLE = CstSourceSuttaExample(
    "DNa1",
    "brahmajālasuttavaṇṇanā",
    "paṭhamamahāsaṅgīti nāma esā dhammasaṅgahakkhandhakā",
)


class FakeController:
    word_in_text = "paṭhamamahāsaṅgīti"

    def clean_quotes(self, text: str) -> str:
        return text

    def english_for(self, example: str) -> str:
        return "This is called the First Great Council."

    def highlight_term_for(self, text: str) -> str:
        return self.word_in_text


@pytest.fixture
def view() -> Pass2PreProcessView:
    v = object.__new__(Pass2PreProcessView)
    v.controller = FakeController()  # type: ignore[assignment]
    v.exceptions_set = set()
    v.exceptions_switch = SimpleNamespace(value=True)  # type: ignore[assignment]
    v.eng_switch = SimpleNamespace(value=True)  # type: ignore[assignment]
    v.examples_list = [EXAMPLE]
    v.examples_shown = 50
    v.examples_page_size = 50
    v.search_query = ""
    v.selected_sentence_index = 0
    return v


def test_search_matches_english_when_shown(view: Pass2PreProcessView) -> None:
    view.search_query = "great council"
    view._filter_examples()
    assert view.filtered_examples == [(0, EXAMPLE)]


def test_search_ignores_english_when_hidden(view: Pass2PreProcessView) -> None:
    view.eng_switch.value = False
    view.search_query = "great council"
    view._filter_examples()
    assert view.filtered_examples == []


def test_search_still_matches_pali(view: Pass2PreProcessView) -> None:
    view.search_query = "vinayapiṭake"
    view._filter_examples()
    assert view.filtered_examples == [(0, EXAMPLE)]


# ── selection follows what is on screen ─────────────────────────────────────


def test_visible_selection_is_kept_and_ticked(view: Pass2PreProcessView) -> None:
    view.examples_list = [EXAMPLE, OTHER_EXAMPLE]
    view.selected_sentence_index = 1
    view._filter_examples()
    radio_group = view._build_examples_radio_group()
    assert view.selected_sentence_index == 1
    assert radio_group.value == "1"


def test_hidden_selection_moves_to_first_example_shown(
    view: Pass2PreProcessView,
) -> None:
    view.examples_list = [EXAMPLE, OTHER_EXAMPLE]
    view.selected_sentence_index = 0
    view.search_query = "dhammasaṅgaha"  # hides example 0
    view._filter_examples()
    radio_group = view._build_examples_radio_group()
    assert view.selected_sentence_index == 1
    assert radio_group.value == "1"


def test_yes_saves_nothing_when_no_example_is_shown(
    view: Pass2PreProcessView,
) -> None:
    saved: list[object] = []
    messages: list[str] = []
    view.controller.current_headword = lambda: SimpleNamespace(id=1)  # type: ignore[attr-defined]
    view.controller.file_manager = SimpleNamespace(  # type: ignore[attr-defined]
        update_matched=lambda *args: saved.append(args)
    )
    view.update_message = messages.append  # type: ignore[method-assign]
    view.search_query = "no such words"
    view._filter_examples()

    view.handle_yes_click(None)

    assert saved == []
    assert messages == ["no example selected"]
