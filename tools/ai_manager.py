import time
from typing import Any, NamedTuple, Optional

from tools.configger import config_read
from tools.printer import printer as pr


class AIResponse(NamedTuple):
    """
    Represents the response from an AI manager.

    Attributes:
        content: The actual response content from the AI, if successful.
        status_message: A descriptive message about the request's outcome,
                        including provider, model, duration, and any errors.
    """

    content: Optional[str]
    status_message: str


class AIManager:
    # Ordered list of (provider, model, delay_seconds) tuples as fallback defaults
    DEFAULT_MODELS: list[tuple[str, str, int]] = [
        ("gemini", "gemini-2.5-pro", 12),
        ("gemini", "gemini-2.5-flash", 6),
        ("gemini", "gemini-2.5-flash-lite", 4),
        ("openrouter", "x-ai/grok-4-fast:free", 5),
        ("openrouter", "deepseek/deepseek-chat-v3.1:free", 5),
        ("openrouter", "z-ai/glm-4.5-air:free", 5),
        ("openrouter", "qwen/qwen3-235b-a22b:free", 5),
    ]

    # Grounded models for internet searches
    GROUNDED_MODELS = [
        ("gemini", "gemini-2.5-flash", 6),
    ]

    def __init__(self):
        self.providers: dict[str, Any] = {}

        from tools.ai_deepseek_manager import DeepseekManager
        from tools.ai_gemini_manager import GeminiManager
        from tools.ai_open_router import OpenRouterManager

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
        self.min_delay_seconds: float = 5
        # NEW: Track last request time per model for model-specific rate limiting
        self.model_last_request: dict[str, float] = {}

    def _get_model_delay(self, provider: str, model: str) -> float:
        """Get delay for specific model, with fallback to global delay."""
        # Look through all model lists for this provider/model combination
        for model_tuple in self.DEFAULT_MODELS + self.GROUNDED_MODELS:
            if model_tuple[0] == provider and model_tuple[1] == model:
                return model_tuple[2]

        # Fallback to global delay if model not found
        return self.min_delay_seconds

    def request(
        self,
        prompt: str,
        prompt_sys: str | None = None,
        provider_preference: str | None = None,
        model: str | None = None,
        grounding: bool = False,
        **kwargs,
    ) -> AIResponse:  # Changed return type
        """
        Makes a request to an AI provider. Uses a fallback list of models if
        provider_preference and model are not specified.
        Returns an AIResponse object.
        """
        # NEW: Model-specific rate limiting
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

        # NEW: Check rate limits for each model before trying them
        for model_tuple in models_to_try:
            provider_name, model_name = model_tuple[0], model_tuple[1]
            model_key = f"{provider_name}:{model_name}"
            model_delay = self._get_model_delay(provider_name, model_name)

            current_time = time.monotonic()
            last_request = self.model_last_request.get(model_key, 0)
            elapsed_since_last = current_time - last_request
            wait_time = model_delay - elapsed_since_last

            if wait_time > 0:
                pr.info(f"RATE LIMITING for {model_key} - {wait_time:.2f}s")
                time.sleep(wait_time)

            # Update last request time for this model
            self.model_last_request[model_key] = time.monotonic()

        for model_tuple in models_to_try:
            provider_name, model_name = model_tuple[0], model_tuple[1]
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            start_time = time.monotonic()
            self.last_request_time = start_time
            pr.info(f"REQUEST {provider_name} - {model_name}")

            try:
                ai_response = provider.request(
                    prompt=prompt,
                    prompt_sys=prompt_sys,
                    model=model_name,
                    timeout=60.0,
                    grounding=grounding,
                    **kwargs,
                )
                end_time = time.monotonic()
                duration = end_time - start_time

                if ai_response.content is not None:
                    status_message = (
                        f"SUCCESS in {duration:.2f}s. {ai_response.status_message}"
                    )
                    pr.info(status_message)
                    return AIResponse(
                        content=ai_response.content,
                        status_message=status_message,
                    )
                else:
                    status_message = f"ERROR in {duration:.2f}s."
                    pr.warning(status_message)
                    pr.error(ai_response.status_message)
            except Exception as e:
                duration = time.monotonic() - start_time
                status_message = f"ERROR in {duration:.2f}s"
                pr.error(status_message)
                pr.error(str(e))

        final_failure_message = "All AI providers failed."
        pr.error(final_failure_message)
        return AIResponse(content=None, status_message=final_failure_message)


if __name__ == "__main__":
    # Example usage
    ai_manager = AIManager()

    prompt = "Explain the concept of recursion in programming in simple terms."
    sys_prompt = "You are a helpful teaching assistant."

    # -----------------------------------------

    pr.info("\n--- Testing Default Preferences ---")
    default_response = ai_manager.request(
        prompt=prompt,
        prompt_sys=sys_prompt,
    )
    pr.info(f"Content: {default_response.content}")
    pr.info(f"Status: {default_response.status_message}")

    # -----------------------------------------

    pr.info("\n--- Testing OpenRouter ---")
    open_router_response = ai_manager.request(
        prompt=prompt,
        prompt_sys=sys_prompt,
        provider_preference="openrouter",
        model="meta-llama/llama-4-maverick:free",
    )
    pr.info(f"Status: {open_router_response.status_message}")
    pr.info(f"Content: {open_router_response.content}")

    # -----------------------------------------

    pr.info("\n--- Testing Grounded Request ---")
    grounded_prompt = "Whats the weather in Kandy, Sri Lanka today?"
    grounded_response = ai_manager.request(
        prompt=grounded_prompt,
        grounding=True,
    )
    pr.info(f"Content: {grounded_response.content}")
    pr.info(f"Status: {grounded_response.status_message}")

    # -----------------------------------------
