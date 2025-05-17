from typing import Any
import time


from tools.configger import config_read
from tools.printer import printer as pr


from typing import NamedTuple, Optional


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
    # Ordered list of (provider, model) tuples as fallback defaults
    DEFAULT_MODELS = [
        ("gemini", "gemini-2.5-flash-preview-04-17"),
        ("gemini", "gemini-2.5-pro-exp-03-25"),
        ("deepseek", "deepseek-chat"),
        ("deepseek", "deepseek-reasoner"),
        ("openrouter", "meta-llama/llama-4-maverick:free"),
        ("openrouter", "qwen/qwen3-235b-a22b:free"),
        ("openrouter", "thudm/glm-4-32b:free"),
    ]

    # Grounded models for internet searches
    GROUNDED_MODELS = [
        ("gemini", "gemini-2.5-flash-preview-04-17"),
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
        self.min_delay_seconds: float = 0

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
        # Rate Limiting
        current_time = time.monotonic()
        elapsed_since_last = current_time - self.last_request_time
        wait_time = self.min_delay_seconds - elapsed_since_last

        if wait_time > 0:
            pr.info(f"RATE LIMITING for {wait_time:.2f}s")
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
