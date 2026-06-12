"""Tests for Antigravity CLI model subprocess isolation."""

from pathlib import Path
from typing import Any

import pytest

import tools.ai_antigravity_cli_models as antigravity_cli_models


def test_run_antigravity_print_uses_isolated_cwd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        cwd = kwargs["cwd"]
        cwd_path = Path(cwd)
        captured["command"] = command
        captured["cwd"] = cwd_path
        captured["cwd_exists_at_call"] = cwd_path.is_dir()
        captured["timeout"] = kwargs["timeout"]
        return antigravity_cli_models.subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(antigravity_cli_models.subprocess, "run", fake_run)

    result = antigravity_cli_models.run_antigravity_print(
        Path("/usr/bin/false"),
        "m",
        "p",
        timeout=7,
    )

    assert result.stdout == "ok"
    assert captured["cwd_exists_at_call"] is True
    assert Path.cwd() not in captured["cwd"].parents
    assert captured["cwd"] != Path.cwd()


def test_run_antigravity_print_passes_sandbox_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        captured["command"] = command
        return antigravity_cli_models.subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(antigravity_cli_models.subprocess, "run", fake_run)

    antigravity_cli_models.run_antigravity_print(Path("/usr/bin/false"), "m", "p")

    assert "--sandbox" in captured["command"]


def test_run_antigravity_print_keeps_command_and_timeout_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: Any) -> Any:
        captured["command"] = command
        captured["timeout"] = kwargs["timeout"]
        return antigravity_cli_models.subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    monkeypatch.setattr(antigravity_cli_models.subprocess, "run", fake_run)

    antigravity_cli_models.run_antigravity_print(
        Path("/usr/bin/false"),
        "model-x",
        "prompt-x",
        timeout=11,
    )

    command = captured["command"]
    assert command[:2] == ["/usr/bin/false", "--sandbox"]
    assert "--model" in command
    assert "model-x" in command
    assert "--print" in command
    assert "prompt-x" in command
    assert "--print-timeout" in command
    assert "11s" in command
    assert captured["timeout"] == 21
