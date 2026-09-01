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
    # stream-json stdin carries large prompts; cap is a sanity guard only
    assert antigravity_cli.MAX_PROMPT_BYTES == 4_000_000


def test_request_rejects_oversized_prompt_before_locating_agy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_locate() -> Path:
        raise AssertionError("agy lookup should not run for oversized prompts")

    monkeypatch.setattr(antigravity_cli, "_locate_antigravity", fail_locate)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="x" * 5_000_000,
        prompt_sys="s",
        model="test-model",
    )

    assert response.content is None
    assert "prompt too large" in response.status_message
    assert "argv transport" not in response.status_message


def test_small_prompt_fits_prompt_budget() -> None:
    prompt = antigravity_cli._build_prompt(
        contents="x" * 100,
        system_instruction="s",
        max_output_tokens=32768,
        temperature=0.1,
    )

    assert len(prompt.encode("utf-8")) < antigravity_cli.MAX_PROMPT_BYTES


def test_request_classifies_timeout_text_as_provider_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_agy(monkeypatch, "Error: timed out waiting for response")

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s", model="test-model"
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
        prompt="p", prompt_sys="s", model="test-model"
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
        prompt="p", prompt_sys="s", model="test-model"
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
        prompt="p", prompt_sys="s", model="test-model"
    )

    assert response.content is None
    assert response.status_message == "test-model returned an empty response"
    assert "possible quota exhaustion" not in response.status_message


def test_request_strips_trailing_timeout_line_and_marks_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = '{"translation": "x",\n "scores": {\nError: timed out waiting for response'
    _patch_agy(monkeypatch, stdout)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s", model="test-model"
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
        prompt="p", prompt_sys="s", model="test-model"
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
        prompt="p", prompt_sys="s", model="test-model"
    )

    assert response.content == '{"ok": true}'
    assert captured["model"] is None


def test_request_keeps_normal_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_agy(monkeypatch, '{"translation": "x", "scores": {}}')

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s", model="test-model"
    )

    assert response.content == '{"translation": "x", "scores": {}}'


def test_request_keeps_multiline_content_mentioning_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = '{"translation": "Error: this is part of a translation",\n "scores": {}}'
    _patch_agy(monkeypatch, stdout)

    response = antigravity_cli.AntigravityCliManager().request(
        prompt="p", prompt_sys="s", model="test-model"
    )

    assert response.content == stdout


def test_provider_boundary_stdin_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    """Integration test: AntigravityCliManager drives run_antigravity_print via stdin.

    Proves: (a) prompt is in input= not argv, (b) a >700 KB prompt is not rejected,
    (c) a normal prompt round-trips through request() to _Response.content.
    """
    from tools.ai_antigravity_cli_models import RunResult

    captured: dict[str, object] = {}
    canned_output = '{"translation": "ok"}'

    def fake_run_antigravity_print(
        agy_path: Path, model: str | None, prompt: str, timeout: int
    ) -> RunResult:
        captured["prompt_arg"] = prompt
        return RunResult(returncode=0, stdout=canned_output, stderr="")

    monkeypatch.setattr(
        antigravity_cli, "_locate_antigravity", lambda: Path("/usr/bin/true")
    )
    monkeypatch.setattr(
        antigravity_cli, "run_antigravity_print", fake_run_antigravity_print
    )

    # (a) + (c): normal prompt round-trips through request()
    response = antigravity_cli.AntigravityCliManager().request(
        prompt="hello", prompt_sys="sys", model="test-model"
    )
    assert response.content == canned_output
    # The prompt was delivered as the Python `prompt` arg to run_antigravity_print,
    # which attaches it to --print (agy >= 1.1.23 no longer reads stdin) — proven
    # by the unit test for run_antigravity_print; here we just confirm the call.
    assert "hello" in str(captured.get("prompt_arg", ""))

    # (b): large prompts (analysis sends ~170KB) are not rejected pre-send
    large_prompt = "x" * 800_000
    captured.clear()
    response_large = antigravity_cli.AntigravityCliManager().request(
        prompt=large_prompt, prompt_sys="sys", model="test-model"
    )
    assert response_large.content is not None
    assert "prompt too large" not in (response_large.status_message or "")


def test_extract_stream_response_success() -> None:
    init = '{"event":"init","init":{"model":"m"}}'
    result = (
        '{"event":"result","result":{"status":"SUCCESS","response":"4\\n","error":""}}'
    )
    stdout = init + "\n" + result + "\n"
    assert antigravity_cli._extract_stream_response(stdout) == "4\n"


def test_extract_stream_response_error_status_raises() -> None:
    result = '{"event":"result","result":{"status":"ERROR","response":"","error":"quota blown"}}'
    with pytest.raises(
        antigravity_cli.AntigravityCliProviderError, match="quota blown"
    ):
        antigravity_cli._extract_stream_response(result)


def test_extract_stream_response_returns_none_without_result_event() -> None:
    # no result event -> caller falls back to legacy plain-text parsing
    assert antigravity_cli._extract_stream_response("plain model output") is None


def test_extract_stream_response_uses_last_result_event() -> None:
    error_line = (
        '{"event":"result","result":{"status":"ERROR","response":"","error":"old"}}'
    )
    ok_line = (
        '{"event":"result","result":{"status":"SUCCESS","response":"ok","error":""}}'
    )
    stdout = error_line + "\n" + ok_line
    assert antigravity_cli._extract_stream_response(stdout) == "ok"
