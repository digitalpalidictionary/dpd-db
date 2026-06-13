"""Antigravity CLI provider for headless LLM requests through the local agy executable."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, NamedTuple, cast

from tools.ai_antigravity_cli_models import (
    AntigravityCliModelError,
    agy_supports_model,
    clean_terminal_output,
    locate_executable,
    run_antigravity_print,
)
from tools.printer import printer as pr

PROBE_CONTENTS = "Return OK only."
PROBE_SYSTEM_INSTRUCTION = "Return exactly OK and nothing else."
MAX_PROMPT_BYTES = 4_000_000
AUTH_PROMPT_MARKERS = ("Authentication required", "accounts.google.com")
MAX_ERROR_LINE_LENGTH = 200
IMMEDIATE_EMPTY_SECONDS = 10.0
TOOL_CALL_MARKER = "include:default_api:"

_warned_model_unsupported = False


class _Response(NamedTuple):
    content: str | None
    status_message: str


class AntigravityCliManager:
    def request(
        self,
        prompt: str,
        prompt_sys: str | None = None,
        model: str = "Gemini 3.5 Flash (Low)",
        timeout: float = 150.0,
        **_kwargs: Any,
    ) -> _Response:
        try:
            content = generate_content(
                contents=prompt,
                system_instruction=prompt_sys or "",
                model=model,
                timeout=int(timeout),
            )
            warnings: list[str] = []
            content, trailing_error = _split_trailing_error(content)
            if trailing_error:
                warnings.append(f"partial: {trailing_error}")
            if TOOL_CALL_MARKER in content:
                warnings.append("tool-call text in response")
            status_message = (
                "; ".join(warnings) if warnings else f"antigravity_cli/{model}"
            )
            return _Response(content=content, status_message=status_message)
        except AntigravityCliProviderError as e:
            return _Response(content=None, status_message=str(e))


class AntigravityCliProviderError(RuntimeError):
    """Raised when the Antigravity CLI provider cannot complete a request."""


def get_working_key(model: str = "Gemini 3.5 Flash (Low)") -> bool:
    """Check whether Antigravity CLI can call the selected model."""

    try:
        response = generate_content(
            contents=PROBE_CONTENTS,
            system_instruction=PROBE_SYSTEM_INSTRUCTION,
            model=model,
            max_output_tokens=10,
            temperature=0.0,
            timeout=60,
        )
    except Exception as e:  # noqa: BLE001
        pr.red(f"Antigravity CLI model {model} failed: {e}")
        return False

    return bool(response.strip())


def generate_content(
    contents: str,
    system_instruction: str,
    model: str,
    max_output_tokens: int = 32768,
    temperature: float = 0.1,
    timeout: int = 150,
) -> str:
    """Generate content using Antigravity CLI print mode."""

    prompt = _build_prompt(contents, system_instruction, max_output_tokens, temperature)
    prompt_bytes = len(prompt.encode("utf-8"))
    if prompt_bytes > MAX_PROMPT_BYTES:
        raise AntigravityCliProviderError(
            f"prompt too large ({prompt_bytes} bytes > {MAX_PROMPT_BYTES})"
        )

    agy_path = _locate_antigravity()

    model_to_use: str | None = model
    if not agy_supports_model(agy_path):
        global _warned_model_unsupported
        if not _warned_model_unsupported:
            pr.amber(
                "agy does not support --model (run `agy update` to upgrade); "
                f"ignoring requested model {model!r} and using agy's default model"
            )
            _warned_model_unsupported = True
        model_to_use = None

    pr.green(f"  -> antigravity-cli {model} (timeout={timeout}s)...")
    try:
        started_at = time.monotonic()
        result = run_antigravity_print(
            agy_path,
            model_to_use,
            prompt,
            timeout=timeout,
        )
        elapsed = time.monotonic() - started_at
    except subprocess.TimeoutExpired as error:
        raise AntigravityCliProviderError(
            f"{model} timed out after {timeout}s"
        ) from error
    except AntigravityCliModelError as error:
        raise AntigravityCliProviderError(str(error)) from error

    if result.returncode != 0:
        raise AntigravityCliProviderError(
            f"{model} failed: {_brief_command_error(result.stdout, result.stderr, result.returncode)}"
        )

    response = _extract_response(result.stdout)
    if response is None or not response.strip():
        if elapsed < IMMEDIATE_EMPTY_SECONDS:
            raise AntigravityCliProviderError(
                f"{model} returned an immediate empty response "
                "(possible quota exhaustion)"
            )
        raise AntigravityCliProviderError(f"{model} returned an empty response")
    error_reason = _classify_error_text(response)
    if error_reason:
        raise AntigravityCliProviderError(f"{model} error response: {error_reason}")
    return response


def _locate_antigravity() -> Path:
    try:
        return locate_executable("agy")
    except AntigravityCliModelError as error:
        raise AntigravityCliProviderError("agy executable not found on PATH") from error


def _build_prompt(
    contents: str, system_instruction: str, max_output_tokens: int, temperature: float
) -> str:
    return (
        "Follow the system instruction below. Treat the USER CONTENT section as the "
        "full user input. Do not inspect local files or use tools unless the user "
        "content explicitly requires it.\n\n"
        "SYSTEM INSTRUCTION:\n"
        f"{system_instruction}\n\n"
        "REQUEST SETTINGS:\n"
        f"- max_output_tokens: {max_output_tokens}\n"
        f"- temperature: {temperature}\n"
        "\nUSER CONTENT:\n"
        f"{contents}\n"
    )


def _extract_response(stdout: str) -> str | None:
    cleaned = clean_terminal_output(stdout)
    if not cleaned:
        return None

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return cleaned

    if isinstance(parsed, str):
        return parsed
    if not isinstance(parsed, dict):
        return cleaned

    response = cast(dict[str, Any], parsed).get("response")
    if isinstance(response, str):
        return response
    text = cast(dict[str, Any], parsed).get("text")
    if isinstance(text, str):
        return text
    content = cast(dict[str, Any], parsed).get("content")
    if isinstance(content, str):
        return content
    return cleaned


def _classify_error_text(response: str) -> str | None:
    """Detect agy failure text printed to stdout with exit code 0.

    agy reports timeouts ("Error: timed out waiting for response") and Google
    OAuth login prompts on stdout while exiting 0. Both must surface as provider
    errors so AIManager falls back, instead of being parsed as model content.
    """
    stripped = response.strip()
    if all(marker in stripped for marker in AUTH_PROMPT_MARKERS):
        return "authentication required (agy is not logged in)"
    if (
        stripped.startswith("Error:")
        and "\n" not in stripped
        and len(stripped) <= MAX_ERROR_LINE_LENGTH
    ):
        return stripped
    return None


def _split_trailing_error(response: str) -> tuple[str, str | None]:
    """Split a trailing single-line agy error off partial streamed content."""
    lines = response.rstrip().splitlines()
    if len(lines) < 2:
        return response, None

    last = lines[-1].strip()
    if last.startswith("Error:") and len(last) <= MAX_ERROR_LINE_LENGTH:
        content = "\n".join(lines[:-1]).rstrip()
        if content:
            return content, last

    return response, None


def _brief_command_error(
    stdout: str | None, stderr: str | None, returncode: int
) -> str:
    message = clean_terminal_output(stderr) or clean_terminal_output(stdout)
    if not message:
        message = str(returncode)
    if len(message) <= 500:
        return message
    return f"{message[:497]}..."
