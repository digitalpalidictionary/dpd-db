import time
from typing import Optional

from openai import APIError, OpenAI

from tools.ai_manager import AIResponse
from tools.configger import config_read
from tools.printer import printer as pr

DEFAULT_API_KEY_NAME = "nvidia"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NvidiaManager:
    def __init__(self, api_key_name: str = DEFAULT_API_KEY_NAME) -> None:
        self.api_key = config_read("apis", api_key_name)
        self.api_key_name = api_key_name
        if not self.api_key:
            pr.amber(f"NVIDIA API key '{api_key_name}' not found in config.ini")
            self.client = None
            return

        try:
            self.client = OpenAI(
                base_url=NVIDIA_BASE_URL,
                api_key=self.api_key,
            )
        except Exception as e:
            pr.red(f"Failed to initialize OpenAI client for NVIDIA: {e}")
            self.client = None

    def request(
        self,
        prompt: str,
        model: str,
        prompt_sys: Optional[str] = None,
        timeout: float = 60.0,
        grounding: bool = False,
        **kwargs,
    ) -> AIResponse:
        if not self.client:
            return AIResponse(
                content=None,
                status_message=f"NVIDIA client not initialized for API key '{self.api_key_name}'.",
            )

        start_time = time.monotonic()
        try:
            messages = []
            if prompt_sys:
                messages.append({"role": "system", "content": prompt_sys})
            messages.append({"role": "user", "content": prompt})

            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                timeout=timeout,
                **kwargs,
            )
            duration = time.monotonic() - start_time
            if (
                completion.choices
                and completion.choices[0].message
                and completion.choices[0].message.content
            ):
                content = completion.choices[0].message.content
                return AIResponse(
                    content=content,
                    status_message=f"Success in {duration:.2f}s.",
                )
            else:
                message = "No content in NVIDIA response."
                if completion.model_extra and "error" in completion.model_extra:
                    err = completion.model_extra["error"]
                    if isinstance(err, dict):
                        message = err.get("message", message)
                return AIResponse(content=None, status_message=message)

        except APIError as e:
            duration = time.monotonic() - start_time
            error_description = str(e)
            status_code_val = None

            if hasattr(e, "status_code") and getattr(e, "status_code", None):
                status_code_val = getattr(e, "status_code")

            if isinstance(getattr(e, "body", {}), dict):
                error_details_dict = None
                e_body = getattr(e, "body", {})
                if "error" in e_body and isinstance(e_body["error"], dict):
                    error_details_dict = e_body["error"]
                elif "message" in e_body or "code" in e_body:
                    error_details_dict = e_body

                if error_details_dict:
                    body_message = error_details_dict.get("message")
                    if isinstance(body_message, str):
                        error_description = body_message
                    if status_code_val is None:
                        body_code = error_details_dict.get("code")
                        if body_code is not None:
                            status_code_val = body_code
            elif hasattr(e, "message") and getattr(e, "message", None):
                error_description = getattr(e, "message", str(e))

            status_code_str = (
                f" (Status: {status_code_val})" if status_code_val is not None else ""
            )
            error_message = f"NVIDIA API Error{status_code_str} with {model} after {duration:.2f}s: {error_description}"
            return AIResponse(content=None, status_message=error_message)
        except Exception as e:
            duration = time.monotonic() - start_time
            error_message = f"Unexpected error with NVIDIA ({model}) request after {duration:.2f}s: {e}"
            return AIResponse(content=None, status_message=error_message)


def main():
    """Test the NvidiaManager with a couple of models."""
    manager = NvidiaManager()

    if not manager.client:
        pr.red(
            "NVIDIA client not initialized. Please check your API key configuration."
        )
        return

    prompt = "What is the capital of Sri Lanka? Answer in one short sentence."
    sys_prompt = "You are a concise assistant."

    test_models = [
        "z-ai/glm-5.1",
    ]

    pr.green("=== Testing NVIDIA Models ===")

    for model in test_models:
        pr.green(f"\n--- Testing model: {model} ---")
        start_time = time.monotonic()

        response = manager.request(
            prompt=prompt, model=model, prompt_sys=sys_prompt, timeout=30.0
        )

        duration = time.monotonic() - start_time

        pr.green(f"Duration: {duration:.2f}s")
        pr.green(f"Status: {response.status_message}")

        if response.content:
            preview = (
                response.content[:300] + "..."
                if len(response.content) > 300
                else response.content
            )
            pr.green(f"Content: {preview}")
        else:
            pr.amber("No content received")

        time.sleep(2)

    pr.green("\n=== Testing Complete ===")


if __name__ == "__main__":
    main()
