"""Verify DeepSeek provider request payload handling for JSON-oriented AI calls."""

from typing import Any

import requests

from tools.ai_deepseek_manager import DeepseekManager


class _FakeResponse(requests.Response):
    def __init__(
        self,
        content: str = '{"ok": true}',
        finish_reason: str = "stop",
        reasoning_content: str = "",
        usage: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.status_code = 200
        self.json_content = content
        self.finish_reason = finish_reason
        self.reasoning_content = reasoning_content
        self.usage = usage or {}

    def json(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "choices": [
                {
                    "message": {
                        "content": self.json_content,
                        "reasoning_content": self.reasoning_content,
                    },
                    "finish_reason": self.finish_reason,
                }
            ],
            "usage": self.usage,
        }


class _CapturingDeepseekManager(DeepseekManager):
    def __init__(self) -> None:
        self.api_key = "test"
        self.api_key_name = "deepseek"
        self.headers: dict[str, str] = {}
        self.captured_payload: dict[str, Any] | None = None

    def balance(self) -> dict[str, Any]:
        return {"balance_infos": [{"total_balance": "1"}]}

    def _post_request(
        self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
    ) -> _FakeResponse:
        self.captured_payload = payload
        return _FakeResponse()


def test_request_disables_thinking_mode_by_default() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["thinking"] == {"type": "disabled"}


def test_request_allows_explicit_thinking_override() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(
        prompt="Return JSON.",
        model="deepseek-v4-flash",
        thinking={"type": "enabled", "reasoning_effort": "high"},
    )

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["thinking"] == {
        "type": "enabled",
        "reasoning_effort": "high",
    }


def test_request_uses_raised_max_tokens_default() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["max_tokens"] == 8192


def test_request_allows_explicit_max_tokens_override() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(
        prompt="Return JSON.",
        model="deepseek-v4-flash",
        max_tokens=512,
    )

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["max_tokens"] == 512


def test_request_empty_content_status_message_is_compact() -> None:
    class EmptyContentDeepseekManager(_CapturingDeepseekManager):
        def _post_request(
            self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
        ) -> _FakeResponse:
            self.captured_payload = payload
            return _FakeResponse(
                content="",
                finish_reason="length",
                reasoning_content="x" * 2001,
                usage={"completion_tokens": 2048},
            )

    manager = EmptyContentDeepseekManager()

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content is None
    assert "finish_reason=length" in response.status_message
    assert len(response.status_message) < 500


def test_request_non_empty_content_status_includes_non_stop_finish_reason() -> None:
    class LengthFinishedDeepseekManager(_CapturingDeepseekManager):
        def _post_request(
            self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
        ) -> _FakeResponse:
            self.captured_payload = payload
            return _FakeResponse(content='{"ok": true}', finish_reason="length")

    manager = LengthFinishedDeepseekManager()

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content == '{"ok": true}'
    assert "finish_reason=length" in response.status_message


def test_request_non_empty_content_status_omits_stop_finish_reason() -> None:
    manager = _CapturingDeepseekManager()

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content == '{"ok": true}'
    assert response.status_message == "200"
