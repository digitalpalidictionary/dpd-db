# Dharmamitra contextual word-gloss suggestion in gui2 pass2add

## Overview

> **REVISED 2026-07-27** — the original spec called for a new `meaning_1_add`
> DB column. That was wrong and was implemented, then reverted, before this
> revision: `gui2/dpd_fields.py` already auto-creates a `<field>_add`
> UI-only "suggestion" sibling for every real `FieldConfig` (see
> `self.fields[f"{config.name}_add"] = DpdText()`, `dpd_fields.py:407`) —
> so `meaning_1_add` **already exists** as a transient UI field, with a
> transfer-button accept flow (`update_add_fields`, `transfer_add_value`,
> `check_and_color_add_fields`) already wired up and already rendered in
> `pass2_add_view.py` (`include_add_fields=True` at line 684). No DB schema
> change, no new FieldConfig, and no new UI row are needed at all — this
> thread now only wires a new data source into an existing mechanism.

Add an optional, switch-gated feature to `gui2/pass2_add_view.py`: when a
headword that has an example sentence is opened for editing, send the
example sentence + headword lemma to the Dharmamitra public translation API
and feed the returned contextual gloss into the *existing*
`meaning_1_add` suggestion field via `self.dpd_fields.update_add_fields({"meaning_1": gloss})`,
so the annotator sees it right next to `meaning_1` with the same
red-highlight-if-different + transfer-arrow accept flow every other
AI-suggestion field already uses. The gloss is never written into
`meaning_1` automatically — accepting it is the same one-click transfer
action that already exists for every other field.

Dharmamitra API (public, unauthenticated, verified working via manual curl
test during research):

```
POST https://dharmamitra.org/api-search/cat-translate/v1/translate
Content-Type: application/json

{
  "input_pali": "<example sentence>",
  "focus": "pali",
  "target_language": "english",
  "style_instruction": "After translating, add one line: WORD GLOSS: explain specifically what the word \"<lemma>\" means as used in this exact sentence, in this exact grammatical form."
}
```

Response: `{"translation": "<english translation>\n\nWORD GLOSS: ..."}`

## What it should do

1. **New API client module**, isolated from `pass2_add_view.py` — e.g.
   `tools/dharmamitra_client.py` — exposing one function:
   ```python
   def get_contextual_gloss(example_sentence: str, lemma: str) -> str | None:
   ```
   - Builds the request body shown above.
   - Calls `requests.post(...)` synchronously (matches the existing
     blocking-call pattern used by `AiAutofill` / `ai_manager.py` — no
     thread/async offload).
   - Wraps the call in try/except covering network errors, non-200 status,
     and malformed JSON; returns `None` on any failure (never raises out to
     the GUI layer).
   - Applies a reasonable request timeout (e.g. 30s — the endpoint is
     LLM-backed but single-sentence, not a long document like `AiAutofill`'s
     150s default).
   - Parses and returns the `"translation"` field as-is (no further
     parsing/splitting of the WORD GLOSS line out of the surrounding
     translation text — store the whole response string).

2. **New Switch in `gui2/pass2_add_view.py`**, placed directly after the
   existing `self._missing_words_switch` inside the same
   `_action_menu_button` `PopupMenuButton` items list (after line ~187,
   before the closing `]`):
   ```python
   self._dharmamitra_gloss_switch = ft.Switch(
       label="Dharmamitra Gloss",
       value=False,
   )
   ```
   wrapped the same way: `ft.PopupMenuItem(content=self._dharmamitra_gloss_switch)`.
   In-memory only (no config.ini entry) — matches the existing
   `_missing_words_switch` pattern and keeps the gate simple, since the
   Dharmamitra endpoint needs no API key to gate on.

3. **Hook point**: inside `_click_edit_headword` (`gui2/pass2_add_view.py`,
   ~line 441-471), after `self.dpd_fields.update_db_fields(headword)` and
   `self.add_headword_to_examples_and_commentary()` succeed and a headword
   is loaded:
   - Only proceed if `self._dharmamitra_gloss_switch.value` is `True`.
   - Only proceed if the headword has a non-empty `example_1` (or
     `example_2` if `example_1` is empty — mirror whichever example is
     actually populated; if neither, skip silently).
   - Call `dharmamitra_client.get_contextual_gloss(example_text, headword.lemma_clean)`.
   - On success (non-`None`): call
     `self.dpd_fields.update_add_fields({"meaning_1": gloss})` — the
     *existing* mechanism used by AiAutofill/pass2auto. This writes into
     the already-existing `meaning_1_add` UI field, enables its existing
     transfer-arrow button, and triggers the existing red-highlight-if-
     different coloring (`check_and_color_add_fields`). No new field, no
     new UI row, no DB write of any kind — accepting the suggestion into
     `meaning_1` is the same one-click transfer flow every other
     AI-suggested field already has.
   - On failure (`None`): show a message via `self.update_message(...)`
     (e.g. "dharmamitra gloss failed") and leave the `meaning_1_add` UI
     field untouched. Never raise, never block headword loading if the API
     is down/slow — but note the call IS synchronous/blocking like
     `AiAutofill`, so a slow or hung API will visibly stall the UI for up
     to the timeout; this is accepted as consistent with existing behavior
     in this view, not a new regression to solve here.

There is no field wiring task: `meaning_1_add` already exists as a UI field
(auto-created for every `FieldConfig`, `dpd_fields.py:407`) and is already
rendered with a transfer button (`include_add_fields=True`,
`pass2_add_view.py:684`). `db/models.py` and `gui2/dpd_fields.py`'s
`field_configs` list are **not touched by this thread at all**.

## Assumptions & uncertainties

- Assuming `example_1` is the field to prioritize when both `example_1` and
  `example_2` are populated (mirrors existing precedence elsewhere in the
  codebase, e.g. `.meaning_combo`, `.example` cached properties). Not
  verified against every existing precedent — flag if wrong.
- Assuming `lemma_clean` (not `lemma_1`, which may carry a homonym-numbering
  suffix) is the right string to send as the target word for glossing —
  matches existing usage in `_click_edit_headword`'s neighborhood (e.g.
  `lemma_clean[:-1]` used for `word_to_find_field` nearby).
- Assuming no need to strip/parse the "WORD GLOSS:" line out of the full
  translation response — the whole string is stored as-is in the
  `meaning_1_add` UI field, to keep the client function trivial. If the
  user wants only the gloss line isolated, that's a follow-up, not part of
  this spec.
- Assuming a 30s timeout is reasonable for a single-sentence call; no data
  on Dharmamitra's real-world latency distribution beyond the one manual
  test (which returned in a few seconds).
- This thread does NOT touch `db/models.py`, `db_tests/`, exporters, or any
  other consumer of `DpdHeadword` fields — confirmed unnecessary now that
  the suggestion lives entirely in the pre-existing `_add` UI-field
  mechanism, never in the database.
- No GitHub issue is associated with this thread.

## Constraints

- Must not write to `meaning_1`/`meaning_2` automatically under any
  circumstance — only the existing transfer-button click (unchanged code)
  does that, same as every other suggestion field.
- Must not require any config.ini change or API key — endpoint is public.
- Must not add a DB column, a new `FieldConfig`, or a new UI row — reuse
  the existing `meaning_1_add` UI field and its existing accept/reject
  machinery (`update_add_fields`, `transfer_add_value`,
  `check_and_color_add_fields`) exactly as-is.
- New code must be additive and isolated: a new client module, one new
  switch, and a small hook in the existing `_click_edit_headword` method.
  No refactor of existing example-lookup or AiAutofill code paths.
- Follow project type-hint conventions (`str | None`, etc.) and run
  ruff/pyright/pytest on every touched file per project pre-commit gate.

## How we'll know it's done

- New "Dharmamitra Gloss" switch appears in the Actions popup menu directly
  below "Missing Words", default OFF.
- With the switch OFF, opening any headword (with or without an example)
  behaves exactly as today — zero API calls, zero behavior change.
- With the switch ON, opening a headword that has a populated `example_1`
  (or `example_2`) sends one request to the Dharmamitra API and populates
  the existing `meaning_1_add` UI field via `update_add_fields`, enabling
  its existing transfer-arrow button (or shows a failure message if the
  request errors/times out).
- With the switch ON, opening a headword with no example sentence performs
  no API call.
- `db/models.py` is unmodified by this thread; the live `dpd.db` schema is
  never touched.
- `uv run ruff check`, `uv run ruff format`, `uv run pyright` all pass clean
  on every touched file; `uv run pytest` passes for any new/existing tests
  touching these files.

## What's not included

- No automatic parsing/splitting of the gloss line from the surrounding
  translation text.
- No config.ini-backed persistence of the switch's on/off state across app
  restarts (always defaults to OFF on launch).
- No retry logic, caching, or rate-limit handling beyond a single
  try/except-and-give-up per call.
- No batch/background pre-fetching of glosses for multiple headwords — this
  is strictly a single, on-demand call per headword-open event.
- No changes to `db/models.py`, exporters, `db_tests/`, or any other
  consumer of `DpdHeadword` — nothing here is DB-persisted.
