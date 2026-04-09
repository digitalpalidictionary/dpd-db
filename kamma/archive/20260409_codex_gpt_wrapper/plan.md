# Plan: Add minimal Codex GPT wrapper

## Phase 1
- [x] Create `tools/ai_gpt_manager.py` as a thin `codex exec` wrapper.
- [x] Return `AIResponse(content, status_message)` and handle simple failures.

- [x] Verification
- [x] Run a small local check that the wrapper imports and can invoke `codex`.

## Phase 2
- [x] Register the new provider in `tools/ai_manager.py`.
- [x] Add the two GPT model entries to `tools/ai_models.json`.

- [x] Verification
- [x] Confirm the provider/model names line up and load into `DEFAULT_MODELS`.

## Phase 3
- [x] Confirm pass1 auto and pass2 auto pick up the new models through existing dropdown logic.
- [x] Prepare a short manual test for you.

- [x] Verification
- [x] Re-read the changed files and do one final targeted check.
