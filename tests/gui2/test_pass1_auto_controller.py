"""The Pass1Auto loop must let the screen redraw and read Stop while it runs."""

import asyncio
import time
from typing import Any
from types import SimpleNamespace

import pytest

import gui2.pass1_auto_controller as controller_module
from gui2.pass1_auto_controller import Pass1AutoController

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
    ctrl.related_entries_list = []
    ctrl.response = None
    ctrl.ai_status_message = ""

    def slow_request(**_):
        time.sleep(AI_DELAY)
        return SimpleNamespace(content=GOOD_JSON, status_message="ok")

    ctrl.db = SimpleNamespace(
        make_inflections_lists=lambda: None,
        get_related_dict_entries=lambda w: [],
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
    return ctrl


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
