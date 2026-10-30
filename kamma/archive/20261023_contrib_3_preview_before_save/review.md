# Review: 20261023_contrib_3_preview_before_save

**Verdict: PASSED** (2026-10-30)

Reviewers: a Sonnet subagent (`/kamma:3-review`), CodeRabbit (`--agent --include-untracked --dir gui2`, second run; the first failed with "WebSocket closed"), and a pi agent in another herdr pane.

## Files Changed
- `.gitignore`, `gui2/README.md`, `gui2/pass1_add_controller.py`, `gui2/pass2_add_view.py`, `gui2/preview.py` (new), `tests/gui2/test_preview.py` (new)

## Findings
- Preview failure blocked saving, with no message (all three reviewers).
- Double press could save twice (Sonnet, pi).
- README bullet added twice (all three).
- No test covered the dialog flow or the handler wiring (Sonnet, pi).
- Username went into the preview file name unchecked (Sonnet).
- CodeRabbit: use `page.pop_dialog()` to close the dialog.

## Fixes Applied
- `preview_and_confirm` catches a failed render, write or open and shows the error in a dialog that still offers Save and Cancel.
- A module guard ignores a second preview while one is open or saving. Save runs once.
- One README bullet removed.
- The username is cleaned before it becomes a file name.
- 10 new tests: dialog flow, failure path, guards, Pass1Add handler. With the guards off, 3 fail.
- Skipped: `pop_dialog`. It does the same two steps as the current code and closes the topmost dialog, not necessarily ours.

## Test Evidence
- `uv run pytest tests/`: 2664 passed, 12 deselected.
- `just typecheck`: 0 errors.
- ruff check and format clean on all touched files; `pyright --project /dev/null` clean on `gui2/preview.py` and the test file; no new errors in the two edited handlers.
- Live, user-confirmed: desktop Pass1Add and Pass2Add (preview, Cancel, Escape, Save); contributor web run (preview opens, Save wrote the contributor JSON and not the db).

## Not covered
- Pass2Add handler wiring has no unit test (live run only).
- Audio button in the preview: problem children item 10.
