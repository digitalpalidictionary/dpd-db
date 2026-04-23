# Spec — Contributor additions/corrections flow

## Overview
Contributors to dpd-db run their own copy of `gui2` with a username, producing per-user files `additions_<user>.json` and `corrections_<user>.json`. The primary user (bdhrs) pulls these files and processes each proposed addition/correction through the Pass 2 Add view, which writes the accepted item to `additions_added.json` / `corrections_added.json`.

The current implementation is half-done: the creation side (contributors writing per-user files) works, but the consuming side destructively merges contributor files into `additions.json` / `corrections.json` on load and then wipes the contributor file to `{}`. This can leak contributor-curated items into the primary user's queue files and loses the visibility of which contributor proposed each item.

## What it should do
- On GUI load as primary user, `AdditionsManager` / `CorrectionsManager` read the in-memory pending queue from **all** contributor files (`additions_*.json`, `corrections_*.json`, excluding `_added` files) without modifying any file on disk.
- Each in-memory entry tracks its source file (origin) so the manager can mutate it when the item is processed.
- When the primary user processes an item in Pass 2 Add (`_click_additions_button` / `_click_corrections_button` → `_click_add_to_db` → `save_processed_addition` / `save_processed_correction`):
  1. The item is appended to `additions_added.json` / `corrections_added.json` with a new `_contributor` field recording the username (derived from the origin filename stem).
  2. The same key is deleted from the contributor origin file on disk. If the origin file becomes empty, it is rewritten as `{}` (preserving the file so the contributor can add more).
- The primary user never uses `additions.json` / `corrections.json`. These files are dead and are removed from the repo.

## Assumptions & uncertainties
- **Primary user never adds directly via `additions.json` queue.** User confirmed additions go straight to the DB. So the primary path for default `Gui2Paths` is unused.
- **Pass 1 Add is not affected.** User confirmed they only process via Pass 2 Add. `pass1_add_controller.py` uses `additions_manager` only to *write* proposals (contributor side) — that still works unchanged because contributors continue to write to their own file via `for_user(username)`.
- Proofreader flow (line 937 `proofreader_manager.get_next_correction`) is a separate manager and is out of scope.
- `paths.py` `for_user` already handles per-user paths correctly for the contributor writing side.

## Constraints
- Must not lose any contributor data. The current working tree already has `additions_deva.json` / `corrections_deva.json` restored to HEAD, and `additions.json` / `corrections.json` hold duplicates from an earlier (now undone) merge run.
- Python type hints, `Path` from `pathlib`, `icecream` if debugging is needed.
- Minimal change footprint. No new files besides the thread docs.

## How we'll know it's done
- Contributor files in the data dir are NOT modified when the GUI is opened as primary user.
- Processing an addition/correction in Pass 2 Add removes exactly that one key from the contributor's file (preserving the other keys byte-for-byte as JSON allows) and appends to `_added.json` with `_contributor` set to the contributor username.
- `additions.json` / `corrections.json` are removed from the working tree.
- A smoke test confirms: load the 60-key `corrections_deva.json`, process one via Pass 2 Add, verify `corrections_deva.json` shrinks to 59 keys and `corrections_added.json` has the new entry with `_contributor: "deva"`.

## What's not included
- No UI changes (no new buttons, no display of contributor attribution in the UI).
- No new contributor-management tooling.
- No migration of legacy `additions_added.json` / `corrections_added.json` entries (which lack `_contributor`). New entries going forward will carry the field; old entries stay untouched.
- No changes to the Pass 1 contributor-writing flow.
- No changes to `proofreader_manager`.
