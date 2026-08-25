# Plan: consolidate the OpenAI-compatible AI providers

Spec: `kamma/threads/20260825_ai_provider_consolidation/spec.md`
Research: `kamma/threads/20260825_pydantic_ai_evaluation/research.md`
No GitHub issue.

## Architecture Decisions

| Decision | Rationale |
|---|---|
| One class `OpenAiCompatManager(provider_name)` driven by a `PROVIDER_SPECS` table, not four classes or a base class with four subclasses | The four providers differ only in key name, URL, and two payload defaults. A data table expresses that; inheritance would not. Verified: NVIDIA and OpenRouter differ by 62 lines, all cosmetic bar one guard. |
| Transport is plain `requests`, not the OpenAI SDK | `from openai import ...` appears in exactly two files repo-wide, both deleted here — so this retires the `openai` dependency rather than spreading it. The two SDK-based wrappers are also the two with no tests, so building on the `requests` path preserves existing coverage. Nothing here needs streaming, tools, structured output, or async. |
| `PROVIDER_SPECS` lives in code, not in `ai_models.json` | That file is hot-reloadable from a button in three gui2 views, but providers are built once at `AIManager.__init__` and never rebuilt. Putting connection details there would make the reload button half-honest. |
| Error extraction tries nested `error` → RFC 7807 `detail`/`title` → raw text → exception string | Live probing found three genuinely different error body shapes across the four providers; NVIDIA uses RFC 7807 and also returns plain text on 404. The prototype was validated against all five real bodies. |
| The four old modules are deleted, not kept as thin aliases | No caller imports a provider class directly — everything goes through `AIManager` (verified by sweep). Aliases would be dead code. |
| `AIResponse`, the `request()` signature, and `AIManager`'s never-raises contract are untouched | Every consumer in `gui2/`, `exporter/analysis/`, `tools/proofreader.py` and `scripts/extractor/` is written against them. |
| Stale model config found while probing is reported, not fixed | `tencent/hy3:free` is dead and NVIDIA's demo model is end-of-life. That is data, not code, and changing which models are tried is explicitly out of scope. |

## Baseline (recorded before any edit)

Captured live on 2026-08-25 so regressions are detectable:

| Provider | Success status today | Bad-model status today |
|---|---|---|
| openrouter | `Success in 11.35s.` | `OpenRouter API Error (Status: 400) with … : … is not a valid model ID` |
| nvidia | `Success in 1.01s.` | `NVIDIA API Error (Status: 404) with … : 404 page not found` |
| deepseek | `200` | `post_request returned None` ← **detail discarded, the defect being fixed** |
| zai | `200` | `HTTP 400: [1214] modelCode: does not exist` |

Pre-existing, not this thread's to fix: no test files exist for OpenRouter or NVIDIA;
`tencent/hy3:free` is dead in `ai_models.json`.

---

## Phase 1 — Shared module, wired for Z.ai only

Vertical slice: one provider goes end-to-end through the new code before the rest follow.

- [x] Create `tools/ai_openai_compat.py` with `ProviderSpec`, `PROVIDER_SPECS` (all four entries populated), `OpenAiCompatManager`, `_error_detail()`, and the shared response parser. Only the `zai` spec is exercised this phase.
  → verify: `uv run pyright tools/ai_openai_compat.py` clean; `uv run ruff check tools/ai_openai_compat.py` and `uv run ruff format` clean.
- [x] Write `tests/tools/test_ai_openai_compat.py`, porting the payload/parse assertions from `tests/tools/test_ai_zai_manager.py` and adding cases for each of the five real error bodies recorded in the spec (nested `error` with int code, nested with string code, RFC 7807 `detail`, plain-text body, no response object).
  → verify: `uv run pytest tests/tools/test_ai_openai_compat.py` — all pass; assertions must cover all five error shapes, not just the nested one.
- [x] Point `AIManager` at the new class for `zai` only; leave the other three imports as they are.
  → verify: `uv run pytest tests/tools/test_ai_manager.py` passes; then ask the user to send one Z.ai request from the editor and confirm the reply arrives and the status line reads `Success`.

## Phase 2 — Migrate the remaining three, delete the old modules

- [x] Switch `AIManager` to build `deepseek`, `openrouter` and `nvidia` from `OpenAiCompatManager`, and delete `tools/ai_zai_manager.py`, `tools/ai_deepseek_manager.py`, `tools/ai_open_router.py`, `tools/ai_nvidia.py`.
  → verify: `rg -n "ai_zai_manager|ai_deepseek_manager|ai_open_router|ai_nvidia" --hidden` returns nothing outside `kamma/` and `graphify-out/`.
- [x] Carry the DeepSeek-specific coverage over from `tests/tools/test_ai_deepseek_manager.py` (the `_format_empty_content_status` cases — `finish_reason` plus `usage`, and the `reasoning_content` fallback) into the merged test file, then delete `tests/tools/test_ai_zai_manager.py` and `tests/tools/test_ai_deepseek_manager.py`.
  → verify: `uv run pytest tests/tools/` passes; the merged file's test count is at least the sum of what the two deleted files contributed.
- [x] Add a test asserting the DeepSeek defect is fixed: a 400 with a nested error body must surface the API's message in `status_message`, never `post_request returned None`.
  → verify: the new test fails against the old behaviour and passes against the new.
- [x] Add tests for the uniform success/truncation statuses: `finish_reason == "stop"` → exactly `"Success"`; `finish_reason == "length"` with content → a status naming the finish reason; `finish_reason == "length"` with `content: None` (the real OpenRouter truncation shape) → `content is None` and an informative status.
  → verify: `uv run pytest tests/tools/test_ai_openai_compat.py` passes.
  → verify: ask the user to send one request each through DeepSeek, OpenRouter and NVIDIA from the editor and confirm all three answer. NVIDIA is in no fallback chain, so it must be selected explicitly.

## Phase 3 — Dependency and repo-wide checks

- [x] Remove `openai>=1.54.4` from the `tools` dependency group in `pyproject.toml` and run `uv sync --all-groups`.
  → verify: `uv run deptry .` does not report `openai` as unused or missing; `rg -n "^\s*(from|import) openai" --hidden` returns nothing.
- [x] Run the repo-wide gates.
  → verify: `uv run pytest tests/` fully green (full suite, not just `tests/tools/`), `just typecheck` clean, `uv run pyright` clean on every touched file.
- [x] Update `kamma/tech.md` with a dated note recording that the four OpenAI-compatible providers are now one module and that `openai` is no longer a dependency.
  → verify: the note is present and dated 2026-08-25.
- [x] Run `graphify update .` so the knowledge graph reflects the deleted modules.
  → verify: `graphify query "ai provider manager"` no longer returns the deleted module names.
  → NOTE: first attempt was marked done off a backgrounded command that had not finished — caught by review finding A2. Re-run to completion and verified: `graphify-out/graph.json` now holds 855 references to `ai_openai_compat` and 0 to the four deleted modules.

## Deviations from the plan as written

Recorded as they happened, per the drift gate.

1. **Phase 1's "wire Z.ai only" step was merged into Phase 2.** All four providers
   share one code path and one test file, so staging the wiring one provider at a
   time produced no information the tests did not already give.
2. **The spec's claim that no caller imports a provider class directly was wrong.**
   `scripts/extractor/extract_cone.py` imported `OpenRouterManager` and checked
   `manager.client` — an attribute the shared class does not have. Found by the
   post-delete sweep, not by the original survey, which counted the file's matches
   without reading them. Fixed in the same phase: it now builds
   `OpenAiCompatManager("openrouter")` and checks `manager.api_key`.
3. **Two CLI test files stubbed the deleted modules into `sys.modules`.**
   `tests/tools/test_ai_claude_manager.py` and `tests/tools/test_ai_gpt_manager.py`
   injected fake `ai_deepseek_manager` / `ai_open_router` modules. `AIManager` no
   longer imports those, and the tests patch `config_read` to `None` so no compat
   provider is built — the stubs were removed rather than repointed.
4. **Dropping `tencent/hy3:free` was added to scope** at the user's request after the
   probe found it dead. `ai_models.json` now lists 10 default models, not 11.
6. **`tools/ai_models.json` also carries the user's own swap** of the OpenRouter
   `z-ai/glm-5.2` entry for `stealth/ox-alpha`. Not made by this thread; the user
   confirmed it is theirs and asked for it to ride along in this commit.

5. **Removing `openai` also uninstalled `jiter` and `tqdm`** as transitives. Verified
   safe: the only direct `tqdm` importers are inside the `other-dictionaries` and
   `sc-data` submodules, and `other-dictionaries` declares `tqdm` in its own
   `pyproject.toml`.

## Results

| Check | Result |
|---|---|
| `uv run pytest tests/tools/` | 623 passed, 7 deselected (pre-review) |
| `uv run pytest tests/` (full suite) | 1796 passed, 12 deselected (post-review) |
| `just typecheck` (pyrefly, repo-wide) | 0 errors |
| `uv run pyright` on every touched source file | 0 errors |
| `uv run pyright --project /dev/null` on the new test file | 0 errors (a plain run is a no-op — `tests` is excluded) |
| `uv run deptry .` | no `openai` finding outside `archive/`; the 577 reported issues are pre-existing and unrelated |
| Net lines | 745 deleted across four modules, 289 added in one; `openai` dependency removed |

Live smoke completed 2026-08-25: all four providers returned content through the new
class — directly, forced through `AIManager`, and via the default fallback chain. Bad
model names surfaced each API's own message, including DeepSeek, which previously
reported only `post_request returned None`.

Review outcome and the fixes applied afterwards are in `review.md`.

## Phase 4 — Review

- [x] Run `/kamma:3-review`, plus CodeRabbit and an independent from-scratch audit as parallel subagents.
  → verify: `review.md` written, with findings triaged and every real issue fixed.
  → 13 findings across both reviewers, one High (retry loss on the direct-caller path,
    a genuine regression the spec's reasoning missed) plus one self-found. All fixed or
    explicitly accepted with a reason. 11 new tests added for the transport path.

## Out of scope (report, do not fix)

- `tencent/hy3:free` being dead in `ai_models.json`, and NVIDIA having no entry in any chain.
- Pydantic schema validation of AI output — the valuable follow-up identified by the research, but it lives in `exporter/analysis/` and `tools/proofreader.py`, not here.
- The Gemini provider, the three CLI providers, and `AIManager`'s own logic.
