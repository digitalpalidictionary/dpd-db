# Spec: consolidate the OpenAI-compatible AI providers

Thread type: refactor (chore). No GitHub issue.
Background research: `kamma/threads/20260825_pydantic_ai_evaluation/research.md`.

## Overview

`tools/` currently holds four provider wrappers — `ai_open_router.py` (192 lines),
`ai_nvidia.py` (167), `ai_deepseek_manager.py` (202) and `ai_zai_manager.py` (184)
— that all do the same thing: POST an OpenAI-shaped `chat/completions` payload to a
base URL, read `choices[0].message.content`, and return an `AIResponse`.

They do it four different ways. `ai_nvidia.py` and `ai_open_router.py` are the same
file modulo comments and one error-handling branch (verified: 62 differing lines,
all cosmetic or the `model_extra["error"]` guard). `ai_deepseek_manager.py` and
`ai_zai_manager.py` are two hand-rolled `requests` implementations of the same POST.

Replace all four with one configurable class, `tools/ai_openai_compat.py`, keeping
each provider's genuine quirks in a data table rather than in duplicated code.

Nothing else in the AI layer changes: `ai_manager.py`'s fallback chain, the Gemini
provider, and the three CLI providers (`claude`, `codex`, `agy`) are untouched.

## What it should do

### New module `tools/ai_openai_compat.py`

A single class `OpenAiCompatManager`, constructed with a provider name, driven by a
module-level `PROVIDER_SPECS: dict[str, ProviderSpec]`. A spec carries:

- `api_key_name` — the `config.ini` `[apis]` option to read.
- `chat_url` — the completions endpoint.
- `models_url: str | None` — for the existing `get_models()` helper.
- `balance_url: str | None` — DeepSeek only.
- `extra_payload: dict[str, Any]` — provider-specific defaults, currently the
  `thinking: {"type": "disabled"}` and `max_tokens: 8192` that DeepSeek and Z.ai send
  and that OpenRouter and NVIDIA do not.

Behaviour of `request()` matches the current DeepSeek/Z.ai path: build the message
list from `prompt_sys` + `prompt`, merge `extra_payload` then caller `**kwargs`, POST
with `requests`, return `AIResponse`. `get_models()` and `balance()` exist only where
the spec supplies a URL.

Error detail extraction extends the Z.ai `_error_detail()` logic. It tries, in order:
the nested `error.code` / `error.message` shape (OpenRouter, DeepSeek, Z.ai); an
RFC 7807 body's `detail` then `title` (NVIDIA, which has no `error` key at all); the
raw response text truncated (NVIDIA answers a bad model with plain text, not JSON);
and finally the exception string. Only the first, third and fourth existed before —
the RFC 7807 branch is new. See "The error extractor must handle three shapes" below.

### Transport: plain `requests`, not the OpenAI SDK

The four providers become one HTTP path. Verified facts behind this choice:

- `from openai import ...` appears in exactly two files repo-wide — `ai_open_router.py`
  and `ai_nvidia.py`, both deleted by this thread. Consolidating on `requests`
  therefore retires the `openai>=1.54.4` dependency entirely rather than spreading it.
- Those two files are the two with **no** test file; `tests/tools/test_ai_deepseek_manager.py`
  (152 lines) and `tests/tools/test_ai_zai_manager.py` (156) cover the `requests` path.
  Building on the tested path is the lower-risk direction.
- Nothing here uses streaming, tools, structured output, or async — the SDK is
  carrying a plain POST.

### Provider settings stay in code, not in `ai_models.json`

`ai_models.json` is hot-reloadable — `AIManager.reload_models()` is wired to a button
in three gui2 views. Providers are constructed once at `AIManager.__init__` and are
**not** rebuilt on reload. Putting base URLs and key names in that file would make the
reload button half-honest. `PROVIDER_SPECS` lives in the new module.

### Accepted behaviour changes

The user approved "allow small improvements". All of the following were confirmed by
live probes against the real endpoints on 2026-08-25 (see "Probe results" below).

1. **DeepSeek starts reporting why it failed.** Today a DeepSeek failure returns the
   status `"post_request returned None"` — the real message is printed to the console
   by `pr.red` inside `_post_request` and then discarded. Live probe, bad model name:
   the API returned a perfectly good explanation ("The supported API model names are
   deepseek-v4-pro, deepseek-v4-flash, ...") and the caller saw none of it. Z.ai got
   this fixed via `_error_detail()`; DeepSeek never did. The shared path fixes it.
   **This is the most valuable behaviour change in the thread.**
2. **OpenRouter stops producing useless status text on an unguarded path.**
   `ai_open_router.py:71` does `completion.model_extra["error"]["message"]` unguarded.
   Probed directly: it does **not** crash — the bare `except Exception` beneath it
   swallows the `KeyError`/`TypeError` and yields
   `"Unexpected error with OpenRouter (m) request after 0.00s: 'error'"` or
   `"... string indices must be integers, not 'str'"`. So this is a message-quality
   defect, not a crash. (Earlier draft called it a crash — corrected by testing.)
   It is reachable in practice: OpenRouter returns HTTP 200 with
   `finish_reason='length'` and `content=None` on truncation (confirmed live).
3. **Empty-reply reporting becomes uniform,** adopting the richest current version —
   the DeepSeek one, which reports `finish_reason` and `usage`.
4. **Success status messages become uniform.** Confirmed live: OpenRouter and NVIDIA
   return `"Success in 11.35s."` / `"Success in 1.01s."` while DeepSeek and Z.ai
   return the bare `"200"`. `AIManager` appends provider detail only when it does not
   start with `"Success"`, so the same outcome is currently logged two different ways.
   The shared path returns `"Success"` on a clean stop and a `finish_reason=...`
   string otherwise, which the existing `AIManager` filter handles correctly.
5. **Per-provider duration strings are dropped.** `AIManager` already times and reports
   every request; OpenRouter and NVIDIA duplicate that in their status message.
6. **OpenRouter and NVIDIA lose the OpenAI SDK's automatic retries.** Verified in the
   installed source (openai 2.41.0, `DEFAULT_MAX_RETRIES = 2`). The SDK retries on
   429 and 5xx, so today a rate-limited provider is retried twice with backoff before
   `AIManager` is allowed to fall back. Dropping that makes fallback immediate, which
   matches how the manager is designed and matches the standing note that Z.ai 429s
   are server overload and should not be retried in bulk jobs.

### The error extractor must handle three shapes, not one

The earlier draft assumed all four providers nest their error under `error.message`.
**Testing refuted this for NVIDIA.** Verified bodies:

| Provider | HTTP | Body shape |
|---|---|---|
| OpenRouter | 400/401/404 | `{"error": {"message": str, "code": int}}` |
| DeepSeek | 400/401 | `{"error": {"message": str, "type": str, "param": null, "code": str}}` |
| Z.ai | 400/401 | `{"error": {"code": str, "message": str}}` |
| NVIDIA | 410 | `{"type", "title", "status", "detail"}` — RFC 7807, **no `error` key** |
| NVIDIA | 404 | plain text `404 page not found` — **not JSON at all** |

So the shared `_error_detail()` must try, in order: a nested `error` dict
(`code` + `message`); an RFC 7807 body (`detail`, falling back to `title`); the raw
response text truncated; then the exception string. The existing Z.ai version covers
only the first, third and fourth — the RFC 7807 branch is new and is what stops
NVIDIA failures from dumping a raw Python dict repr into the status line.

## Probe results (2026-08-25, live endpoints)

Run from a throwaway script; no repository code was modified to obtain these.

- **Payload acceptance — resolved.** Z.ai, DeepSeek and OpenRouter all returned
  HTTP 200 with `finish_reason: "stop"` for the exact payload the shared class will
  send over plain `requests`, including the per-provider `extra_payload`
  (`thinking`/`max_tokens` for Z.ai and DeepSeek, nothing for OpenRouter and NVIDIA).
  Response shape is uniform: `choices[0].message.content` + `choices[0].finish_reason`.
- **NVIDIA is healthy; only its demo model is dead.** `GET /v1/models` returns 200 with
  a full catalogue. `z-ai/glm-5.1` returns 410 "reached its end of life on
  2026-07-02". A live NVIDIA model (`meta/llama-3.1-8b-instruct`) succeeds. An earlier
  reading of this thread's first probe wrongly concluded the endpoint was retired.
- **Truncation.** All three of OpenRouter, DeepSeek and Z.ai report
  `finish_reason: "length"` when capped. OpenRouter additionally returns
  `content: null` in that case; the other two return partial text.

### Configuration problems found while probing

- `tencent/hy3:free` — first OpenRouter entry in `ai_models.json` — was dead:
  HTTP 404, "This model is unavailable for free. The paid version is available now."
  Every request burned one failed attempt on it before moving on. The other five
  OpenRouter models all answered correctly. **Fixed:** the user asked for it to be
  dropped, so it was; the default chain is now 10 models, not 11.
- NVIDIA is registered as a provider but appears in no chain in `ai_models.json`, and
  the model in its own demo block is end-of-life. Nothing in production is broken by
  this, but the provider is effectively unexercised. **Not fixed** — reported only.

## Constraints

- Python 3.13, modern type hints (`dict[str, str]`, `X | None`), `pathlib.Path`.
- Pre-commit gate: touching a file means owning `ruff check`, `ruff format` and
  `pyright` on it. `just typecheck` (pyrefly, repo-wide) must pass before finishing.
- Shared working tree: other agent sessions may be editing this repo. Stage by
  explicit file list; never `git stash`, `git restore`, or a whole-tree reset.
- Do not run the AI scripts live — the user executes those.

## How we'll know it's done

- `tools/ai_open_router.py`, `tools/ai_nvidia.py`, `tools/ai_deepseek_manager.py` and
  `tools/ai_zai_manager.py` no longer exist; `tools/ai_openai_compat.py` replaces them
  in roughly 200 lines including the spec table.
- `uv run pytest tests/tools/` passes, with the DeepSeek and Z.ai coverage carried
  over into one merged test file plus new coverage for the OpenRouter and NVIDIA
  specs, which have none today.
- `uv run pytest tests/` passes (full suite, to catch anything importing these names).
- `just typecheck` and `uv run pyright` are clean on every touched file.
- `openai` is removed from `pyproject.toml` and `uv run deptry .` does not flag it.
- The user confirms a live request through the editor still succeeds on Z.ai,
  DeepSeek, OpenRouter and NVIDIA.

## What's not included

- Pydantic AI. See the research thread — three of nine providers are CLI subprocesses
  the framework cannot model, and nothing here is agentic.
- Pydantic schema validation of AI output. That is the genuinely valuable follow-up
  identified by the research, but it lives downstream in `exporter/analysis/` and
  `tools/proofreader.py`, not in the transport layer. Separate thread.
- The Gemini provider, the three CLI providers, and `AIManager` itself.
- Anything that changes which models are tried or in what order.
