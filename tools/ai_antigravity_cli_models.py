"""Shared utilities for the Antigravity CLI (agy) provider."""

from __future__ import annotations

import functools
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


@functools.cache
def agy_supports_model(agy_path: Path) -> bool:
    """Check whether this agy build accepts --model (older builds reject it)."""
    try:
        result = subprocess.run(
            [str(agy_path), "--help"],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return "--model" in result.stdout + result.stderr


def run_antigravity_print(
    agy_path: Path,
    model: str | None,
    prompt: str,
    timeout: int = 120,
) -> RunResult:
    """Run agy in print (non-interactive) mode and return stdout/stderr/returncode.

    If `model` is None, the model flag is omitted and agy falls back to its
    own default model (for agy builds that predate --model support).
    """
    command = [str(agy_path), "--sandbox"]
    if model is not None:
        command += ["--model", model]
    command += ["--print", prompt, "--print-timeout", f"{timeout}s"]
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
