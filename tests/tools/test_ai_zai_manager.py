"""Verify Z.ai GLM provider request payload handling."""

from typing import Any

import requests

from tools.ai_zai_manager import ZaiManager, _error_detail


class _FakeResponse(requests.Response):
    def __init__(
        self,
        content: str = '{"ok": true}',
        finish_reason: str = "stop",
    ) -> None:
        super().__init__()
        self.status_code = 200
        self.json_content = content
        self.finish_reason = finish_reason

    def json(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "choices": [
                {
                    "message": {"content": self.json_content},
                    "finish_reason": self.finish_reason,
                }
            ]
        }


class _CapturingZaiManager(ZaiManager):
    def __init__(self) -> None:
        self.api_key = "test"
        self.api_key_name = "zai"
        self.headers: dict[str, str] = {}
        self.captured_payload: dict[str, Any] | None = None

    def _post_request(
        self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
    ) -> tuple[_FakeResponse, None]:
        self.captured_payload = payload
        return _FakeResponse(), None


def test_request_disables_thinking_mode_by_default() -> None:
    manager = _CapturingZaiManager()

    response = manager.request(prompt="Return JSON.", model="glm-5-turbo")

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["thinking"] == {"type": "disabled"}
    assert manager.captured_payload["model"] == "glm-5-turbo"


def test_request_allows_kwargs_override() -> None:
    manager = _CapturingZaiManager()

    response = manager.request(
        prompt="Return JSON.",
        model="glm-5.2",
        max_tokens=512,
        thinking={"type": "enabled"},
    )

    assert response.content == '{"ok": true}'
    assert manager.captured_payload is not None
    assert manager.captured_payload["max_tokens"] == 512
    assert manager.captured_payload["thinking"] == {"type": "enabled"}


def test_request_includes_system_prompt() -> None:
    manager = _CapturingZaiManager()

    manager.request(prompt="hi", prompt_sys="be brief", model="glm-5-turbo")

    assert manager.captured_payload is not None
    assert manager.captured_payload["messages"][0] == {
        "role": "system",
        "content": "be brief",
    }


def test_request_non_stop_finish_reason_in_status() -> None:
    class LengthFinishedZaiManager(_CapturingZaiManager):
        def _post_request(
            self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
        ) -> tuple[_FakeResponse, None]:
            self.captured_payload = payload
            return _FakeResponse(content='{"ok": true}', finish_reason="length"), None

    manager = LengthFinishedZaiManager()

    response = manager.request(prompt="Return JSON.", model="glm-5-turbo")

    assert response.content == '{"ok": true}'
    assert "finish_reason=length" in response.status_message


def test_request_empty_content_returns_none() -> None:
    class EmptyContentZaiManager(_CapturingZaiManager):
        def _post_request(
            self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
        ) -> tuple[_FakeResponse, None]:
            self.captured_payload = payload
            return _FakeResponse(content="", finish_reason="length"), None

    manager = EmptyContentZaiManager()

    response = manager.request(prompt="Return JSON.", model="glm-5-turbo")

    assert response.content is None
    assert "finish_reason=length" in response.status_message


def test_unconfigured_manager_returns_error() -> None:
    manager = ZaiManager(api_key_name="nonexistent_key_name")

    response = manager.request(prompt="hi", model="glm-5-turbo")

    assert response.content is None
    assert "not configured" in response.status_message


def _http_error(status_code: int, body: str, reason: str = "") -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    response.reason = reason
    response._content = body.encode("utf-8")
    return requests.HTTPError(response=response)


def test_error_detail_surfaces_code_and_message() -> None:
    """The real 1305 overload body must reach the user, not the opaque string."""
    exc = _http_error(
        429,
        '{"error":{"code":"1305","message":"The service may be temporarily '
        'overloaded, please try again later"}}',
    )
    detail = _error_detail(exc)
    assert detail == (
        "HTTP 429: [1305] The service may be temporarily overloaded, "
        "please try again later"
    )


def test_error_detail_falls_back_to_raw_body() -> None:
    exc = _http_error(500, "upstream boom", reason="Internal Server Error")
    detail = _error_detail(exc)
    assert detail == "HTTP 500: upstream boom"


def test_error_detail_no_response_uses_exception_text() -> None:
    exc = requests.ConnectionError("connection refused")
    assert _error_detail(exc) == "connection refused"
