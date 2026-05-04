import json
import time
from pathlib import Path
from typing import Any, NamedTuple, Optional

from tools.configger import config_read
from tools.printer import printer as pr

AI_MODELS_PATH = Path("tools/ai_models.json")


def _load_models_from_json() -> dict[str, list[tuple[str, str, int]]]:
    """Load model lists from tools/ai_models.json."""
    try:
        data = json.loads(AI_MODELS_PATH.read_text())
        return {
            "default": [
                (m["provider"], m["model"], m["delay"])
                for m in data.get("default_models", [])
            ],
            "grounded": [
                (m["provider"], m["model"], m["delay"])
                for m in data.get("grounded_models", [])
            ],
        }
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        pr.red(f"Failed to load {AI_MODELS_PATH}: {e}")
        return {"default": [], "grounded": []}


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
    def __init__(self):
        models = _load_models_from_json()
        self.DEFAULT_MODELS: list[tuple[str, str, int]] = models["default"]
        self.GROUNDED_MODELS: list[tuple[str, str, int]] = models["grounded"]

        self.providers: dict[str, Any] = {}

        from tools.ai_claude_manager import ClaudeManager
        from tools.ai_deepseek_manager import DeepseekManager
        from tools.ai_gpt_manager import GptManager
        from tools.ai_gemini_manager import GeminiManager
        from tools.ai_open_router import OpenRouterManager
        from tools.ai_nvidia import NvidiaManager

        self.providers["claude"] = ClaudeManager()
        pr.green("claude initialized")

        self.providers["codex"] = GptManager()
        pr.green("codex initialized")

        if config_read("apis", "openrouter"):
            self.providers["openrouter"] = OpenRouterManager()
            pr.green("openrouter initialized")
        else:
            pr.amber("OpenRouter API key not found, manager not initialized.")

        if config_read("apis", "deepseek"):
            self.providers["deepseek"] = DeepseekManager()
            pr.green("deepseek initialized")
        else:
            pr.amber("DeepSeek API key not found, manager not initialized.")

        if config_read("apis", "gemini"):
            self.providers["gemini"] = GeminiManager()
            pr.green("gemini initialized")
        else:
            pr.amber("Gemini API key not found, manager not initialized.")

        if config_read("apis", "nvidia"):
            self.providers["nvidia"] = NvidiaManager()
            pr.green("nvidia initialized")
        else:
            pr.amber("NVIDIA API key not found, manager not initialized.")

        pr.green(
            f"loaded {len(self.DEFAULT_MODELS)} default models, {len(self.GROUNDED_MODELS)} grounded models"
        )

        self.last_request_time: float = 0
        self.min_delay_seconds: float = 5
        # NEW: Track last request time per model for model-specific rate limiting
        self.model_last_request: dict[str, float] = {}

    def reload_models(self) -> None:
        """Reload model lists from tools/ai_models.json."""
        models = _load_models_from_json()
        self.DEFAULT_MODELS = models["default"]
        self.GROUNDED_MODELS = models["grounded"]
        pr.green(
            f"reloaded {len(self.DEFAULT_MODELS)} default models, {len(self.GROUNDED_MODELS)} grounded models"
        )

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
        models_to_try = []
        errors: list[str] = []

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
                pr.green(f"RATE LIMITING for {model_key} - {wait_time:.2f}s")
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
            pr.green(f"REQUEST {provider_name} - {model_name}")

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
                    pr.green(status_message)
                    return AIResponse(
                        content=ai_response.content,
                        status_message=status_message,
                    )
                else:
                    status_message = f"{provider_name}/{model_name} ERROR in {duration:.2f}s: {ai_response.status_message}"
                    pr.amber(status_message)
                    errors.append(status_message)
            except Exception as e:
                duration = time.monotonic() - start_time
                status_message = (
                    f"{provider_name}/{model_name} ERROR in {duration:.2f}s: {e}"
                )
                pr.red(status_message)
                errors.append(status_message)

        final_failure_message = "All AI providers failed. " + " | ".join(errors)
        pr.red(final_failure_message)
        return AIResponse(content=None, status_message=final_failure_message)


if __name__ == "__main__":
    # Example usage
    ai_manager = AIManager()

    prompt = "Explain the concept of recursion in programming in simple terms."
    sys_prompt = "You are a helpful teaching assistant."

    # -----------------------------------------

    pr.green("\n--- Testing Default Preferences ---")
    default_response = ai_manager.request(
        prompt=prompt,
        prompt_sys=sys_prompt,
    )
    pr.green(f"Content: {default_response.content}")
    pr.green(f"Status: {default_response.status_message}")

    # -----------------------------------------

    pr.green("\n--- Testing OpenRouter ---")
    open_router_response = ai_manager.request(
        prompt=prompt,
        prompt_sys=sys_prompt,
        provider_preference="openrouter",
        model="xiaomi/mimo-v2-flash:free",
    )
    pr.green(f"Status: {open_router_response.status_message}")
    pr.green(f"Content: {open_router_response.content}")

    # -----------------------------------------

    pr.green("\n--- Testing Grounded Request ---")
    grounded_prompt = "Whats the weather in Kandy, Sri Lanka today?"
    grounded_response = ai_manager.request(
        prompt=grounded_prompt,
        grounding=True,
    )
    pr.green(f"Content: {grounded_response.content}")
    pr.green(f"Status: {grounded_response.status_message}")

    # -----------------------------------------
