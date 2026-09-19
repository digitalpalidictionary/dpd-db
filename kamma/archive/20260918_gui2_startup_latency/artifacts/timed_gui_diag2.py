"""Diagnostic: trace the db-worker -> run_thread -> executor -> warm-up chain
stamp by stamp, to locate where the chained warm-up dies. Headless (xvfb)."""

import os
import time

T0 = time.time()

import flet as ft  # noqa: E402

import gui2.main as gm  # noqa: E402
from tools.fast_api_utils import start_dpd_server  # noqa: E402


def stamp(m: str) -> None:
    print(f"[startup] {time.time() - T0:7.2f}s  {m}", flush=True)


orig_db = gm.App._initialize_db_in_background


def diag_db(self):  # type: ignore[no-untyped-def]
    stamp("db worker entered")
    orig_db(self)
    stamp("db worker returned (finally should have chained warm-up)")
    # probe the executor directly with a trivial callback
    self.page.run_thread(lambda: stamp("executor probe OK"))


gm.App._initialize_db_in_background = diag_db

orig_warm = gm.App._warmup_in_background


def diag_warm(self):  # type: ignore[no-untyped-def]
    stamp("warm-up thread entered")
    orig_warm(self)
    stamp("ALL TABS WARMED")


gm.App._warmup_in_background = diag_warm


def main(page: ft.Page) -> None:
    stamp("flet client connected")
    page.title = ""
    s = time.time()
    gm.App(page)
    stamp(f"FIRST PAINT          (App.__init__ {time.time() - s:5.2f}s)")
    start_dpd_server()


ft.run(main)
