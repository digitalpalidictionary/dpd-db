# Spec: GLM (Z.ai coding plan) provider in ai_manager

## Goal
Use the GLM coding-plan subscription (key `zai` in `config.ini [apis]`) as a provider in `tools/ai_manager.py`, and put a big and a fast GLM model at the top of the default models list so gui2 pass2pre uses it first.

## Research findings (verified live 2026-07-19)
- Coding-plan dedicated endpoint (OpenAI-compatible):
  `https://api.z.ai/api/coding/paas/v4/chat/completions`
- Auth: `Authorization: Bearer <zai key>`.
- Live `/models` on that endpoint returns: glm-4.5, glm-4.5-air, glm-4.6, glm-4.7, glm-5, glm-5-turbo, glm-5.1, glm-5.2.
- A test completion with `glm-5-turbo` and `"thinking": {"type": "disabled"}` succeeded (same payload shape as DeepSeek).

## Changes (minimal)
1. **`tools/ai_zai_manager.py`** (new, follows `ai_<name>_manager.py` convention):
   `ZaiManager` modeled directly on `DeepseekManager` — OpenAI-compatible POST, Bearer auth, thinking disabled by default, kwargs override, `get_models()`.
2. **`tools/ai_manager.py`**: register `self.providers["zai"] = ZaiManager()` gated on `config_read("apis", "zai")`, same pattern as deepseek/gemini/nvidia.
3. **`tools/ai_models.json`**: prepend to `default_models`:
   - `zai / glm-5.2` (big)
   - `zai / glm-5-turbo` (fast)
4. **`tests/tools/test_ai_zai_manager.py`**: payload tests mirroring `test_ai_deepseek_manager.py` essentials.

## Out of scope
- Grounded models, balance UI, gui2 changes (pass2pre picks GLM up automatically via the default list).

## Verification
- ruff check/format + pyright on touched files, pytest `tests/tools/`.
- User tests live with gui2 pass2pre.
