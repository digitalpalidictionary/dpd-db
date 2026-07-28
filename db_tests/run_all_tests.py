#!/usr/bin/env python3

"""Run every db_tests script in sequence, pausing between each one.

Order: relationship tests, then everything in db_tests/single/, then the
Flet gui. The single/ scripts are discovered by globbing, so adding or
deleting one is picked up automatically without editing this file.
"""

import subprocess
import sys
import termios
import tty
from pathlib import Path

from tools.printer import printer as pr

SINGLE_DIR = Path("db_tests/single")
FIRST_MODULE = "db_tests.db_tests_relationships"
LAST_MODULE = "db_tests.gui.main"


def find_modules() -> list[str]:
    """Build the ordered list of modules to run."""

    if not SINGLE_DIR.is_dir():
        pr.red(f"{SINGLE_DIR} not found, run this from the project root")
        sys.exit(1)

    singles = [
        f"db_tests.single.{path.stem}" for path in sorted(SINGLE_DIR.glob("*.py"))
    ]
    return [FIRST_MODULE, *singles, LAST_MODULE]


def press_any_key() -> None:
    """Wait for a single keypress. Ctrl-C or Ctrl-D aborts the run."""

    print("press any key to continue... ctrl-c to quit", end="", flush=True)

    if not sys.stdin.isatty():
        input()
        return

    file_descriptor = sys.stdin.fileno()
    old_settings = termios.tcgetattr(file_descriptor)
    try:
        tty.setraw(file_descriptor)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)
    print()

    if key in ("\x03", "\x04"):
        raise KeyboardInterrupt


def run_module(module: str) -> int:
    """Run one module as a subprocess, sharing this terminal."""

    try:
        return subprocess.run([sys.executable, "-m", module]).returncode
    except KeyboardInterrupt:
        return 130


def main() -> None:
    modules = find_modules()

    if "--list" in sys.argv[1:]:
        for index, module in enumerate(modules, start=1):
            print(f"{index:>3}. {module}")
        return

    pr.tic()
    total = len(modules)
    failed: list[str] = []

    for index, module in enumerate(modules, start=1):
        print()
        pr.yellow_title(f"[{index}/{total}] {module}")
        print()
        returncode = run_module(module)

        if returncode != 0:
            failed.append(module)
            pr.red(f"{module} exited with {returncode}")

        if index < total:
            try:
                press_any_key()
            except KeyboardInterrupt:
                print()
                pr.red(f"aborted after {index} of {total}")
                break

    pr.green_title("summary")
    if failed:
        pr.red(f"{len(failed)} failed")
        for module in failed:
            pr.red(f"  {module}")
    else:
        pr.green("no failures")
    pr.toc()


if __name__ == "__main__":
    main()
