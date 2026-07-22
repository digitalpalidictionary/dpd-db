# Spec: Proofreader quality pass (`meaning_1` only)

**GitHub:** [#196](https://github.com/digitalpalidictionary/dpd-db/issues/196) — Automated proofreading
**Thread:** `20260722_proofreader_quality_meaning1`
**Date:** 2026-07-22 (revised 2026-07-22 — added incremental re-check cache)

---

## Overview

Tighten the AI proofreader so a full-database run over `meaning_1` produces a short, usable queue of **obvious British-English spelling and grammar fixes** — not hundreds of iffy style rewrites. Then make repeat runs cheap: check each word exactly once until its `meaning_1` text actually changes.

Expose the run as:

```bash
just proofread
```

Gui2 **PRead** stays as it is (loads the next `meaning_1_corrected` into the add field).

---

## Original behaviour (before this thread)

| Piece | Before |
|---|---|
| Entry point | `python tools/proofreader.py` — no just recipe |
| Model | Hardcoded OpenRouter free nano (`nvidia/nemotron-3-nano-…:free`) |
| Prompt | Soft — invites style, punctuation, and "British rewrite" noise |
| Batch size | 100 |
| Output | Appends to `tools/proofreader.tsv` forever |
| Fields | `id`, `lemma_1`, `meaning_1` → `meaning_1_corrected` |
| Gui2 | Pass2 Add **PRead** pops next TSV row into `meaning_1_add` |
| Re-runs | No memory — every run re-checks all 63k+ rows from scratch |

That combination is why the queue filled with iffy items, and why re-running was always a full, expensive re-scan.

---

## Usage pattern this is designed around

1. **First pass** — one full top-to-bottom run over every non-empty `meaning_1` (~63k rows as of 2026-07-22).
2. **After that** — the user edits `meaning_1` for scattered, unpredictable ids across the whole range (via gui2, PRead, or direct fixes), not in any id order.
3. Re-running the proofreader after edits should **only** re-check the ids whose `meaning_1` text actually changed since it was last checked — never a full re-scan, and never miss an edited word no matter where its id falls.

## What it should do

1. **Prompt** — Correct only clear spelling mistakes and clear grammar errors in `meaning_1`. Use British English. If unsure, omit the entry. Do **not** change meaning, word choice (except true typos), punctuation style, semicolon conventions, or abbreviations like `(comm)`.
2. **Models** — Try `zai` / `glm-5.2` first. If that call returns no content, or content that isn't parseable as a JSON list, retry the same batch on `deepseek` / `deepseek-v4-flash`. A valid JSON list that's empty (`[]`, meaning "nothing needed fixing") is a **success**, not a failure — it does not trigger the fallback. Only if both models fail to return parseable JSON is the batch treated as **not checked** (see incremental cache below), so it's retried on the next run rather than silently skipped forever.
3. **Batch size** — ~20–25 so each line is actually inspected.
4. **Incremental re-check cache** — Persist, per headword id, the exact `meaning_1` text that was last sent to the AI (`tools/proofreader_checked.json`, gitignored — a local, regenerable work-log, not dictionary data). On each run:
   - Load the cache.
   - Only send ids whose current `meaning_1` differs from the cached value (or has no cache entry at all) to the AI.
   - After a batch gets a **successful** parse from either model (even if it finds zero corrections), record the current `meaning_1` for every id in that batch into the cache and save it. A batch that fails on **both** models is left out of the cache so it's retried next run.
   - Deleting the cache file forces a full re-check of everything (used for a fresh test run).
5. **Output queue (`tools/proofreader.tsv`) is additive, not wiped** — since incremental runs must not discard corrections the user hasn't worked through PRead yet:
   - Load any existing queued rows (keyed by id).
   - For every id that was freshly (re-)checked this run: drop its old queued row (if any — it referred to stale text), then add a new row only if this run's check found a correction.
   - Ids that were skipped (unchanged, already checked) keep whatever row they already had in the queue untouched.
   - Write the merged queue back out, sorted by id, header + `id / lemma_1 / meaning_1 / meaning_1_corrected` columns unchanged.
6. **Just recipe** — `just proofread` runs the pipeline from the repo root.
7. **One full batch** — After the code lands, run one complete `just proofread` (with an empty/fresh cache) over all non-empty `meaning_1` rows so PRead has a real queue.

---

## Assumptions

- Closing #196's remaining checkbox (`meaning_lit` / `meaning_2`) is **out of scope** this thread. The issue stays open for that.
- "Full batch" means one complete pass over every headword with a non-empty `meaning_1`, not a sample.
- `tools/proofreader_checked.json` is a local cache, not portable dictionary data — gitignored, like `gui2/data/*.json` caches.
- `tools/proofreader.tsv` is likewise removed from git tracking and gitignored — it's a generated, constantly-mutating work queue (PRead pops rows off it), not canonical dictionary data.
- The cache stores the raw `meaning_1` string per id (not a hash) — simplest, no collision risk, and small enough (63k short strings) that this is not a size concern.
- Unit tests in `tests/tools/proofreader/` cover prompt text, model-fallback wiring, and cache-driven skip/requeue logic. No live-API calls in CI.
- Z.ai and DeepSeek keys are already in `config.ini`.

---

## Constraints

- Touch `tools/proofreader.py`, its tests, `justfile`, `.gitignore`, `tools/paths.py` (for the cache path), and `pyproject.toml`/`uv.lock` (added `filelock` as an explicit dependency for the cross-process TSV lock) — plus the generated TSV and cache file when running.
- `tools/proofreader.tsv` is written by both this CLI and gui2's PRead (`ProofreaderManager.get_next_correction`) — both sides must reload the queue from disk while holding a shared file lock (`tsv_lock()`) right before mutating/saving, not trust an in-memory copy, or one side silently undoes the other's write.
- No spellchecker pre-filter.
- No post-filter of 1-char diffs.
- No two-pass review this thread.
- Do not change gui2 PRead behaviour for `meaning_1`.

---

## How we'll know it's done

- [x] `just proofread` runs end-to-end and writes `tools/proofreader.tsv` + `tools/proofreader_checked.json` — confirmed via a real production run (~63k words, checked mid-run against GLM quota, restarted cleanly twice for post-review fixes).
- [x] Re-running with an unchanged DB checks nothing (all ids already cached) and leaves the TSV queue untouched — covered by `filter_unchecked` unit tests; confirmed in practice on each restart.
- [x] Editing one `meaning_1` and re-running only re-checks that id, regardless of where its id falls in the range — covered by `filter_unchecked` unit tests (`test_filter_unchecked_keeps_new_and_edited`); no separate dedicated live single-edit test was run (noted/accepted in plan.md 4.3).
- [x] Prompt + model fallback + cache skip/requeue logic covered by unit tests — `tests/tools/proofreader/` (23 tests as of review).
- [x] Spot-check of the TSV shows mostly clear spelling/grammar fixes, not style noise — user reviewed ~100 real rows via PRead, happy with signal quality.
- [x] User can work the queue via **PRead** in gui2 — confirmed, used throughout this thread.

---

## What's not included

- `meaning_lit` / `meaning_2` pipeline + multi-field PRead (remaining #196 item)
- Two-pass confirmation
- Spellcheck pre-filter or diff post-filter
- Closing GitHub #196 (leave open until lit/2 are done, unless you decide otherwise)
