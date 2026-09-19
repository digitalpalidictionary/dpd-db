"""Phase 2 task 4 probe: prove the warm-up does not build the sutta text index.

Wraps App._warmup_in_background monkeypatch-style; immediately after the
warm-up completes (pass1auto / pass2pre never opened), inspects every source
in gui2.books.sutta_central_books for segment_dict / word_dict in vars().
Killed by the runner as soon as the probe line prints.
"""

import os
import time

T0 = time.time()

import flet as ft  # noqa: E402

import gui2.books as gb  # noqa: E402
import gui2.main as gm  # noqa: E402
from tools.fast_api_utils import start_dpd_server  # noqa: E402


def stamp(m: str) -> None:
    print(f"[startup] {time.time() - T0:7.2f}s  {m}", flush=True)


orig_warm = gm.App._warmup_in_background


def probe_warm(self):  # type: ignore[no-untyped-def]
    s = time.time()
    orig_warm(self)
    stamp(f"ALL TABS WARMED      (took {time.time() - s:5.2f}s)")
    report = []
    for name, source in gb.sutta_central_books.items():
        present = [k for k in ("segment_dict", "word_dict") if k in vars(source)]
        if present:
            report.append(f"{name}: {present}")
    if report:
        stamp(f"warm-up text index probe: BUILT -> {report}")
    else:
        stamp(
            "warm-up text index probe: CLEAN - no source has "
            f"segment_dict or word_dict (checked {len(gb.sutta_central_books)} sources)"
        )


gm.App._warmup_in_background = probe_warm


def main(page: ft.Page) -> None:
    stamp("flet client connected")
    page.title = ""
    gm.App(page)
    start_dpd_server()


ft.run(main)
