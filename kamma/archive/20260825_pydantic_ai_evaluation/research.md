# Research study: would Pydantic AI benefit `tools/ai_*`?

Date: 2026-08-25
Status: research only — the verdict here led to `20260825_ai_provider_consolidation`.
Question: is there any benefit to refactoring the `tools/ai_…` layer onto Pydantic AI?

> Note: this file was deleted from disk by a concurrent agent session on 2026-08-25
> before it was ever committed, and rewritten from the original analysis. The
> findings and numbers are unchanged; they were all re-derived from the sources
> cited in section 7.

---

## 1. What existed at the time of the study

### 1.1 Files and size

| File | Lines | Role |
|---|---|---|
| `tools/ai_manager.py` | 327 | Facade: provider registry, model fallback chain, per-model delay/timeout, `AIResponse` |
| `tools/ai_open_router.py` | 192 | OpenAI SDK against `openrouter.ai/api/v1` |
| `tools/ai_nvidia.py` | 167 | OpenAI SDK against `integrate.api.nvidia.com/v1` (near-duplicate of the above) |
| `tools/ai_deepseek_manager.py` | 202 | raw `requests` POST to DeepSeek + balance/models endpoints |
| `tools/ai_zai_manager.py` | 184 | raw `requests` POST to Z.ai coding-plan endpoint + models endpoint |
| `tools/ai_gemini_manager.py` | 179 | `google-genai` client, the only provider supporting grounding |
| `tools/ai_claude_manager.py` | 74 | subprocess wrapper around the `claude` CLI |
| `tools/ai_gpt_manager.py` | 89 | subprocess wrapper around the `codex` CLI |
| `tools/ai_antigravity_cli.py` + `_models.py` | 333 | subprocess wrapper around the `agy` CLI, incl. background auth probe |
| **total** | **1747** | |
| tests `tests/tools/test_ai_*.py` | 1465 | |

### 1.2 Contract

Every provider exposed the same method:

```python
def request(self, prompt, model, prompt_sys=None, timeout=60.0, grounding=False, **kwargs) -> AIResponse
```

`AIResponse` is a two-field `NamedTuple`: `content: str | None`, `status_message: str`.
Nothing else crosses the boundary — no message history, no tool calls, no token
counts, no streaming.

`AIManager.request()` walks a list of `(provider, model, delay, timeout)` tuples loaded
from `tools/ai_models.json`, skipping providers that failed to initialise, sleeping out
the per-model delay, catching every exception, and accumulating error strings. The
first non-`None` content wins.

### 1.3 Live configuration

Default chain, in order: `zai/glm-5.2`, `deepseek/deepseek-v4-pro`, `zai/glm-5-turbo`,
`deepseek/deepseek-v4-flash`, six OpenRouter models, then `antigravity_cli`. Grounded
chain: `gemini/gemini-2.5-flash`. **Every `delay` was `0`** — the rate-limiting
machinery in `AIManager` is dormant. `claude`, `codex` and `nvidia` were registered
providers appearing in no chain; reachable only by an explicit `provider_preference`.

### 1.4 Consumers

`AIManager` is used by `gui2/` (ai search window, pass1 and pass2 auto controllers,
the toolkit singleton, plus a "reload models" button in three views);
`exporter/analysis/` (translate core, retry, study passage, the two translate
entry points); `tools/proofreader.py`; and `scripts/extractor/_ai_extraction.py`.

All call sites are **synchronous**, single-turn, and pass only `prompt` / `prompt_sys` /
`model` / `provider_preference` / occasionally `timeout`. No call site uses `**kwargs`,
message history, streaming, or tools.

### 1.5 The real pain point: hand-rolled JSON extraction

Three separate ad-hoc parsers sit downstream of `AIResponse.content`:

- `exporter/analysis/ai_response.py::_parse_ai_json` — strips ```` ```json ```` fences,
  `json.loads`, and on failure falls back to `_extract_partial_response`, which
  **regex-scrapes** `"literal_translation"` and `"score"` values out of malformed text.
- `exporter/analysis/ai_response.py::_extract_word_key_map` — detects that a model
  returned a completely different schema (a flat word→key map, or one wrapped in
  `{"disambiguation": …}`) and salvages it. Its docstring names Antigravity as the
  repeat offender.
- `tools/proofreader.py::_parse_corrected_list` — its own fence-stripping + `json.loads`.

`translate_core.py` additionally has a **reformat round-trip**: when the first response
fails to parse, it sends the bad output back to the model asking for the correct schema
(`_reformat_response`, ~60 lines). Every JSON system prompt carries a
`NO_TOOLS_INSTRUCTION` constant to stop models emitting tool calls.

Roughly 250–300 lines of fragile schema-wrangling, existing precisely because the
transport layer returns an unvalidated string.

---

## 2. What Pydantic AI offers

Verified against current docs (Context7, `/pydantic/pydantic-ai`).

| Capability | Relevant here? |
|---|---|
| `FallbackModel(m1, m2, …)` — try models in sequence, switching on exception classes, exception-predicate callables, **or response-content predicates** | Yes — direct analogue of the chain, plus semantic-failure fallback we do not have |
| `output_type=SomeBaseModel` with `PromptedOutput` / `NativeOutput` / `ToolOutput` modes; validates and **auto-retries on validation failure** | Yes — this is the actual win |
| OpenAI-compatible providers via `OpenAIChatModel` + custom `base_url` | Yes — covers OpenRouter, NVIDIA, DeepSeek, Z.ai in one class |
| `GoogleModel` with Google Search grounding | Yes — replaces the Gemini manager |
| Per-model `ModelSettings` (temperature, max_tokens, timeout) inside a fallback chain | Yes — matches the per-model timeout column |
| `run_sync()` | Yes — all call sites are sync |
| Custom `Model` subclass for unsupported backends | Needed for the three CLI providers; there is no subprocess model |
| Agents, tools, MCP, message history, streaming, durable execution, evals, Logfire | **No** — nothing here is agentic |

Pydantic v2 was already installed transitively (fastapi, openai, mcp). `pydantic-ai-slim`
with the `openai` + `google` extras would add roughly `griffe`, `genai-prices`,
`typing-inspection`, `eval-type-backport`, `opentelemetry-api`. Not enormous, but `gui2`
is packaged with Flet, so anything on the toolkit's import path lands in the app bundle.

---

## 3. The blocker: three of nine providers are CLI subprocesses

`claude`, `codex` and `agy` are not HTTP APIs. They exist specifically so requests ride
the user's **CLI subscription** rather than metered API keys. Pydantic AI has no
subprocess model; each would need a custom `Model` subclass implementing `request()`,
`ModelRequestParameters` handling, and message-part translation — meaningfully *more*
code than the current 74/89/248-line wrappers, and no structured-output benefit, since
a CLI returns free text either way.

`antigravity_cli` is not optional: it is the last-resort entry in the live default
chain, and `AIManager` carries dedicated machinery for it (background auth probe
thread, `_ensure_antigravity_ready()`, gating it out of the chain until the probe
succeeds). None of that has an equivalent in Pydantic AI's lifecycle.

So "refactor to Pydantic AI" could not be a clean replacement. It would be: six
providers become ~40 lines of model construction, three become bespoke `Model`
subclasses, and a hybrid dispatch layer sits over both. Net line count flat to worse;
conceptual complexity clearly worse.

---

## 4. Other things the current layer does that Pydantic AI does not

- **Hot reload.** `reload_models()` re-reads `ai_models.json` while `gui2` is running;
  three views expose a button for it. A `FallbackModel` is constructed once.
- **Per-model throttling.** `model_last_request` keyed by `provider:model`. Dormant
  today (all delays `0`) but it is the mechanism if a provider starts rate-limiting.
- **Rich failure strings.** The Z.ai manager digs the `[1305] service temporarily
  overloaded` code out of the HTTP body; OpenRouter/NVIDIA do the same for
  `APIError.body`. `AIResponse.status_message` is displayed in the gui2 UI and in
  proofreader logs. Pydantic AI raises typed exceptions instead.
- **Never raises.** `AIManager.request()` returns `AIResponse(content=None, …)` on total
  failure and every consumer is written against that. Pydantic AI raises
  `FallbackExceptionGroup` when all models fail.

---

## 5. Where the genuine benefit is

Strip away the transport and one thing remains: **the codebase has no schema validation
on AI output, and pays for it in three parsers, one regex salvager, one wrong-schema
detector, one reformat round-trip, and a `NO_TOOLS_INSTRUCTION` constant.**

Pydantic AI's `PromptedOutput` + `output_type` is exactly that fix. But the benefit
lives **downstream in `exporter/analysis/`, not in `tools/ai_*`** — and the same benefit
is available without Pydantic AI at all: a `pydantic.BaseModel` plus
`model_validate_json()` on the existing `AIResponse.content` gets validation and typed
output today, using a library already installed.

---

## 6. Verdict

**No refactor of `tools/ai_*` to Pydantic AI.**

1. Three of nine providers are CLI subprocesses Pydantic AI cannot model without custom
   `Model` subclasses larger than the wrappers they replace — and one is live in the
   default chain.
2. Nothing in the codebase is agentic. Single-turn, sync, no tools, no history, no
   streaming. The framework's centre of gravity is unused.
3. Four behaviours (hot model reload, per-model throttle keys, provider-specific
   human-readable error strings, never-raises contract) would all need rebuilding.
4. `AIManager` is stable, covered by ~1465 lines of tests, and understood. Churning it
   buys type-safety at a boundary that has no type-safety problem — the boundary is
   `str | None`, which is honestly what a text completion is.

**Recommended instead, and now underway:** consolidate the four duplicated
OpenAI-compatible providers into one module — see
`kamma/threads/20260825_ai_provider_consolidation/`. Separately, and still open:
introduce `pydantic.BaseModel` schemas for the AI JSON contracts in
`exporter/analysis/` and `tools/proofreader.py`. That attacks the actual fragility
without adding a framework.

Confidence: 8/10. Main uncertainty is whether the CLI providers are still valued; if
`claude`, `codex` and `agy` were dropped, Pydantic AI becomes a reasonable (though
still not compelling) option.

---

## 7. Facts verified during this study

- Provider file line counts: `wc -l tools/ai_*.py` → 1747 total.
- Test line counts: `wc -l tests/tools/test_ai_*.py` → 1465 total.
- Every `delay` in `ai_models.json` was `0` — read from the file directly.
- `claude`, `codex`, `nvidia` appeared in neither `default_models` nor `grounded_models`.
- No call site of `AIManager.request()` passes extra `**kwargs`.
- `pydantic` 2.13.4 and `pydantic_core` already present in `.venv`; `pydantic` is a
  declared dependency of `fastapi`, `openai` and `mcp` in `uv.lock`.
- Pydantic AI capabilities checked against current docs, not memory: `FallbackModel`
  semantics and `fallback_on` handlers; `PromptedOutput` / `NativeOutput` / `ToolOutput`;
  per-model `ModelSettings` in a chain; custom `Model` subclassing being required for
  non-OpenAI-compatible APIs.

**One claim from this study was later found wrong** by the consolidation thread's live
probing: it asserted no caller imports a provider class directly. In fact
`scripts/extractor/extract_cone.py` imported `OpenRouterManager` and used its `.client`
attribute. The survey counted that file's matches without reading them.
