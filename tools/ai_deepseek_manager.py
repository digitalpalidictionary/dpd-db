from typing import Optional
import json
import requests
from rich import print
from tools.printer import printer as pr

from tools.configger import config_read

DEFAULT_USER_PROMPT = "Hi"

DEFAULT_API_KEY_NAME = "deepseek"

DS_BALANCE = "https://api.deepseek.com/user/balance"
DS_CHAT = "https://api.deepseek.com/chat/completions"
DS_CHAT_FIN = "https://api.deepseek.com/beta/completions"
DS_CHAT_MODELS = "https://api.deepseek.com/models"


class DeepseekManager:
    def __init__(self, api_key_name=DEFAULT_API_KEY_NAME):
        api_key = config_read("apis", api_key_name)
        if api_key is None:
            pr.warning(f"DeepSeek API key '{api_key_name}' not found in config.ini")
            self.api_key = None
            return
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def balance(self):
        if not self.api_key:  # Added check
            return {"error": "API key not configured"}
        try:  # Added try/except for robustness
            response = requests.get(
                DS_BALANCE, headers=self.headers, timeout=10
            )  # Added timeout
            response.raise_for_status()  # Check for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            pr.error(f"DeepSeek Balance Error: {e}")
            return {"error": f"Request failed: {e}"}

    def _post_request(self, api_url, payload, stream):
        if not self.api_key:
            pr.warning("DeepSeekManager not configured (no API key).")
            return None
        try:
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(payload),
                stream=stream,
                timeout=60,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            pr.error(f"DeepSeek API request failed: {e}")
            return None

    def completion_impl(self, response, type_="chat"):
        try:
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        line = line[6:].strip()
                    if not line or line == "[DONE]":
                        break
                    decoded_line = json.loads(line)
                    if "choices" in decoded_line:
                        finish_reason = decoded_line["choices"][0].get("finish_reason")
                        if type_ == "chat":
                            delta_content = (
                                decoded_line["choices"][0]
                                .get("delta", {})
                                .get("content")
                            )
                        elif type_ == "fim":
                            delta_content = decoded_line["choices"][0].get("text")
                        if delta_content:
                            yield delta_content
                        if finish_reason == "stop":
                            break
        except requests.exceptions.ChunkedEncodingError as e:
            pr.error(f"DeepSeek stream error: {e}")
            # Decide how to handle stream errors, maybe yield an error message or just stop
            yield "[STREAM ERROR]"
        except json.JSONDecodeError as e:
            pr.error(f"DeepSeek stream JSON decode error: {e}")
            yield "[STREAM JSON ERROR]"
        except Exception as e:
            pr.error(f"Unexpected error in DeepSeek stream: {e}")
            yield "[UNEXPECTED STREAM ERROR]"

    def request(
        self,
        prompt: str,
        model: str,
        prompt_sys: Optional[str] = None,
        stream: bool = False,
        timeout: float = 60.0,
        **kwargs,
    ) -> Optional[str]:
        if not self.api_key:
            pr.warning("DeepSeekManager not configured (no API key).")
            return None

        balance_info = self.balance()
        balance_before = (
            float(balance_info.get("balance_infos", [{}])[0].get("total_balance", 0))
            if "error" not in balance_info
            else 0
        )

        # Use the default model if None is passed
        current_model = model if model is not None else "deepseek-chat"

        payload = {
            "model": current_model,  # Use the potentially defaulted model
            "max_tokens": 2048,
            "presence_penalty": 0,
            "stream": stream,
            "temperature": 1,
            "top_p": 1,
            "logprobs": False,
            "messages": [
                {"content": prompt_sys, "role": "system"},
                {"content": prompt, "role": "user"},
            ]
            if isinstance(prompt, str)
            else prompt,
        }
        payload.update(kwargs)

        # Conditionally add stream_options only if stream is True
        if stream:
            payload["stream_options"] = {
                "include_usage": True
            }  # Example, adjust if needed

        response = self._post_request(DS_CHAT, payload, stream)
        if response is None:
            return None

        balance_info_after = self.balance()
        balance_after = (
            float(
                balance_info_after.get("balance_infos", [{}])[0].get("total_balance", 0)
            )
            if "error" not in balance_info_after
            else 0
        )
        cost = balance_before - balance_after
        pr.info(f"DeepSeek Cost: {cost:.6f}")

        if stream:
            # Note: Streaming implementation doesn't easily fit returning None on error mid-stream
            # The generator handles errors internally by yielding error messages or stopping
            return self.completion_impl(response, "chat")
        else:
            try:
                response_json = response.json()
                return (
                    response_json.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
                )
            except json.JSONDecodeError as e:
                pr.error(f"DeepSeek JSON decode error: {e}")
                pr.error(f"Response text: {response.text}")
                return None
            except IndexError:
                pr.error(
                    "DeepSeek response format error: 'choices' list is empty or malformed."
                )
                pr.error(f"Response JSON: {response_json}")
                return None

    def fim_completion(
        self,
        prompt=DEFAULT_USER_PROMPT,
        stream=False,
        model="deepseek-chat",
        **kwargs,
    ):
        if not self.api_key:
            pr.warning("DeepSeekManager not configured (no API key).")
            return None

        payload = {
            "model": model,
            "prompt": prompt,
            "echo": False,
            "frequency_penalty": 0,
            "logprobs": 0,
            "max_tokens": 1024,
            "presence_penalty": 0,
            "stop": None,
            "stream": stream,
            "stream_options": None,
            "suffix": None,
            "temperature": 1,
            "top_p": 1,
        }

        payload.update(kwargs)
        response = self._post_request(DS_CHAT_FIN, payload, stream)
        if response is None:
            return None

        if stream:
            return self.completion_impl(response, "fim")
        else:
            try:
                response_json = response.json()
                return response_json.get("choices", [{}])[0].get("text")
            except json.JSONDecodeError as e:
                pr.error(f"DeepSeek FIM JSON decode error: {e}")
                pr.error(f"Response text: {response.text}")
                return None
            except IndexError:
                pr.error(
                    "DeepSeek FIM response format error: 'choices' list is empty or malformed."
                )
                pr.error(f"Response JSON: {response_json}")
                return None

    def get_models(self):
        if not self.api_key:
            pr.warning("DeepSeekManager not configured (no API key).")
            return []
        try:
            response = requests.get(DS_CHAT_MODELS, headers=self.headers, timeout=10)
            response.raise_for_status()
            r = response.json()
            models = [i.get("id") for i in r.get("data", []) if i.get("id")]
            return models
        except requests.exceptions.RequestException as e:
            pr.error(f"DeepSeek Get Models Error: {e}")
            return []
        except json.JSONDecodeError as e:
            pr.error(f"DeepSeek Get Models JSON decode error: {e}")
            return []


if __name__ == "__main__":
    try:
        ds = DeepseekManager()
        if ds.api_key:
            balance = ds.balance()
            pr.info(f"Balance Info: {balance}")
            models = ds.get_models()
            pr.info(f"Available Models: {models}")

            if models:
                pr.info("\n--- Testing Non-Streaming Request ---")
                response = ds.request(
                    model="deepseek-chat",
                    prompt="Explain the theory of relativity simply.",
                    prompt_sys="You are Albert Einstein.",
                )
                if response:
                    pr.info(f"Response:\n{response}")
                else:
                    pr.error("Request failed or returned None.")

            else:
                pr.warning("No models found, skipping request tests.")
        else:
            pr.warning(
                "DeepseekManager could not be initialized (likely missing API key)."
            )

    except Exception as e:
        pr.error(f"An error occurred during testing: {e}")
