# Plan: Popout never enters minimized state

**Thread:** 20260722_popout_never_minimize
**Spec:** `spec.md` in this folder — read it first for the full decision trail.
**GitHub issue:** #253 — report only, do NOT write to the tracker.

## Architecture Decisions (made during planning — do not relitigate)

- Fix at the source in `DictionaryPanel` via an explicit `neverMinimize` flag,
  not DOM-sniffing.
- Effective-minimized computed in `_applySettings`; storage/settings untouched.
- #254 observer stays as a safety net.
- In-page panel unchanged (flag defaults `false`).

## Tasks

- [x] **1. Add `neverMinimize` to `DictionaryPanel`**
  - Add `private neverMinimize: boolean` field.
  - Accept an optional constructor param `opts: { neverMinimize?: boolean } = {}`
    and set `this.neverMinimize = opts.neverMinimize ?? false`.
  - → verify: `npm run compile` clean; in-page `new DictionaryPanel()` still valid.

- [x] **2. Use effective-minimized in `_applySettings`**
  - `const minimized = this.neverMinimize ? false : this.settings.minimized;`
  - Replace the three reads of `this.settings.minimized` in `_applySettings`
    (class toggle line ~218, width branch line ~222, positioning branch line ~238)
    with `minimized`.
  - → verify: `npm run compile` clean.

- [x] **3. Popout constructs with the flag**
  - `entrypoints/popout/main.ts`: `new DictionaryPanel({ neverMinimize: true })`.
  - → verify: `npm run compile` clean.

- [x] **4. Build + smoke**
  - `npm run build:chrome` succeeds.
  - Reason through the timing: even if `settingsMinimized:true` loads, effective
    `minimized` is `false`, so the class is never added and the observer never
    has to fire. Confirm no other caller passes minimized.
  - → verify: build output clean.

- [x] **5. (added mid-thread) Popout words clickable**
  - Pre-existing bug found during manual verification: popout never wired
    select/double-click-to-search. NOT caused by the minimize change (git-confirmed).
  - `entrypoints/popout/main.ts`: import + call `addListenersToTextElements()` after
    panel setup, mirroring `content.ts:162`.
  - Restores **double-click-to-search** (user-confirmed working 2026-07-22).
  - → verify: `npm run compile` + `npm run build:chrome` clean; user confirmed
    double-click a word in the popout results triggers a lookup.

- [x] **6. (added mid-thread) Popout drag-select-to-search (option A)**
  - Decision 2026-07-22: enable drag-select in the popout; copy trade judged a
    non-issue by user. See spec "Decision".
  - `entrypoints/popout/main.ts`: set `window.dpdIsPopout = true` before wiring.
  - `utils/utils.ts`: `handleMouseUp` panel guard becomes
    `if (!window.dpdIsPopout && target.closest('#dict-panel-25445')) return;`.
    In-page untouched (flag only set in the popout window).
  - → verify: `npm run compile` + `npm run build:chrome` clean; user confirms
    drag-select searches in popout AND in-page sidebar drag-select still copies.

## Review

- [x] Independent zero-context subagent + inline review — see `review.md`. PASSED.
  Change A correct/complete; Change B's drag-select gap fixed per user decision.

## Manual verification (user)

- [x] User-confirmed 2026-07-22: popout renders full-size with `settingsMinimized`
  on (not a blank/30px strip); word double-click works; drag-select enabled.
