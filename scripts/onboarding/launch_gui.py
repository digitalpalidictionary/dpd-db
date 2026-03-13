"""GUI launch wrapper for DPD contributors.

Ensures dependencies are up to date, then launches the Flet GUI.
This script is invoked by the desktop shortcut.
"""

import subprocess
import sys

from tools.printer import printer as pr


def sync_dependencies() -> bool:
    """Run uv sync to ensure dependencies are current."""
    try:
        result = subprocess.run(
            ["uv", "sync"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def launch_gui() -> None:
    """Sync dependencies and launch the GUI."""
    pr.green_tmr("syncing dependencies")
    if sync_dependencies():
        pr.yes("ok")
    else:
        pr.no("failed")
        pr.amber("Dependency sync failed. The GUI may still work.")

    pr.green_tmr("launching DPD GUI")
    pr.yes("ok")

    subprocess.run(
        [sys.executable, "gui2/main.py"],
        check=False,
    )


if __name__ == "__main__":
    launch_gui()
