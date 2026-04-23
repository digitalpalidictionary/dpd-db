# Plan — Contributor additions/corrections flow

## Architecture Decisions
- **No primary queue file.** `additions.json` / `corrections.json` are removed. The manager reads only contributor files (`additions_*.json` / `corrections_*.json`, excluding `_added`). Rationale: primary user never uses the queue — their additions go straight to the DB.
- **In-memory origin map.** Each manager keeps `self._origin: dict[str, Path]` alongside `self.additions_dict` / `self.corrections_dict` to track which contributor file each key came from. Rationale: simplest way to know which file to mutate when processing an item; no JSON schema changes.
- **Surgical file mutation.** On process, the manager reads the origin file, removes the single key, and writes it back. If the file becomes empty, it is written as `{}` (not deleted). Rationale: preserves contributor file existence so the contributor doesn't need to recreate it.
- **`_contributor` field on processed items.** The filename stem minus the `additions_` / `corrections_` prefix is stored on each entry in `_added.json`. Rationale: one-line audit trail, no new files.
- **Collision handling.** If two contributor files contain the same key, the later-loaded one wins in memory and a warning is printed via `pr.red`. Rationale: rare; explicit failure mode beats silent data loss.

## Phase 1 — Rewrite managers (non-destructive load, origin tracking)

- [x] Rewrite `AdditionsManager.load_additions` (gui2/additions_manager.py:17):
  - Glob `additions_*.json` in the data dir, excluding names containing `additions_added`.
  - Build `merged: AdditionsDict` and `self._origin: dict[str, Path]`.
  - On duplicate key across files, keep the later file's value and print a `pr.red` warning.
  - Do **not** write any file.
  - Return `merged`.
  → verify: add a temp script that instantiates the manager with two fake contributor files, assert both files are unchanged on disk and `merged` contains all keys with correct origins.

- [x] Mirror the same changes in `CorrectionsManager.load_corrections` (gui2/corrections_manager.py:17).
  → verify: same script pattern for corrections.

- [x] Change `AdditionsManager.get_next_addition` signature to return `tuple[dict | None, Path | None, int]` (item, origin_path, remaining). Pop the key from both `additions_dict` and `_origin`. Do not save to disk here.
  → verify: temp script pops an item, confirms the contributor file on disk is unchanged and `_origin` no longer contains that key.

- [x] Mirror in `CorrectionsManager.get_next_correction`.
  → verify: same script pattern for corrections.

- [x] Rewrite `AdditionsManager.save_processed_addition` to take `origin_path: Path` and `word_data: dict`:
  - Derive `_contributor` from `origin_path.stem` by stripping the leading `additions_` prefix (e.g., `additions_deva` → `deva`).
  - Append `{**word_data, "_contributor": contributor}` to `_added.json` (create if missing).
  - Read the origin file, remove `word_data["id"]` key (str-coerced), write back. If dict now empty, write `{}`.
  → verify: temp script processes one item, asserts `_added.json` received the `_contributor` field and the origin file lost exactly that key.

- [x] Mirror in `CorrectionsManager.save_processed_correction`.
  → verify: same script pattern for corrections.

- [x] **Phase 1 verification:** run `uv run python -c "from gui2.toolkit import ToolKit; ..."` — skip if toolkit instantiation requires full GUI. Otherwise just load the two manager modules standalone with temp data dirs and assert behavior.

## Phase 2 — Update Pass 2 Add callers

- [x] In `pass2_add_view.py`, add instance fields `self._current_addition_origin: Path | None = None` and `self._current_correction_origin: Path | None = None` (near where `current_correction` / `current_addition` are initialized).
  → verify: grep confirms the fields exist.

- [x] Update `_click_additions_button` (gui2/pass2_add_view.py:894): unpack `(addition_data, origin, remaining)` from `get_next_addition()`, store `self._current_addition_origin = origin`.
  → verify: grep shows the 3-tuple unpacking and assignment.

- [x] Update `_click_corrections_button` (gui2/pass2_add_view.py:840): unpack `(correction_data, origin, remaining)` from `get_next_correction()`, store `self._current_correction_origin = origin`.
  → verify: grep shows the 3-tuple unpacking and assignment.

- [x] Update `_click_add_to_db` (gui2/pass2_add_view.py:724, 747): pass `self._current_addition_origin` / `self._current_correction_origin` to `save_processed_addition` / `save_processed_correction`.
  → verify: grep shows the origin argument at both call sites.

- [x] **Phase 2 verification:** `uv run python -c "import ast; ast.parse(open('gui2/pass2_add_view.py').read())"` to confirm syntactic validity.

## Phase 3 — Cleanup dead files

- [x] Delete `gui2/data/additions.json` and `gui2/data/corrections.json` (they duplicate the contributor data in the current working tree and are no longer used). Use `git rm --cached` followed by filesystem delete, or `rm` then `git add`.
  → verify: `ls gui2/data/additions.json gui2/data/corrections.json` returns "no such file".

- [x] Check `gui2/paths.py` — leave `additions_path` / `corrections_path` fields defined (they're still used by contributors via `for_user`). No change needed.
  → verify: grep confirms `for_user` still sets per-user paths.

- [x] Grep for any remaining reads of the primary `additions.json` / `corrections.json` across the repo.
  → verify: `grep -rn "additions.json\|corrections.json" --include='*.py'` shows no dangling references outside the managers and paths.py.

- [x] **Phase 3 verification:** confirm `additions_deva.json` and `corrections_deva.json` still hold the 1 + 60 entries respectively (restored earlier), and the two primary files are gone.

## Phase 4 — Smoke test

- [x] User runs the GUI as primary, confirms:
  - `additions_deva.json` / `corrections_deva.json` are NOT modified on load.
  - Processing one correction causes `corrections_deva.json` to shrink from 60 → 59 keys, and `corrections_added.json` gains one entry with `_contributor: "deva"`.
  → verify: manual inspection + `git diff --stat gui2/data/` shows only the expected contributor file mutation.
