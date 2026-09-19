"""Phase 5 diagnostic — timed_gui with per-component initialize_db stamps."""

import time

T0 = time.time()
import flet as ft  # noqa: E402
import gui2.main as gm  # noqa: E402
from tools.fast_api_utils import start_dpd_server  # noqa: E402


def stamp(m: str) -> None:
    print(f"[startup] {time.time() - T0:7.2f}s  {m}", flush=True)


from gui2.database_manager import DatabaseManager  # noqa: E402

for name in [
    "get_all_lemma_1_and_lemma_clean",
    "get_all_pos",
    "get_all_roots",
    "get_all_root_families",
    "get_all_compound_families",
    "get_all_word_families",
    "get_all_patterns",
    "get_all_decon_no_headwords",
    "load_corpus",
]:
    orig = getattr(DatabaseManager, name)

    def make(orig_fn=orig, n=name):
        def wrapper(self):
            s = time.time()
            orig_fn(self)
            stamp(f"  {n:<38} {time.time() - s:5.2f}s")

        return wrapper

    setattr(DatabaseManager, name, make())

orig_db = gm.App._initialize_db_in_background


def timed_db(self):
    s = time.time()
    orig_db(self)
    stamp(f"database loaded      (took {time.time() - s:5.2f}s)")


gm.App._initialize_db_in_background = timed_db


def main(page: ft.Page) -> None:
    stamp("flet client connected")
    page.title = ""
    s = time.time()
    gm.App(page)
    stamp(f"FIRST PAINT          (App.__init__ {time.time() - s:5.2f}s)")
    start_dpd_server()


ft.run(main)
