"""Failed-load path test (Phase 3 task 3).

Simulates the database load failing by patching DatabaseManager.initialize_db
to raise — the real dpd.db is never touched. Everything else is the stock app.

Run:  uv run python kamma/threads/20260918_gui2_startup_latency/artifacts/failed_load_gui.py

Expected:
1. red "Database load failed: ..." snackbar shortly after launch
2. warm-up still runs (tabs fill in, "All tabs and tools ready." snackbar)
3. clicking a tab triggers the retry load → failure snackbar again,
   no hang, no visible pile-up of duplicate warm-ups
"""

import flet as ft

from gui2.database_manager import DatabaseManager
import gui2.main as gm


def failing_initialize_db(self) -> None:
    raise FileNotFoundError("simulated database load failure (failed-load test)")


DatabaseManager.initialize_db = failing_initialize_db  # type: ignore[method-assign]


def main(page: ft.Page) -> None:
    page.title = "failed-load TEST"
    gm.App(page)


ft.run(main)
