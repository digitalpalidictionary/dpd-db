"""Tests for tools/ai_gemini_manager.py response handling.

`GeminiManager.request` is driven with a fake client so no API key or network is
needed. The manager is built with `__new__` to bypass `__init__`, which would
otherwise read config.ini and construct a real genai.Client.

The parts-joining case is the one that matters: `part.text` is typed `str | None`
and the old `hasattr(part, "text")` filter let a None part through, so `"".join`
raised TypeError. That was swallowed by the bare `except Exception` at the bottom
of `request`, turning a recoverable response into an opaque failure.
"""

from dataclasses import dataclass, field
from typing import Any

from google.api_core import exceptions as google_exceptions

from tools.ai_gemini_manager import GeminiManager


@dataclass
class FakePart:
    text: str | None


@dataclass
class FakeContent:
    parts: list[FakePart] | None


@dataclass
class FakeCandidate:
    content: FakeContent | None


@dataclass
class FakeFeedback:
    block_reason: str | None = None


@dataclass
class FakeResponse:
    text: str | None = None
    candidates: list[FakeCandidate] | None = None
    prompt_feedback: FakeFeedback | None = None


@dataclass
class FakeModels:
    result: Any
    calls: list[dict[str, Any]] = field(default_factory=list)

    def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@dataclass
class FakeClient:
    models: FakeModels


def _manager(result: Any) -> GeminiManager:
    """A GeminiManager wired to a fake client, skipping __init__."""
    mgr = GeminiManager.__new__(GeminiManager)
    mgr.api_key = "test-key"
    mgr.api_key_name = "gemini"
    mgr.client = FakeClient(FakeModels(result))  # type: ignore[assignment]
    return mgr


def _with_parts(*texts: str | None) -> FakeResponse:
    parts = [FakePart(t) for t in texts]
    return FakeResponse(candidates=[FakeCandidate(FakeContent(parts))])


def test_uninitialised_client_reports_clearly() -> None:
    mgr = GeminiManager.__new__(GeminiManager)
    mgr.api_key = None
    mgr.api_key_name = "gemini"
    mgr.client = None

    result = mgr.request("hello", "gemini-2.0-flash")

    assert result.content is None
    assert "not initialized" in result.status_message


def test_plain_text_response_is_returned_directly() -> None:
    result = _manager(FakeResponse(text="a straight answer")).request(
        "hello", "gemini-2.0-flash"
    )

    assert result.content == "a straight answer"


def test_blocked_response_reports_the_reason() -> None:
    response = FakeResponse(prompt_feedback=FakeFeedback(block_reason="SAFETY"))

    result = _manager(response).request("hello", "gemini-2.0-flash")

    assert result.content is None
    assert "SAFETY" in result.status_message
    assert "blocked" in result.status_message


def test_parts_are_joined_when_there_is_no_top_level_text() -> None:
    result = _manager(_with_parts("one ", "two ", "three")).request(
        "hello", "gemini-2.0-flash"
    )

    assert result.content == "one two three"
    assert "Success" in result.status_message


def test_none_parts_are_skipped_rather_than_crashing_the_join() -> None:
    """The regression guard. A None part used to raise TypeError inside join."""
    result = _manager(_with_parts("kept ", None, "also kept")).request(
        "hello", "gemini-2.0-flash"
    )

    assert result.content == "kept also kept"
    assert "TypeError" not in result.status_message
    assert "NoneType" not in result.status_message


def test_all_parts_none_falls_through_to_the_empty_response_path() -> None:
    result = _manager(_with_parts(None, None)).request("hello", "gemini-2.0-flash")

    assert result.content is None
    assert "NoneType" not in result.status_message


def test_empty_string_parts_are_skipped() -> None:
    result = _manager(_with_parts("", "text", "")).request("hello", "gemini-2.0-flash")

    assert result.content == "text"


def test_missing_candidates_returns_no_content() -> None:
    result = _manager(FakeResponse(candidates=[])).request("hello", "gemini-2.0-flash")

    assert result.content is None


def test_google_api_error_is_reported_not_raised() -> None:
    error = google_exceptions.GoogleAPICallError("quota exhausted")

    result = _manager(error).request("hello", "gemini-2.0-flash")

    assert result.content is None
    assert "quota exhausted" in result.status_message


def test_unexpected_error_is_reported_not_raised() -> None:
    result = _manager(RuntimeError("socket died")).request("hello", "gemini-2.0-flash")

    assert result.content is None
    assert "socket died" in result.status_message


def test_bare_model_name_gains_the_models_prefix() -> None:
    mgr = _manager(FakeResponse(text="ok"))
    mgr.request("hello", "gemini-2.0-flash")

    assert mgr.client.models.calls[0]["model"] == "models/gemini-2.0-flash"  # type: ignore[union-attr]


def test_already_prefixed_model_name_is_left_alone() -> None:
    mgr = _manager(FakeResponse(text="ok"))
    mgr.request("hello", "models/gemini-2.0-flash")

    assert mgr.client.models.calls[0]["model"] == "models/gemini-2.0-flash"  # type: ignore[union-attr]


def test_system_prompt_is_prepended_to_the_user_prompt() -> None:
    mgr = _manager(FakeResponse(text="ok"))
    mgr.request("the question", "gemini-2.0-flash", prompt_sys="be terse")

    assert mgr.client.models.calls[0]["contents"] == "be terse\n\nthe question"  # type: ignore[union-attr]


def test_grounding_attaches_a_search_tool() -> None:
    mgr = _manager(FakeResponse(text="ok"))
    mgr.request("hello", "gemini-2.0-flash", grounding=True)

    config = mgr.client.models.calls[0]["config"]  # type: ignore[union-attr]
    assert config.tools, "grounding should attach at least one tool"


def test_no_grounding_attaches_no_tools() -> None:
    mgr = _manager(FakeResponse(text="ok"))
    mgr.request("hello", "gemini-2.0-flash")

    config = mgr.client.models.calls[0]["config"]  # type: ignore[union-attr]
    assert not config.tools
