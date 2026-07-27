# Plan: Dharmamitra contextual word-gloss suggestion in gui2 pass2add

No GitHub issue associated with this thread.

> **REVISED 2026-07-27** — the original Phase 1 (new `meaning_1_add` DB
> column + FieldConfig + docs entry) was implemented, discovered to break
> every headword load in gui2 (SQLAlchemy selects all mapped columns; the
> live `dpd.db` file was never rebuilt with the new column), and fully
> reverted. Root cause of the plan being wrong: `gui2/dpd_fields.py`
> already auto-creates a `<field>_add` UI-only suggestion sibling for
> every `FieldConfig` (`dpd_fields.py:407`), and `meaning_1_add` already
> exists this way with a working transfer-button accept flow. This plan is
> rewritten to use that existing mechanism instead of adding any DB/schema
> surface. Phase 1 (DB column) is deleted outright; Phase 2 (API client) is
> unchanged; Phase 3 is simplified (no FieldConfig/docs task needed).

## Architecture Decisions

- **No DB column, no FieldConfig, no new UI row**: `meaning_1_add` already
  exists as a transient UI field, auto-created for every real `FieldConfig`
  (`dpd_fields.py:407`), already rendered with a transfer button
  (`include_add_fields=True`, `pass2_add_view.py:684`), already wired to
  `update_add_fields` / `transfer_add_value` / `check_and_color_add_fields`.
  This thread reuses that mechanism verbatim rather than inventing a new
  one — this is the corrected, minimal design.
- **New isolated client module** `tools/dharmamitra_client.py`: keeps the
  HTTP call, error handling, and request-shaping fully out of
  `gui2/pass2_add_view.py`. This bounds the blast radius — a bug in the
  Dharmamitra integration can only ever break this one module, never the
  rest of the view.
- **Synchronous/blocking call, matching existing precedent**: `AiAutofill`
  in this same view (`gui2/pass2_add_view.py` → `pass2_auto_control.py` →
  `tools/ai_manager.py`) already makes a blocking LLM API call directly
  inside a click handler with no thread/async offload. We follow the same
  pattern rather than introducing new concurrency machinery for one
  request.
- **Switch-only gate, no config.ini**: the Dharmamitra endpoint needs no
  API key, so unlike `AiAutofill`'s per-provider `config.ini` gating there's
  nothing to store persistently. A single in-memory `ft.Switch`, default
  `False`, is the entire on/off surface — matches the existing
  `_missing_words_switch` pattern exactly.
- **Feed the result through `update_add_fields`, not a direct field write**:
  calling `self.dpd_fields.update_add_fields({"meaning_1": gloss})` is the
  exact same call AiAutofill/pass2auto already make for other fields — it
  writes the existing `meaning_1_add` field, enables its existing transfer
  button, and triggers existing diff-coloring. Zero new UI code.

## Phase 1 — Build the isolated Dharmamitra API client

- [x] Create `tools/dharmamitra_client.py` with:
  ```python
  def get_contextual_gloss(example_sentence: str, lemma: str) -> str | None:
  ```
  POSTs to `https://dharmamitra.org/api-search/cat-translate/v1/translate`
  with body `{"input_pali": example_sentence, "focus": "pali",
  "target_language": "english", "style_instruction": "<gloss the lemma in
  context>"}` (exact text in `spec.md`) via `requests.post(..., timeout=30)`.
  Wrap in try/except covering `requests.RequestException`, non-200 status
  (via `raise_for_status()`), and `ValueError`/`KeyError` on response
  parsing; return `None` on any failure, the `"translation"` string on
  success. No retries, no caching.
  → verify: this file survived the Phase-1-DB revert untouched (it never depended on the DB column). Live call `uv run python -c "from tools.dharmamitra_client import get_contextual_gloss; print(get_contextual_gloss('Sabbe sattā bhavantu sukhitattā.', 'sattā'))"` printed a real translation + WORD GLOSS line. ruff/pyright clean.

- [x] Add `tests/tools/test_dharmamitra_client.py` using `pytest`'s
  `monkeypatch` to mock `requests.post` for three cases: successful
  response → returns translation string; non-200 status → returns `None`;
  request raises `requests.RequestException` → returns `None`. No real
  network calls in the test suite.
  → verify: `uv run pytest tests/tools/test_dharmamitra_client.py` → 3 passed; `uv run ruff check`, `uv run ruff format`, `uv run pyright` clean on both files

**Phase 1 verification**: `uv run pytest tests/tools/test_dharmamitra_client.py` → 3 passed with mocked HTTP (no live network dependency in CI); the one-off manual live call confirmed real-world behavior. `db/models.py` was not touched by this phase — nothing to break in the live `dpd.db`.

## Phase 2 — Wire the switch and hook into `pass2_add_view.py`

- [x] Add `self._dharmamitra_gloss_switch = ft.Switch(label="Dharmamitra Gloss", value=False)`
  in `gui2/pass2_add_view.py` directly after `self._missing_words_switch`
  (~line 173), and add `ft.PopupMenuItem(content=self._dharmamitra_gloss_switch)`
  to the `_action_menu_button`'s `items` list directly after the existing
  `ft.PopupMenuItem(content=self._missing_words_switch)` (~line 187).
  → verify: code added correctly (reviewed); interactive confirmation is part of the pending manual walkthrough below.

- [x] In `_click_edit_headword`, after the pass2auto block and inside
  `if self.headword is not None`: added `_apply_dharmamitra_gloss(headword)`
  helper (keeps the click handler itself to a one-line call). The helper:
  returns immediately if `self._dharmamitra_gloss_switch.value` is falsy;
  returns immediately if both `headword.example_1` and `headword.example_2`
  are empty; otherwise calls `get_contextual_gloss(example_sentence,
  headword.lemma_clean)`; on success calls
  `self.dpd_fields.update_add_fields({"meaning_1": gloss})`; on `None`
  calls `self.update_message("dharmamitra gloss failed")`. Imported
  `get_contextual_gloss` at the top of the file alongside other `tools.*`
  imports.
  → verify: `uv run pytest tests/gui2/` → 284 passed; `uv run ruff check`/`ruff format` clean; interactive confirmation pending (see below).

- [x] Manual regression check: with switch OFF, open several headwords with
  and without examples — confirm behavior is byte-for-byte identical to
  pre-thread gui2 (no new messages, no fields populated, no latency added
  to headword loading, and — critically this time — confirm ordinary
  headword loading still works at all, i.e. no exception on open).
  → verify: user ran the manual walkthrough after a full gui2 restart, confirmed working: switch on + headword with example → terminal shows "dharmamitra gloss: querying API for <word>" then "done", and `meaning_1_add` populates. Confirmed by user: "ok works."

- [x] Add terminal logging to `_apply_dharmamitra_gloss` (via `tools.printer.printer as pr`,
  the project's standard console-output convention) so the API call is
  observable in the terminal regardless of GUI rendering: `pr.cyan_tmr`
  before the request, `pr.yes("done")`/`pr.no("failed")` after, and
  `pr.amber(...)` when skipped due to no example sentence. Added after the
  first manual test showed no visible sign of activity — root cause turned
  out to be gui2 needing a restart to pick up the code changes (Flet does
  not hot-reload), and the logging was a reasonable permanent addition
  regardless, giving future debugging a clear signal. Not in the original
  plan — added as a small, in-scope follow-up once the gap was noticed.
  → verify: `uv run ruff check`/`ruff format` clean, `uv run pytest tests/gui2/` → 284 passed, user confirmed the log lines appear during a real run.

**Phase 2 verification (automated portion)**: `uv run pytest tests/gui2/ --ignore=tests/db/memory` → 284 passed. `uv run ruff check`/`ruff format --check` clean on `gui2/pass2_add_view.py`. `db/models.py` untouched this time — confirmed via `git diff --stat` showing zero diff, so the live `dpd.db` cannot be broken by this thread.

**Manual GUI walkthrough: CONFIRMED by user ("ok works").**

**Smoke gate (full repo, per workflow.md)**: `uv run pytest tests/ --ignore=tests/db/memory` → 1713 passed, 1 unrelated failure (`tests/tools/test_docs_update_bibliography.py::test_make_bibliography_md_matches_golden_master`, caused by `shared_data/reference/bibliography.tsv` being modified by another concurrent kamma thread's uncommitted work, not by anything in this thread — confirmed `git status` at session start already showed this file dirty before this thread began). `tests/db/memory/*` excluded throughout, as those two files query the live `dpd.db` directly and are unrelated to this thread's (now DB-free) design.
