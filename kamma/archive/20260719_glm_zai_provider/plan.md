# Plan: GLM (Z.ai coding plan) provider

## Phase 1: Implement
- [x] 1. Create `tools/ai_zai_manager.py` (ZaiManager, deepseek pattern, coding-plan endpoint)
  → verify: `uv run pyright tools/ai_zai_manager.py` — 0 errors
- [x] 2. Register `zai` provider in `tools/ai_manager.py` gated on `config_read("apis", "zai")`
  → verify: ruff + pyright clean
- [x] 3. Add `zai/glm-5.2` and `zai/glm-5-turbo` to top of `default_models` in `tools/ai_models.json`
  → verify: JSON parses
- [x] 4. Add `tests/tools/test_ai_zai_manager.py`
  → verify: 6 tests pass

## Phase 2: Verify
- [x] 5. Lint gate on all touched files + `uv run pytest tests/tools/` — 560 passed
- [x] 6. User live-test with gui2 pass2pre — confirmed working 2026-07-19
