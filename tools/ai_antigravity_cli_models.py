"""Shared utilities for the Antigravity CLI (agy) provider."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]|\x1b\][^\x07]*\x07")


class AntigravityCliModelError(RuntimeError):
    """Raised when an Antigravity CLI operation fails."""


class RunResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


def locate_executable(name: str) -> Path:
    executable = shutil.which(name)
    if executable is None:
        raise AntigravityCliModelError(f"{name} executable not found on PATH")
    return Path(executable)


def run_antigravity_print(
    agy_path: Path,
    model: str,
    prompt: str,
    timeout: int = 120,
) -> RunResult:
    """Run agy in print (non-interactive) mode and return stdout/stderr/returncode."""
    command = [
        str(agy_path),
        "--sandbox",
        "--model",
        model,
        "--print",
        prompt,
        "--print-timeout",
        f"{timeout}s",
    ]
    with tempfile.TemporaryDirectory(prefix="agy_print_") as scratch_dir:
        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            cwd=scratch_dir,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=timeout + 10,
        )
    return RunResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def clean_terminal_output(text: str | None) -> str:
    """Strip ANSI escape sequences and surrounding whitespace."""
    if not text:
        return ""
    return ANSI_ESCAPE.sub("", text).strip()
