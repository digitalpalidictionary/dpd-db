"""Verify the shared OpenAI-compatible provider: payload shaping, response parsing, error detail.

Merges the coverage previously held by test_ai_zai_manager.py and
test_ai_deepseek_manager.py, and adds the OpenRouter/NVIDIA cases that never had any.
The error-body fixtures are the real bodies those four APIs returned when probed
on 2026-08-25 — see the thread spec for the captured responses.
"""

import json
import time
from typing import Any

import pytest
import requests

from tools.ai_openai_compat import (
    PROVIDER_SPECS,
    OpenAiCompatManager,
    _error_detail,
)


class _FakeResponse(requests.Response):
    def __init__(
        self,
        content: str | None = '{"ok": true}',
        finish_reason: str = "stop",
        reasoning_content: str = "",
        usage: dict[str, Any] | None = None,
        payload: Any = None,
        text: str = "",
    ) -> None:
        super().__init__()
        self.status_code = 200
        self.json_content = content
        self.finish_reason = finish_reason
        self.reasoning_content = reasoning_content
        self.usage = usage or {}
        self.override_payload: Any = payload
        self._content = text.encode("utf-8")

    def json(self, **kwargs: Any) -> Any:
        if self.override_payload is not None:
            return self.override_payload
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


def _manager(provider: str, response: _FakeResponse | None = None) -> Any:
    """A manager wired to a canned response, bypassing config.ini and the network."""

    class _Capturing(OpenAiCompatManager):
        def __init__(self) -> None:
            self.provider_name = provider
            self.spec = PROVIDER_SPECS[provider]
            self.api_key = "test"
            self.api_key_name = provider
            self.headers: dict[str, str] = {}
            self.captured_payload: dict[str, Any] | None = None
            self.captured_url: str | None = None

        def _post_request(
            self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
        ) -> tuple[requests.Response | None, str | None]:
            self.captured_payload = payload
            self.captured_url = api_url
            return (response or _FakeResponse()), None

    return _Capturing()


# --------------------------------------------------------------------------
# payload shaping
# --------------------------------------------------------------------------


@pytest.mark.parametrize("provider", ["zai", "deepseek"])
def test_thinking_disabled_and_max_tokens_by_default(provider: str) -> None:
    manager = _manager(provider)

    response = manager.request(prompt="Return JSON.", model="a-model")

    assert response.content == '{"ok": true}'
    assert manager.captured_payload["thinking"] == {"type": "disabled"}
    assert manager.captured_payload["max_tokens"] == 8192
    assert manager.captured_payload["model"] == "a-model"


@pytest.mark.parametrize("provider", ["openrouter", "nvidia"])
def test_openai_native_providers_send_no_extras(provider: str) -> None:
    """OpenRouter and NVIDIA accepted a bare payload when probed; keep it bare."""
    manager = _manager(provider)

    manager.request(prompt="Return JSON.", model="a-model")

    assert "thinking" not in manager.captured_payload
    assert "max_tokens" not in manager.captured_payload
    assert manager.captured_payload["stream"] is False


def test_deepseek_keeps_its_sampling_defaults() -> None:
    manager = _manager("deepseek")

    manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert manager.captured_payload["presence_penalty"] == 0
    assert manager.captured_payload["temperature"] == 1
    assert manager.captured_payload["top_p"] == 1
    assert manager.captured_payload["logprobs"] is False


@pytest.mark.parametrize("provider", ["zai", "deepseek"])
def test_kwargs_override_provider_defaults(provider: str) -> None:
    manager = _manager(provider)

    response = manager.request(
        prompt="Return JSON.",
        model="a-model",
        max_tokens=512,
        thinking={"type": "enabled", "reasoning_effort": "high"},
    )

    assert response.content == '{"ok": true}'
    assert manager.captured_payload["max_tokens"] == 512
    assert manager.captured_payload["thinking"] == {
        "type": "enabled",
        "reasoning_effort": "high",
    }


def test_system_prompt_becomes_first_message() -> None:
    manager = _manager("zai")

    manager.request(prompt="hi", prompt_sys="be brief", model="glm-5-turbo")

    assert manager.captured_payload["messages"][0] == {
        "role": "system",
        "content": "be brief",
    }
    assert manager.captured_payload["messages"][1] == {"role": "user", "content": "hi"}


def test_no_system_prompt_sends_only_user_message() -> None:
    manager = _manager("zai")

    manager.request(prompt="hi", model="glm-5-turbo")

    assert manager.captured_payload["messages"] == [{"role": "user", "content": "hi"}]


def test_request_posts_to_the_spec_chat_url() -> None:
    manager = _manager("openrouter")

    manager.request(prompt="hi", model="m")

    assert manager.captured_url == PROVIDER_SPECS["openrouter"].chat_url


# --------------------------------------------------------------------------
# response parsing
# --------------------------------------------------------------------------


def test_clean_stop_status_is_exactly_success() -> None:
    """AIManager suppresses provider detail only when it starts with 'Success'."""
    manager = _manager("deepseek")

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content == '{"ok": true}'
    assert response.status_message == "Success"


def test_truncated_response_with_content_reports_finish_reason() -> None:
    manager = _manager("zai", _FakeResponse(finish_reason="length"))

    response = manager.request(prompt="Return JSON.", model="glm-5-turbo")

    assert response.content == '{"ok": true}'
    assert "finish_reason=length" in response.status_message


def test_openrouter_truncation_with_null_content() -> None:
    """Probed live: OpenRouter returns finish_reason 'length' with content null."""
    manager = _manager(
        "openrouter", _FakeResponse(content=None, finish_reason="length")
    )

    response = manager.request(prompt="Return JSON.", model="z-ai/glm-5.2")

    assert response.content is None
    assert "finish_reason=length" in response.status_message


def test_empty_content_status_is_compact_and_names_usage() -> None:
    manager = _manager(
        "deepseek",
        _FakeResponse(
            content="",
            finish_reason="length",
            reasoning_content="x" * 2001,
            usage={"completion_tokens": 2048},
        ),
    )

    response = manager.request(prompt="Return JSON.", model="deepseek-v4-flash")

    assert response.content is None
    assert "finish_reason=length" in response.status_message
    assert "completion_tokens" in response.status_message
    assert len(response.status_message) < 500


def test_missing_choices_is_reported_not_raised() -> None:
    manager = _manager("nvidia", _FakeResponse(payload={"detail": "nope"}, text="nope"))

    response = manager.request(prompt="hi", model="m")

    assert response.content is None
    assert "choices" in response.status_message


def test_empty_choices_list_is_reported_not_raised() -> None:
    manager = _manager("openrouter", _FakeResponse(payload={"choices": []}, text="{}"))

    response = manager.request(prompt="hi", model="m")

    assert response.content is None
    assert "choices" in response.status_message


def test_non_object_json_body_is_reported_not_raised() -> None:
    manager = _manager("openrouter", _FakeResponse(payload=["unexpected"], text="[]"))

    response = manager.request(prompt="hi", model="m")

    assert response.content is None
    assert "non-object" in response.status_message


# --------------------------------------------------------------------------
# error detail — fixtures are the real bodies captured on 2026-08-25
# --------------------------------------------------------------------------


def _http_error(status_code: int, body: str, reason: str = "") -> requests.HTTPError:
    response = requests.Response()
    response.status_code = status_code
    response.reason = reason
    response._content = body.encode("utf-8")
    return requests.HTTPError(response=response)


def test_error_detail_zai_overload_code() -> None:
    exc = _http_error(
        429,
        '{"error":{"code":"1305","message":"The service may be temporarily '
        'overloaded, please try again later"}}',
    )
    assert _error_detail(exc) == (
        "HTTP 429: [1305] The service may be temporarily overloaded, "
        "please try again later"
    )


def test_error_detail_openrouter_integer_code() -> None:
    exc = _http_error(
        400, '{"error":{"message":"nope-xyz is not a valid model ID","code":400}}'
    )
    assert _error_detail(exc) == "HTTP 400: [400] nope-xyz is not a valid model ID"


def test_error_detail_deepseek_names_the_supported_models() -> None:
    """The defect this refactor fixes: the old DeepSeek path threw this away."""
    exc = _http_error(
        400,
        '{"error":{"message":"The supported API model names are deepseek-v4-pro, '
        'deepseek-v4-flash.","type":"invalid_request_error","param":null,'
        '"code":"invalid_request_error"}}',
    )
    detail = _error_detail(exc)
    assert "The supported API model names are" in detail
    assert "invalid_request_error" in detail
    assert "returned None" not in detail


def test_error_detail_nvidia_rfc7807_body() -> None:
    """NVIDIA has no 'error' key at all; it answers with RFC 7807 problem+json."""
    exc = _http_error(
        410,
        '{"type":"about:blank","title":"Gone","status":410,'
        '"detail":"The model \'z-ai/glm-5.1\' has reached its end of life."}',
    )
    assert _error_detail(exc) == (
        "HTTP 410: The model 'z-ai/glm-5.1' has reached its end of life."
    )


def test_error_detail_nvidia_rfc7807_falls_back_to_title() -> None:
    exc = _http_error(410, '{"type":"about:blank","title":"Gone","status":410}')
    assert _error_detail(exc) == "HTTP 410: Gone"


def test_error_detail_plain_text_body() -> None:
    """NVIDIA answers a bad model with plain text, not JSON."""
    exc = _http_error(404, "404 page not found\n")
    assert _error_detail(exc) == "HTTP 404: 404 page not found"


def test_error_detail_empty_body_uses_status_and_reason() -> None:
    exc = _http_error(502, "", reason="Bad Gateway")
    assert _error_detail(exc) == "HTTP 502 Bad Gateway"


def test_error_detail_no_response_uses_exception_text() -> None:
    assert _error_detail(requests.ConnectionError("connection refused")) == (
        "connection refused"
    )


def test_failed_post_surfaces_the_detail_never_a_placeholder() -> None:
    """Regression guard for the DeepSeek defect: the API's message must reach the caller."""

    class _FailingManager(OpenAiCompatManager):
        def __init__(self) -> None:
            self.provider_name = "deepseek"
            self.spec = PROVIDER_SPECS["deepseek"]
            self.api_key = "test"
            self.api_key_name = "deepseek"
            self.headers: dict[str, str] = {}

        def _post_request(
            self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
        ) -> tuple[requests.Response | None, str | None]:
            return None, _error_detail(
                _http_error(
                    400,
                    '{"error":{"message":"The supported API model names are '
                    'deepseek-v4-pro, deepseek-v4-flash.","code":'
                    '"invalid_request_error"}}',
                )
            )

    response = _FailingManager().request(prompt="hi", model="nope")

    assert response.content is None
    assert "The supported API model names are" in response.status_message
    assert response.status_message != "post_request returned None"


# --------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------


def test_unconfigured_provider_returns_error_not_raise() -> None:
    manager = OpenAiCompatManager("zai", api_key_name="nonexistent_key_name")

    response = manager.request(prompt="hi", model="glm-5-turbo")

    assert response.content is None
    assert "not configured" in response.status_message


def test_unknown_provider_name_raises() -> None:
    with pytest.raises(ValueError, match="Unknown OpenAI-compatible provider"):
        OpenAiCompatManager("not-a-provider")


def test_every_spec_has_a_key_name_and_chat_url() -> None:
    for name, spec in PROVIDER_SPECS.items():
        assert spec.api_key_name, name
        assert spec.chat_url.startswith("https://"), name


def test_balance_only_offered_where_the_spec_has_an_endpoint() -> None:
    assert PROVIDER_SPECS["deepseek"].balance_url is not None
    assert PROVIDER_SPECS["zai"].balance_url is None
    assert _manager("zai").balance()["error"].endswith("no balance endpoint")


# --------------------------------------------------------------------------
# transport — exercises _post_request itself, the code the SDK swap replaced
# --------------------------------------------------------------------------


class _StubHttpResponse(requests.Response):
    def __init__(self, status_code: int = 200, body: str = "{}") -> None:
        super().__init__()
        self.status_code = status_code
        self._content = body.encode("utf-8")


def _live_manager(provider: str, max_retries: int = 0) -> OpenAiCompatManager:
    manager = OpenAiCompatManager.__new__(OpenAiCompatManager)
    manager.provider_name = provider
    manager.spec = PROVIDER_SPECS[provider]
    manager.api_key = "test-key"
    manager.api_key_name = provider
    manager.max_retries = max_retries
    manager.headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Bearer test-key",
    }
    return manager


def test_post_request_serialises_payload_and_passes_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    def fake_post(url: str, **kwargs: Any) -> requests.Response:
        seen["url"] = url
        seen.update(kwargs)
        return _StubHttpResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    manager = _live_manager("zai")

    response, error = manager._post_request(
        manager.spec.chat_url, {"model": "m", "messages": []}, timeout=12.5
    )

    assert error is None
    assert response is not None
    assert seen["url"] == PROVIDER_SPECS["zai"].chat_url
    assert seen["timeout"] == 12.5
    assert seen["headers"]["Authorization"] == "Bearer test-key"
    assert json.loads(seen["data"]) == {"model": "m", "messages": []}


def test_post_request_does_not_retry_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AIManager wants an immediate fall through to the next model in its chain."""
    calls: list[int] = []

    def fake_post(url: str, **kwargs: Any) -> requests.Response:
        calls.append(1)
        return _StubHttpResponse(status_code=503, body="upstream down")

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    response, error = _live_manager("zai")._post_request(
        PROVIDER_SPECS["zai"].chat_url, {}
    )

    assert response is None
    assert len(calls) == 1
    assert error is not None and "503" in error


def test_post_request_retries_transient_failures_when_asked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """extract_cone has no fallback chain; one 429 must not end a whole batch."""
    calls: list[int] = []
    slept: list[float] = []

    def fake_post(url: str, **kwargs: Any) -> requests.Response:
        calls.append(1)
        if len(calls) < 3:
            return _StubHttpResponse(status_code=429, body="rate limited")
        return _StubHttpResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(s))

    response, error = _live_manager("openrouter", max_retries=2)._post_request(
        PROVIDER_SPECS["openrouter"].chat_url, {}
    )

    assert error is None
    assert response is not None
    assert len(calls) == 3
    assert slept == [0.5, 1.0]


def test_post_request_does_not_retry_a_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bad model name will never succeed; burning retries on it is pure delay."""
    calls: list[int] = []

    def fake_post(url: str, **kwargs: Any) -> requests.Response:
        calls.append(1)
        return _StubHttpResponse(
            status_code=400, body='{"error":{"message":"bad model"}}'
        )

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    response, error = _live_manager("openrouter", max_retries=2)._post_request(
        PROVIDER_SPECS["openrouter"].chat_url, {}
    )

    assert response is None
    assert len(calls) == 1
    assert error is not None and "bad model" in error


def test_connection_error_is_treated_as_transient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def fake_post(url: str, **kwargs: Any) -> requests.Response:
        calls.append(1)
        if len(calls) < 2:
            raise requests.exceptions.ConnectionError("connection refused")
        return _StubHttpResponse()

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(time, "sleep", lambda _s: None)

    response, _ = _live_manager("nvidia", max_retries=2)._post_request(
        PROVIDER_SPECS["nvidia"].chat_url, {}
    )

    assert response is not None
    assert len(calls) == 2


def test_provider_extras_are_not_shared_between_requests() -> None:
    """The spec table is module-level; a request must not be able to mutate it."""
    manager = _manager("zai")

    manager.request(prompt="hi", model="m")
    first = manager.captured_payload
    assert first is not None
    first["thinking"]["type"] = "mutated"

    manager.request(prompt="hi", model="m")

    assert manager.captured_payload is not None
    assert manager.captured_payload["thinking"] == {"type": "disabled"}
    assert PROVIDER_SPECS["zai"].extra_payload["thinking"] == {"type": "disabled"}


def test_http_200_error_object_without_choices_surfaces_the_message() -> None:
    """OpenRouter answers 200 with an error object and no choices; say what it said."""
    manager = _manager(
        "openrouter",
        _FakeResponse(
            payload={"error": {"code": 429, "message": "upstream is rate limited"}},
            text='{"error":{"code":429,"message":"upstream is rate limited"}}',
        ),
    )

    response = manager.request(prompt="hi", model="m")

    assert response.content is None
    assert "upstream is rate limited" in response.status_message
    assert "choices" not in response.status_message


# --------------------------------------------------------------------------
# get_models / balance
# --------------------------------------------------------------------------


def test_get_models_returns_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **k: _StubHttpResponse(
            body='{"data":[{"id":"m-one"},{"id":"m-two"},{"no_id":true}]}'.replace(
                "true", "1"
            )
        ),
    )
    assert _live_manager("zai").get_models() == ["m-one", "m-two"]


def test_get_models_reports_a_decode_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reachable only because transport and decode errors are now caught separately."""
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _StubHttpResponse(body="not json")
    )
    assert _live_manager("zai").get_models() == []


def test_balance_returns_the_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        requests,
        "get",
        lambda *a, **k: _StubHttpResponse(body='{"balance_infos":[{"total":"1"}]}'),
    )
    assert _live_manager("deepseek").balance() == {"balance_infos": [{"total": "1"}]}


def test_balance_rejects_a_non_object_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        requests, "get", lambda *a, **k: _StubHttpResponse(body="[1, 2]")
    )
    assert "Unexpected balance payload" in _live_manager("deepseek").balance()["error"]
