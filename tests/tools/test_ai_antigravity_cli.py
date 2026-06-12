"""Tests for the Antigravity CLI provider prompt transport guard."""

from pathlib import Path

import pytest

import tools.ai_antigravity_cli as antigravity_cli
from tools.ai_antigravity_cli_models import RunResult


def _patch_agy(monkeypatch: pytest.MonkeyPatch, stdout: str) -> None:
    monkeypatch.setattr(
        antigravity_cli, "_locate_antigravity", lambda: Path("/usr/bin/true")
    )
    monkeypatch.setattr(
        antigravity_cli,
        "run_antigravity_print",
        lambda *args, **kwargs: RunResult(returncode=0, stdout=stdout, stderr=""),
    )


def test_prompt_size_budget_is_safe_margin() -> None:
    assert antigravity_cli.MAX_ARGV_PROMPT_BYTES == 700_000


def test_request_rejects_oversized_prompt_before_locating_agy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_locate() -> Path:
        raise AssertionError("agy lookup should not run for oversized prompts")

    monkeypatch.setattr(antigravity_cli, "_locate_antigravity", fail_locate)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="x" * 800_000,
        prompt_sys="s",
    )

    assert response.content is None
    assert "too large for argv transport" in response.status_message


def test_small_prompt_fits_prompt_budget() -> None:
    prompt = antigravity_cli._build_prompt(
        contents="x" * 100,
        system_instruction="s",
        max_output_tokens=32768,
        temperature=0.1,
    )

    assert len(prompt.encode("utf-8")) < antigravity_cli.MAX_ARGV_PROMPT_BYTES


def test_request_classifies_timeout_text_as_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(monkeypatch, "Error: timed out waiting for response")

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content is None
    assert "timed out waiting for response" in response.status_message


def test_request_classifies_auth_prompt_as_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(
        monkeypatch,
        "Authentication required. Please visit the URL to log in:\n"
        "  https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=x",
    )

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content is None
    assert "authentication required" in response.status_message


def test_immediate_empty_response_flags_possible_quota_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(monkeypatch, "")
    times = iter([100.0, 107.5])
    monkeypatch.setattr(antigravity_cli.time, "monotonic", lambda: next(times))

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s", model="Gemini 3.5 Flash (High)"
    )

    assert response.content is None
    assert "immediate empty response" in response.status_message
    assert "possible quota exhaustion" in response.status_message


def test_slow_empty_response_keeps_plain_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(monkeypatch, "")
    times = iter([100.0, 111.0])
    monkeypatch.setattr(antigravity_cli.time, "monotonic", lambda: next(times))

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s", model="Gemini 3.5 Flash (High)"
    )

    assert response.content is None
    assert (
        response.status_message == "Gemini 3.5 Flash (High) returned an empty response"
    )
    assert "possible quota exhaustion" not in response.status_message


def test_request_strips_trailing_timeout_line_and_marks_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = '{"translation": "x",\n "scores": {\nError: timed out waiting for response'
    _patch_agy(monkeypatch, stdout)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content == '{"translation": "x",\n "scores": {'
    assert "partial: Error: timed out waiting for response" in response.status_message


def test_request_marks_tool_call_text_in_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = (
        "include:default_api:write_to_file{TargetFile:/tmp/query.py}\n"
        "Error: timed out waiting for response"
    )
    _patch_agy(monkeypatch, stdout)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert (
        response.content
        == "include:default_api:write_to_file{TargetFile:/tmp/query.py}"
    )
    assert "partial: Error: timed out waiting for response" in response.status_message
    assert "tool-call text in response" in response.status_message


def test_split_trailing_error_cases() -> None:
    whole_error = "Error: timed out waiting for response"
    assert antigravity_cli._split_trailing_error(whole_error) == (whole_error, None)

    clean_json = '{"translation": "x", "scores": {}}'
    assert antigravity_cli._split_trailing_error(clean_json) == (clean_json, None)

    partial = '{"translation": "x",\n "scores": {\nError: timed out waiting'
    assert antigravity_cli._split_trailing_error(partial) == (
        '{"translation": "x",\n "scores": {',
        "Error: timed out waiting",
    )

    long_error = (
        f'{{"translation": "x"}}\nError: {"x" * antigravity_cli.MAX_ERROR_LINE_LENGTH}'
    )
    assert antigravity_cli._split_trailing_error(long_error) == (long_error, None)


def test_request_falls_back_to_default_model_when_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run_antigravity_print(
        agy_path: Path, model: str | None, prompt: str, timeout: int
    ) -> RunResult:
        captured["model"] = model
        return RunResult(returncode=0, stdout='{"ok": true}', stderr="")

    monkeypatch.setattr(
        antigravity_cli, "_locate_antigravity", lambda: Path("/usr/bin/true")
    )
    monkeypatch.setattr(antigravity_cli, "agy_supports_model", lambda agy_path: False)
    monkeypatch.setattr(
        antigravity_cli, "run_antigravity_print", fake_run_antigravity_print
    )

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s", model="Gemini 3.5 Flash (Low)"
    )

    assert response.content == '{"ok": true}'
    assert captured["model"] is None


def test_request_keeps_normal_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_agy(monkeypatch, '{"translation": "x", "scores": {}}')

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content == '{"translation": "x", "scores": {}}'


def test_request_keeps_multiline_content_mentioning_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = '{"translation": "Error: this is part of a translation",\n "scores": {}}'
    _patch_agy(monkeypatch, stdout)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s"
    )

    assert response.content == stdout
