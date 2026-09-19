import time, threading
T0 = time.time()
import flet as ft
import gui2.main as gm
import gui2.toolkit as tk
from tools.fast_api_utils import start_dpd_server

def stamp(m): print(f"[startup] {time.time()-T0:7.2f}s  {m}", flush=True)

# --- break down App.__init__ ---
orig_tk = tk.ToolKit.__init__
def timed_tk(self, page):
    s = time.time(); orig_tk(self, page); stamp(f"  toolkit built      ({time.time()-s:5.2f}s)")
tk.ToolKit.__init__ = timed_tk
gm.ToolKit.__init__ = timed_tk

orig_build = gm.App.build_ui
def timed_build(self):
    s = time.time(); orig_build(self); stamp(f"  build_ui done      ({time.time()-s:5.2f}s)")
gm.App.build_ui = timed_build

# --- warm-up waits for the db instead of racing it ---
db_done = threading.Event()

orig_db = gm.App._initialize_db_in_background
def timed_db(self):
    s = time.time()
    try:
        orig_db(self)
    finally:
        stamp(f"DATABASE LOADED      ({time.time()-s:5.2f}s)  <-- app usable")
        db_done.set()
gm.App._initialize_db_in_background = timed_db

orig_warm = gm.App._warmup_in_background
def timed_warm(self):
    db_done.wait()
    s = time.time(); orig_warm(self); stamp(f"tabs warmed after db ({time.time()-s:5.2f}s)")
gm.App._warmup_in_background = timed_warm

def main(page: ft.Page) -> None:
    stamp("flet client connected")
    page.title = ""
    s = time.time()
    gm.App(page)
    stamp(f"FIRST PAINT          (App.__init__ {time.time()-s:5.2f}s)")
    start_dpd_server()

ft.run(main)
