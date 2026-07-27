## Thread
- **ID:** 20260727_dharmamitra_gloss
- **Objective:** Optional, switch-gated Dharmamitra API contextual word-gloss suggestion in gui2 pass2add, feeding into the existing `meaning_1_add` suggestion field.

## Files Changed
- `tools/dharmamitra_client.py` — new, isolated client: `get_contextual_gloss(example_sentence, lemma) -> str | None`, calls the public Dharmamitra translate API, returns `None` on any failure.
- `tests/tools/test_dharmamitra_client.py` — 3 mocked-`requests.post` tests (success, non-200, request exception).
- `gui2/pass2_add_view.py` — new "Dharmamitra Gloss" `ft.Switch` (default off) below "Missing Words"; `_apply_dharmamitra_gloss` helper called from `_click_edit_headword`, feeding results through the existing `update_add_fields({"meaning_1": gloss})` mechanism; terminal logging via `tools.printer` for observability.

## Findings
No findings.

## Fixes Applied
None needed.

## Test Evidence
- `uv run pytest tests/tools/test_dharmamitra_client.py tests/gui2/ --ignore=tests/db/memory` → 287 passed
- `uv run ruff check` / `uv run ruff format --check` on all 3 touched files → clean
- `uv run pyright tools/dharmamitra_client.py tests/tools/test_dharmamitra_client.py` → 0 errors (gui2/ confirmed pyright-excluded via pyproject.toml, so `pass2_add_view.py` correctly not pyright-checked)
- `git diff db/models.py` → confirmed zero dharmamitra-related diff — the schema-drift regression that broke the first (reverted) attempt cannot recur
- Manual GUI walkthrough — confirmed working by the user after a full gui2 restart (switch on + headword with example → terminal logs + `meaning_1_add` populates); switch-off/PRead-button scope explicitly confirmed as out of scope by the user

## Verdict
PASSED
- Review date: 2026-07-27
- Reviewer: independent Sonnet subagent (spawned by implementing agent per kamma:3-review §3.0 independence escalation)
