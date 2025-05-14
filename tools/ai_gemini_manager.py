import time
from typing import Optional

from google import genai
from google.api_core import exceptions as google_exceptions
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool, HttpOptions

from tools.configger import config_read
from tools.printer import printer as pr
from tools.ai_manager import AIResponse

DEFAULT_API_KEY_NAME = "gemini"


class GeminiManager:
    def __init__(self, api_key_name: str = DEFAULT_API_KEY_NAME) -> None:
        self.api_key = config_read("apis", api_key_name)
        self.client: genai.Client | None = None
        self.api_key_name = api_key_name
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
    ) -> AIResponse:  # Changed return type
        if not self.client:
            return AIResponse(
                content=None,
                status_message=f"Gemini client not initialized for API key '{self.api_key_name}'.",
            )

        start_time = time.monotonic()
        try:
            # Prepare prompt and model string
            if prompt_sys:
                full_prompt = f"{prompt_sys}\n\n{prompt}"
                contents = full_prompt
            else:
                contents = prompt

            api_model_string = model
            if not model.startswith("models/"):
                api_model_string = f"models/{model}"

            if grounding:
                google_search_tool = Tool(google_search=GoogleSearch())
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=contents,
                    config=GenerateContentConfig(
                        tools=[google_search_tool],
                        response_modalities=["TEXT"],
                    ),
                )
            else:
                response = self.client.models.generate_content(
                    model=api_model_string,
                    contents=contents,
                    config=GenerateContentConfig(
                        response_modalities=["TEXT"],
                        http_options=HttpOptions(
                            # timeout is in milliseconds
                            timeout=int(timeout * 1000)
                        ),
                    ),
                )

            duration = time.monotonic() - start_time

            # Non-streaming response handling
            if (
                hasattr(response, "text") and response.text
            ):  # Simplest case: text attribute is present and non-empty
                return AIResponse(
                    content=response.text,
                    status_message="",
                )
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                reason = response.prompt_feedback.block_reason
                error_msg = f"Gemini ({api_model_string}) response blocked in {duration:.2f}s. Reason: {reason}"
                pr.error(error_msg)
                return AIResponse(content=None, status_message=error_msg)
            else:  # More complex case: check candidates and parts
                if (
                    response.candidates
                    and response.candidates[0].content
                    and response.candidates[0].content.parts
                ):
                    text_content = "".join(
                        part.text
                        for part in response.candidates[0].content.parts
                        if hasattr(part, "text")  # type: ignore
                    )
                    if text_content:
                        return AIResponse(
                            content=text_content,
                            status_message=f"Success with Gemini ({api_model_string}) in {duration:.2f}s (extracted from parts).",
                        )

                # Fallback if no text and not explicitly blocked
                return AIResponse(
                    content=None, status_message=f"{response.prompt_feedback}"
                )

        except google_exceptions.GoogleAPICallError as e:
            pr.error(str(e))
            return AIResponse(content=None, status_message=str(e))
        except Exception as e:
            return AIResponse(content=None, status_message=str(e))

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

    # List available models
    gemini_manager.list_models()

    models = [
        "models/gemini-2.5-pro-exp-03-25",
        "models/gemini-2.5-pro-preview-03-25",
        "models/gemini-2.5-flash-preview-04-17",
        "models/gemini-2.5-flash-preview-04-17-thinking",
        "models/gemini-2.5-pro-preview-05-06",
    ]

    test_prompt = "Explain the concept of recursion in programming in simple terms."
    test_sys_prompt = "You are a helpful teaching assistant."

    pr.info(f"Sending request with prompt: '{test_prompt}'")
    ai_response = gemini_manager.request(
        prompt=test_prompt,
        prompt_sys=test_sys_prompt,
        model="models/gemini-2.5-pro-preview-05-06",
    )

    pr.info(f"Gemini request status: {ai_response.status_message}")
    if ai_response.content:
        pr.info("Response received:")
        pr.info(ai_response.content)
    else:
        pr.warning("Gemini request content was None.")
