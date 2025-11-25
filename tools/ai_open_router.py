import time
from typing import Optional  # Tuple removed

from openai import APIError, OpenAI

from tools.ai_manager import AIResponse
from tools.configger import config_read
from tools.printer import printer as pr

DEFAULT_API_KEY_NAME = "openrouter"


class OpenRouterManager:
    def __init__(self, api_key_name: str = DEFAULT_API_KEY_NAME) -> None:
        self.api_key = config_read("apis", api_key_name)
        self.api_key_name = api_key_name  # Store for messages
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
        timeout: float = 60.0,
        grounding: bool = False,
        **kwargs,
    ) -> AIResponse:  # Changed return type
        if not self.client:
            return AIResponse(
                content=None,
                status_message=f"OpenRouter client not initialized for API key '{self.api_key_name}'.",
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
            # print(completion) # Useful for debugging
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
                message = completion.model_extra["error"]["message"]
                return AIResponse(content=None, status_message=message)

        except APIError as e:
            duration = time.monotonic() - start_time

            error_description = str(e)  # Default error description
            status_code_val = None

            # 1. Try to get HTTP status code directly from the exception attribute
            if hasattr(e, "status_code") and getattr(e, "status_code", None):
                status_code_val = getattr(e, "status_code")

            # 2. Parse e.body for more detailed error information
            if isinstance(getattr(e, "body", {}), dict):
                error_details_dict = None
                e_body = getattr(e, "body", {})
                # Check for a nested 'error' dictionary, common in OpenAI-like responses
                if "error" in e_body and isinstance(e_body["error"], dict):
                    error_details_dict = e_body["error"]
                # Fallback: e.body itself might be the error dictionary
                elif "message" in e_body or "code" in e_body:
                    error_details_dict = e_body

                if error_details_dict:
                    body_message = error_details_dict.get("message")
                    if isinstance(
                        body_message, str
                    ):  # Prefer this more specific message
                        error_description = body_message

                    if status_code_val is None:  # If not set by e.status_code
                        body_code = error_details_dict.get("code")
                        if body_code is not None:  # Can be int or str
                            status_code_val = body_code
            # 3. Fallback to e.message if e.body wasn't helpful or not a dict
            elif hasattr(e, "message") and getattr(
                e, "message", None
            ):  # Fallback if body is not dict or no suitable message in body
                error_description = getattr(e, "message", str(e))

            status_code_str = (
                f" (Status: {status_code_val})" if status_code_val is not None else ""
            )

            error_message = f"OpenRouter API Error{status_code_str} with {model} after {duration:.2f}s: {error_description}"
            return AIResponse(content=None, status_message=error_message)
        except Exception as e:
            duration = time.monotonic() - start_time
            error_message = f"Unexpected error with OpenRouter ({model}) request after {duration:.2f}s: {e}"
            return AIResponse(content=None, status_message=error_message)


def main():
    """Test the OpenRouterManager with different models."""
    from tools.printer import printer as pr

    manager = OpenRouterManager()

    if not manager.client:
        pr.error(
            "OpenRouter client not initialized. Please check your API key configuration."
        )
        return

    # Test prompt
    prompt = (
        "What is the capital of Sri Lanka and what are some interesting facts about it?"
    )
    sys_prompt = (
        "You are a helpful assistant that provides concise and accurate information."
    )

    # Test models from the DEFAULT_MODELS list
    test_models = [
        "x-ai/grok-4.1-fast",
        "kwaipilot/kat-coder-pro:free",
        "tngtech/deepseek-r1t-chimera:free",
        "nvidia/nemotron-nano-12b-v2-vl:free",
        "openrouter/bert-nebulon-alpha",
        # "z-ai/glm-4.5-air:free",
        # "qwen/qwen3-235b-a22b:free",
        # "meta-llama/llama-4-maverick:free",
    ]

    pr.info("=== Testing OpenRouter Models ===")

    for model in test_models:
        pr.info(f"\n--- Testing model: {model} ---")
        start_time = time.monotonic()

        response = manager.request(
            prompt=prompt, model=model, prompt_sys=sys_prompt, timeout=30.0
        )

        duration = time.monotonic() - start_time

        pr.info(f"Duration: {duration:.2f}s")
        pr.info(f"Status: {response.status_message}")

        if response.content:
            # Show first 200 characters of content
            preview = (
                response.content[:200] + "..."
                if len(response.content) > 200
                else response.content
            )
            pr.info(f"Content preview: {preview}")
        else:
            pr.warning("No content received")

        # Small delay between requests
        time.sleep(2)

    pr.info("\n=== Testing Complete ===")


if __name__ == "__main__":
    main()
