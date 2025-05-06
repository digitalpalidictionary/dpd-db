from typing import Optional, Any
import time

from tools.ai_deepseek_manager import DeepseekManager
from tools.ai_gemini_manager import GeminiManager
from tools.ai_open_router import OpenRouterManager  # Import the new manager
from tools.configger import config_read
from tools.printer import printer as pr


class AIManager:
    # Ordered list of (provider, model) tuples as fallback defaults
    DEFAULT_MODELS = [
        ("openrouter", "meta-llama/llama-4-maverick:free"),
        ("gemini", "gemini-2.5-flash-preview-04-17"),
        ("deepseek", "deepseek-chat"),
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
        prompt_sys: Optional[str] = None,
        provider_preference: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False,
        grounding: bool = False,
        **kwargs,
    ) -> Optional[str]:
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

        # Build list of (provider, model) pairs to try
        models_to_try = []

        # Handle grounding requests - force Gemini with 2.0-flash
        if grounding:
            models_to_try.append(("gemini", "gemini-2.0-flash"))
        # Otherwise proceed normally
        elif provider_preference and model:
            models_to_try.append((provider_preference, model))
        else:
            models_to_try.extend(self.DEFAULT_MODELS)

        for provider_name, model_name in models_to_try:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]
            pr.info(f"Attempting request with {provider_name}/{model_name}...")

            start_time = time.monotonic()
            self.last_request_time = start_time

            try:
                response = provider.request(
                    prompt=prompt,
                    prompt_sys=prompt_sys,
                    model=model_name,
                    stream=stream,
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
    # Example Usage
    ai_manager = AIManager()

    if ai_manager.providers:
        test_prompt = "Explain the concept of recursion in programming in simple terms."
        test_sys_prompt = "You are a helpful teaching assistant."

        # pr.info("\n--- Testing AI Manager Request (Default Preference) ---")
        # response = ai_manager.request(prompt=test_prompt, prompt_sys=test_sys_prompt)
        # if response:
        #     print(
        #         "Response:\n", response
        #     )  # Use standard print for potentially long AI output
        # else:
        #     pr.error("Request failed.")

        # pr.info("\n--- Testing AI Manager Request (Prefer OpenRouter) ---")
        # response_or = ai_manager.request(
        #     prompt=test_prompt,
        #     prompt_sys=test_sys_prompt,
        #     provider_preference="openrouter",
        # )
        # if response_or:
        #     print("Response:\n", response_or)
        # else:
        #     pr.error("Request failed.")

        pr.info("\n--- Testing Grounded Request ---")
        prompt = "search www.wisdomlib.org for a definition of mahānāma"
        response_grounded = ai_manager.request(
            prompt=prompt,
            grounding=True,
        )
        if response_grounded:
            print("Grounded Response:\n", response_grounded)
        else:
            pr.error("Grounded request failed.")

    else:
        pr.warning("No AI providers are configured.")
