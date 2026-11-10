import asyncio
import inspect
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import flet as ft
import pytest
from flet.messaging.session import Session

from gui2 import server_lifecycle as sl
from gui2.server_lifecycle import (
    COUNTDOWN_SECONDS,
    IDLE_MINUTES,
    IdleAction,
    Lifecycle,
    banner_step,
    banner_text,
    decide_idle,
    idle_seconds_from_env,
    minutes_left,
)
from tools.contrib_notice import write_notice

IDLE = 60 * 30


def decide(
    now: float = 10_000.0,
    last_activity: float = 10_000.0,
    countdown_started: float | None = None,
    idle_seconds: int = IDLE,
    any_connected: bool = True,
    offline_sent: bool = False,
) -> IdleAction:
    return decide_idle(
        now,
        last_activity,
        countdown_started,
        idle_seconds,
        any_connected,
        offline_sent,
    )


class TestDecideIdle:
    def test_recent_activity_does_nothing(self) -> None:
        assert decide(now=10_000 + IDLE - 1) is IdleAction.NOTHING

    def test_idle_with_a_page_shows_the_countdown(self) -> None:
        assert decide(now=10_000 + IDLE) is IdleAction.SHOW_COUNTDOWN

    def test_idle_with_no_page_sleeps_at_once(self) -> None:
        assert decide(now=10_000 + IDLE, any_connected=False) is IdleAction.SLEEP

    def test_countdown_running_waits(self) -> None:
        started = 20_000.0
        action = decide(
            now=started + COUNTDOWN_SECONDS - 1,
            countdown_started=started,
        )
        assert action is IdleAction.NOTHING

    def test_countdown_over_sleeps(self) -> None:
        started = 20_000.0
        action = decide(now=started + COUNTDOWN_SECONDS, countdown_started=started)
        assert action is IdleAction.SLEEP

    def test_countdown_over_with_no_page_still_sleeps(self) -> None:
        started = 20_000.0
        action = decide(
            now=started + COUNTDOWN_SECONDS,
            countdown_started=started,
            any_connected=False,
        )
        assert action is IdleAction.SLEEP

    def test_activity_after_the_countdown_start_cancels_it(self) -> None:
        started = 20_000.0
        action = decide(
            now=started + COUNTDOWN_SECONDS + 50,
            last_activity=started + 5,
            countdown_started=started,
        )
        assert action is IdleAction.CANCEL_COUNTDOWN

    def test_offline_sent_overrides_everything(self) -> None:
        assert decide(now=10_000 + IDLE * 3, offline_sent=True) is IdleAction.NOTHING
        assert (
            decide(
                now=50_000,
                countdown_started=20_000,
                offline_sent=True,
                any_connected=False,
            )
            is IdleAction.NOTHING
        )

    def test_idle_zero_turns_it_off(self) -> None:
        assert decide(now=10_000 + IDLE * 9, idle_seconds=0) is IdleAction.NOTHING


class TestIdleSecondsFromEnv:
    def test_unset_uses_the_default(self) -> None:
        assert idle_seconds_from_env({}) == (IDLE_MINUTES * 60, "default")

    def test_zero_is_off(self) -> None:
        assert idle_seconds_from_env({sl.IDLE_ENV: "0"}) == (0, "off by env")

    def test_positive_number_is_minutes(self) -> None:
        assert idle_seconds_from_env({sl.IDLE_ENV: "2"}) == (120, "env")

    @pytest.mark.parametrize("raw", ["abc", "-3", "", "1.5"])
    def test_bad_value_falls_back_and_says_so(self, raw: str) -> None:
        seconds, reason = idle_seconds_from_env({sl.IDLE_ENV: raw})
        assert seconds == IDLE_MINUTES * 60
        assert reason == f"bad env value {raw}, using {IDLE_MINUTES}"


class TestBannerMaths:
    NOW = datetime(2026, 11, 9, 19, 0, 0, tzinfo=UTC)

    def test_minutes_left_rounds_up(self) -> None:
        assert minutes_left(self.NOW + timedelta(minutes=29, seconds=1), self.NOW) == 30
        assert minutes_left(self.NOW + timedelta(minutes=30), self.NOW) == 30
        assert minutes_left(self.NOW + timedelta(seconds=30), self.NOW) == 1

    @pytest.mark.parametrize(
        ("minutes", "step"),
        [
            (31, None),
            (30, 30),
            (16, 30),
            (15, 15),
            (12, 15),
            (10, 10),
            (6, 10),
            (5, 5),
            (2, 5),
            (1, 1),
            (0, None),
        ],
    )
    def test_banner_step(self, minutes: int, step: int | None) -> None:
        assert banner_step(minutes) == step

    def test_a_stop_time_in_the_past_gives_zero_or_less(self) -> None:
        assert minutes_left(self.NOW - timedelta(seconds=30), self.NOW) == 0
        assert minutes_left(self.NOW - timedelta(seconds=61), self.NOW) == -1

    def test_banner_text_singular_and_plural(self) -> None:
        assert "in 1 minute." in banner_text(1)
        assert "in 15 minutes." in banner_text(15)


def test_countdown_body_names_the_minutes() -> None:
    assert "for 30 minutes." in sl.countdown_body(1800)
    assert "for 1 minute." in sl.countdown_body(60)
    assert "sleep in 2 minutes." in sl.countdown_body(1800)


def test_flet_session_still_has_the_two_inbound_methods() -> None:
    """Idle sleep wraps these two Flet internals (spec A.2, A.3).

    If this fails after a Flet upgrade, idle sleep has no way to see what the
    browser sends: read thread 20261109_contrib_idle_notices spec A.3.
    """
    assert inspect.iscoroutinefunction(Session.dispatch_event), (
        "Session.dispatch_event is gone or no longer async (spec A.3)"
    )
    assert callable(Session.apply_patch), "Session.apply_patch is gone (spec A.3)"
    # attach() wraps apply_patch with a plain function; an async one would
    # turn the wrapper's return value into an un-awaited coroutine.
    assert not inspect.iscoroutinefunction(Session.apply_patch), (
        "Session.apply_patch became async: the wrapper in attach() must await it"
    )


def test_the_window_waits_longer_than_one_editor_check_plus_the_flush() -> None:
    """The window stops the editors OFFLINE_GRACE_SECONDS after the announced
    stop time. If the editors' check interval grows past that, no editor sees
    the stop time before the process dies."""
    from scripts.server_contrib.maintenance_window import OFFLINE_GRACE_SECONDS

    assert OFFLINE_GRACE_SECONDS > sl.TICK_SECONDS + sl.SLEEP_FLUSH_SECONDS


def test_the_sleep_flush_is_a_real_wait() -> None:
    assert sl.SLEEP_FLUSH_SECONDS > 0


class FakeSession:
    def __init__(self) -> None:
        self.connection: object | None = object()
        self.dispatched: list[tuple] = []
        self.patched: list[tuple] = []

    async def dispatch_event(self, *args) -> str:
        self.dispatched.append(args)
        return "dispatched"

    def apply_patch(self, *args) -> str:
        self.patched.append(args)
        return "patched"


class FakePage:
    def __init__(self) -> None:
        self.session = FakeSession()
        self.shown: list = []
        self.updates = 0

    def run_task(self, handler):
        # Flet refuses anything but a coroutine function; so does this.
        if not inspect.iscoroutinefunction(handler):
            raise TypeError("handler must be a coroutine function")
        asyncio.run(handler())

    def show_dialog(self, dialog) -> None:
        dialog.open = True
        self.shown.append(dialog)

    def update(self) -> None:
        self.updates += 1


class GonePage(FakePage):
    @property
    def session(self):  # type: ignore[override]
        raise RuntimeError("session destroyed")

    @session.setter
    def session(self, value) -> None:
        pass


@pytest.fixture
def launched(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    urls: list[str] = []

    async def fake_launch(url: str) -> None:
        urls.append(url)

    monkeypatch.setattr(sl, "_launch", fake_launch)
    return urls


def make(tmp_path: Path, idle: int = 60) -> Lifecycle:
    return Lifecycle(notice_file=tmp_path / "notice.json", idle_seconds=idle)


class TestAttach:
    @pytest.fixture(autouse=True)
    def _fresh(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sl, "_lifecycle", None)
        monkeypatch.setattr(Lifecycle, "start_thread", lambda self: None)
        monkeypatch.setattr(sl, "resolve_username", lambda: "alice")

    def test_both_methods_are_wrapped_and_still_call_the_originals(self) -> None:
        page = FakePage()
        session = page.session
        sl.attach(page)  # type: ignore[arg-type]
        lifecycle = sl._lifecycle
        assert lifecycle is not None
        lifecycle.last_activity = 0.0

        result = asyncio.run(session.dispatch_event(1, "click", None))
        assert result == "dispatched"
        assert session.dispatched == [(1, "click", None)]
        assert lifecycle.last_activity > 0.0

        lifecycle.last_activity = 0.0
        assert session.apply_patch(2, {"value": "x"}) == "patched"
        assert session.patched == [(2, {"value": "x"})]
        assert lifecycle.last_activity > 0.0

    def test_session_without_the_methods_turns_idle_off(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        class Bare:
            connection = object()

        page = FakePage()
        page.session = Bare()  # type: ignore[assignment]
        sl.attach(page)  # type: ignore[arg-type]
        assert sl._lifecycle is not None
        assert sl._lifecycle.idle_seconds == 0
        assert "idle sleep off" in capsys.readouterr().out

    def test_a_session_that_is_already_gone_is_not_added(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        sl.attach(GonePage())  # type: ignore[arg-type]
        assert sl._lifecycle is not None
        assert sl._lifecycle.pages == []
        assert "page gone before attach" in capsys.readouterr().out

    def test_process_start_line_names_pid_user_and_idle(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        sl.attach(FakePage())  # type: ignore[arg-type]
        out = capsys.readouterr().out
        assert f"pid {os.getpid()}" in out
        assert "user alice" in out
        assert "lifecycle: page connected" in out

    def test_a_page_attached_after_offline_goes_to_the_offline_page(
        self, launched: list[str]
    ) -> None:
        sl.attach(FakePage())  # type: ignore[arg-type]
        assert sl._lifecycle is not None
        sl._lifecycle.offline_sent = True
        sl.attach(FakePage())  # type: ignore[arg-type]
        assert launched == [sl.OFFLINE_URL]


class TestTickHousekeeping:
    def test_a_gone_page_is_pruned_with_its_entries(self, tmp_path: Path) -> None:
        lifecycle = make(tmp_path)
        alive = FakePage()
        gone = GonePage()
        lifecycle.add_page(alive)  # type: ignore[arg-type]
        lifecycle.pages.append(gone)  # type: ignore[arg-type]
        lifecycle.countdown_dialogs[id(gone)] = ft.AlertDialog()
        lifecycle.was_connected[id(gone)] = True

        lifecycle.tick()

        assert lifecycle.pages == [alive]
        assert id(gone) not in lifecycle.countdown_dialogs
        assert id(gone) not in lifecycle.was_connected

    def test_a_page_that_reconnects_counts_as_activity(self, tmp_path: Path) -> None:
        lifecycle = make(tmp_path)
        page = FakePage()
        lifecycle.add_page(page)  # type: ignore[arg-type]
        page.session.connection = None
        lifecycle.tick(now_mono=lifecycle.last_activity + 1)
        lifecycle.last_activity = 5.0
        page.session.connection = object()
        lifecycle.tick(now_mono=6.0)
        assert lifecycle.last_activity > 5.0


class TestIdleFlow:
    def test_countdown_then_cancel_by_activity(
        self, tmp_path: Path, launched: list[str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        lifecycle = make(tmp_path)
        page = FakePage()
        lifecycle.add_page(page)  # type: ignore[arg-type]
        lifecycle.last_activity = 1000.0

        lifecycle.tick(now_mono=1061.0)
        assert lifecycle.countdown_started == 1061.0
        dialog = page.shown[0]
        assert dialog.open is True
        assert dialog.title.value == "Still there?"

        lifecycle.last_activity = 1070.0
        lifecycle.tick(now_mono=1075.0)
        assert lifecycle.countdown_started is None
        assert dialog.open is False
        assert "countdown cancelled" in capsys.readouterr().out
        assert launched == []

    def test_im_here_button_closes_the_dialog(self, tmp_path: Path) -> None:
        lifecycle = make(tmp_path)
        page = FakePage()
        lifecycle.add_page(page)  # type: ignore[arg-type]
        lifecycle.last_activity = 1000.0
        lifecycle.tick(now_mono=1061.0)
        dialog = page.shown[0]

        dialog.actions[0].on_click(None)

        assert dialog.open is False

    def test_a_countdown_left_alone_sleeps_in_the_right_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, launched: list[str]
    ) -> None:
        lifecycle = make(tmp_path)
        page = FakePage()
        lifecycle.add_page(page)  # type: ignore[arg-type]
        lifecycle.last_activity = 1000.0
        events: list[str] = []

        async def fake_launch(url: str) -> None:
            events.append(f"navigate {url}")

        monkeypatch.setattr(sl, "_launch", fake_launch)
        monkeypatch.setattr(sl.time, "sleep", lambda s: events.append(f"sleep {s}"))
        monkeypatch.setattr(sl.os, "_exit", lambda code: events.append(f"exit {code}"))

        lifecycle.tick(now_mono=1061.0)
        lifecycle.tick(now_mono=1061.0 + COUNTDOWN_SECONDS)

        assert events == [
            f"navigate {sl.ASLEEP_URL}",
            f"sleep {sl.SLEEP_FLUSH_SECONDS}",
            "exit 0",
        ]

    def test_no_page_connected_sleeps_without_a_countdown(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, launched: list[str]
    ) -> None:
        lifecycle = make(tmp_path)
        page = FakePage()
        lifecycle.add_page(page)  # type: ignore[arg-type]
        page.session.connection = None
        lifecycle.last_activity = 1000.0
        exits: list[int] = []
        monkeypatch.setattr(sl.time, "sleep", lambda s: None)
        monkeypatch.setattr(sl.os, "_exit", exits.append)

        lifecycle.tick(now_mono=1061.0)

        assert exits == [0]
        assert launched == []
        assert page.shown == []


class TestBannerFlow:
    NOW = datetime(2026, 11, 9, 19, 0, 0, tzinfo=UTC)

    def setup_one(self, tmp_path: Path) -> tuple[Lifecycle, FakePage]:
        lifecycle = make(tmp_path, idle=0)
        page = FakePage()
        lifecycle.add_page(page)  # type: ignore[arg-type]
        return lifecycle, page

    def test_no_file_means_no_banner_and_one_log_line(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        lifecycle, page = self.setup_one(tmp_path)
        lifecycle.tick(now_mono=1.0, now_utc=self.NOW)
        lifecycle.tick(now_mono=2.0, now_utc=self.NOW)
        assert page.shown == []
        assert capsys.readouterr().out.count("notice file: absent") == 1

    def test_banner_steps_refresh_and_dismiss(
        self, tmp_path: Path, launched: list[str]
    ) -> None:
        lifecycle, page = self.setup_one(tmp_path)
        stop = self.NOW + timedelta(minutes=12)
        write_notice(lifecycle.notice_file, stop)

        lifecycle.tick(now_mono=1.0, now_utc=self.NOW)
        assert len(page.shown) == 1
        first = page.shown[0]
        assert "in 12 minutes" in first.content.value
        assert first.bgcolor == ft.Colors.AMBER_700
        assert first.content.color == ft.Colors.BLACK
        assert first.actions[0].style.color == ft.Colors.BLACK

        lifecycle.tick(now_mono=2.0, now_utc=self.NOW + timedelta(minutes=1))
        assert len(page.shown) == 1
        assert "in 11 minutes" in first.content.value

        lifecycle.tick(now_mono=3.0, now_utc=self.NOW + timedelta(minutes=2))
        assert len(page.shown) == 2
        assert first.open is False
        second = page.shown[1]
        assert "in 10 minutes" in second.content.value

        second.actions[0].on_click(None)
        assert second.open is False
        lifecycle.tick(now_mono=4.0, now_utc=self.NOW + timedelta(minutes=3))
        assert len(page.shown) == 2

        lifecycle.tick(now_mono=5.0, now_utc=self.NOW + timedelta(minutes=7))
        assert len(page.shown) == 3
        assert page.shown[2].bgcolor == ft.Colors.RED_700
        assert page.shown[2].content.color == ft.Colors.WHITE
        assert page.shown[2].actions[0].style.color == ft.Colors.WHITE

    def test_stop_time_sends_the_page_offline_and_idle_stays_quiet(
        self, tmp_path: Path, launched: list[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        lifecycle, page = self.setup_one(tmp_path)
        lifecycle.idle_seconds = 60
        lifecycle.last_activity = 0.0
        exits: list[int] = []
        monkeypatch.setattr(sl.os, "_exit", exits.append)
        write_notice(lifecycle.notice_file, self.NOW)

        lifecycle.tick(now_mono=10_000.0, now_utc=self.NOW)
        assert launched == [sl.OFFLINE_URL]
        assert lifecycle.offline_sent is True

        lifecycle.tick(now_mono=20_000.0, now_utc=self.NOW + timedelta(seconds=15))
        assert launched == [sl.OFFLINE_URL]
        assert exits == []
        assert page.shown == []

    def test_a_later_notice_shows_its_steps_again_after_a_dismissed_one(
        self, tmp_path: Path
    ) -> None:
        lifecycle, page = self.setup_one(tmp_path)
        write_notice(lifecycle.notice_file, self.NOW + timedelta(minutes=10))
        lifecycle.tick(now_mono=1.0, now_utc=self.NOW)
        page.shown[0].actions[0].on_click(None)
        lifecycle.notice_file.unlink()
        lifecycle.tick(now_mono=2.0, now_utc=self.NOW + timedelta(minutes=1))

        later = self.NOW + timedelta(hours=24)
        write_notice(lifecycle.notice_file, later + timedelta(minutes=10))
        lifecycle.tick(now_mono=3.0, now_utc=later)

        assert len(page.shown) == 2
        assert page.shown[1].open is True

    @pytest.mark.parametrize(
        ("minutes", "colour", "ink"),
        [
            (6, ft.Colors.AMBER_700, ft.Colors.BLACK),
            (5, ft.Colors.RED_700, ft.Colors.WHITE),
        ],
    )
    def test_the_banner_turns_red_exactly_at_five_minutes(
        self, tmp_path: Path, minutes: int, colour: str, ink: str
    ) -> None:
        lifecycle, page = self.setup_one(tmp_path)
        write_notice(lifecycle.notice_file, self.NOW + timedelta(minutes=minutes))

        lifecycle.tick(now_mono=1.0, now_utc=self.NOW)

        assert page.shown[0].bgcolor == colour
        assert page.shown[0].content.color == ink

    def test_a_page_that_joins_during_a_step_gets_the_banner(
        self, tmp_path: Path
    ) -> None:
        lifecycle, first_page = self.setup_one(tmp_path)
        write_notice(lifecycle.notice_file, self.NOW + timedelta(minutes=12))
        lifecycle.tick(now_mono=1.0, now_utc=self.NOW)
        late = FakePage()
        lifecycle.add_page(late)  # type: ignore[arg-type]

        lifecycle.tick(now_mono=2.0, now_utc=self.NOW + timedelta(minutes=1))

        assert len(late.shown) == 1
        assert len(first_page.shown) == 1
