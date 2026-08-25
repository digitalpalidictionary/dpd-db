# Review: consolidate the OpenAI-compatible AI providers

Date: 2026-08-25
Reviewers: CodeRabbit CLI (`coderabbit review --agent --uncommitted --include-untracked`)
and an independent from-scratch adversarial audit, run as parallel subagents.

## Coverage — what was actually checked

- **CodeRabbit:** all 23 changed files, with both new untracked files confirmed present
  in its `reviewedFiles` list. 3 findings, all severity `minor`.
- **Independent audit:** read-only. Diffed every deleted module against the new shared
  class from `git show HEAD:…`; swept the whole repo with `rg --hidden` for the deleted
  names and for `.client`; re-ran `just typecheck`, `ruff check` and the AI tests
  independently; verified the dependency removal and its transitives; compared the
  merged test file against both deleted test files. 10 findings.
- **Live smoke:** all four providers exercised through the new class — directly, forced
  through `AIManager`, and via the default fallback chain. All returned content. Error
  paths checked with a bad model name per provider.

**Not covered:** no test drives a real network call (by design); the Gemini and three
CLI providers were out of scope and untouched; `deptry`'s 577 repo-wide findings are
pre-existing and were not triaged beyond confirming none concern `openai`.

## Findings and disposition

| # | Severity | Finding | Disposition |
|---|---|---|---|
| A1 | High | Dropping the SDK's 2 automatic retries has no fallback safety net in `scripts/extractor/extract_cone.py`, which builds the provider directly. One transient 429/5xx would end a whole batch run — the spec's justification only covered `AIManager`. | **Fixed.** `OpenAiCompatManager` gained `max_retries` (default `0`, preserving the immediate-fallback behaviour `AIManager` and the Z.ai overload note both want). `extract_cone.py` constructs with `max_retries=2`, restoring exactly what the SDK gave it. Backoff 0.5s doubling; only 408/409/429/5xx and connection/timeout errors retry — a bad model name never does. |
| A2 | Medium | `graphify update .` was marked `[x]` but never completed; the graph still held 460 references to the deleted modules and none to the new one. | **Fixed.** The step was un-ticked, then re-run to completion; the graph now holds 855 references to `ai_openai_compat` and 0 to the four deleted modules. The claim was false and should not have been marked done off a backgrounded command. |
| A3 | Medium | `tests/tools/test_ai_openai_compat.py:241` had a real pyright error (`list` passed where `dict \| None` was annotated). Plain `uv run pyright <file>` reported 0 errors only because `[tool.pyright].exclude` swallows `tests/` — exactly the trap recorded in `kamma/tech.md` on 2026-08-21. | **Fixed.** Annotation corrected; verified with `uv run pyright --project /dev/null`, which bypasses the exclude. The original "pyright clean on every touched file" claim was unearned. |
| A4 | Medium | No test exercised `_post_request` — the actual SDK→`requests` swap. Every test stubbed it out. `get_models()` and `balance()` success paths were untested and callerless. | **Fixed.** Added 11 tests driving the real `_post_request` with a monkeypatched `requests.post`: payload serialisation, header and timeout passing, retry/no-retry behaviour, connection-error handling, plus `get_models()` and `balance()` success, decode-error and bad-shape paths. |
| A5 | Low-Med | An undocumented model swap (`z-ai/glm-5.2` → `stealth/ox-alpha`) appeared in `tools/ai_models.json` alongside this thread's change. | **Resolved, not a defect.** The user confirmed they made it and asked for it to be included in this commit. |
| A6 | Low | DeepSeek's `deepseek-chat` model default was silently lost. | **Accepted and documented** in the spec. `model` is a required `str` and every caller passes one, so the branch was already unreachable; reintroducing it would be dead code. |
| A7 | Low | All four deleted modules had `__main__` smoke blocks; the new one had none, leaving `balance()`/`get_models()` unreachable from anywhere. | **Fixed.** Added a `__main__` block taking a provider and optional model, printing balance (where the spec has an endpoint), the model list, and a test request. |
| A8 | Low | `get_models()`'s `except ValueError` was unreachable — `requests.exceptions.JSONDecodeError` subclasses `RequestException`, which was caught first. | **Fixed.** Transport and decode are now caught in separate `try` blocks in both `get_models()` and `balance()`, making both branches reachable. |
| A9 | Low | An HTTP 200 carrying `{"error": …}` and no `choices` fell into the raw-body branch instead of structured extraction, losing what the old OpenRouter code deliberately read. | **Fixed.** Extracted `_nested_error_message()`, now shared by `_error_detail()` and `_parse_chat_response()`; the no-choices path surfaces the provider's own message when present. |
| A10 | Nit | `json=payload` serialises with `allow_nan=False`, adding an uncaught `ValueError` path the old `json.dumps` did not have. | **Fixed** by reverting to `data=json.dumps(payload)`, which is byte-for-byte what the deleted modules sent. |
| C1 | Minor | Spec described the dropped model as an unfixed out-of-scope problem after it had been fixed. | **Fixed** in the spec. |
| C2 | Minor | Spec claimed NVIDIA nests its error message like the others — the opposite of what the code does and documents. | **Fixed** in the spec; the implementation was already correct. |
| C3 | Minor | `balance()` returned unvalidated JSON. | **Fixed** as part of A8 — decode error handled, non-dict payload rejected. |
| S1 | — | Self-found before review: the module-level spec table built its `thinking` dict once, so every request shared one nested object; the deleted code rebuilt it per call. | **Fixed.** `copy.deepcopy` of the provider extras per request, with a regression test asserting a mutated payload cannot leak into the next request or into the spec table. |

## Confirmed clean by the audit

Payload merge order (caller kwargs correctly override provider defaults; extras cannot
clobber `messages` or `model`); the `Response.__bool__` truthiness trap avoided
everywhere via `is None`; no broken callers repo-wide; the `.client` → `.api_key`
conversion in the extractor semantically correct; the `openai` removal genuinely sound
including transitives (`tqdm` resolves from the submodule's own `pyproject.toml`); all
five real error bodies covered with exact-string assertions; every assertion from both
deleted test files carried over; no circular import.

One thing survived by coincidence rather than design and is worth knowing:
`scripts/extractor/_ai_extraction.py` tests `"Success" in status_message`, which is
satisfied by both the old `"Success in 11.35s."` and the new exact `"Success"`.

## Gates after fixes

| Check | Result |
|---|---|
| `uv run pytest tests/` | 1796 passed, 12 deselected |
| `uv run pytest tests/tools/test_ai_openai_compat.py` | 41 passed |
| `just typecheck` (pyrefly, repo-wide) | 0 errors |
| `uv run pyright` on touched source files | 0 errors |
| `uv run pyright --project /dev/null` on the new test file | 0 errors |
| Live smoke, all four providers | all returned content, direct and via the fallback chain |

## Verdict

Ready. Every finding was either fixed or explicitly accepted with a reason recorded.
The one High finding was a genuine regression the spec's reasoning had missed.
