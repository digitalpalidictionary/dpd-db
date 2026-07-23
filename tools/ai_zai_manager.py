"""Send AI requests to the Z.ai GLM coding-plan API (OpenAI-compatible endpoint) and list available models. Used by tools/ai_manager.py as the 'zai' provider."""

import json
from typing import Any

import requests

from tools.ai_manager import AIResponse
from tools.configger import config_read
from tools.printer import printer as pr

DEFAULT_API_KEY_NAME = "zai"

ZAI_CHAT = "https://api.z.ai/api/coding/paas/v4/chat/completions"
ZAI_CHAT_MODELS = "https://api.z.ai/api/coding/paas/v4/models"
DISABLED_THINKING_MODE = {"type": "disabled"}
DEFAULT_MAX_TOKENS = 8192


def _error_detail(exc: requests.exceptions.RequestException) -> str:
    """Build a human-useful message from a failed Z.ai request.

    On an HTTP error the useful part (e.g. code 1305 "service temporarily
    overloaded") lives in the JSON body, which the bare exception string drops.
    Pull the status code plus error.code/error.message out of the response
    when present, falling back to the raw body, then to the exception text.
    """
    response = exc.response
    if response is None:
        return str(exc)

    error: dict[str, Any] = {}
    try:
        parsed = response.json()
        if isinstance(parsed, dict) and isinstance(parsed.get("error"), dict):
            error = parsed["error"]
    except ValueError:
        pass

    message = error.get("message")
    if message:
        code = error.get("code")
        prefix = f"[{code}] " if code else ""
        return f"HTTP {response.status_code}: {prefix}{message}"

    body = response.text.strip()
    if body:
        return f"HTTP {response.status_code}: {body[:300]}"
    return f"HTTP {response.status_code} {response.reason}"


class ZaiManager:
    def __init__(self, api_key_name: str = DEFAULT_API_KEY_NAME) -> None:
        api_key = config_read("apis", api_key_name)
        if not api_key:
            pr.amber(f"Z.ai API key '{api_key_name}' not found in config.ini")
            self.api_key = None
            self.api_key_name = api_key_name
            return
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.api_key_name = api_key_name

    def _post_request(
        self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
    ) -> tuple[requests.Response | None, str | None]:
        """Returns (response, error_detail). On failure response is None and
        error_detail carries the useful message from the response body."""
        if not self.api_key:
            pr.amber("ZaiManager not configured (no API key).")
            return None, "not configured (no API key)"
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
            pr.red(f"Z.ai API request failed: {detail}")
            return None, detail

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
            msg = f"ZaiManager not configured (no API key '{self.api_key_name}')."
            pr.amber(msg)
            return AIResponse(content=None, status_message=msg)

        messages = []
        if prompt_sys:
            messages.append({"role": "system", "content": prompt_sys})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "thinking": dict(DISABLED_THINKING_MODE),
            "stream": False,
            "messages": messages,
        }
        payload.update(kwargs)

        response, error = self._post_request(ZAI_CHAT, payload, timeout=timeout)

        if response is None:
            return AIResponse(
                content=None,
                status_message=error or "request failed",
            )

        try:
            response_json = response.json()
            choice = response_json.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content")
            finish_reason = choice.get("finish_reason")
            if content:
                if finish_reason and finish_reason != "stop":
                    status_message = (
                        f"{response.status_code} "
                        f"(finish_reason={finish_reason}, model={model})"
                    )
                else:
                    status_message = str(response.status_code)
                return AIResponse(content=content, status_message=status_message)
            else:
                return AIResponse(
                    content=None,
                    status_message=f"empty content (finish_reason={finish_reason})",
                )
        except json.JSONDecodeError as e:
            error_msg = f"Z.ai JSON decode error with {model}.\n{e}.\nResponse text: {response.text}"
            pr.red(error_msg)
            return AIResponse(content=None, status_message=error_msg)
        except IndexError:
            error_msg = f"'choices' list empty/malformed. Response: {response.text}"
            pr.red(error_msg)
            return AIResponse(content=None, status_message=error_msg)

    def get_models(self) -> list[str]:
        if not self.api_key:
            pr.amber("ZaiManager not configured (no API key).")
            return []
        try:
            response = requests.get(ZAI_CHAT_MODELS, headers=self.headers, timeout=10)
            response.raise_for_status()
            r = response.json()
            models: list[str] = [i.get("id") for i in r.get("data", []) if i.get("id")]
            return models
        except requests.exceptions.RequestException as e:
            pr.red(f"Z.ai Get Models Error: {_error_detail(e)}")
            return []
        except json.JSONDecodeError as e:
            pr.red(f"Z.ai Get Models JSON decode error: {e}")
            return []


if __name__ == "__main__":
    zai = ZaiManager()
    if zai.api_key:
        models = zai.get_models()
        pr.green(f"Available Models: {models}")

        ai_response = zai.request(
            model="glm-5-turbo",
            prompt="Explain the theory of relativity simply.",
            prompt_sys="You are Albert Einstein.",
        )
        pr.green(f"Z.ai request status: {ai_response.status_message}")
        pr.green(f"Response:\n{ai_response.content if ai_response.content else 'None'}")
