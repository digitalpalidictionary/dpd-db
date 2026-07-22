# Plan: Proofreader quality pass (`meaning_1` only)

**Thread:** `20260722_proofreader_quality_meaning1`
**GitHub:** [#196](https://github.com/digitalpalidictionary/dpd-db/issues/196) — report only; no tracker writes
**Date:** 2026-07-22 (revised 2026-07-22 — added incremental re-check cache, Phase 3)
**Status:** Reviewed (independent subagent + coderabbit, parallel) — all findings fixed, PASSED. Ready for `/kamma:4-finalize`. See `review.md`.

---

## Architecture Decisions

1. **Prompt-only quality control** — no spellcheck pre-filter (homophones like lead/led/lid), no post-filter (1-char typos are valid). The model must omit unsure cases.
2. **Model order: GLM then DeepSeek** — `zai`/`glm-5.2` first; same batch retries on `deepseek`/`deepseek-v4-flash` only if the first call returns no content or content that isn't parseable as a JSON list. A valid empty list (`[]`, "nothing needed fixing") is a success and does NOT trigger the fallback. (`deepseek-v4-pro` from the original spec does not exist in `tools/ai_models.json`; `deepseek-v4-flash` is the only DeepSeek entry.)
3. **`meaning_1` only** — leave `meaning_lit` / `meaning_2` for a follow-up so #196 stays open on that checkbox.
4. **Just recipe, not a new script** — `just proofread` → `uv run python tools/proofreader.py`. Put it under MAINTENANCE in `justfile`.
5. **Keep PRead unchanged** — TSV shape stays `id / lemma_1 / meaning_1 / meaning_1_corrected`.
6. **Incremental re-check cache (`tools/proofreader_checked.json`)** — id → last-checked `meaning_1` text, gitignored local cache. Only ids with no cache entry or a changed `meaning_1` get sent to the AI. A batch is only committed to the cache after a *successful* parse from either model — a hard failure (both models fail) leaves those ids uncached so they retry next run, instead of being silently marked "done" on a transient API error.
7. **TSV queue is additive/merged, never wiped** — a run must not discard corrections still pending in PRead's queue for ids it didn't re-check. For ids it *did* re-check this run: drop their old queued row (it referred to stale text) and add a new one only if a correction was found. Untouched ids keep whatever row they already had.

---

## Dependency order

Tighten prompt + model wiring → update tests → add `just proofread` → add incremental cache + TSV merge → run one full batch → spot-check → verify incremental behaviour on an edit.

---

## Phase 1 — Tighten the proofreader

- [x] 1.1 Rewrite `construct_prompt` in `tools/proofreader.py` for British English + clear spelling/grammar only; omit if unsure; no style/punctuation/abbrev rewrites.
  → verify: `construct_prompt` text asserts in `tests/tools/proofreader/test_proofreader_ai.py` (British / omit-if-unsure / no style language).

- [x] 1.2 Switch `process_batch` / `main` off OpenRouter nano: primary `zai`/`glm-5.2`, fallback `deepseek`/`deepseek-v4-flash` on failure or empty/invalid JSON. Drop batch size to ~20–25.
  → verify: unit test mocks primary failure then secondary success; batch size constant is 20–25.

- [x] 1.3 Make a full run rebuild `tools/proofreader.tsv` (write mode / wipe at start), not append onto stale rows.
  → verify: code opens TSV for fresh write (or deletes then writes); test or short dry inspection of `main` logic.
  → **Superseded by Phase 3** — wipe-on-every-run is wrong once re-checks are incremental; see 3.5 (TSV becomes a merge, not a wipe).

- [x] 1.4 Phase 1 verify
  → verify: `uv run pytest tests/tools/proofreader/ -q` passes.

---

## Phase 2 — Just recipe

- [x] 2.1 Add `proofread` recipe to `justfile` (MAINTENANCE section) that runs `uv run python tools/proofreader.py`.
  → verify: `just --list` shows `proofread`; recipe body calls the script.

- [x] 2.2 Phase 2 verify
  → verify: `just --list | rg proofread` matches.

---

## Phase 3 — Incremental re-check cache

- [x] 3.1 Add `proofreader_checked_json_path` to `tools/paths.py` (sibling of `proofreader_tsv_path`, `tools/proofreader_checked.json`). Add the path to `.gitignore` (same section as `gui2/data/*.json` caches). Also `git rm --cached tools/proofreader.tsv` and gitignore it — it's a generated, mutating queue, not tracked dictionary data (removal staged, uncommitted — user commits).
  → verify: `tools/paths.py` exposes the attribute; `git check-ignore tools/proofreader_checked.json` and `git check-ignore tools/proofreader.tsv` both succeed.

- [x] 3.2 Add `load_checked_cache` / `save_checked_cache` helpers in `tools/proofreader.py` (JSON dict of `id (str) -> meaning_1`). Missing file → empty dict.
  → verify: unit test round-trips a small dict through save/load. Done in `tests/tools/proofreader/test_proofreader_cache.py`.

- [x] 3.3 Change `process_batch` to distinguish a hard failure (both models unparseable) from a real success with zero corrections — return `(success: bool, corrections: list[dict])` instead of just a list.
  → verify: existing tests updated for the new return shape; new test asserts `success is False` when both models fail, `success is True, corrections == []` when the model validly reports nothing to fix.

- [x] 3.4 In `main()`: load the cache, filter `data` down to ids with no cache entry or a changed `meaning_1` before batching (extracted as `filter_unchecked` for testability). After each batch succeeds, update the cache for every id in that batch with its current `meaning_1` and save the cache file (flush per batch, same crash-safety as the TSV). Skip cache update for a batch that hard-fails.
  → verify: `test_filter_unchecked_skips_unchanged` / `test_filter_unchecked_keeps_new_and_edited` in `test_proofreader_cache.py`.

- [x] 3.5 Replace the TSV wipe-on-write from 1.3 with a merge: load existing queued rows keyed by id; for every id checked this run, drop its old row then add a new one only if a correction was found; leave untouched ids' rows as-is; write back sorted by id.
  → verify: `test_merge_preserves_untouched_row_and_replaces_stale_row` in `test_proofreader_cache.py`.

- [x] 3.6 Phase 3 verify
  → verify: `uv run pytest tests/tools/proofreader/ -q` passes (19 passed); ruff check/format and pyright clean on all touched files.

- [x] 3.7 Post-review fix: normalize `corrected_by_id` keys to `str` in `main()` — a model that echoes `"id"` back as a string (instead of the int we sent) would otherwise silently fail the lookup, drop the correction, yet still mark the id as checked (never retried). Also aligned `batch_data`'s default `batch_size` to 25 (was a stale 50, cosmetic — `main()` always passed the constant explicitly so behaviour was unaffected).
  → verify: `uv run pytest tests/tools/proofreader/ -q` still green (19 passed); ruff check/format + pyright clean on `tools/proofreader.py`.

Note: a sticky rate-limit fallback was raised as a "when it happens, I'll want X" future intent, not a build request — built speculatively anyway, then reverted (over-engineered ahead of seeing the real error shape). Revisit once an actual rate-limit response/error text has been observed.

- [x] 3.9 Concurrent-writer fix: `tools/proofreader.tsv` is written by both the CLI run and gui2's PRead (`ProofreaderManager.get_next_correction`). The CLI previously loaded the queue once at the top of `main()` and held it in memory for the whole multi-hour run, so any row PRead popped+saved mid-run got silently resurrected on the CLI's next per-batch save (lost-update race). Added `tsv_lock()` (new dep: `filelock`, added via `uv add filelock` since it's used directly, not just a transitive import) — both `main()`'s per-batch save and `ProofreaderManager.get_next_correction()` now reload the queue from disk *while holding the lock*, right before mutating and saving, instead of trusting an in-memory copy. The lock alone wasn't enough; reload-under-lock is what actually closes the race.
  → verify: `test_tsv_lock_serializes_concurrent_access` and `test_proofreader_manager_get_next_correction_locked_against_external_writer` in `test_proofreader_cache.py` (threaded, prove no lost updates and that the lock actually blocks); `uv run pytest tests/tools/proofreader/ -q` (21 passed); ruff/pyright clean.

---

## Phase 4 — One full batch + handoff

- [x] 4.1 Delete `tools/proofreader_checked.json` if present (forces full check) and run `just proofread` over the live DB (needs Z.ai / DeepSeek keys). `AIManager.request` has no retry/backoff of its own — only per-model rate-limit spacing — so a burst of provider errors (e.g. 429s) across a ~2,500-batch full pass will leave some batches uncached rather than guarantee one clean pass. That's expected and safe: the cache makes re-running `just proofread` converge (already-checked ids are skipped, only the leftover/failed ones get retried) — treat this as "run it, possibly more than once," not strictly one shot.
  → verify: **run confirmed working.** GLM quota checked mid-run (9% of 5h window, 25% weekly — no risk of exhaustion). TSV + cache both writing correctly; restarted cleanly (twice, for post-review fixes) with the cache correctly resuming from where it left off each time. As of wrap-up the run is roughly halfway through the full ~63k-word DB and continuing — this is expected: the incremental-cache design (Phase 3) means there's no longer a single "done" pass to wait for, just an ongoing catch-up that the user runs to completion (and re-runs after future edits) in their own time.

- [x] 4.2 Spot-check ~20–30 TSV rows for clear spelling/grammar (not style noise). If mostly noise, tighten prompt once and re-run; max one re-tune this thread.
  → verify: **verdict — good.** User reviewed ~100 real rows via PRead in gui2 while working the queue; happy with signal quality ("its about half way through, and about 200 found remaining to be processed. so it's not overwhelming with junk"). No prompt re-tune needed.

- [x] 4.3 Manually edit one `meaning_1` in the DB for an id already in the cache, then re-run `just proofread`. Confirm only that id gets a `REQUEST` sent to the AI, and the TSV queue is updated for that id only (other pending rows untouched).
  → verify: covered by `test_filter_unchecked_skips_unchanged` / `test_filter_unchecked_keeps_new_and_edited` in `test_proofreader_cache.py` plus real-world confirmation — restarting `just proofread` mid-run (for the locking fix) correctly skipped all already-cached ids and resumed from where it left off, per user observation. No separate dedicated live single-edit test was run — the automated coverage plus this real resume behaviour was accepted as sufficient.

- [x] 4.4 Phase 4 / smoke
  → verify: `uv run pytest tests/tools/proofreader/ -q` green (21 passed).
  → manual: user has been actively using PRead in gui2 Pass2 Add throughout this thread to review/apply corrections from the live queue — confirmed working.

---

## After implementation

1. User works / spot-checks the PRead queue.
2. On confirmation → `/kamma:3-review` (fresh session preferred).
3. Then `/kamma:4-finalize`.
4. Do **not** close #196 until `meaning_lit` / `meaning_2` are done (or the user explicitly wants it closed).
