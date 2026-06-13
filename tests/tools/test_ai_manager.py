"""Unit tests for AIManager request behavior, focused on the per-request timeout."""

from typing import Any, NamedTuple

import pytest

from tools import ai_manager as ai_manager_module
from tools.ai_manager import AIManager, _load_models_from_json


class _StubResponse(NamedTuple):
    content: str | None
    status_message: str


class _RecordingProvider:
    """Provider stub that records the timeout it was called with."""

    def __init__(self, status_message: str = "stub") -> None:
        self.received_timeout: float | None = None
        self.calls: list[dict[str, Any]] = []
        self.status_message = status_message

    def request(self, **kwargs: Any) -> _StubResponse:
        self.calls.append(dict(kwargs))
        self.received_timeout = kwargs.get("timeout")
        return _StubResponse(content="ok", status_message=self.status_message)


class _FailingProvider:
    """Provider stub that records a failed provider attempt."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def request(self, **kwargs: Any) -> _StubResponse:
        self.calls.append(dict(kwargs))
        return _StubResponse(content=None, status_message="first provider failed")


class _RaisingProvider:
    """Provider stub that raises to exercise AIManager exception reporting."""

    def request(self, **kwargs: Any) -> _StubResponse:
        raise RuntimeError("boom")


def _make_manager(
    provider: _RecordingProvider,
    timeout: float = 150.0,
) -> AIManager:
    """Build an AIManager without running its heavy __init__ provider setup."""
    manager = object.__new__(AIManager)
    manager.providers = {"stub": provider}
    manager.DEFAULT_MODELS = [("stub", "stub-model", 0, timeout)]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}
    return manager


def _make_fallback_manager(
    failing_provider: _FailingProvider,
    success_provider: _RecordingProvider,
) -> AIManager:
    """Build an AIManager with one failing provider before one successful provider."""
    manager = object.__new__(AIManager)
    manager.providers = {"failing": failing_provider, "stub": success_provider}
    manager.DEFAULT_MODELS = [
        ("failing", "failing-model", 0, 150.0),
        ("stub", "stub-model", 0, 150.0),
    ]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}
    return manager


def test_request_passes_150s_timeout_to_provider() -> None:
    provider = _RecordingProvider()
    manager = _make_manager(provider, timeout=150.0)

    response = manager.request(prompt="hi", prompt_sys="sys")

    assert response.content == "ok"
    assert provider.received_timeout == 150.0


def test_request_clean_success_omits_failed_attempt_suffix() -> None:
    provider = _RecordingProvider()
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert response.status_message.startswith("SUCCESS")
    assert "failed attempt" not in response.status_message


def test_request_success_status_names_provider_and_model() -> None:
    provider = _RecordingProvider()
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "stub/stub-model" in response.status_message


def test_request_success_after_failure_includes_failed_attempt_details() -> None:
    failing_provider = _FailingProvider()
    success_provider = _RecordingProvider()
    manager = _make_fallback_manager(failing_provider, success_provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert response.status_message.startswith("SUCCESS")
    assert "after 1 failed attempt(s):" in response.status_message
    assert "failing/failing-model ERROR" in response.status_message
    assert "first provider failed" in response.status_message


def test_request_fallback_success_names_succeeding_provider() -> None:
    manager = _make_fallback_manager(_FailingProvider(), _RecordingProvider())

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "stub/stub-model" in response.status_message
    assert "after 1 failed attempt(s):" in response.status_message


def test_request_drops_bland_success_provider_detail() -> None:
    provider = _RecordingProvider(status_message="Success in 1.00s")
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "(Success" not in response.status_message


def test_request_keeps_informative_success_provider_detail() -> None:
    provider = _RecordingProvider(status_message="model: special-variant")
    manager = _make_manager(provider)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert "(model: special-variant)" in response.status_message


def test_request_all_providers_fail_returns_none_content() -> None:
    failing_provider = _FailingProvider()
    manager = object.__new__(AIManager)
    manager.providers = {"failing": failing_provider}
    manager.DEFAULT_MODELS = [("failing", "failing-model", 0, 150.0)]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}

    response = manager.request(prompt="hi")

    assert response.content is None
    assert "All AI providers failed" in response.status_message


def test_request_provider_exception_is_caught_and_reported() -> None:
    manager = object.__new__(AIManager)
    manager.providers = {"raising": _RaisingProvider()}
    manager.DEFAULT_MODELS = [("raising", "raising-model", 0, 150.0)]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}

    response = manager.request(prompt="hi")

    assert response.content is None
    assert "boom" in response.status_message


def test_request_skips_missing_provider() -> None:
    provider = _RecordingProvider()
    manager = object.__new__(AIManager)
    manager.providers = {"stub": provider}
    manager.DEFAULT_MODELS = [
        ("nonexistent", "m", 0, 150.0),
        ("stub", "stub-model", 0, 150.0),
    ]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert provider.calls[0]["model"] == "stub-model"


def test_request_grounding_uses_grounded_models() -> None:
    provider = _RecordingProvider()
    manager = object.__new__(AIManager)
    manager.providers = {"stub": provider}
    manager.DEFAULT_MODELS = []
    manager.GROUNDED_MODELS = [("stub", "grounded-model", 0, 150.0)]
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}

    response = manager.request(prompt="hi", grounding=True)

    assert response.content == "ok"
    assert "grounded-model" in response.status_message
    assert provider.calls[0]["grounding"] is True


def test_request_forced_model_bypasses_default_chain() -> None:
    failing_provider = _FailingProvider()
    recording_provider = _RecordingProvider()
    manager = object.__new__(AIManager)
    manager.providers = {
        "failing": failing_provider,
        "forced": recording_provider,
    }
    manager.DEFAULT_MODELS = [("failing", "failing-model", 0, 150.0)]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}

    response = manager.request(
        prompt="hi",
        provider_preference="forced",
        model="custom-m",
    )

    assert response.content == "ok"
    assert len(recording_provider.calls) == 1
    assert recording_provider.calls[0]["model"] == "custom-m"
    assert failing_provider.calls == []


def test_request_forced_missing_provider_returns_failure() -> None:
    manager = object.__new__(AIManager)
    manager.providers = {}
    manager.DEFAULT_MODELS = []
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}

    response = manager.request(
        prompt="hi",
        provider_preference="missing",
        model="custom-m",
    )

    assert response.content is None
    assert "All AI providers failed" in response.status_message


def test_request_does_not_sleep_for_unused_fallback_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_provider = _RecordingProvider()
    second_provider = _RecordingProvider()
    third_provider = _RecordingProvider()
    manager = object.__new__(AIManager)
    manager.providers = {
        "first": first_provider,
        "second": second_provider,
        "third": third_provider,
    }
    manager.DEFAULT_MODELS = [
        ("first", "first-model", 10, 150.0),
        ("second", "second-model", 10, 150.0),
        ("third", "third-model", 10, 150.0),
    ]
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    now = ai_manager_module.time.monotonic()
    manager.model_last_request = {
        f"{provider_name}:{model_name}": now
        for provider_name, model_name, _, _ in manager.DEFAULT_MODELS
    }
    sleep_calls: list[float] = []

    def record_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(ai_manager_module.time, "sleep", record_sleep)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert len(sleep_calls) == 1
    assert sleep_calls[0] > 0
    assert len(first_provider.calls) == 1
    assert second_provider.calls == []
    assert third_provider.calls == []


def test_rate_limit_sleep_applies_to_tried_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _RecordingProvider()
    manager = _make_manager(provider)
    manager.DEFAULT_MODELS = [("stub", "stub-model", 10, 150.0)]
    sleep_calls: list[float] = []

    def record_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    monkeypatch.setattr(ai_manager_module.time, "sleep", record_sleep)

    first_response = manager.request(prompt="hi")
    second_response = manager.request(prompt="hi")

    assert first_response.content == "ok"
    assert second_response.content == "ok"
    assert len(sleep_calls) == 1
    assert sleep_calls[0] > 0


def test_antigravity_has_per_model_timeout() -> None:
    """antigravity_cli work models must carry 150s timeouts before DeepSeek."""
    models = _load_models_from_json()
    agy_entries = [m for m in models["default"] if m[0] == "antigravity_cli"]
    assert [m[1] for m in agy_entries] == ["Gemini 3.5 Flash (Low)"]
    assert all(len(m) == 4 for m in agy_entries), (
        "model tuple must be (provider, model, delay, timeout)"
    )
    assert all(m[3] == 150.0 for m in agy_entries)

    first_deepseek_index = next(
        i for i, m in enumerate(models["default"]) if m[0] == "deepseek"
    )
    last_agy_index = max(
        i for i, m in enumerate(models["default"]) if m[0] == "antigravity_cli"
    )
    assert last_agy_index < first_deepseek_index


def test_request_uses_per_model_timeout() -> None:
    """request() must pass the per-model timeout to the provider, not the hardcoded 150s."""
    provider = _RecordingProvider()
    manager = _make_manager(provider, timeout=90.0)

    response = manager.request(prompt="hi")

    assert response.content == "ok"
    assert provider.received_timeout == 90.0


def _make_probe_manager() -> tuple[AIManager, list[bool]]:
    """Build a manager with a spy on _ensure_antigravity_ready."""
    manager = object.__new__(AIManager)
    manager.providers = {}
    manager.DEFAULT_MODELS = []
    manager.GROUNDED_MODELS = []
    manager.last_request_time = 0.0
    manager.min_delay_seconds = 0.0
    manager.model_last_request = {}
    calls: list[bool] = []
    manager._ensure_antigravity_ready = lambda: calls.append(True)  # type: ignore[method-assign]
    return manager, calls


def test_forced_antigravity_waits_for_probe() -> None:
    """A forced antigravity_cli request must wait for the background probe."""
    manager, calls = _make_probe_manager()

    manager.request(
        prompt="hi",
        provider_preference="antigravity_cli",
        model="Gemini 3.5 Flash (Low)",
    )

    assert calls == [True]


def test_forced_antigravity_skips_wait_when_already_registered() -> None:
    """No redundant wait once antigravity_cli is already in providers."""
    manager, calls = _make_probe_manager()
    provider = _RecordingProvider()
    manager.providers = {"antigravity_cli": provider}

    manager.request(
        prompt="hi",
        provider_preference="antigravity_cli",
        model="Gemini 3.5 Flash (Low)",
    )

    assert calls == []


def test_default_chain_does_not_wait_for_antigravity_probe() -> None:
    """The default fallback chain must skip antigravity, never block on the probe."""
    manager, calls = _make_probe_manager()
    provider = _RecordingProvider()
    manager.providers = {"deepseek": provider}
    manager.DEFAULT_MODELS = [
        ("antigravity_cli", "Gemini 3.5 Flash (Low)", 0, 150.0),
        ("deepseek", "deepseek-v4-flash", 0, 150.0),
    ]

    response = manager.request(prompt="hi")

    assert calls == []
    assert response.content == "ok"
