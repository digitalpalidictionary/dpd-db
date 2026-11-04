"""Task 1.1: list DeepSeek API models and send a 1-line test to each target model."""

from tools.ai_manager import AIManager
from tools.ai_openai_compat import OpenAiCompatManager

print("deepseek models:", OpenAiCompatManager("deepseek").get_models())
print("zai models:", OpenAiCompatManager("zai").get_models())

ai = AIManager()
for provider, model in [("deepseek", "deepseek-v4-flash"), ("zai", "glm-5.3-flash")]:
    r = ai.request(
        prompt="Reply with the single word: ok",
        provider_preference=provider,
        model=model,
    )
    print(provider, model, "| content:", repr((r.content or "")[:40]), "|", r.status_message)
