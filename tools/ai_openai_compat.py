"""Send AI requests to any OpenAI-compatible chat/completions endpoint (OpenRouter, NVIDIA, DeepSeek, Z.ai). Used by tools/ai_manager.py as those four providers."""

import copy
import json
import time
from dataclasses import dataclass, field
from typing import Any, cast

import requests

from tools.ai_manager import AIResponse
from tools.configger import config_read
from tools.printer import printer as pr

MAX_ERROR_DETAIL_CHARS = 300
DISABLED_THINKING_MODE = {"type": "disabled"}
DEFAULT_MAX_TOKENS = 8192

# Retried only for callers that ask; AIManager wants an immediate fall through to
# the next model in its chain, and a bulk job must not sit on an overloaded provider.
TRANSIENT_STATUS_CODES = frozenset({408, 409, 429, 500, 502, 503, 504})
RETRY_BACKOFF_SECONDS = 0.5


@dataclass(frozen=True)
class ProviderSpec:
    """Everything that distinguishes one OpenAI-compatible provider from another."""

    api_key_name: str
    chat_url: str
    models_url: str | None = None
    balance_url: str | None = None
    extra_payload: dict[str, Any] = field(default_factory=dict)


PROVIDER_SPECS: dict[str, ProviderSpec] = {
    "openrouter": ProviderSpec(
        api_key_name="openrouter",
        chat_url="https://openrouter.ai/api/v1/chat/completions",
        models_url="https://openrouter.ai/api/v1/models",
    ),
    "nvidia": ProviderSpec(
        api_key_name="nvidia",
        chat_url="https://integrate.api.nvidia.com/v1/chat/completions",
        models_url="https://integrate.api.nvidia.com/v1/models",
    ),
    "deepseek": ProviderSpec(
        api_key_name="deepseek",
        chat_url="https://api.deepseek.com/chat/completions",
        models_url="https://api.deepseek.com/models",
        balance_url="https://api.deepseek.com/user/balance",
        extra_payload={
            "max_tokens": DEFAULT_MAX_TOKENS,
            "thinking": dict(DISABLED_THINKING_MODE),
            "presence_penalty": 0,
            "temperature": 1,
            "top_p": 1,
            "logprobs": False,
        },
    ),
    "zai": ProviderSpec(
        api_key_name="zai",
        chat_url="https://api.z.ai/api/coding/paas/v4/chat/completions",
        models_url="https://api.z.ai/api/coding/paas/v4/models",
        extra_payload={
            "max_tokens": DEFAULT_MAX_TOKENS,
            "thinking": dict(DISABLED_THINKING_MODE),
        },
    ),
}


def _truncate_error_detail(value: Any) -> str:
    text = str(value)
    if len(text) <= MAX_ERROR_DETAIL_CHARS:
        return text
    return f"{text[:MAX_ERROR_DETAIL_CHARS]}..."


def _nested_error_message(body: Any) -> str | None:
    """Read the ``{"error": {"code": ..., "message": ...}}`` shape three of the four
    providers use. ``code`` is an int on OpenRouter and a string on DeepSeek/Z.ai."""
    if not isinstance(body, dict):
        return None
    error = cast(dict[str, Any], body).get("error")
    if not isinstance(error, dict):
        return None
    error_dict = cast(dict[str, Any], error)
    message = error_dict.get("message")
    if not message:
        return None
    code = error_dict.get("code")
    prefix = f"[{code}] " if code else ""
    return f"{prefix}{message}"


def _is_transient(exc: requests.exceptions.RequestException) -> bool:
    response = exc.response
    if response is None:
        return isinstance(
            exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)
        )
    return response.status_code in TRANSIENT_STATUS_CODES


def _error_detail(exc: requests.exceptions.RequestException) -> str:
    """Build a human-useful message from a failed request.

    The four providers report errors three different ways, so each shape needs its
    own branch: OpenRouter/DeepSeek/Z.ai nest ``error.message`` (with ``code`` being
    an int, a string, or absent); NVIDIA returns RFC 7807 ``{type,title,status,detail}``
    with no ``error`` key at all, and answers a bad model with plain text rather than
    JSON. The bare exception string drops all of it.
    """
    response = exc.response
    if response is None:
        return str(exc)

    parsed: Any = None
    try:
        parsed = response.json()
    except ValueError:
        parsed = None

    nested = _nested_error_message(parsed)
    if nested:
        return f"HTTP {response.status_code}: {nested}"

    if isinstance(parsed, dict):
        parsed_dict = cast(dict[str, Any], parsed)
        detail = parsed_dict.get("detail") or parsed_dict.get("title")
        if isinstance(detail, str) and detail:
            return f"HTTP {response.status_code}: {detail}"

    body = response.text.strip()
    if body:
        return f"HTTP {response.status_code}: {body[:MAX_ERROR_DETAIL_CHARS]}"
    return f"HTTP {response.status_code} {response.reason}"


def _format_empty_content_status(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    choice: dict[str, Any] = {}
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        choice = cast(dict[str, Any], choices[0])

    message: dict[str, Any] = {}
    message_raw = choice.get("message")
    if isinstance(message_raw, dict):
        message = cast(dict[str, Any], message_raw)

    finish_reason = choice.get("finish_reason")
    usage = _truncate_error_detail(response_json.get("usage"))
    status = f"empty content (finish_reason={finish_reason}, usage={usage})"

    detail_value = message.get("content") or message.get("reasoning_content")
    if detail_value:
        detail = _truncate_error_detail(detail_value)
        return f"{status}; detail={detail}"
    return status


class OpenAiCompatManager:
    def __init__(
        self,
        provider_name: str,
        api_key_name: str | None = None,
        max_retries: int = 0,
    ) -> None:
        spec = PROVIDER_SPECS.get(provider_name)
        if spec is None:
            raise ValueError(
                f"Unknown OpenAI-compatible provider '{provider_name}'. "
                f"Known: {', '.join(sorted(PROVIDER_SPECS))}."
            )
        self.provider_name = provider_name
        self.spec = spec
        self.max_retries = max_retries
        self.api_key_name = api_key_name or spec.api_key_name
        self.api_key = config_read("apis", self.api_key_name)
        self.headers: dict[str, str] = {}
        if not self.api_key:
            pr.amber(
                f"{provider_name} API key '{self.api_key_name}' not found in config.ini"
            )
            return
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _post_request(
        self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
    ) -> tuple[requests.Response | None, str | None]:
        """Returns (response, error_detail). On failure response is None and
        error_detail carries the useful message from the response body."""
        if not self.api_key:
            pr.amber(f"{self.provider_name} not configured (no API key).")
            return None, "not configured (no API key)"
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    api_url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=timeout,
                )
                response.raise_for_status()
                return response, None
            except requests.exceptions.RequestException as e:
                detail = _error_detail(e)
                if attempt < self.max_retries and _is_transient(e):
                    backoff = RETRY_BACKOFF_SECONDS * (2**attempt)
                    pr.amber(
                        f"{self.provider_name} transient failure ({detail}); "
                        f"retrying in {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                    continue
                pr.red(f"{self.provider_name} API request failed: {detail}")
                return None, detail

        return None, "request failed"

    def request(
        self,
        prompt: str,
        model: str,
        prompt_sys: str | None = None,
        timeout: float = 60.0,
        grounding: bool = False,
        **kwargs,
    ) -> AIResponse:
        if not self.api_key:
            msg = (
                f"{self.provider_name} not configured "
                f"(no API key '{self.api_key_name}')."
            )
            pr.amber(msg)
            return AIResponse(content=None, status_message=msg)

        messages: list[dict[str, str]] = []
        if prompt_sys:
            messages.append({"role": "system", "content": prompt_sys})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {"model": model, "stream": False}
        payload.update(copy.deepcopy(self.spec.extra_payload))
        payload["messages"] = messages
        payload.update(kwargs)

        response, error = self._post_request(
            self.spec.chat_url, payload, timeout=timeout
        )
        if response is None:
            return AIResponse(content=None, status_message=error or "request failed")

        return self._parse_chat_response(response, model)

    def _parse_chat_response(
        self, response: requests.Response, model: str
    ) -> AIResponse:
        try:
            response_json = response.json()
        except ValueError as e:
            error_msg = (
                f"{self.provider_name} JSON decode error with {model}.\n{e}.\n"
                f"Response text: {response.text}"
            )
            pr.red(error_msg)
            return AIResponse(content=None, status_message=error_msg)

        if not isinstance(response_json, dict):
            error_msg = (
                f"{self.provider_name} returned a non-object response with {model}: "
                f"{_truncate_error_detail(response_json)}"
            )
            pr.red(error_msg)
            return AIResponse(content=None, status_message=error_msg)

        response_dict = cast(dict[str, Any], response_json)
        choices = response_dict.get("choices")
        if not isinstance(choices, list) or not choices:
            # OpenRouter can answer HTTP 200 with an error object and no choices at
            # all; that message is far more useful than a slice of the raw body.
            nested = _nested_error_message(response_dict)
            error_msg = nested or (
                f"'choices' list empty/malformed. "
                f"Response: {_truncate_error_detail(response.text)}"
            )
            pr.red(error_msg)
            return AIResponse(content=None, status_message=error_msg)

        choice_raw = cast(list[Any], choices)[0]
        choice: dict[str, Any] = (
            cast(dict[str, Any], choice_raw) if isinstance(choice_raw, dict) else {}
        )
        message_raw = choice.get("message")
        message: dict[str, Any] = (
            cast(dict[str, Any], message_raw) if isinstance(message_raw, dict) else {}
        )

        content = message.get("content")
        finish_reason = choice.get("finish_reason")

        if content:
            if finish_reason and finish_reason != "stop":
                return AIResponse(
                    content=content,
                    status_message=f"finish_reason={finish_reason} (model={model})",
                )
            return AIResponse(content=content, status_message="Success")

        return AIResponse(
            content=None, status_message=_format_empty_content_status(response_dict)
        )

    def get_models(self) -> list[str]:
        if not self.spec.models_url:
            pr.amber(f"{self.provider_name} has no models endpoint.")
            return []
        if not self.api_key:
            pr.amber(f"{self.provider_name} not configured (no API key).")
            return []
        try:
            response = requests.get(
                self.spec.models_url, headers=self.headers, timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            pr.red(f"{self.provider_name} Get Models Error: {_error_detail(e)}")
            return []

        try:
            payload = response.json()
        except ValueError as e:
            pr.red(f"{self.provider_name} Get Models JSON decode error: {e}")
            return []

        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list):
            return []
        return [
            entry["id"]
            for entry in cast(list[Any], data)
            if isinstance(entry, dict) and entry.get("id")
        ]

    def balance(self) -> dict[str, Any]:
        if not self.spec.balance_url:
            return {"error": f"{self.provider_name} has no balance endpoint"}
        if not self.api_key:
            return {"error": "API key not configured"}
        try:
            response = requests.get(
                self.spec.balance_url, headers=self.headers, timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            detail = _error_detail(e)
            pr.red(f"{self.provider_name} Balance Error: {detail}")
            return {"error": f"Request failed: {detail}"}

        try:
            payload = response.json()
        except ValueError as e:
            pr.red(f"{self.provider_name} Balance JSON decode error: {e}")
            return {"error": f"Invalid JSON: {e}"}

        if not isinstance(payload, dict):
            return {
                "error": f"Unexpected balance payload: {_truncate_error_detail(payload)}"
            }
        return cast(dict[str, Any], payload)


if __name__ == "__main__":
    import sys

    provider = sys.argv[1] if len(sys.argv) > 1 else "zai"
    model = sys.argv[2] if len(sys.argv) > 2 else ""

    manager = OpenAiCompatManager(provider)
    if not manager.api_key:
        pr.red(f"{provider} not configured.")
        raise SystemExit(1)

    if manager.spec.balance_url:
        pr.green(f"Balance: {manager.balance()}")

    models = manager.get_models()
    pr.green(f"Available models ({len(models)}): {models[:20]}")

    if model:
        ai_response = manager.request(
            prompt="Explain the theory of relativity simply.",
            prompt_sys="Be brief.",
            model=model,
        )
        pr.green(f"Status: {ai_response.status_message}")
        pr.green(f"Response:\n{ai_response.content}")
