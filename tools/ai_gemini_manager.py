from typing import Optional
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from google.api_core import exceptions as google_exceptions
from google.api_core.exceptions import GoogleAPICallError

from tools.configger import config_read
from tools.printer import printer as pr

DEFAULT_API_KEY_NAME = "gemini"


class GeminiManager:
    def __init__(self, api_key_name: str = DEFAULT_API_KEY_NAME) -> None:
        self.api_key = config_read("apis", api_key_name)
        self.client: genai.Client | None = None
        if not self.api_key:
            pr.warning(f"Gemini API key '{api_key_name}' not found in config.ini")
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            pr.error(f"Failed to configure Gemini API: {e}")
            self.client = None

    def request(
        self,
        prompt: str,
        model: str,
        prompt_sys: Optional[str] = None,
        stream: bool = False,
        timeout: float = 60.0,
        grounding: bool = False,
        **kwargs,
    ) -> str | None:
        if not self.client:
            return None

        try:
            if prompt_sys:
                full_prompt = f"{prompt_sys}\n\n{prompt}"
                contents = full_prompt
            else:
                contents = prompt

            api_model_string = model
            if "preview" in model or "/" in model:
                api_model_string = f"models/{model}"

            pr.info(f"model='{api_model_string}'")

            # Create generation config with grounding if needed
            if grounding:
                google_search_tool = Tool(google_search=GoogleSearch())
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contents,
                    config=GenerateContentConfig(
                        tools=[google_search_tool],
                        response_modalities=["TEXT"],
                    ),
                    **kwargs,
                )
            else:
                response = self.client.models.generate_content(
                    model=api_model_string,
                    contents=contents,
                    **kwargs,
                )

            if stream:
                # TODO:
                pr.warning("Gemini streaming not implemented yet.")
                return response.text
            else:
                try:
                    return response.text
                except ValueError as e:
                    pr.error(
                        f"Gemini response blocked or empty. Reason: {response.prompt_feedback}"
                    )
                    pr.error(f"ValueError: {e}")
                    return None

        except google_exceptions.GoogleAPICallError as e:
            pr.error(f"Gemini API call error: {e}")
            return None
        except Exception as e:
            pr.error(f"Gemini API request failed: {e}")
            return None

    def list_models(self):
        try:
            if not self.client:
                return None
            models = self.client.models.list()
            models_list = [m.name for m in models if m.name and "2.5" in m.name]
            print(models_list)
            return models_list
        except Exception as e:
            pr.error(f"Error listing models: {e}")
            return None


if __name__ == "__main__":
    pr.info("--- Testing GeminiManager ---")
    gemini_manager = GeminiManager()

    if gemini_manager.client:
        pr.info("Gemini client initialized successfully.")

        # List available models
        gemini_manager.list_models()

        test_prompt = "Explain the concept of recursion in programming in simple terms."
        test_sys_prompt = "You are a helpful teaching assistant."

        pr.info(f"Sending request with prompt: '{test_prompt}'")
        response = gemini_manager.request(
            prompt=test_prompt,
            prompt_sys=test_sys_prompt,
            model="gemini-2.5-pro-exp-03-25",
        )

        # gemini-2.5-pro-exp-03-25
        # gemini-2.5-pro-preview-03-25
        # gemini-2.5-flash-preview-04-17

        if response:
            pr.info("Response received:")
            print(response)
        else:
            pr.error("Request failed or returned None.")
    else:
        pr.warning(
            "Gemini client could not be initialized. Check API key in config.ini."
        )
