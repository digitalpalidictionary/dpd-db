"""The Pass1Auto loop must let the screen redraw and read Stop while it runs."""

import asyncio
import time
from typing import Any
from types import SimpleNamespace

import pytest

import gui2.pass1_auto_controller as controller_module
from gui2.books import SuttaCentralSegment
from gui2.pass1_auto_controller import Pass1AutoController
from gui2.pass1_context import AllowedValues

WORDS = ["narena", "naro", "nara"]
AI_DELAY = 0.15
GOOD_JSON = '{"lemma_1": "nara", "comment": "c"}'


class FakeUI:
    def __init__(self) -> None:
        self.ai_model_dropdown = SimpleNamespace(value=None)
        self.messages: list[str] = []

    def __getattr__(self, name: str):
        return lambda *a, **k: None

    def update_message(self, message: str) -> None:
        self.messages.append(message)


def make_controller(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Any:
    monkeypatch.setattr(controller_module, "open_in_goldendict", lambda _: None)
    ctrl: Any = object.__new__(Pass1AutoController)
    ctrl.ui = FakeUI()
    ctrl.stop_flag = False
    ctrl._run_in_progress = False
    ctrl.gd_toggle = False
    ctrl.book = "text"
    ctrl.auto_processed_dict = {}
    ctrl.auto_processed_keys = []
    ctrl.initial_auto_processed = 0
    ctrl.current_book_processed = 0
    ctrl.missing_words_dict = {}
    ctrl.chosen_sentences = []
    ctrl.epitaka_dict = {}
    ctrl.allowed = AllowedValues([], [], [], [])
    ctrl.sentence_data = []
    ctrl.response = None
    ctrl.ai_status_message = ""

    def slow_request(**_):
        time.sleep(AI_DELAY)
        return SimpleNamespace(content=GOOD_JSON, status_message="ok")

    ctrl.db = SimpleNamespace(
        make_inflections_lists=lambda: None,
        new_db_session=lambda: None,
        db_session=None,
        all_inflections=set(),
        sandhi_ok_list=set(),
        pth=SimpleNamespace(temp_dir=tmp_path),
    )
    ctrl.ai_manager = SimpleNamespace(request=slow_request)
    ctrl.variant_readings = SimpleNamespace(variants_dict={})
    ctrl.spelling_mistakes = SimpleNamespace(spelling_mistakes_dict={})
    ctrl.load_auto_processed = lambda: None
    ctrl.add_word = lambda book, word, data: ctrl.auto_processed_dict.update(
        {word: data}
    )
    monkeypatch.setattr(controller_module, "clean_machine", lambda t: t)
    monkeypatch.setattr(controller_module, "related_headwords", lambda db, w: [])
    monkeypatch.setattr(controller_module, "peu_entries", lambda w: [])
    monkeypatch.setattr(
        controller_module,
        "load_allowed_values",
        lambda db: AllowedValues([], [], [], []),
    )
    return ctrl


def compile_for(
    ctrl: Any, word: str, sc: list[tuple[str, str]], epitaka: list[tuple[str, str]]
) -> None:
    ctrl.book = "vv"
    ctrl.word_in_text = word
    ctrl.sentence_data = [
        SuttaCentralSegment(f"seg{i}", pali, english)
        for i, (pali, english) in enumerate(sc)
    ]
    ctrl.epitaka_dict = {word: epitaka}
    ctrl.compile_prompt()


def test_sc_sentences_come_before_epitaka(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    ctrl = make_controller(monkeypatch, tmp_path)
    compile_for(
        ctrl,
        "nara",
        [("sc pali one", "sc english")],
        [("epitaka pali two", "ep english")],
    )

    assert ctrl.chosen_sentences == [
        ("sc pali one", "sc english"),
        ("epitaka pali two", "ep english"),
    ]
    assert ctrl.prompt.index("sc pali one") < ctrl.prompt.index("epitaka pali two")


def test_never_more_than_three_sentences(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    ctrl = make_controller(monkeypatch, tmp_path)
    sc = [("sentence_a", "1"), ("sentence_b", "2")]
    epitaka = [("sentence_c", "3"), ("sentence_d", "4"), ("sentence_e", "5")]
    compile_for(ctrl, "nara", sc, epitaka)

    assert len(ctrl.chosen_sentences) == 3
    assert "sentence_d" not in ctrl.prompt


def test_no_epitaka_uses_sc_only(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    ctrl = make_controller(monkeypatch, tmp_path)
    compile_for(ctrl, "nara", [("sc pali", "sc english")], [])

    assert ctrl.chosen_sentences == [("sc pali", "sc english")]


def test_no_peu_means_no_peu_block(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    ctrl = make_controller(monkeypatch, tmp_path)
    compile_for(ctrl, "nara", [], [])
    assert "Pali English Ultimate" not in ctrl.prompt

    monkeypatch.setattr(controller_module, "peu_entries", lambda w: ["nara: man"])
    compile_for(ctrl, "nara", [], [])
    assert "Pali English Ultimate" in ctrl.prompt
    assert "- nara: man" in ctrl.prompt


def test_example_1_is_the_first_chosen_sentence(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    ctrl = make_controller(monkeypatch, tmp_path)
    compile_for(
        ctrl, "nara", [("sc pali", "sc english")], [("epitaka pali", "ep english")]
    )
    ctrl.response = GOOD_JSON
    ctrl.update_auto_processed(None, None)

    saved = ctrl.auto_processed_dict["nara"]
    assert saved["example_1"] == "sc pali"
    assert saved["translation_1"] == "sc english"
    assert saved["example_2"] == "epitaka pali"


def test_loop_lets_the_screen_run_during_ai_calls(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    ctrl = make_controller(monkeypatch, tmp_path)

    async def run() -> int:
        ticks = 0

        async def ticker() -> None:
            nonlocal ticks
            while True:
                await asyncio.sleep(0.01)
                ticks += 1

        task = asyncio.create_task(ticker())
        await ctrl.auto_process_text(" ".join(WORDS))
        task.cancel()
        return ticks

    ticks = asyncio.run(run())
    # 3 words x 0.15 s of AI wait = 0.45 s, so about 45 ticks if the loop yields.
    assert ticks >= 20
    assert set(ctrl.auto_processed_dict) == set(WORDS)


def test_stop_halts_after_the_current_word(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    ctrl = make_controller(monkeypatch, tmp_path)

    async def run() -> None:
        async def stopper() -> None:
            await asyncio.sleep(AI_DELAY / 2)
            ctrl.stop_flag = True

        task = asyncio.create_task(stopper())
        await ctrl.auto_process_text(" ".join(WORDS))
        await task

    asyncio.run(run())
    assert len(ctrl.auto_processed_dict) == 1
