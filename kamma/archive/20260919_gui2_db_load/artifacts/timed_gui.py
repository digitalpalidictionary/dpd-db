"""Instrumented launcher: stamps first paint, tab builds, warm-up, db load.

Timing-only monkeypatching — no behaviour change. Run from the project root:
PYTHONPATH=. uv run python kamma/threads/20260919_gui2_db_load/artifacts/timed_gui.py
"""

import os
import time

T0 = time.time()
NO_WARMUP = os.environ.get("NO_WARMUP") == "1"

import flet as ft  # noqa: E402
import gui2.main as gm  # noqa: E402
from tools.fast_api_utils import start_dpd_server  # noqa: E402


def stamp(m):
    print(f"[startup] {time.time() - T0:7.2f}s  {m}", flush=True)


orig_db = gm.App._initialize_db_in_background


def timed_db(self):
    s = time.time()
    orig_db(self)
    stamp(f"database loaded      (took {time.time() - s:5.2f}s)")


gm.App._initialize_db_in_background = timed_db

orig_ensure = gm.App._ensure_tab_built


def timed_ensure(self, index):
    if index in self._mounted_tabs:
        return
    s = time.time()
    orig_ensure(self, index)
    stamp(f"tab {index:2d} built        (took {time.time() - s:5.2f}s)")


gm.App._ensure_tab_built = timed_ensure

orig_warm = gm.App._warmup_in_background


def timed_warm(self):
    if NO_WARMUP:
        stamp("warm-up SKIPPED")
        return
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
