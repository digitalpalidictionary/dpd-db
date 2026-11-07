# Subagent review — raw output — 2026-11-21
# Reviewer: pi subagent "reviewer", independent context, no shell access.
# Prompt: kamma/threads/20261107_pass1auto_unknown_first/egm/prompts/20261121_subagent_review.md

## Review — kamma/threads/20261107_pass1auto_unknown_first

### Scope of what I examined
- `kamma/threads/20261107_pass1auto_unknown_first/spec.md`, `plan.md`, `kamma/workflow.md`, `kamma/project.md`, `kamma/tech.md` — all read.
- `gui2/pass1_auto_controller.py` and `tests/gui2/test_pass1_auto_controller.py` — read in full (these are stated to be the thread's entire code diff).
- `db/models.py` `Lookup` model (lines 213–234) — read to verify the column list the query relies on.
- `gui2/books.py` / `tests/gui2/test_books.py` — excluded per instruction.

**Tooling constraint, stated up front:** this review session has only file-inspection tools (read/grep/find/ls) — no shell. I could **not** execute `git diff`, `pytest`, `ruff`, or `pyright`. The requested commands must be run by the calling agent before finalize; my verification below is static. This is the single largest residual risk in this review.

### Correctness check (static, vs spec.md)

Verified by reading the code:

- **Unknown definition** (`gui2/pass1_auto_controller.py`, `find_unknown_words`): derives data columns from `Lookup.__table__.columns` excluding `lookup_key` and `epd`, then `or_(coalesce(col, "") != "")`. The model's actual columns (`headwords, roots, deconstructor, variant, see, spelling, grammar, help, abbrev, abbrev_other, rpd, other, sinhala, devanagari, thai`) match the spec's known-column list exactly. `coalesce(..., "")` correctly treats raw-SQL NULLs as empty. An `epd`-only row is therefore unknown; a row with any other data is known. ✔
- **Unknown first, group order kept** (`_auto_process_book`): `reordered` is built as unknown-words dict-comprehension, then `.update(...)` with the rest — Python dicts preserve insertion order and `update` never reorders existing keys, so order inside each group is kept. The loop iterates `missing_words_dict.items()`, so reordering the dict is sufficient, as the spec assumed. ✔
- **Status line**: `f"Unknown words (not in lookup): {len(self.unknown_words)} of {self.total_missing}"` — matches spec wording. Per-word label `Processing X (unknown)` only for the unknown group. ✔
- **`_auto_process_text` untouched**: the text path has no reorder, no unknown label, and never reads `self.unknown_words`. ✔ (Stale `unknown_words` from a previous book run is harmless — unused in the text path.)
- **Chunking**: 900 keys per `IN` — under SQLite's parameter limit, indexed on the primary key, no full 1.28M-row load. ✔
- **No ORM mutation**: read-only `query(Lookup.lookup_key)`, plain set of covered keys — respects the constraint. ✔
- **Edge cases**: empty `missing_words_dict` → zero chunks, `reordered` empty, message reads "0 of 0" — fine. Duplicate input words impossible (dict keys). Parameterized query, no injection surface.
- **Plan adherence**: architecture decisions (one method on controller, session already held, `self.unknown_words` on controller, loop unchanged) all followed; all plan checkboxes `[x]` including the revert-and-verify step and live check. Deviations: none observed.

### Test check ("the check, not just its result")

Static inspection of `tests/gui2/test_pass1_auto_controller.py`:

- `test_find_unknown_words_returns_epd_only_and_absent` (lines 211–228) covers exactly the spec's verify case: headword row, deconstructor-only row, epd-only row, absent word, plus a NULL+epd row. Matches the plan's stated fixture one-for-one.
- `test_book_run_processes_unknown_words_first` (lines 231–276) drives the real `auto_process_book` through a fake session and asserts: processed order `["m2", "m4", "m1", "m3"]` (unknown first, original order kept), the unknown set, the status message, and the per-word labels both present and absent. This directly covers all three spec "How we'll know it's done" code behaviours: unknown first ✔, group order kept ✔, and — for the paste-text path — the two pre-existing text-loop tests (`test_loop_lets_the_screen_run_during_ai_calls`, `test_stop_halts_after_the_current_word`) still exercise `_auto_process_text` unchanged ✔.
- Test isolation is sound: in-memory sqlite, `object.__new__` controller with fakes, no network, no real db.

**BUT: I could not run the suite.** A static pass proves the assertions exist and target the right behaviours; it does not prove they are green. The calling agent must run the three commands before finalize.

### Findings

1. **minor** — `gui2/pass1_auto_controller.py:144` — `find_unknown_words` runs synchronously on the asyncio event loop (not wrapped in `asyncio.to_thread`) inside `_auto_process_book`.
   - Why it matters: tech.md documents that sync work in Flet 1.0 async handlers freezes UI patch dispatch. For a large book (e.g. 20k missing words ≈ 23 indexed PK queries on a 1.28M-row table) this is likely only milliseconds, so the practical impact is small — but every other db-heavy step in this method is wrapped in `to_thread`, and the same file is on record as needing that shape.
   - Suggested fix: `unknown_list = await asyncio.to_thread(self.find_unknown_words, list(self.missing_words_dict))`. One line, no behaviour change.

2. **nit** — `tests/gui2/test_pass1_auto_controller.py` — no test exercises the chunk boundary (>900 words), so the chunk loop is only exercised with a single chunk.
   - Why it matters: low — the loop is three lines and `words[i:i+900]` slicing is standard; but a chunk-boundary regression would silently mis-classify and reorder words.
   - Suggested fix (optional): a unit test with ~901 words where word 900 is known, or leave as accepted risk.

3. **nit** — `gui2/pass1_auto_controller.py:148-158` — the two-step reorder (comprehension + `update`) is slightly more roundabout than needed; `{**{w: ... for w in unknown_list}, **{w: s for w, s in ... if ...}}` or a single loop would read the same. Purely stylistic; behaviour is correct.

No blocking or major findings.

### What's good
- The column list is derived from the model rather than hardcoded — it auto-adapts if `Lookup` gains a column, and cannot drift from the spec's list (which I verified against `db/models.py`).
- Spec, plan, and implementation line up with no silent deviations; the NULL-vs-empty-string gotcha is both handled in code and pinned by a dedicated test row.
- Tests assert the actual processing order through the real public entry point (`auto_process_book`), not just the helper — a regression in the reorder is caught even if `find_unknown_words` itself stays correct.
- `_auto_process_text` is verifiably untouched.

### Summary
Static review is clean: the implementation matches spec and plan exactly, the tests target the spec's done-criteria, and the only substantive concern is the minor event-loop blocking nit. **Coverage / residual risk:** I verified code semantics, model-column agreement, spec-conformance, and test coverage by inspection only. I did **not** run pytest, ruff, `pyright --project /dev/null`, `just typecheck`, or `git diff` — no shell in this review harness — so green results are reported by the implementer, not independently reproduced here, and the exact diff boundary (vs the concurrent books.py session) rests on the calling agent's file list. The live book-run confirmation (plan Phase 2) is recorded as user-confirmed and not re-verifiable statically. Recommended next step for the calling agent: run the three commands, optionally apply the one-line `to_thread` fix, then proceed to `/kamma:4-finalize`.
