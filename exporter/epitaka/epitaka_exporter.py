#!/usr/bin/env python3

"""Install the mobile DPD database into the local ePitaka app."""

import sqlite3
import subprocess
from pathlib import Path

import psutil

from tools.configger import config_read, config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr

APP_DPD_FILENAME = "dpd-mobile.db"


def app_processes() -> list[psutil.Process]:
    """Running ePitaka processes."""

    return [p for p in psutil.process_iter(["name"]) if p.info["name"] == "epitaka"]


def close_app(procs: list[psutil.Process], timeout: float = 30) -> bool:
    """Ask ePitaka to quit. True when every process has exited."""

    pr.green_tmr("close epitaka")
    for p in procs:
        try:
            p.terminate()
        except psutil.NoSuchProcess:
            pass
    _, alive = psutil.wait_procs(procs, timeout=timeout)
    if alive:
        pr.no("still on")
        return False
    pr.yes("ok")
    return True


def open_app() -> None:
    """Start ePitaka through its desktop entry, detached from this build."""

    pr.green_tmr("open epitaka")
    try:
        subprocess.Popen(
            ["gtk-launch", "epitaka"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as e:
        # A failed reopen must not abort the rest of the export.
        pr.no("failed")
        pr.red(str(e))
        return
    pr.yes("ok")


def install(src_path: Path, dest: Path) -> bool:
    """Copy the mobile database into the app's file through SQLite's backup,
    which handles the destination's WAL file correctly. The backup waits
    for as long as another process holds a write lock, so close the app
    first."""

    pr.green_tmr("install")
    if not src_path.exists():
        pr.no("missing")
        pr.red(f"{src_path} not found, run the mobile exporter first")
        return False

    src = sqlite3.connect(src_path)
    dst = sqlite3.connect(dest)
    try:
        src.backup(dst)
    finally:
        src.close()
        dst.close()
    pr.yes("ok")
    return True


def main() -> None:
    pr.tic()
    pr.yellow_title("install dpd mobile db in epitaka")

    if not config_test("exporter", "make_epitaka", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    db_path = Path(config_read("epitaka", "db_path") or "")
    if db_path.name != APP_DPD_FILENAME or not db_path.parent.is_dir():
        pr.red(f"[epitaka] db_path must be an existing folder's {APP_DPD_FILENAME}")
        pr.red(f"it is '{db_path}'")
        pr.toc()
        return

    src_path = ProjectPaths().dpd_mobile_db_path
    if not src_path.exists():
        pr.red(f"{src_path} not found, run the mobile exporter first")
        pr.toc()
        return

    procs = app_processes()
    if procs and not close_app(procs):
        pr.red("ePitaka did not close, not installed; close it and run again")
        pr.toc()
        return
    try:
        install(src_path, db_path)
    finally:
        # The app was running before, so it comes back even if the copy fails.
        if procs:
            open_app()
    pr.toc()


if __name__ == "__main__":
    main()
