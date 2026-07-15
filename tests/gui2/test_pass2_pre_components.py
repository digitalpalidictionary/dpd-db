# -*- coding: utf-8 -*-
"""Tests for the pass2 preprocessor's "in comps" mode in
gui2.pass2_pre_controller: one work item per compound, whose
missing-example components are reviewed against sentences containing
the compound itself."""

import pytest

import gui2.pass2_pre_controller as controller_module
from gui2.pass2_pre_controller import Pass2PreController


class FakeHeadword:
    def __init__(self, id: int, lemma_1: str) -> None:
        self.id = id
        self.lemma_1 = lemma_1


class FakeDb:
    def __init__(self) -> None:
        self.all_inflections_missing_example: set[str] = {
            "buddho",
            "assakhaluṅka",
            "assakhaluṅkā",
            "dhammacakka",
            "khaluṅka",
            "dhamma",
            "sīla",
        }
        self.all_decon_no_headwords: set[str] = set()
        self.compound_components_map: dict[str, list[str]] = {
            "assakhaluṅka": ["assa", "khaluṅka"],
            "assakhaluṅkā": ["assa", "khaluṅka"],
            "dhammacakka": ["dhamma", "cakka"],
            "sīlakkhandha": ["sīla", "khandha"],
        }
        # word -> its missing-example headwords
        self.headwords: dict[str, list[FakeHeadword]] = {}

    def make_pass2_lists(self) -> None:
        pass

    def make_compound_components_map(self) -> None:
        pass

    def get_headwords(self, word: str) -> list[FakeHeadword]:
        return list(self.headwords.get(word, []))


class FakeFileManager:
    def __init__(self, book: str, paths) -> None:
        self.unmatched: dict[str, list] = {}
        self.matched: dict[str, list] = {}
        self.new_word: dict[str, list] = {}


class FakeSource:
    def __init__(self, word_dict: dict[str, list]) -> None:
        self.sc_book = "mn"
        self.cst_books = ["mn1"]
        self.word_dict = word_dict


class FakeFiles:
    variants_dict: dict[str, str] = {}
    spelling_mistakes_dict: dict[str, str] = {}


@pytest.fixture
def controller(monkeypatch: pytest.MonkeyPatch) -> Pass2PreController:
    """Pass2PreController with stubbed db, file manager and book sources."""
    sc_segments = [("mn1:1.1", "dhammacakkaṃ pavattitaṃ", "")]
    fake_books = {"mn": FakeSource({"dhammacakka": sc_segments})}
    # "sīlakkhandha" is a compound that already has an example (not missing),
    # so it is only queued because its component "sīla" is missing one
    cst_words = ["buddho", "assakhaluṅka", "assakhaluṅkā", "assa", "sīlakkhandha"]

    monkeypatch.setattr(controller_module, "sutta_central_books", fake_books)
    monkeypatch.setattr(controller_module, "Pass2PreFileManager", FakeFileManager)
    monkeypatch.setattr(
        controller_module, "make_cst_text_list", lambda *a, **k: cst_words
    )

    c = object.__new__(Pass2PreController)
    c.db = FakeDb()
    c.variant_readings = FakeFiles()
    c.spelling_mistakes = FakeFiles()
    c.sutta_central_books = fake_books
    c.all_cst_words = []
    c.missing_examples_dict = {}
    c.in_comps = False
    c.comps_components = {}
    c.entry_headword_sources = {}
    return c


def test_in_comps_queues_compounds_with_missing_components(
    controller: Pass2PreController,
):
    controller.find_words_with_missing_examples("mn", None, in_comps=True)  # type: ignore[arg-type]

    # all work items appear in text order — "sīlakkhandha" has an example
    # itself but is queued at its place in the text for its component "sīla"
    assert list(controller.missing_examples_dict) == [
        "buddho",
        "assakhaluṅka",
        "assakhaluṅkā",
        "sīlakkhandha",
        "dhammacakka",
    ]
    assert controller.missing_examples_dict["sīlakkhandha"] == []
    # each compound work item knows which components are missing examples
    assert controller.comps_components == {
        "assakhaluṅka": ["khaluṅka"],
        "assakhaluṅkā": ["khaluṅka"],
        "dhammacakka": ["dhamma"],
        "sīlakkhandha": ["sīla"],
    }


def test_in_comps_off_leaves_queue_unchanged(controller: Pass2PreController):
    controller.find_words_with_missing_examples("mn", None, in_comps=False)  # type: ignore[arg-type]

    assert list(controller.missing_examples_dict) == [
        "buddho",
        "assakhaluṅka",
        "assakhaluṅkā",
        "dhammacakka",
    ]
    assert controller.comps_components == {}


def test_processed_compound_still_queued_for_missing_components(
    controller: Pass2PreController,
):
    # the compound itself was already matched in a previous run,
    # but its component "sīla" still needs an example — requeue it
    controller.find_words_with_missing_examples("mn", None, in_comps=True)  # type: ignore[arg-type]
    controller.file_manager.matched["sīlakkhandha"] = {}
    controller.missing_examples_dict = {}
    controller.comps_components = {}

    controller.make_all_words_dict()
    controller.add_sc_words()
    assert controller.comps_components["sīlakkhandha"] == ["sīla"]
    assert "sīlakkhandha" in controller.missing_examples_dict


def test_rerun_with_switch_off_clears_comps_state(controller: Pass2PreController):
    # run ON, then rerun OFF: no comps state may leak into the second run
    controller.find_words_with_missing_examples("mn", None, in_comps=True)  # type: ignore[arg-type]
    assert controller.comps_components

    controller.missing_examples_dict = {}
    controller.find_words_with_missing_examples("mn", None, in_comps=False)  # type: ignore[arg-type]
    assert controller.comps_components == {}
    assert controller.entry_headword_sources == {}
    assert list(controller.missing_examples_dict) == [
        "buddho",
        "assakhaluṅka",
        "assakhaluṅkā",
        "dhammacakka",
    ]


def test_no_on_subword_hides_only_that_pair(controller: Pass2PreController):
    # No on "khaluṅka" under "assakhaluṅka" is saved as the pair key,
    # so "assakhaluṅka" no longer queues for it...
    controller.find_words_with_missing_examples("mn", None, in_comps=True)  # type: ignore[arg-type]
    controller.file_manager.unmatched["assakhaluṅka + khaluṅka"] = [1]
    controller.missing_examples_dict = {}
    controller.comps_components = {}

    controller.make_all_words_dict()
    controller.add_sc_words()
    assert "assakhaluṅka" not in controller.comps_components
    # ...but other compounds containing "khaluṅka" still surface it
    assert controller.comps_components["assakhaluṅkā"] == ["khaluṅka"]


def test_unmatched_key_is_pair_for_subword(controller: Pass2PreController):
    compound_hw = FakeHeadword(1, "sīlakkhandha 1")
    sila_hw = FakeHeadword(2, "sīla 1")
    controller.db.headwords = {  # type: ignore[attr-defined]
        "sīlakkhandha": [compound_hw],
        "sīla": [sila_hw],
    }
    controller.comps_components = {"sīlakkhandha": ["sīla"]}
    controller.word_in_text = "sīlakkhandha"
    controller.headwords = controller.get_entry_headwords("sīlakkhandha")  # type: ignore[assignment]

    # No on the compound's own headword keeps the plain key
    controller.headword_index = 0
    assert controller.current_unmatched_key() == "sīlakkhandha"
    # No on the sub word's headword is keyed by the pair
    controller.headword_index = 1
    assert controller.current_unmatched_key() == "sīlakkhandha + sīla"


def test_decided_component_not_requeued(controller: Pass2PreController):
    # once the component itself has been matched, the compound
    # no longer becomes a work item
    controller.find_words_with_missing_examples("mn", None, in_comps=True)  # type: ignore[arg-type]
    controller.file_manager.matched["sīla"] = {}
    controller.missing_examples_dict = {}
    controller.comps_components = {}

    controller.make_all_words_dict()
    controller.add_sc_words()
    assert "sīlakkhandha" not in controller.comps_components
    assert "sīlakkhandha" not in controller.missing_examples_dict


# ── headword resolution per work item ────────────────────────────────────────


def test_entry_headwords_include_missing_components(
    controller: Pass2PreController,
):
    compound_hw = FakeHeadword(1, "sīlakkhandha 1")
    sila_hw = FakeHeadword(2, "sīla 1")
    controller.db.headwords = {  # type: ignore[attr-defined]
        "sīlakkhandha": [],  # compound has an example -> no own headwords
        "sīla": [sila_hw],
    }
    controller.comps_components = {"sīlakkhandha": ["sīla"]}
    assert controller.get_entry_headwords("sīlakkhandha") == [sila_hw]

    # a compound missing its own example lists itself first, then components
    controller.db.headwords["sīlakkhandha"] = [compound_hw]  # type: ignore[attr-defined]
    assert controller.get_entry_headwords("sīlakkhandha") == [compound_hw, sila_hw]


def test_entry_headwords_deduplicated_by_id(controller: Pass2PreController):
    shared = FakeHeadword(7, "dhamma 1")
    controller.db.headwords = {  # type: ignore[attr-defined]
        "dhammacakka": [shared],
        "dhamma": [shared],
    }
    controller.comps_components = {"dhammacakka": ["dhamma"]}
    assert controller.get_entry_headwords("dhammacakka") == [shared]


def test_regular_word_headwords_unchanged(controller: Pass2PreController):
    hw = FakeHeadword(3, "buddha 1")
    controller.db.headwords = {"buddho": [hw]}  # type: ignore[attr-defined]
    assert controller.get_entry_headwords("buddho") == [hw]


def test_decisions_recorded_under_component_word(controller: Pass2PreController):
    compound_hw = FakeHeadword(1, "sīlakkhandha 1")
    sila_hw = FakeHeadword(2, "sīla 1")
    controller.db.headwords = {  # type: ignore[attr-defined]
        "sīlakkhandha": [compound_hw],
        "sīla": [sila_hw],
    }
    controller.comps_components = {"sīlakkhandha": ["sīla"]}
    controller.word_in_text = "sīlakkhandha"
    controller.headwords = controller.get_entry_headwords("sīlakkhandha")  # type: ignore[assignment]

    # the compound's own headword is saved under the compound word
    controller.headword_index = 0
    assert controller.current_source_word() == "sīlakkhandha"
    # the component's headword is saved under the component word,
    # so it never overwrites the compound's own match
    controller.headword_index = 1
    assert controller.current_source_word() == "sīla"


def test_current_headword_none_when_index_stale(controller: Pass2PreController):
    hw = FakeHeadword(1, "sīla 1")
    controller.headwords = [hw]  # type: ignore[assignment]
    controller.headword_index = 0
    assert controller.current_headword() is hw

    # exhausted queue leaves an empty list / stale index behind
    controller.headwords = []
    assert controller.current_headword() is None
    controller.headwords = [hw]  # type: ignore[assignment]
    controller.headword_index = 5
    assert controller.current_headword() is None
    controller.headword_index = -1
    assert controller.current_headword() is None


# ── display and example search ───────────────────────────────────────────────


def test_display_depends_on_current_headword(controller: Pass2PreController):
    compound_hw = FakeHeadword(1, "sīlakkhandha 1")
    sila_hw = FakeHeadword(2, "sīla 1")
    controller.db.headwords = {  # type: ignore[attr-defined]
        "sīlakkhandha": [compound_hw],
        "sīla": [sila_hw],
    }
    controller.comps_components = {"sīlakkhandha": ["sīla"]}
    controller.word_in_text = "sīlakkhandha"
    controller.headwords = controller.get_entry_headwords("sīlakkhandha")  # type: ignore[assignment]

    # the compound's own headword shows just the main word
    controller.headword_index = 0
    assert controller.display_word_in_text() == "sīlakkhandha"
    # a component headword shows [main word] sub word
    controller.headword_index = 1
    assert controller.display_word_in_text() == "[sīlakkhandha] sīla"


def test_highlight_term_is_subword_shortened_until_found(
    controller: Pass2PreController,
):
    sila_hw = FakeHeadword(2, "sīla 1")
    controller.db.headwords = {"sīlakkhandha": [], "sīla": [sila_hw]}  # type: ignore[attr-defined]
    controller.comps_components = {"sīlakkhandha": ["sīla"]}
    controller.word_in_text = "sīlakkhandha"
    controller.headwords = controller.get_entry_headwords("sīlakkhandha")  # type: ignore[assignment]
    controller.headword_index = 0

    # the sub word is highlighted, not the compound
    assert controller.highlight_term_for("sīlakkhandho samatto") == "sīla"
    # not found whole -> shorten from the end until it matches
    assert controller.highlight_term_for("sīḷakkhandho") == "sī"


def test_highlight_term_for_regular_word_never_shortened(
    controller: Pass2PreController,
):
    # a regular word absent from the sentence gets no spurious
    # fragment highlight — highlight_terms drops non-matching terms
    controller.word_in_text = "buddho"
    controller.headwords = []  # type: ignore[assignment]
    controller.headword_index = -1
    assert controller.highlight_term_for("na kiñci ettha") == "buddho"


def test_examples_search_for_the_compound_itself(
    controller: Pass2PreController,
):
    captured: list[str] = []

    class FakeIndex:
        def find_examples(self, regex: str) -> list:
            captured.append(regex)
            return []

    controller._cst_index = FakeIndex()  # type: ignore[assignment]
    controller.cst_books = ["mn1"]
    controller.comps_components = {"sīlakkhandha": ["sīla"]}
    controller.word_in_text = "sīlakkhandha"
    controller.missing_examples_dict = {"sīlakkhandha": []}
    controller.get_cst_examples()
    assert captured == [r"\bsīlakkhandha\b"]
