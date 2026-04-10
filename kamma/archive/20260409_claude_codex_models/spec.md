# Spec: Add Claude CLI models to the shared AI manager

## Overview
Add a separate Claude CLI-backed provider so Claude models available through the local `claude` CLI can be selected in the same shared dropdown used by gui2 pass1 auto and pass2 auto.

## What it should do
- Add a `claude` provider in `tools/ai_manager.py`.
- Add the three Claude CLI model aliases to `tools/ai_models.json` so they appear in the same dropdowns as the existing providers.
- Use the local `claude` CLI model aliases the user requested: `opus`, `sonnet`, and `haiku`.
- Preserve current gui2 wiring so no pass1/pass2 UI code changes are needed.
- Keep the model ordering sensible in `tools/ai_models.json` so the dropdown remains readable.

## Relevant repo context
- `tools/ai_claude_manager.py` is a thin subprocess wrapper around `claude -p --output-format json`.
- `tools/ai_manager.py` registers providers and routes requests through a shared `AIResponse` contract.
- `tools/ai_models.json` drives the default AI dropdown contents for gui2.
- `gui2/pass1_auto_view.py` and `gui2/pass2_auto_view.py` already build dropdown options from `toolkit.ai_manager.DEFAULT_MODELS`.
- `tests/tools/test_ai_claude_manager.py` verifies the Claude wrapper path and provider registration.
- The Claude CLI returns a JSON envelope, so the wrapper must extract the `result` field and pass that plain text back into gui2.

## Constraints
- Keep this minimal and parallel to the GPT Codex work.
- Do not change `.ini` files.
- Do not rework gui2 unless necessary.
- Use the existing shared AI manager and AIResponse contract.
- Preserve JSON-oriented behavior for gui2 by returning the Claude CLI `result` field, not the raw CLI envelope.

## How we'll know it's done
- The three Claude models are added to `tools/ai_models.json` under provider `claude`.
- The `claude` provider can invoke them through the current wrapper.
- The models appear in gui2 pass1 auto and pass2 auto via existing dropdown plumbing.
- Targeted verification still passes after the model list change.

## What's not included
- A new Anthropic API integration.
- GUI redesign.
- Unsupported or unverified Claude model aliases beyond `opus`, `sonnet`, and `haiku`.
