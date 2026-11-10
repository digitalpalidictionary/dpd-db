"""Idle sleep and nightly-update warnings for the contributor web server.

Runs only for web sessions on the contributor server (see `attach`). Two jobs:

- Idle sleep: after IDLE_MINUTES with no action from the browser, show a
  countdown, then send the browser to a static page and end the process. With
  no page connected there is nobody to show a countdown to, so it sleeps at
  once. DPD_GUI2_IDLE_MINUTES overrides the minutes; 0 turns idle sleep off.
  CPython rarely gives freed memory back to the OS, so ending the process is
  the dependable way to free the ~1 GB a loaded editor holds. systemd brings
  back an empty process.
- Nightly warning: the maintenance window writes its stop time to the notice
  file (`tools/contrib_notice.py`). This module shows a banner at set steps and
  sends the browser to the offline page at the stop time.

The decisions are pure functions so they can be tested without Flet. Every
change to the page goes through `page.run_task`, so it runs on the page's own
event loop and not on the watcher thread.
"""

import enum
import math
import os
import threading
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import flet as ft

from gui2.user import resolve_username
from tools.contrib_notice import NOTICE_FILE, read_notice

IDLE_MINUTES = 30
COUNTDOWN_SECONDS = 120
TICK_SECONDS = 15
BANNER_STEPS = (30, 15, 10, 5, 1)
RED_FROM_MINUTES = 5
SLEEP_FLUSH_SECONDS = 3
ASLEEP_URL = "_dpd/asleep.html"
OFFLINE_URL = "_dpd/offline.html"
IDLE_ENV = "DPD_GUI2_IDLE_MINUTES"
PROCESS_START = time.monotonic()


def log(message: str) -> None:
    """One line for `journalctl`. Plain text and flushed: systemd's pipe is block-buffered."""
    print(f"lifecycle: {message}", flush=True)


def idle_seconds_from_env(environ: Mapping[str, str]) -> tuple[int, str]:
    """Idle seconds and the reason for them. 0 seconds means idle sleep is off."""
    raw = environ.get(IDLE_ENV)
    if raw is None:
        return IDLE_MINUTES * 60, "default"
    try:
        minutes = int(raw)
    except ValueError:
        minutes = -1
    if minutes == 0:
        return 0, "off by env"
    if minutes > 0:
        return minutes * 60, "env"
    return IDLE_MINUTES * 60, f"bad env value {raw}, using {IDLE_MINUTES}"


class IdleAction(enum.Enum):
    NOTHING = "nothing"
    SHOW_COUNTDOWN = "show countdown"
    CANCEL_COUNTDOWN = "cancel countdown"
    SLEEP = "sleep"


def decide_idle(
    now: float,
    last_activity: float,
    countdown_started: float | None,
    idle_seconds: int,
    any_connected: bool,
    offline_sent: bool,
) -> IdleAction:
    if offline_sent or idle_seconds == 0:
        return IdleAction.NOTHING
    if countdown_started is not None:
        if last_activity > countdown_started:
            return IdleAction.CANCEL_COUNTDOWN
        if now - countdown_started >= COUNTDOWN_SECONDS:
            return IdleAction.SLEEP
        return IdleAction.NOTHING
    if now - last_activity >= idle_seconds:
        if not any_connected:
            return IdleAction.SLEEP
        return IdleAction.SHOW_COUNTDOWN
    return IdleAction.NOTHING


def minutes_left(stop_at: datetime, now_utc: datetime) -> int:
    return math.ceil((stop_at - now_utc).total_seconds() / 60)


def banner_step(minutes: int) -> int | None:
    """The smallest banner step that is at least `minutes`, or None when no banner is due."""
    if minutes > BANNER_STEPS[0] or minutes <= 0:
        return None
    return min(step for step in BANNER_STEPS if step >= minutes)


def banner_text(minutes: int) -> str:
    unit = "minute" if minutes == 1 else "minutes"
    return (
        f"The editor restarts for its daily update in {minutes} {unit}. "
        "Save your work now. Anything unsaved will be lost."
    )


def countdown_title() -> str:
    return "Still there?"


def countdown_body(idle_seconds: int) -> str:
    idle_minutes = idle_seconds // 60
    unit = "minute" if idle_minutes == 1 else "minutes"
    return (
        f"You have not used the editor for {idle_minutes} {unit}. "
        "To free memory for other contributors, it will go to sleep in "
        f"{COUNTDOWN_SECONDS // 60} minutes. Anything you have not saved will be lost."
    )


async def _launch(url: str) -> None:
    # "_self" replaces this tab; the URL is relative, so it resolves under the
    # per-user mount prefix.
    await ft.UrlLauncher().launch_url(url, web_only_window_name="_self")


class Lifecycle:
    def __init__(
        self,
        notice_file: Path = NOTICE_FILE,
        idle_seconds: int = IDLE_MINUTES * 60,
    ) -> None:
        self.last_activity = time.monotonic()
        self.pages: list[ft.Page] = []
        self.countdown_started: float | None = None
        self.countdown_dialogs: dict[int, ft.AlertDialog] = {}
        self.banners: dict[int, tuple[ft.Banner, ft.Text]] = {}
        self.last_step_shown: int | None = None
        self.dismissed_step: int | None = None
        self.offline_sent = False
        self.notice_reason: str | None = None
        self.notice_stop: datetime | None = None
        self.idle_seconds = idle_seconds
        self.notice_file = notice_file
        self.was_connected: dict[int, bool] = {}
        self.lock = threading.Lock()

    # ----- activity -----

    def touch(self) -> None:
        self.last_activity = time.monotonic()

    def add_page(self, page: ft.Page) -> None:
        with self.lock:
            self.pages.append(page)
            self.was_connected[id(page)] = True
        self.touch()

    @staticmethod
    def is_connected(page: ft.Page) -> bool:
        try:
            return page.session.connection is not None
        except RuntimeError:
            return False

    def _connected_pages(self) -> list[ft.Page]:
        with self.lock:
            pages = list(self.pages)
        return [page for page in pages if self.is_connected(page)]

    def _prune(self) -> None:
        with self.lock:
            kept: list[ft.Page] = []
            for page in self.pages:
                try:
                    page.session
                except RuntimeError:
                    key = id(page)
                    self.countdown_dialogs.pop(key, None)
                    self.banners.pop(key, None)
                    self.was_connected.pop(key, None)
                else:
                    kept.append(page)
            self.pages = kept

    def _note_reconnects(self) -> None:
        # A Flet reconnect can reuse the session and so never run main() again.
        for page in self._connected_pages():
            key = id(page)
            if not self.was_connected.get(key, False):
                log("page reconnected")
                self.touch()
            self.was_connected[key] = True
        with self.lock:
            for page in self.pages:
                if not self.is_connected(page):
                    self.was_connected[id(page)] = False

    # ----- page actions (each runs on the page's own loop) -----

    def _run(self, page: ft.Page, handler) -> None:
        try:
            page.run_task(handler)
        except Exception as exc:
            log(f"could not reach a page: {exc}")

    def _navigate(self, page: ft.Page, url: str) -> None:
        # run_task needs a coroutine function; a lambda returning a coroutine
        # is refused.
        async def go() -> None:
            await _launch(url)

        self._run(page, go)

    def _navigate_all(self, url: str) -> int:
        pages = self._connected_pages()
        for page in pages:
            self._navigate(page, url)
        return len(pages)

    def _show_countdown(self, page: ft.Page) -> None:
        async def show() -> None:
            def close(_: object) -> None:
                dialog.open = False
                page.update()

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(countdown_title()),
                content=ft.Text(countdown_body(self.idle_seconds)),
                actions=[ft.TextButton("I'm here", on_click=close)],
            )
            self.countdown_dialogs[id(page)] = dialog
            page.show_dialog(dialog)

        self._run(page, show)

    def _close_countdown(self, page: ft.Page) -> None:
        dialog = self.countdown_dialogs.pop(id(page), None)
        if dialog is None:
            return

        async def close() -> None:
            dialog.open = False
            page.update()

        self._run(page, close)

    def _show_banner(self, page: ft.Page, minutes: int, step: int) -> None:
        async def show() -> None:
            old = self.banners.pop(id(page), None)
            if old is not None:
                old[0].open = False
                page.update()

            def got_it(_: object) -> None:
                self.dismissed_step = step
                banner.open = False
                page.update()

            urgent = minutes <= RED_FROM_MINUTES
            # White is unreadable on amber, black is unreadable on red.
            ink = ft.Colors.WHITE if urgent else ft.Colors.BLACK
            text = ft.Text(banner_text(minutes), color=ink)
            banner = ft.Banner(
                content=text,
                bgcolor=ft.Colors.RED_700 if urgent else ft.Colors.AMBER_700,
                actions=[
                    ft.TextButton(
                        "Got it", on_click=got_it, style=ft.ButtonStyle(color=ink)
                    )
                ],
            )
            self.banners[id(page)] = (banner, text)
            page.show_dialog(banner)

        self._run(page, show)

    def _refresh_banner(self, page: ft.Page, minutes: int) -> None:
        entry = self.banners.get(id(page))
        if entry is None:
            return
        banner, text = entry

        async def refresh() -> None:
            text.value = banner_text(minutes)
            page.update()

        self._run(page, refresh)

    def _close_banner(self, page: ft.Page) -> None:
        entry = self.banners.pop(id(page), None)
        if entry is None:
            return
        banner = entry[0]

        async def close() -> None:
            banner.open = False
            page.update()

        self._run(page, close)

    # ----- decisions -----

    def _drive_notice(self, now_utc: datetime) -> None:
        if self.offline_sent:
            return
        stop_at, reason = read_notice(self.notice_file, now_utc)
        label = reason if stop_at is None else f"ok {stop_at.isoformat()}"
        if label != self.notice_reason:
            self.notice_reason = label
            if stop_at is None:
                log(f"notice file: {reason}")
            else:
                log(f"notice seen: stop at {stop_at.isoformat()}")
        if stop_at is None:
            # A later notice in this same process starts its steps afresh.
            self.last_step_shown = None
            self.dismissed_step = None
            return
        minutes = minutes_left(stop_at, now_utc)
        pages = self._connected_pages()
        if minutes <= 0:
            sent = self._navigate_all(OFFLINE_URL)
            self.offline_sent = True
            log(f"sent {sent} page(s) to the offline page")
            return
        step = banner_step(minutes)
        if step is None:
            for page in pages:
                self._close_banner(page)
            return
        if step != self.last_step_shown:
            self.last_step_shown = step
            if step != self.dismissed_step:
                log(f"banner step {step}: {minutes} minute(s) left")
                for page in pages:
                    self._show_banner(page, minutes, step)
            return
        if step == self.dismissed_step:
            return
        for page in pages:
            if id(page) in self.banners:
                self._refresh_banner(page, minutes)
            else:
                self._show_banner(page, minutes, step)

    def _drive_idle(self, now_mono: float) -> None:
        pages = self._connected_pages()
        action = decide_idle(
            now_mono,
            self.last_activity,
            self.countdown_started,
            self.idle_seconds,
            bool(pages),
            self.offline_sent,
        )
        if action is IdleAction.SHOW_COUNTDOWN:
            self.countdown_started = now_mono
            log(
                f"countdown shown after {(now_mono - self.last_activity) / 60:.1f} min idle"
            )
            for page in pages:
                self._show_countdown(page)
        elif action is IdleAction.CANCEL_COUNTDOWN:
            self.countdown_started = None
            log("countdown cancelled")
            for page in list(self.countdown_dialogs_pages()):
                self._close_countdown(page)
        elif action is IdleAction.SLEEP:
            self._sleep(now_mono, bool(pages))

    def countdown_dialogs_pages(self) -> list[ft.Page]:
        with self.lock:
            return [p for p in self.pages if id(p) in self.countdown_dialogs]

    def _sleep(self, now_mono: float, connected: bool) -> None:
        idle_minutes = (now_mono - self.last_activity) / 60
        sent = self._navigate_all(ASLEEP_URL)
        log(
            f"asleep: {idle_minutes:.1f} min idle, {sent} page(s) sent away, "
            f"connected={connected}"
        )
        time.sleep(SLEEP_FLUSH_SECONDS)
        os._exit(0)

    def tick(
        self, now_mono: float | None = None, now_utc: datetime | None = None
    ) -> None:
        now_mono = time.monotonic() if now_mono is None else now_mono
        now_utc = now_utc or datetime.now(UTC)
        self._prune()
        self._note_reconnects()
        self._drive_notice(now_utc)
        self._drive_idle(now_mono)

    # ----- thread -----

    def _loop(self) -> None:
        while True:
            time.sleep(TICK_SECONDS)
            try:
                self.tick()
            except Exception as exc:
                log(f"tick failed: {exc}")

    def start_thread(self) -> None:
        threading.Thread(target=self._loop, name="lifecycle", daemon=True).start()


_lifecycle: Lifecycle | None = None
_attach_lock = threading.Lock()


def attach(page: ft.Page) -> None:
    """Watch this page. Call once per page from `main()`, web sessions on the server only."""
    global _lifecycle
    with _attach_lock:
        if _lifecycle is None:
            idle_seconds, reason = idle_seconds_from_env(os.environ)
            _lifecycle = Lifecycle(NOTICE_FILE, idle_seconds)
            log(
                f"process start: pid {os.getpid()}, user {resolve_username()}, "
                f"idle {idle_seconds // 60} min ({reason})"
            )
            _lifecycle.start_thread()
        lifecycle = _lifecycle
    try:
        session = page.session
    except RuntimeError:
        log("page gone before attach")
        return
    lifecycle.add_page(page)

    # Capture the originals first: calling session.dispatch_event inside the
    # wrapper would call the wrapper again.
    try:
        original_dispatch = session.dispatch_event
        original_patch = session.apply_patch
    except AttributeError as exc:
        log(f"idle sleep off: Flet session has no {exc.name}")
        lifecycle.idle_seconds = 0
    else:

        async def dispatch(*args, **kwargs):
            lifecycle.touch()
            return await original_dispatch(*args, **kwargs)

        def patch(*args, **kwargs):
            lifecycle.touch()
            return original_patch(*args, **kwargs)

        session.dispatch_event = dispatch
        session.apply_patch = patch
    log("page connected")
    if lifecycle.offline_sent:
        lifecycle._navigate(page, OFFLINE_URL)
