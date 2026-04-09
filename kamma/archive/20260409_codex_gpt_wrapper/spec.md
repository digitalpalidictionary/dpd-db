# Spec: Add a simple Codex-backed GPT wrapper

## Overview
Add a very small wrapper in `tools/ai_gpt_manager.py` that calls the already-authenticated `codex` CLI, register it in `tools/ai_manager.py`, and add two GPT model entries to `tools/ai_models.json` so they show up in gui2 pass1 auto and pass2 auto.

## What it should do
- Call `codex exec` non-interactively from Python.
- Return the result through the existing `AIResponse` shape.
- Register the provider in `tools/ai_manager.py`.
- Add two model entries to `tools/ai_models.json`.
- Let existing gui2 dropdown wiring pick them up automatically.

## Constraints
- Keep it minimal.
- No OpenAI API integration.
- No config changes.
- No GUI rewiring unless strictly necessary.

## Done when
- The wrapper exists.
- `AIManager` can route to it.
- The two GPT models are in `tools/ai_models.json`.
- They appear in pass1/pass2 auto model dropdowns.
