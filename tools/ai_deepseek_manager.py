import json
from typing import Any

import requests

from tools.configger import config_read
from tools.printer import printer as pr
from tools.ai_manager import AIResponse


DEFAULT_API_KEY_NAME = "deepseek"

DS_BALANCE = "https://api.deepseek.com/user/balance"
DS_CHAT = "https://api.deepseek.com/chat/completions"
DS_CHAT_MODELS = "https://api.deepseek.com/models"


class DeepseekManager:
    def __init__(self, api_key_name: str = DEFAULT_API_KEY_NAME) -> None:
        api_key = config_read("apis", api_key_name)
        if not api_key:
            pr.warning(f"DeepSeek API key '{api_key_name}' not found in config.ini")
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
            pr.error(f"DeepSeek Balance Error: {e}")
            return {"error": f"Request failed: {e}"}

    def _post_request(
        self, api_url: str, payload: dict[str, Any], timeout: float = 60.0
    ) -> requests.Response | None:
        if not self.api_key:
            pr.warning("DeepSeekManager not configured (no API key).")
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
            pr.error(f"DeepSeek API request failed: {e}")
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
            pr.warning(msg)
            return AIResponse(content=None, status_message=msg)

        balance_info = self.balance()
        balance_before = (
            float(balance_info.get("balance_infos", [{}])[0].get("total_balance", 0))
            if "error" not in balance_info
            else 0
        )

        current_model = model if model is not None else "deepseek-chat"

        messages = []
        if prompt_sys:
            messages.append({"role": "system", "content": prompt_sys})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": current_model,  # Use the potentially defaulted model
            "max_tokens": 2048,
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
            content = (
                response_json.get("choices", [{}])[0].get("message", {}).get("content")
            )
            if content:
                return AIResponse(
                    content=content,
                    status_message=str(response.status_code),
                )
            else:
                return AIResponse(
                    content=None,
                    status_message=f"{response_json}",
                )
        except json.JSONDecodeError as e:
            error_msg = f"DeepSeek JSON decode error with {current_model}.\n{e}.\nResponse text: {response.text}"
            pr.error(error_msg)
            return AIResponse(content=None, status_message=error_msg)
        except IndexError:
            error_msg = f"'choices' list empty/malformed. Response: {response.json() if response else 'N/A'}"
            pr.error(error_msg)
            return AIResponse(content=None, status_message=error_msg)
        except Exception as e:
            error_msg = f"{e}"
            pr.error(error_msg)
            return AIResponse(content=None, status_message=error_msg)

    def get_models(self) -> list[str]:
        if not self.api_key:
            pr.warning("DeepSeekManager not configured (no API key).")
            return []
        try:
            response = requests.get(DS_CHAT_MODELS, headers=self.headers, timeout=10)
            response.raise_for_status()
            r = response.json()
            models: list[str] = [i.get("id") for i in r.get("data", []) if i.get("id")]
            return models
        except requests.exceptions.RequestException as e:
            pr.error(f"DeepSeek Get Models Error: {e}")
            return []
        except json.JSONDecodeError as e:
            pr.error(f"DeepSeek Get Models JSON decode error: {e}")
            return []


if __name__ == "__main__":
    ds = DeepseekManager()
    if ds.api_key:
        balance = ds.balance()
        pr.info(f"Balance Info: {balance}")

        models = ds.get_models()
        pr.info(f"Available Models: {models}")

        ai_response = ds.request(
            model="deepseek-chat",
            prompt="Explain the theory of relativity simply.",
            prompt_sys="You are Albert Einstein.",
        )
        pr.info(f"DeepSeek request status: {ai_response.status_message}")
        pr.info(f"Response:\n{ai_response.content if ai_response.content else 'None'}")
