"""Pass2Auto batch processing must not block the flet event loop.

In flet 1.0 a plain (non-async) event handler is awaited inline on the event
loop, so a handler that runs a whole book keeps every queued UI patch from
reaching the client until it returns. These tests drive the controller the way
flet drives a handler and assert the loop still gets turns while a word is
being processed.
"""

import asyncio
import inspect
import json
import time
from pathlib import Path
from typing import Any

import pytest

from gui2 import pass2_auto_control
from gui2.pass2_auto_control import Pass2AutoController
from gui2.pass2_auto_file_manager import Pass2AutoFileManager
from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit

BOOK = "test_book"
BLOCKING_SECONDS = 0.05
TICK_INTERVAL = 0.001


class UiSpy:
    """Stand-in for Pass2AutoView recording what the controller displayed."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.counts: list[str] = []
        self.words: list[str] = []
        self.results: list[str] = []
        self.cleared: int = 0

    def update_message(self, message: str) -> None:
        self.messages.append(message)

    def update_auto_processed_count(self, count: str) -> None:
        self.counts.append(str(count))

    def update_word_in_text(self, word: str) -> None:
        self.words.append(word)

    def update_ai_results(self, results: str) -> None:
        self.results.append(results)

    def clear_all_fields(self) -> None:
        self.cleared += 1


class HeadwordStub:
    def __init__(self, headword_id: int, lemma: str) -> None:
        self.id = headword_id
        self.lemma_1 = lemma
        self.source_1 = ""
        self.sutta_1 = ""
        self.example_1 = ""


class DbStub:
    def __init__(self, headwords: dict[int, HeadwordStub]) -> None:
        self._headwords = headwords

    def get_headword_by_id(self, headword_id: int) -> HeadwordStub | None:
        return self._headwords.get(headword_id)


def _write_pass2_pre_file(paths: Gui2Paths, words: dict[str, int]) -> None:
    matched = {
        word: {
            "id": headword_id,
            "sentence": [f"SN 1.{headword_id}", "sutta name", "example text"],
        }
        for word, headword_id in words.items()
    }
    json_path = paths.gui2_data_path / f"pass2_pre_{BOOK}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(
            {"unmatched": {}, "matched": matched, "new_word": {}, "processed": []}
        ),
        encoding="utf-8",
    )


def _controller(
    tmp_path: Path, words: dict[str, int]
) -> tuple[Pass2AutoController, UiSpy]:
    """Build a controller without ToolKit.__init__ (flet.Page + live dpd.db)."""
    paths = Gui2Paths(base_dir=tmp_path)
    _write_pass2_pre_file(paths, words)

    toolkit = object.__new__(ToolKit)
    toolkit.paths = paths

    controller = object.__new__(Pass2AutoController)
    ui = UiSpy()
    controller.ui = ui  # pyright: ignore[reportAttributeAccessIssue]
    controller.db = DbStub(  # pyright: ignore[reportAttributeAccessIssue]
        {
            headword_id: HeadwordStub(headword_id, word)
            for word, headword_id in words.items()
        }
    )
    controller._gui2pth = paths
    controller._failures_path = paths.pass2_auto_failures_path
    controller._pass2_auto_file_manager = Pass2AutoFileManager(toolkit)
    controller._sc_books = {}
    controller._provider_preference = None
    controller._model_name = None
    controller.processed_count = 0
    controller.stop_flag = False
    controller.gd_toggle = False
    controller._run_in_progress = False
    return controller, ui


async def _drive(controller: Pass2AutoController, method_name: str) -> None:
    """Call the handler entry point the way flet awaits an event handler."""
    result = getattr(controller, method_name)(BOOK)
    if inspect.isawaitable(result):
        await result


async def _run_with_ticker(
    controller: Pass2AutoController,
    method_name: str,
    tick_interval: float = TICK_INTERVAL,
) -> int:
    """Run the batch alongside a ticker task; return how many turns the loop got.

    `tick_interval=0` counts bare loop turns, which is the right measure for a
    batch that is fast but must still yield. A non-zero interval counts real
    elapsed turns, so the count tells the two cases apart: a batch that blocks
    the loop yields only at its own explicit yield points, while one that is
    genuinely offloaded lets the ticker run for the whole duration.
    """
    ticks = 0

    async def ticker() -> None:
        nonlocal ticks
        while True:
            await asyncio.sleep(tick_interval)
            ticks += 1

    ticker_task = asyncio.create_task(ticker())
    try:
        await _drive(controller, method_name)
    finally:
        ticker_task.cancel()
        try:
            await ticker_task
        except asyncio.CancelledError:
            pass
    return ticks


@pytest.fixture
def no_late_examples(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pass2_auto_control, "has_only_late_examples", lambda _hw: False)


class TestEventLoopStaysResponsive:
    def test_ai_batch_yields_to_the_loop(
        self, tmp_path: Path, no_late_examples: None
    ) -> None:
        words = {"karoti": 1, "gacchati": 2, "bhavati": 3}
        controller, _ui = _controller(tmp_path, words)

        def blocking_ai(*_args: Any, **_kwargs: Any) -> dict[str, str]:
            time.sleep(BLOCKING_SECONDS)
            return {"lemma_1": "karoti", "pos": "pr"}

        controller._process_headword_with_ai = blocking_ai  # pyright: ignore[reportAttributeAccessIssue]

        ticks = asyncio.run(_run_with_ticker(controller, "auto_process_book"))

        # One tick per millisecond for the whole blocking span if the request is
        # genuinely off the loop. Running it inline yields only at the handful of
        # explicit yield points, so a generous fraction still separates the two.
        expected_ticks = (BLOCKING_SECONDS * len(words)) / TICK_INTERVAL
        assert ticks > expected_ticks / 3, (
            f"only {ticks} loop turns during the run: the AI request is still "
            "being made on the event loop, so no UI patch can reach the client "
            "while a word is being processed"
        )

    def test_no_ai_batch_yields_to_the_loop(
        self, tmp_path: Path, no_late_examples: None
    ) -> None:
        words = {"karoti": 1, "gacchati": 2, "bhavati": 3}
        controller, _ui = _controller(tmp_path, words)
        controller._fields = ["id", "lemma_1"]

        ticks = asyncio.run(
            _run_with_ticker(controller, "auto_process_book_no_ai", tick_interval=0)
        )

        assert ticks > 0, (
            "the event loop never got a turn while the book was processing, "
            "so no UI patch can reach the client until the whole run is over"
        )


class TestBatchStillProcesses:
    def test_every_word_is_displayed_and_saved(
        self, tmp_path: Path, no_late_examples: None
    ) -> None:
        words = {"karoti": 1, "gacchati": 2, "bhavati": 3}
        controller, ui = _controller(tmp_path, words)
        controller._process_headword_with_ai = lambda *_a, **_k: {"lemma_1": "x"}  # pyright: ignore[reportAttributeAccessIssue]

        asyncio.run(_drive(controller, "auto_process_book"))

        assert ui.words == list(words)
        assert len(ui.results) == len(words)
        assert set(controller._pass2_auto_file_manager.get_pass2_auto_data()) == {
            "1",
            "2",
            "3",
        }


class TestConcurrentRunsAreRejected:
    def test_a_second_click_does_not_start_a_second_batch(
        self, tmp_path: Path, no_late_examples: None
    ) -> None:
        """The batch loops are async, so their buttons stay live during a run."""
        words = {"karoti": 1, "gacchati": 2, "bhavati": 3}
        controller, ui = _controller(tmp_path, words)

        def blocking_ai(*_args: Any, **_kwargs: Any) -> dict[str, str]:
            time.sleep(BLOCKING_SECONDS)
            return {"lemma_1": "karoti", "pos": "pr"}

        controller._process_headword_with_ai = blocking_ai  # pyright: ignore[reportAttributeAccessIssue]

        async def double_click() -> None:
            await asyncio.gather(
                _drive(controller, "auto_process_book"),
                _drive(controller, "auto_process_book"),
            )

        asyncio.run(double_click())

        assert ui.words == list(words), (
            f"each word must be processed exactly once, got {ui.words}"
        )
        assert "Already processing. Press Stop first." in ui.messages

    def test_the_guard_is_released_after_a_run(
        self, tmp_path: Path, no_late_examples: None
    ) -> None:
        words = {"karoti": 1}
        controller, _ui = _controller(tmp_path, words)
        controller._process_headword_with_ai = lambda *_a, **_k: {"lemma_1": "x"}  # pyright: ignore[reportAttributeAccessIssue]

        asyncio.run(_drive(controller, "auto_process_book"))

        assert controller._run_in_progress is False
