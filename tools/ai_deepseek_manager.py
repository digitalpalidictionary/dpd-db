import json
from typing import Any, cast

import requests

from tools.ai_manager import AIResponse
from tools.configger import config_read
from tools.printer import printer as pr

DEFAULT_API_KEY_NAME = "deepseek"

DS_BALANCE = "https://api.deepseek.com/user/balance"
DS_CHAT = "https://api.deepseek.com/chat/completions"
DS_CHAT_MODELS = "https://api.deepseek.com/models"
DISABLED_THINKING_MODE = {"type": "disabled"}
DEFAULT_MAX_TOKENS = 8192
MAX_ERROR_DETAIL_CHARS = 300


def _truncate_error_detail(value: Any) -> str:
    text = str(value)
    if len(text) <= MAX_ERROR_DETAIL_CHARS:
        return text
    return f"{text[:MAX_ERROR_DETAIL_CHARS]}..."


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


class DeepseekManager:
    def __init__(self, api_key_name: str = DEFAULT_API_KEY_NAME) -> None:
        api_key = config_read("apis", api_key_name)
        if not api_key:
            pr.amber(f"DeepSeek API key '{api_key_name}' not found in config.ini")
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

    def balance(self) -> dict[str, Any]:
        if not self.api_key:
            return {"error": "API key not configured"}
        try:
            response = requests.get(DS_BALANCE, headers=self.headers, timeout=10)
            response.raise_for_status()  # Check for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            pr.red(f"DeepSeek Balance Error: {e}")
            return {"error": f"Request failed: {e}"}

    def _post_request(
        self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
    ) -> requests.Response | None:
        if not self.api_key:
            pr.amber("DeepSeekManager not configured (no API key).")
            return None
        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=timeout,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            pr.red(f"DeepSeek API request failed: {e}")
            return None

    def request(
        self,
        prompt: str,
        model: str,
        prompt_sys: str | None = None,
        timeout: float = 60.0,
        **kwargs,
    ) -> AIResponse:  # Changed return type
        if not self.api_key:
            msg = f"DeepSeekManager not configured (no API key '{self.api_key_name}')."
            pr.amber(msg)
            return AIResponse(content=None, status_message=msg)

        current_model = model if model is not None else "deepseek-chat"

        messages = []
        if prompt_sys:
            messages.append({"role": "system", "content": prompt_sys})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": current_model,  # Use the potentially defaulted model
            "max_tokens": DEFAULT_MAX_TOKENS,
            "thinking": dict(DISABLED_THINKING_MODE),
            "presence_penalty": 0,
            "stream": False,
            "temperature": 1,
            "top_p": 1,
            "logprobs": False,
            "messages": messages,
        }
        payload.update(kwargs)

        response = self._post_request(DS_CHAT, payload, timeout=timeout)

        if response is None:
            return AIResponse(
                content=None,
                status_message="post_request returned None",
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
                        f"(finish_reason={finish_reason}, model={current_model})"
                    )
                else:
                    status_message = str(response.status_code)
                return AIResponse(
                    content=content,
                    status_message=status_message,
                )
            else:
                return AIResponse(
                    content=None,
                    status_message=_format_empty_content_status(response_json),
                )
        except json.JSONDecodeError as e:
            error_msg = f"DeepSeek JSON decode error with {current_model}.\n{e}.\nResponse text: {response.text}"
            pr.red(error_msg)
            return AIResponse(content=None, status_message=error_msg)
        except IndexError:
            error_msg = f"'choices' list empty/malformed. Response: {response.json() if response else 'N/A'}"
            pr.red(error_msg)
            return AIResponse(content=None, status_message=error_msg)

    def get_models(self) -> list[str]:
        if not self.api_key:
            pr.amber("DeepSeekManager not configured (no API key).")
            return []
        try:
            response = requests.get(DS_CHAT_MODELS, headers=self.headers, timeout=10)
            response.raise_for_status()
            r = response.json()
            models: list[str] = [i.get("id") for i in r.get("data", []) if i.get("id")]
            return models
        except requests.exceptions.RequestException as e:
            pr.red(f"DeepSeek Get Models Error: {e}")
            return []
        except json.JSONDecodeError as e:
            pr.red(f"DeepSeek Get Models JSON decode error: {e}")
            return []


if __name__ == "__main__":
    ds = DeepseekManager()
    if ds.api_key:
        balance = ds.balance()
        pr.green(f"Balance Info: {balance}")

        models = ds.get_models()
        pr.green(f"Available Models: {models}")

        ai_response = ds.request(
            model="deepseek-chat",
            prompt="Explain the theory of relativity simply.",
            prompt_sys="You are Albert Einstein.",
        )
        pr.green(f"DeepSeek request status: {ai_response.status_message}")
        pr.green(f"Response:\n{ai_response.content if ai_response.content else 'None'}")
