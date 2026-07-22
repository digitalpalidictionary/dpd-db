# Plan: WXT extension hardening

**Thread:** 20260722_wxt_extension_hardening
**GitHub issue:** #253 — report only; no tracker writes.
**Date:** 2026-07-22
**Status:** Implemented + reviewed (2026-07-22). All tasks complete or explicitly skipped; review findings applied. Ready for `/kamma:4-finalize`.
**Reviewed 2026-07-22 vs merged PR #257:** items 4 & 6 dropped (done/obsolete),
item 3 reduced to an optional residual, items 8 & 9 reworded. See spec.md notes.

## Architecture Decisions

1. **Shared search module first (item 19)** — extract once, then hang status
   check (1), GoldenDict/offline (2), and race guard (5) on it. Avoids triple
   edits in content + popout.
2. **Popout lifecycle is HOST-keyed (PR #257) — do NOT reintroduce a tab map.**
   Ownership lives in `popout_host_<host>` (`storage.local`), one popout per
   site, reused across tabs, validated with `windows.get`. The session record is
   `popout_win_<winId> → {host, tab}` (background-only). Any remaining lifecycle
   work (item 3 residual) hangs off host, not a `popout_tab_<tabId>` reverse map.
3. **CSS guards stay extension-side** — id-scoped overrides only; no webapp
   class rename in this thread (the `.jump` rename was dropped for good).
4. **Firefox popout = docs only by default** — document the gap; only implement
   if a short spike proves MV3 Firefox can host the popout page.
5. **No new GitHub issues** — all items live under #253 in this thread's docs.

## Dependency order

19 → 1,2,5 → 7 → 8,9 → 10–15 → 16–18
*(items 4 & 6 removed — closed by PR #257; item 3 is an optional standalone.)*

---

## Phase 1 — Shared search + correctness

- [x] 1.1 Extract `utils/search.ts` with `searchWord(query, panel, opts)`
  covering: cleanWord, setSearchValue/setText, fetchData via background,
  success/empty/error handling, offline + GoldenDict when available.
  Wire `content.ts` and `popout/main.ts` to it; delete duplicated inline
  search bodies.
  → verify: `npm run compile` (tsc --noEmit) passes; chrome build OK; both
    entrypoints import `searchWord`. DONE 2026-07-22.
  → note: dropped the cosmetic per-search `getApiBaseUrl` console-log round-trip
    from content (was in-page only, not real behaviour) as part of consolidation.

- [x] 1.2 Item 1 — `fetchData` checks `response.ok` before parsing; non-OK
  returns `{ success: false, error }`.
  → verify: `response.ok` gate added in `background.ts`; non-JSON/network still
    caught → `{success:false}`. tsc + build OK. DONE 2026-07-22.

- [x] 1.3 Item 5 — add monotonic generation (or AbortController) inside
  `searchWord`; ignore stale responses when applying to panel.
  → verify: `searchGeneration` counter added; response/catch bail via `isStale()`.
    tsc + build OK. Manual rapid double-click smoke pending user. DONE 2026-07-22.

- [x] 1.4 Item 2 — popout uses shared helper so offline/GoldenDict/error
  parity matches in-page (GoldenDict via `panel.openInGoldenDict` where
  applicable).
  → verify: `popout/main.ts` has no private fetch/fallback fork — calls
    `searchWord(raw, panel)`. Satisfied by 1.1. DONE 2026-07-22.
  → follow-up bug found during user test (2026-07-22): enabling GoldenDict in the
    popout didn't hold. Root cause: `_loadInitialSettings` in `dictionary-panel.ts`
    omitted `settingsGoldenDict` from its `storage.local.get([...])` array, so the
    saved preference was never restored on any fresh panel (popout OR in-page
    reload). Fix: added `settingsGoldenDict` to the fetch array. Now the popout and
    reloaded panels honour the persisted GoldenDict preference.

- [x] 1.5 Phase 1 verify
  → verify: `npm run compile` clean; `npm run build:chrome` + `build:firefox` OK.
    DONE 2026-07-22.

---

## Phase 2 — Popout lifecycle

- [x] 2.1 Item 4 — singleton popout. ✅ DONE by PR #257 (host-keyed:
  `openPopout` focuses the existing validated `popout_host_<host>` window). No work.

- [x] 2.2 Item 3 — SKIPPED by decision (2026-07-22). User: "happy with a single
  popup for multiple pages of the same site … anything else is overkill."
  Path analysis confirmed no real orphan bug — `dismissOnTab(deadTabId, host)`
  acts on the host not the dead tab, and #257's `windows.get` revalidation
  self-heals stale flags. A tab-less popout is an intended floating dictionary.
  No code change; adding `tabs.onRemoved` logic would risk the intended reuse.

- [x] 2.3 Item 6 — early crosstalk. ✅ OBSOLETE via PR #257 (`myTabId` removed;
  forwarding tagged with `location.hostname`, no unresolved-id window). No work.

- [x] 2.4 Item 7 — on in-page auto-theme change, send theme key to popout
  (host-scoped runtime broadcast `popoutTheme`); popout applies it.
  → verify: content forwards resolved `next` key when `poppedOut`; popout
    `onMessage` calls `applyTheme(msg.theme)`, host-filtered. tsc + build OK.
    Only fires on `auto` sites (guarded); manual popout theme unaffected.
    DONE 2026-07-22.

- [x] 2.5 Phase 2 verify
  → verify: `npm run compile` clean; chrome + firefox builds OK. DONE 2026-07-22.

---

## Phase 3 — CSS

- [x] 3.1 Item 9 — VERIFIED DEAD, then removed. Sweep proved nothing uses a bare
  `.button` class: panel HTML uses `dpd-button`; fetched webapp HTML is
  `class="dpd-button" name="…-button"` (the `-button` hits are `name` attrs, not
  CSS classes); commit `8b6aa320` already labelled it dead (removed only its
  line-height). Removed `.button`, `.button.active`, and the `.button svg`
  selector; kept all `.dpd-button` rules and folded the line-height guard comment
  into the surviving `.dpd-button` rule. Behaviour-preserving (dead = unmatched);
  content.css 23.15→22.85 kB. DONE 2026-07-22.

- [x] 3.2 Item 8 — NO ACTION NEEDED (premise was false). First attempt scoped 7
  "bare" `dpd.css` content selectors + `.apostrophe`; this REGRESSED the panel
  (inflection/freq tables lost rounded corners, sutta/examples lost colour) and
  was fully REVERTED after user testing.
  → ROOT CAUSE of the false positive: those selectors are already scoped via a
    dangling-prefix pattern where `#dict-panel-25445` sits on its OWN line before
    a comment, then the selector on the next line, e.g.
      `#dict-panel-25445 /* inflection tables */`
      (blank)
      `table.inflection { … }`
    CSS joins these across the comment into `#dict-panel-25445 table.inflection`.
    A line-based `rg -v '#dict-panel-25445'` sees only the `table.inflection {`
    line and wrongly reports it unscoped. Prepending the id produced
    `#dict-panel-25445 … #dict-panel-25445 table.inflection` (id nested in itself)
    which matches nothing → styling vanished.
  → Conclusion: all 7 DPD content selectors ARE already scoped; there is no
    outward leak to fix. Item 8 closed as no-op. `.jump` untouched.
  → Lone genuinely-bare selector: `.apostrophe` (chrome-extension.css, preceded
    by `}` not a dangling id) — sets only `pointer-events:none` on apostrophe
    spans; trivial, left as-is. Optional tiny follow-up if ever desired.

- [x] 3.3 Phase 3 verify
  → verify: after revert, `git diff dpd.css` is EMPTY; chrome build green;
    user to reconfirm styling restored. DONE 2026-07-22.

---

## Phase 4 — UX polish

- [x] 4.1 Item 10 (+ mid-thread additions) — hide popout-irrelevant settings rows
  when `neverMinimize` (the popout marker): "Minimize Panel", plus per user request
  2026-07-22 "Panel Left / Right" and "Use GoldenDict". Minimize & Panel-side are
  dead in a popout; GoldenDict still functions but the user chose to hide its toggle
  there (a value set from the in-page panel still applies globally). All three rows
  wrapped in `${this.neverMinimize ? "" : `…`}`; wiring already guards missing
  elements. tsc + build OK. DONE 2026-07-22.

- [x] 4.2 Item 11 — add PAUK Society to theme dropdown.
  → verify: `{ key: "paauksociety", name: "PAUK Society" }` added to options list
    (name matches `THEMES.paauksociety.name`). tsc + build OK. DONE 2026-07-22.

- [x] 4.3 Item 12 — default niggahita true for `s.4nt.org` hostname branch.
  → verify: `else if (domain.includes("s.4nt.org")) niggahita = true` added to
    `_loadInitialSettings` (matches s4nt theme + `detectTheme` host check). Only
    applies when no saved `settingsNiggahita`. tsc + build OK. DONE 2026-07-22.

- [x] 4.4 Item 13 — SKIPPED by decision (2026-07-22). User didn't want a keyboard
  shortcut (low value; double-click already covers lookup). No code change.

- [x] 4.5 Item 14 — persist/restore popout width/height + position via
  `storage.local` (`popout_geometry`). `windows.onBoundsChanged` saves bounds once
  per resize/move gesture, but ONLY for windows with a `popout_win_<id>` record;
  `openPopout` reads geometry and reopens there, defaulting to 480x820 first time.
  onBoundsChanged is Chromium-only (cast + `?.`; Firefox no-ops, popout is
  Chrome-only anyway). tsc + chrome + firefox builds OK. DONE 2026-07-22.

- [x] 4.6 Item 15 — docs-only. Added a "Pop-out Window" note to `_showInfo`:
  on Firefox it states the feature is Chrome/Edge only; on Chrome it explains the
  header icon. No Firefox spike attempted (existing content.ts comment already
  documents that detached extension-page windows misbehave on Firefox). tsc +
  build OK. DONE 2026-07-22.

- [x] 4.7 Phase 4 verify
  → verify: `npm run compile` clean; chrome + firefox builds OK. DONE 2026-07-22.

---

## Phase 5 — Engineering hygiene

- [x] 5.1 Item 16 — added Vitest (WXT's `WxtVitest` integration for `@/` alias +
  `wxt/browser` polyfill + `import.meta.env.BROWSER`) with `happy-dom` env
  (jsdom avoided: overrides Uint8Array, trips esbuild transform). `npm test` =
  `vitest run`. Tests under `tests/utils/` mirroring source:
  `domains.test.ts` (isAutoDomain/isExcludedDomain: exact/subdomain/exclusion),
  `utils.test.ts` (cleanWord: lowercase/trim, punctuation+digit strip, doubling
  collapse + its guards), `themes.test.ts` (detectTheme URL routing —
  deterministic hosts exact, dark-aware hosts by family). 13 tests pass; tsc +
  build green. DONE 2026-07-22.

- [x] 5.2 Item 17 — removed the per-message `console.log` and the paired baseUrl
  debug log in `background.ts`. Kept all `console.error`/`console.warn` and the
  once-per-search route-info log (:156). tsc + build OK. DONE 2026-07-22.

- [x] 5.3 Item 18 — updated `exporter/wxt_extension/spec.md`: refreshed
  auto-domains (incl. s.4nt.org, from live `domains.ts`), documented the
  host-keyed popout + cross-tab sync + neverMinimize + hidden popout settings
  rows + geometry persistence + live theme sync, added `utils/search.ts` (shared
  search + race guard), fixed `fetchData` non-OK behaviour, theme list, and
  `_showInfo`. DONE 2026-07-22.

- [x] 5.4 Phase 5 + full smoke — 2026-07-22:
    `npm run compile` (tsc --noEmit) clean; `npm test` 13/13 pass;
    `build:chrome` ✔; `build:firefox` ✔. All phases complete. Ready for user
    smoke + `/kamma:3-review`.

## Post-review additions

- [x] Em-dash word-boundary fix (`utils/utils.ts`) — user-spotted during finalize
  (2026-07-22): `upakkileso’ti—iti` searched for the glued nonsense
  `upakkilesotiiti`. Em-dash was deleted by `cleanWord`'s PUNCTUATION_REGEX and
  not a stop char in `expandSelectionToWord`. Fix: em-dash → space in cleanWord
  (+ whitespace collapse), removed from the delete-set, and added to expansion
  `stopChars` so double-click stops at it. Scope limited to em-dash (hyphen left
  as-is for Pāḷi compounds). Test added in `tests/utils/utils.test.ts`; 20/20
  pass, tsc + build green.
