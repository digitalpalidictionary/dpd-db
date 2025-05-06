from typing import Optional
from openai import OpenAI, APIError
from tools.configger import config_read
from tools.printer import printer as pr

DEFAULT_API_KEY_NAME = "openrouter"


class OpenRouterManager:
    def __init__(self, api_key_name: str = DEFAULT_API_KEY_NAME) -> None:
        self.api_key = config_read("apis", api_key_name)
        if not self.api_key:
            pr.warning(f"OpenRouter API key '{api_key_name}' not found in config.ini")
            self.client = None
            return

        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
        except Exception as e:
            pr.error(f"Failed to initialize OpenAI client for OpenRouter: {e}")
            self.client = None

    def request(
        self,
        prompt: str,
        model: str,
        prompt_sys: Optional[str] = None,
        **kwargs,
    ) -> Optional[str]:
        if not self.client:
            return None

        try:
            messages = []
            if prompt_sys:
                messages.append({"role": "system", "content": prompt_sys})
            messages.append({"role": "user", "content": prompt})

            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
            )
            return completion.choices[0].message.content if completion.choices else None

        except APIError as e:
            pr.error(f"OpenRouter API Error: {e}")
            return None
        except Exception as e:
            pr.error(f"Unexpected error with OpenRouter request: {e}")
            return None
