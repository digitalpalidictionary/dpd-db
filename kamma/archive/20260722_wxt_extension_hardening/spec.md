# Spec: WXT extension hardening (full backlog)

**Thread:** 20260722_wxt_extension_hardening
**Date:** 2026-07-22
**GitHub issue:** #253 (Browser extension updates) — do NOT write to the tracker; report only.
**Area:** `exporter/wxt_extension/`
**Status:** Implemented + reviewed (2026-07-22). See plan.md for per-item outcomes.
**Reviewed:** 2026-07-22 against merged PR #257 — items 4 & 6 closed by that PR;
items 3, 8, 9 rewritten (see notes). Numbering kept stable so plan.md refs hold.

> Self-contained: a fresh agent with zero conversational context can execute from this spec + plan.md.

## Overview

Harden the DPD WXT browser extension after the #253 popout / s.4nt.org work.
Originally nineteen items; **PR #257 landed the host-keyed popout singleton +
cross-tab sync**, closing items 4 and 6 and superseding most of item 3. The rest
(each with Issue / Problem / Solution below) cover correctness bugs, CSS host
collisions, UX gaps, and engineering hygiene.

**Post-#257 architecture note:** popout ownership is keyed by **hostname**
(`popout_host_<host>` in `storage.local`), NOT by tab id. A site has at most one
popout, reused across its tabs and reloads; every tab syncs via
`storage.onChanged`. Any new item must assume this model, not the old
`popout_win_<winId> → tabId` tab map.

## Current state (repo context)

- Entrypoints: `entrypoints/content.ts`, `background.ts`, `popout/main.ts`
- UI: `components/dictionary-panel.ts`
- Utils: `utils/api.ts`, `utils/utils.ts`, `utils/themes.ts`, `utils/domains.ts`
- Styles: `assets/styles/chrome-extension.css`, `dpd.css`
- Search is duplicated between content script and popout; popout lacks GoldenDict /
  offline fallback; `fetchData` treats any JSON parse as success; no request
  sequencing.
- Popout lifecycle now host-keyed (PR #257): singleton per site, cross-tab sync,
  duplicate-open focuses the existing window, stale flags self-heal via
  `windows.get`. Remaining lifecycle gap is only the last-tab-close orphan (item 3).
- Zero automated tests under `tests/` for the extension.
- Spec.md is stale (pre-popout, missing s.4nt.org).

## Items

### 1. HTTP status ignored in `fetchData`
- **Issue:** API errors look like successful empty lookups.
- **Problem:** `background.ts` always `return { success: true, data }` after
  `response.json()` with no `response.ok` check. 4xx/5xx JSON bodies skip the
  GoldenDict fallback path in `content.ts`.
- **Solution:** Check `response.ok` (and fail closed on non-JSON / bad status);
  return `{ success: false, error }` so callers can fall back.

### 2. Popout missing offline / GoldenDict fallback
- **Issue:** Popout search fails worse than in-page search.
- **Problem:** `content.ts` falls back to GoldenDict on offline / API failure;
  `popout/main.ts` only shows "Error" / "No results".
- **Solution:** Route popout through the same shared search helper as the
  in-page panel (see item 19), including offline + GoldenDict paths.

### 3. Orphan popout / stale flag when the LAST tab of a site closes  *(rewritten post-#257)*
- **Issue:** Closing the last reading tab of a popped-out site can leave a
  popout window with no host tab and a lingering `popout_host_<host>` flag.
- **Problem:** #257 deliberately decoupled the popout from any single tab (it is
  reused across a site's tabs), so closing ONE tab must NOT close the popout.
  The `popout_win_<winId>` record's `tab` field can, however, point at a now-dead
  tab, and `dismissOnTab` would fall back to reading that tab's url.
- **Note:** Largely self-healing already — `dismissOnTab(tabId, host)` is passed
  the host and no longer depends on the tab being alive, and `openPopout` /
  `started` / `onClicked` all revalidate the flag with `windows.get` and clear
  stale entries. **Residual, OPTIONAL:** on `tabs.onRemoved`, if the removed tab
  was the popout record's `tab` and no other tab of that host remains, either
  repoint the record to a surviving tab or leave the standalone popout as-is.
  Low priority — do only if a real orphan is observed in smoke testing.

### 4. Multiple popouts from one tab  ✅ DONE — closed by PR #257 (removed from backlog)
- Superseded by the host-keyed singleton: `openPopout` looks up
  `popout_host_<host>`, validates the window with `windows.get`, and focuses the
  existing window instead of creating another. Stronger than the originally
  planned per-`sourceTabId` singleton. No further work.

### 5. Stale search results (race)
- **Issue:** Rapid lookups can show the wrong entry.
- **Problem:** No generation counter / abort; out-of-order responses overwrite
  newer results.
- **Solution:** Monotonic `searchGeneration` (or AbortController) in the shared
  search helper; ignore stale responses.

### 6. Early popout crosstalk window  ✅ OBSOLETE — closed by PR #257 (removed from backlog)
- The `myTabId` round-trip that created the race is gone. Forwarded
  `popoutSearch` messages are now tagged with `window.location.hostname`, which
  is available synchronously from the first selection, and the popout filters by
  `host`. There is no unresolved-id window, so no crosstalk gap. No further work.

### 7. Popout theme goes stale
- **Issue:** Host dark/light toggle doesn't update the popout.
- **Problem:** Theme is baked into the popout URL once; no live sync.
- **Solution:** Content script, on resolved auto-theme change, message the
  popout (or background → popout) with the new theme key; popout calls
  `applyTheme`.

### 8. CSS collision audit (broader generic classes)  *(reworded post-#257)*
- **Issue:** Next host site may break panel layout like s.4nt.org did.
- **Problem:** Generic classes in fetched HTML (`content`, other legacy bare
  names) can collide with host CSS.
- **Solution:** Audit template classes used inside the panel; add id-scoped
  (`#dict-panel-25445 …`) guards where needed.
- **Note:** The `.jump` leak is already handled — the id-scoped band-aid is in
  place and the full `.jump` → `dpd-jump` webapp rename was deliberately dropped
  (commits `7aabd040`, `b36144dd`). Do NOT re-add the rename; this item is now
  only the *other* generic classes.

### 9. `.button` CSS — verify dead vs. deliberate host guard  *(reworded post-#257)*
- **Issue:** `#dict-panel-25445 .button` / `.button.active` / `.button svg`
  rules remain alongside the `dpd-button` rules.
- **Problem/uncertainty:** These may NOT be dead. A recent commit (`8b6aa320`)
  inspected them and *kept* them (dropping only an inert `line-height`),
  suggesting they intentionally guard host-page or fetched-HTML `.button`
  elements from collision.
- **Solution:** First confirm whether any element the panel renders/fetches uses
  a bare `.button` class. If none, remove the rules; if they are a deliberate
  guard, leave them and drop this item. **Likely already resolved — verify, do
  not blindly delete.**

### 10. Hide Minimize toggle in popout
- **Issue:** Dead settings UI in the popout.
- **Problem:** `neverMinimize` already prevents the sliver; the Minimize toggle
  still shows and confuses.
- **Solution:** Hide the minimize settings row when `neverMinimize` is true.
  (Extended 2026-07-22 per user: also hide "Panel Left / Right" and "Use
  GoldenDict" rows in the popout. Panel-side is meaningless in a standalone
  window; GoldenDict still works but its toggle is hidden there (a global value
  set from the in-page panel still applies). Same `neverMinimize` gate.)

### 11. PAUK Society missing from theme dropdown
- **Issue:** Manual theme picker incomplete vs auto-detect.
- **Problem:** `THEMES.paauksociety` + `detectTheme` exist; dropdown omits it.
- **Solution:** Add `{ key: "paauksociety", name: "PAUK Society" }` to the
  theme options list.

### 12. Default niggahita for s.4nt.org
- **Issue:** Fresh installs on s.4nt may flash wrong ṃ/ṁ.
- **Problem:** `_loadInitialSettings` has domain defaults for SC/DPR/VRI/etc.
  but not s.4nt; theme's `niggahita: true` applies later.
- **Solution:** Add `s.4nt.org` → default `niggahita: true` branch (match theme).

### 13. Keyboard shortcut
- **Issue:** No keyboard way to search selection / focus search.
- **Problem:** Manifest has no `commands`; users expect Alt+D-style shortcuts.
- **Solution:** Add a `commands` entry (e.g. look up selection / focus search);
  wire in background → content. Keep Chrome + Firefox compatible; document in
  info panel.

### 14. Remember popout window size/position
- **Issue:** Popout always opens 480×820.
- **Problem:** No persistence of window geometry.
- **Solution:** On popout close (or resize debounce), save width/height/(left/top
  if available) to `storage.local`; pass into next `windows.create`.

### 15. Firefox popout gap
- **Issue:** Firefox users get no popout affordance and no explanation.
- **Problem:** Popout gated off for Firefox; info UI doesn't say why.
- **Solution:** Document in the info panel that popout is Chromium-only for now.
  Do not invent a Firefox popout in this thread unless a short spike shows MV3
  Firefox can render the extension page window reliably.

### 16. Zero automated tests
- **Issue:** Regressions in word cleaning / domains / themes go unnoticed.
- **Problem:** No tests for pure utils.
- **Solution:** Add unit tests (Vitest or project-native runner already used for
  TS if any; else minimal node/vitest under `exporter/wxt_extension/` or
  `tests/exporter/wxt_extension/`) for `cleanWord`, `isAutoDomain` /
  `isExcludedDomain`, and `detectTheme` URL mapping. Prefer pure-function tests
  with no browser harness.

### 17. Noisy background logging
- **Issue:** Service-worker console flooded in production.
- **Problem:** Logs every incoming message.
- **Solution:** Gate verbose logs behind a dev flag or remove the per-message
  log; keep error logs.

### 18. Stale `spec.md`
- **Issue:** Extension `spec.md` misleads the next agent.
- **Problem:** Missing s.4nt.org, popout, neverMinimize, recent domains.
- **Solution:** Update `exporter/wxt_extension/spec.md` to match current
  behaviour (concise; not a second copy of this thread). Must cover the #257
  host-keyed popout singleton + cross-tab `storage.onChanged` sync, s.4nt.org
  auto-domain/theme, and `neverMinimize`.

### 19. Consolidate search into one module
- **Issue:** content vs popout search drift (items 1, 2, 5 depend on this).
- **Problem:** Duplicated fetch / status / fallback logic.
- **Solution:** Extract `utils/search.ts` (or similar) with one
  `searchWord(q, panel, opts)` used by content + popout; include status check,
  race guard, GoldenDict/offline. Minimal API — no broader refactor.

## Assumptions & uncertainties

- Issue link is #253 (user typed #153 by mistake; #153 is closed Flutter beta).
- No GitHub issue create/comment/close unless user explicitly asks later.
- Item 8's webapp `.jump` rename is parked — extension-side CSS only.
- Item 15 is documentation unless Firefox popout is trivially viable.
- Test runner for TS extension: verify what's already in
  `exporter/wxt_extension/package.json` before adding a new one.
- Manual browser testing still required for popout lifecycle / themes.

## Constraints

- Touch only `exporter/wxt_extension/` (+ tests / this kamma thread). No webapp
  template renames in this thread.
- Match existing TypeScript / WXT patterns; no new heavy frameworks.
- Minimal-first within each item: smallest change that closes the Issue.
- Concurrent kamma threads share this working tree — stage by explicit file list.
- Do not commit unless asked.

## How we'll know it's done

- Items 4 & 6 are closed by PR #257 (no work). Every remaining item has an
  implementation (or an explicit parked/optional note: residual of 3, other-class
  audit of 8, verify-only 9, optional Firefox of 15).
- Shared search path used by content + popout; HTTP failures fall back correctly.
- Popout singleton + tab-close cleanup verified manually.
- Utils unit tests pass; `tsc --noEmit` (or project equivalent) clean.
- `exporter/wxt_extension/spec.md` updated.
- User manual smoke on Chrome (and Firefox for non-popout paths) confirms OK.

## What's not included

- New GitHub issues per item
- Coordinated webapp `.jump` rename + redeploy
- Full Firefox popout implementation (unless spike says yes — then scope via
  drift gate)
- Safari packaging changes
- Unrelated exporter / webapp work
