#!/usr/bin/env python3

"""
Cross-platform script runner tool.
"""

import os
import subprocess
import sys

from tools.paths import ProjectPaths


def check_db_exists() -> None:
    """Check if dpd.db exists, exit if not found."""
    pth = ProjectPaths()
    if not pth.dpd_db_path.exists():
        print("Error: dpd.db file not found.")
        sys.exit(1)


def touch_file(filename: str) -> None:
    """Create empty file if it doesn't exist."""
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as _:
            pass


def run_script(title: str, commands: list[str]) -> None:
    """
    Run a complete script with title and simple command list.
    Auto-detects use_uv based on file extension.
    Includes timing and minimal printing.
    """
    import datetime
    import time

    print(
        f"Starting: {title} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"  # noqa: DTZ005
    )
    start_time = time.time()

    for cmd in commands:
        full_command = _build_command(cmd)
        cmd_start = time.time()

        try:
            subprocess.run(full_command, shell=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Command failed with exit code {e.returncode}")
            sys.exit(e.returncode)
        except Exception as e:  # noqa: BLE001
            print(f"Error: {e!s}")
            sys.exit(1)
        finally:
            print(f"\n─── {cmd}: {time.time() - cmd_start:.1f}s wall\n")

    # Print elapsed time
    end_time = time.time()
    elapsed = end_time - start_time
    print(
        f"Finished: {title} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"  # noqa: DTZ005
    )
    print(f"Completed in {int(elapsed // 60)} minutes\n")


def _build_command(command: str) -> str:
    """
    Build the full command string with auto-detected execution method.
    """
    if _should_use_uv(command):
        return f"uv run python {command}"
    else:
        return command


def _should_use_uv(command: str) -> bool:
    """
    Determine if a command should use uv run based on its extension.
    """
    return command.strip().endswith(".py")
