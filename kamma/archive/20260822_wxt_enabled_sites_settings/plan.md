# Plan: Enabled-sites list in extension settings

**Thread:** 20260822_wxt_enabled_sites_settings
**Date:** 2026-08-22
**Area:** `exporter/wxt_extension/`
**Status:** Complete 2026-08-22. Reviewed (CodeRabbit + independent agent), findings fixed, archived. Manual browser pass partly covered — see review.md.

## Architecture decisions

1. **Reuse the existing storage key, invent nothing.** Add/remove writes and
   deletes the same `state_<hostname>` entry the toolbar click already uses.
   No parallel store, no migration, no new key namespace.
2. **Exact hostnames only.** No matcher, no wildcards, no regex. The gate in
   `content.ts` stays a direct key lookup.
3. **`normalizeHostname` lives in `utils/domains.ts`, not in the panel.**
   That module is already unit-tested; parsing/normalising logic buried in a UI
   file cannot be tested cheaply.
4. **Removal deletes the key rather than writing `"OFF"`.** Deleting restores
   default behaviour; writing `"OFF"` would permanently pin an auto-domain off,
   which is a different and unrequested behaviour.
5. **Render the list from storage each time the dropdown opens** — no cached
   copy in the panel object. The toolbar icon can change state from outside the
   panel, so a cache would go stale.
6. **No manifest, permission, or `AUTO_DOMAINS` changes.** The content script
   already matches all URLs; this is confirmed, not assumed.

## Dependency order

Phase 1 (helper + tests) → Phase 2 (teardown fix) → Phase 3 (UI) → Phase 4 (verify)

Phase 2 before Phase 3 deliberately: the teardown gap is the one real bug, and
fixing it first means the UI is built against correct behaviour rather than
having the bug surface during manual testing.

---

## Phase 1 — Hostname helper

- [x] 1.1 Add `normalizeHostname(input: string): string | null` to
  `utils/domains.ts`. Trim, lowercase, strip a scheme and any path/port by
  parsing as a URL when possible and falling back to the bare string. Return
  `null` for empty input or anything that does not yield a plausible hostname.
  → verify: `npm run compile` clean.

- [x] 1.2 Add cases to `tests/utils/domains.test.ts`: full URL with scheme, port
  and path; bare hostname; mixed case; surrounding whitespace; empty string;
  whitespace-only; an obviously invalid string. Assert `localhost` and
  `127.0.0.1` normalise to themselves and stay **distinct**.
  → verify: `npm run test` green.

## Phase 2 — Teardown on key removal (the real bug)

- [x] 2.1 In `entrypoints/content.ts`, extend the `storage.onChanged` listener
  (currently ~line 240) so it tears down not only when the value becomes
  `"OFF"` but also when the `state_<hostname>` key is **removed**, unless the
  hostname is a live auto-domain (in which case default behaviour is on and the
  panel should stay).
  → verify: `npm run compile` clean; confirmed manually in Phase 4 step 4.

## Phase 3 — Settings UI

- [x] 3.1 In `components/dictionary-panel.ts`, append an "Enabled Sites" section
  to the settings dropdown markup in `_toggleSettingsDropdown`, below the last
  toggle row, after a divider. Include a container for the list and a row with a
  text input plus an Add button. Match the surrounding rows' inline-style idiom
  and theme variables rather than introducing a new styling approach.
  → verify: `npm run compile` clean; section renders at the bottom and the
    dropdown still scrolls within its 400px cap.

- [x] 3.2 Add a render routine that reads all of `storage.local`, keeps
  `state_*` entries whose value is `"ON"`, sorts by hostname, and paints one row
  per site with an `×` control. Render the empty-state line when there are none.
  → verify: manual — list matches the sites actually enabled.

- [x] 3.3 Wire the `×` handler in `_setupSettingsEventListeners`: remove the
  key, re-render the list in place. Panel teardown for the current site comes
  from Phase 2, not from this handler — do not duplicate it here.
  → verify: manual — Phase 4 steps 3 and 4.

- [x] 3.4 Wire the Add handler: normalise via `normalizeHostname`, reject `null`
  with an inline message, no-op on a name already listed, otherwise write
  `state_<name> = "ON"` and re-render. Submit on Enter as well as the button.
  → verify: manual — Phase 4 step 2; invalid input shows a message and writes
    nothing.

- [x] 3.5 **Added mid-thread (R5).** Scroll affordance: a sticky chevron over a
  fade at the bottom edge of the dropdown, shown only while scrolled above the
  bottom, `pointer-events: none` so it cannot block the row underneath.
  Re-measures on a short timeout because the sites list paints asynchronously.
  → verify: `npm run compile` clean; tests green; manual — user confirmed the
    section is now findable. DONE 2026-08-22.

## Phase 4 — Verification

- [x] 4.1 Automated: `npm run compile`, `npm run test`, `npm run build:chrome`.
  → verify: all three clean.

- [~] 4.2 Manual browser pass — load the unpacked chrome build and walk the five
  steps in spec.md "Verification". This is mandatory; a headless test cannot
  prove dropdown rendering, live teardown, or persistence across a restart.
  → verify: all five steps pass; record any that do not.

- [x] 4.3 Confirm nothing outside the WXT extension changed, and that the
  archived legacy extension is still in place and still unreferenced.
  → verify: scoped `git status --porcelain`, cross-referenced against this
    thread's file list — other sessions share this tree.

## Risks

- **R2 teardown is the one place a silent bug can hide.** If the listener
  change is wrong, removing the current site leaves a working panel and the user
  concludes the feature is broken. Phase 4 step 4 exists specifically for this.
- **Dropdown height.** The section is added to a fixed-height scrolling
  container; a user with many sites gets a long scroll. Acceptable for now —
  if it becomes unpleasant, that is the argument for a real options page, which
  is explicitly out of scope here.
- **Shared working tree.** Other kamma threads run against this repo
  concurrently. Re-read files immediately before editing, and stage by explicit
  file list only.

## Phase 5 — Review fixes (added after the review passes)

- [x] 5.1 Add `init()` on an ON-transition in the content script's storage
  listener, so a site enabled from elsewhere activates in already-open tabs.
  Found independently by both reviewers. → verify: compile + tests + build.
- [x] 5.2 Allow underscores in `normalizeHostname`; test added. → verify: tests.
- [x] 5.3 Exclude built-in sites from the list entirely via a shared
  `isDefaultOnDomain`, reused by the content script. → verify: compile + build.
