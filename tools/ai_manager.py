from typing import Any
import time

from tools.ai_deepseek_manager import DeepseekManager
from tools.ai_gemini_manager import GeminiManager
from tools.ai_open_router import OpenRouterManager
from tools.configger import config_read
from tools.printer import printer as pr


class AIManager:
    # Ordered list of (provider, model) tuples as fallback defaults
    DEFAULT_MODELS = [
        ("gemini", "gemini-2.5-pro-preview-05-06"),
        ("deepseek", "deepseek-chat"),
        ("openrouter", "meta-llama/llama-4-maverick:free"),
    ]

    # Grounded models for internet searches
    GROUNDED_MODELS = [
        ("gemini", "gemini-2.5-flash-preview-04-17"),
    ]

    def __init__(self):
        self.providers: dict[str, Any] = {}

        if config_read("apis", "openrouter"):
            self.providers["openrouter"] = OpenRouterManager()
            pr.info("openrouter initialized")
        else:
            pr.warning("OpenRouter API key not found, manager not initialized.")

        if config_read("apis", "deepseek"):
            self.providers["deepseek"] = DeepseekManager()
            pr.info("deepseek initialized")
        else:
            pr.warning("DeepSeek API key not found, manager not initialized.")

        if config_read("apis", "gemini"):
            self.providers["gemini"] = GeminiManager()
            pr.info("gemini initialized")
        else:
            pr.warning("Gemini API key not found, manager not initialized.")

        self.last_request_time: float = 0
        self.min_delay_seconds: float = 10.0

    def request(
        self,
        prompt: str,
        prompt_sys: str | None = None,
        provider_preference: str | None = None,
        model: str | None = None,
        grounding: bool = False,
        **kwargs,
    ) -> str | None:
        """
        Makes a request to an AI provider.
        If no model is specified, uses DEFAULT_MODELS in order.
        """
        # Rate Limiting
        current_time = time.monotonic()
        elapsed_since_last = current_time - self.last_request_time
        wait_time = self.min_delay_seconds - elapsed_since_last

        if wait_time > 0:
            pr.info(f"Rate limiting: waiting for {wait_time:.2f} seconds...")
            time.sleep(wait_time)

        models_to_try = []

        # Use a grounded model for internet searches
        if grounding:
            models_to_try.extend(self.GROUNDED_MODELS)

        # Otherwise use the specified model
        elif provider_preference and model:
            models_to_try.append((provider_preference, model))

        # Otherwise use the fallback list
        else:
            models_to_try.extend(self.DEFAULT_MODELS)

        for provider_name, model_name in models_to_try:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            start_time = time.monotonic()
            self.last_request_time = start_time

            try:
                response = provider.request(
                    prompt=prompt,
                    prompt_sys=prompt_sys,
                    model=model_name,
                    timeout=60.0,
                    grounding=grounding,
                    **kwargs,
                )
                end_time = time.monotonic()
                duration = end_time - start_time

                if response is not None:
                    pr.info(
                        f"Request successful with {provider_name} in {duration:.2f} seconds."
                    )
                    return response
                else:
                    pr.warning(
                        f"{provider_name} request failed or returned None (took {duration:.2f}s)."
                    )
            except Exception as e:
                pr.error(f"Error during {provider_name} request: {e}")

        pr.error("All AI providers failed.")
        return None


if __name__ == "__main__":
    # Example usage
    ai_manager = AIManager()

    prompt = "Explain the concept of recursion in programming in simple terms."
    sys_prompt = "You are a helpful teaching assistant."

    pr.info("\n--- Testing Default Preferences ---")
    default_response = ai_manager.request(
        prompt=prompt,
        prompt_sys=sys_prompt,
    )
    if default_response:
        print(default_response)
    else:
        pr.warning("Default request failed or returned None.")

    pr.info("\n--- Testing OpenRouter ---")
    open_router_response = ai_manager.request(
        prompt=prompt,
        prompt_sys=sys_prompt,
        provider_preference="openrouter",
    )
    if open_router_response:
        print(open_router_response)
    else:
        pr.warning("OpenRouter request failed or returned None.")

    pr.info("\n--- Testing Grounded Request ---")
    grounded_prompt = "Whats the weather in Kandy, Sri Lanka today?"
    response_grounded = ai_manager.request(
        prompt=grounded_prompt,
        grounding=True,
    )
    if response_grounded:
        print(response_grounded)
    else:
        pr.warning("Grounded request failed or returned None.")
