"""timed_gui.py + a stamp when the warm-up thread actually starts, so a
missing ALL TABS WARMED can be attributed to the thread never starting vs
its first build blocking. Run under xvfb-run for headless measurement."""

import os
import time

T0 = time.time()
NO_WARMUP = os.environ.get("NO_WARMUP") == "1"

import flet as ft  # noqa: E402

import gui2.main as gm  # noqa: E402
from tools.fast_api_utils import start_dpd_server  # noqa: E402


def stamp(m: str) -> None:
    print(f"[startup] {time.time() - T0:7.2f}s  {m}", flush=True)


orig_db = gm.App._initialize_db_in_background


def timed_db(self):  # type: ignore[no-untyped-def]
    s = time.time()
    orig_db(self)
    stamp(f"database loaded      (took {time.time() - s:5.2f}s)")


gm.App._initialize_db_in_background = timed_db

orig_ensure = gm.App._ensure_tab_built


def timed_ensure(self, index):  # type: ignore[no-untyped-def]
    if index in self._mounted_tabs:
        return
    s = time.time()
    orig_ensure(self, index)
    stamp(f"tab {index:2d} built        (took {time.time() - s:5.2f}s)")


gm.App._ensure_tab_built = timed_ensure

orig_warm = gm.App._warmup_in_background


def timed_warm(self):  # type: ignore[no-untyped-def]
    if NO_WARMUP:
        stamp("warm-up SKIPPED")
        return
    stamp("warm-up thread started")
    s = time.time()
    orig_warm(self)
    stamp(f"ALL TABS WARMED      (took {time.time() - s:5.2f}s)")


gm.App._warmup_in_background = timed_warm


def main(page: ft.Page) -> None:
    stamp("flet client connected")
    page.title = ""
    s = time.time()
    gm.App(page)
    stamp(f"FIRST PAINT          (App.__init__ {time.time() - s:5.2f}s)")
    start_dpd_server()


ft.run(main)
