#!/usr/bin/env python3

"""
Cross-platform script runner tool.
"""

import subprocess
import sys
import os


def check_db_exists() -> None:
    """Check if dpd.db exists, exit if not found."""
    if not os.path.exists("dpd.db"):
        print("Error: dpd.db file not found.")
        sys.exit(1)


def touch_file(filename: str) -> None:
    """Create empty file if it doesn't exist."""
    if not os.path.exists(filename):
        with open(filename, "w") as _:
            pass


def run_script(title: str, commands: list[str]) -> None:
    """
    Run a complete script with title and simple command list.
    Auto-detects use_uv based on file extension.
    Includes timing and minimal printing.
    """
    import time
    import datetime

    print(
        f"Starting: {title} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    start_time = time.time()

    for cmd in commands:
        full_command = _build_command(cmd)

        try:
            subprocess.run(full_command, shell=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: Command failed with exit code {e.returncode}")
            sys.exit(e.returncode)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

    # Print elapsed time
    end_time = time.time()
    elapsed = end_time - start_time
    print(
        f"Finished: {title} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
