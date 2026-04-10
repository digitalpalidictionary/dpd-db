# Plan: Add Claude CLI models to the shared AI manager

## Phase 1: Verify the exact Claude CLI model approach
- [x] Inspect the current AI setup in:
  - [x] `tools/ai_claude_manager.py`
  - [x] `tools/ai_manager.py`
  - [x] `tools/ai_models.json`
- [x] Run local CLI checks for the three Claude variants requested:
  - [x] Opus
  - [x] Sonnet
  - [x] Haiku
- [x] Record the intended CLI model aliases and the temporary account-limit constraint.

- [x] Verification
- [x] Confirm the Claude CLI command shape and account-limit response locally.

## Phase 2: Add the Claude models to the shared model registry
- [x] Add `tools/ai_claude_manager.py` as a thin `claude -p --output-format json` wrapper.
- [x] Register the `claude` provider in `tools/ai_manager.py`.
- [x] Update `tools/ai_models.json` to add the Claude CLI model IDs under provider `claude`.
- [x] Place the new entries in a sensible order among the existing model entries.
- [x] Keep all existing GPT Codex model entries intact.

- [x] Verification
- [x] Re-read `tools/ai_models.json` and confirm the ordering and provider/model names are consistent.

## Phase 3: Verify existing wiring still covers gui2 and tests
- [x] Re-check that `gui2/pass1_auto_view.py` and `gui2/pass2_auto_view.py` still consume `DEFAULT_MODELS` without any special handling.
- [x] Run the targeted wrapper tests:
  - [x] `pytest tests/tools/test_ai_claude_manager.py tests/tools/test_ai_gpt_manager.py`
- [x] Prepare short manual test steps for reloading or restarting gui2 and checking the new Claude models in pass1 auto and pass2 auto.
- [x] Validate the models manually after CLI credit reset.

- [x] Verification
- [x] Confirm the changed files and test output support the spec with no extra provider or UI work.
