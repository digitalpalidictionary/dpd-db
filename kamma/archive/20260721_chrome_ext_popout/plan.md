# Plan — chrome_ext_popout

All paths under `exporter/wxt_extension/`.

## Phase 1 — CSS + localized bug fixes (fixes 1, 2, 3, 5, 7)
- [x] 1.1 Fix 1: deleted panel-local `--dpd-panel-width: 33.33vw;`; kept on `html.dpd-active`.
- [x] 1.2 Fix 7: scoped tooltip hover rule to `#dict-panel-25445 .dpd-tooltip:hover .dpd-tooltip-text`.
- [x] 1.3 Fix 3 (CSS): added `@media (min-width:1020px){ #dict-panel-25445:not(.dpd-minimized){min-width:340px} }`.
- [x] 1.4 Fix 5: added `·‧∙⋅・` to `PUNCTUATION_REGEX` in `utils/utils.ts`.
- [x] 1.5 Fix 2: primed `this.savedWidth` in `_loadInitialSettings`; drag floor 340 in 2.1.

## Phase 2 — robust resize (fix 4)
- [x] 2.1 Rewrote `_setupResize`: overlay + `buttons===0` self-heal + Escape/blur stop;
  340 floor; syncs `this.savedWidth` and persists on every stop path.

## Phase 3 — popout feature (fix 6)
- [x] 3.1 `background.ts`: `openPopout` + `popIn` in the `onMessage` listener;
  `windows.onRemoved` + `dismissOnTab` (reuses `updateIcon`).
- [x] 3.2 `content.ts`: `poppedOut` state; `injectPopoutButton()` after panel creation;
  `handleSelectedWord` forwards `popoutSearch` when popped out; object-message handling;
  `dpd-popped-out` toggle.
- [x] 3.3 `chrome-extension.css`: added `html.dpd-active.dpd-popped-out body{padding:0}` rule.
- [x] 3.4 New `entrypoints/popout/index.html` + `main.ts` — builds via ES imports; emits `popout.html`.

## Phase 4 — build & verify
- [x] 4.1 `npm run build` → exit 0; `popout.html` present; permissions still `["storage","activeTab"]` (no new perms).
- [x] 4.1b `npx tsc --noEmit` → exit 0 (clean).
- [x] 4.2 User in-browser test round 1 (Chrome, load-unpacked). Result: resize/persist/min-width,
  middle-dot, tooltips, popout open/close, and page→popout forwarding all confirmed working.
  One transient JS console error on the popout's first run (user cleared it; worked after — text
  not captured; likely a benign "port closed" from a fire-and-forget message, already `.catch`ed).
  Follow-up surfaced: popout theme was hardcoded `auto`, not matching the source page.

## Phase 5 — theme consistency (from user test round 1)  [SUPERSEDED by Phase 6]
- [x] 5.1 `content.ts`: `currentThemeKey()` resolved a theme KEY (`detectTheme()` for `auto`).
- [x] 5.2 `background.ts`: append `&theme=<key>` to the popout URL.
- [x] 5.3 `popout/main.ts`: `applyTheme(key)`.
- [x] 5.4 built clean.

## Phase 6 — theme transfer redesign (from user test round 2, CDP-confirmed root cause)
Live diagnosis (Chrome DevTools console in the real popout) proved: `applyTheme` WORKS in the
popout (`applyTheme('suttacentral_dark')` → panel `#414141`), but the key passed was `"auto"`, and
`applyTheme('auto')` is meaningless in a detached window — `detectTheme()` sees the
`chrome-extension://` URL and `extractColors()` reads the popout's own light bg. So NO key that can
be `"auto"` will ever work. Fix = transfer the *resolved colours*, not a key.
- [x] 6.1 `content.ts`: replace `currentThemeKey()` with `currentThemeData()` — serialise the source
  panel's inline `--*` custom properties + theme marker classes (`dark-mode`, `dpd-theme-*`) +
  font as JSON; send in `openPopout`.
- [x] 6.2 `popout/main.ts`: `applyResolvedTheme()` parses the JSON and replays vars/classes/font
  directly onto the popout panel; falls back to `applyTheme('auto')` only if no usable payload
  (older content script). `background.ts` URL param unchanged (now carries JSON).
- [x] 6.3 `tsc --noEmit` exit 0; `npm run build` exit 0.
- [ ] 6.4 User retest — **must reload the source TAB**, not just the extension (content.ts changed;
  open tabs keep running the old content script until reloaded).

## Phase 7 — proper s.4nt.org theme (correct fix; Phase 6 hack REVERTED)
Root cause of all theme flakiness: `s.4nt.org` had no theme, so it fell into fragile
`extractColors()` auto-guessing — doubly broken in the popout (its DOM ≠ source). CDP-console
diagnosis proved `applyTheme` works with named keys but not `"auto"` in a detached window.
Correct fix = give the site a first-class theme (its own `kamma/threads/20260721_wxt_s4nt_theme`
handoff), then pass the resolved KEY to the popout (the simple path that provably works).
- [x] 7.1 Reverted Phase 6 JSON-vars-copy: `content.ts` back to `currentThemeKey()` (resolves
  `auto`→concrete key via `detectTheme()` on the live page); `popout/main.ts` back to `applyTheme(key)`.
- [x] 7.2 Added `s4nt_light`/`s4nt_dark` themes (see sibling thread) — auto-detected via the site's
  own `data-theme` attribute, which `isDark()` already reads. niggahita ṁ default (`niggahita: true`).
- [x] 7.3 `tsc --noEmit` exit 0; build exit 0; `s4nt_*` + header-bar vars present in built content.js
  and popout chunk.
- [x] 7.4 User live test on s.4nt.org: light + dark both confirmed good (header de-brown'd,
  gold+black buttons); popout matches page theme in Chrome.

## Phase 8 — memory leak + Firefox (from user testing rounds 3–4)
- [x] 8.1 Guarded unbounded async in `content.ts`: theme `MutationObserver` was un-throttled, never
  disconnected, ran `storage.local.get` + `applyTheme` on every attribute mutation → runaway RAM
  (user hit 27GB on s.4nt.org). Fixed: 200ms debounce, dedupe on `detectTheme()` change, disconnect
  + clear timer in `destroy`, self-disconnect on invalidated context. Also `.catch` on the `started`
  send. Fixes the "Extension context invalidated" red errors too (orphaned script now fails silent).
- [x] 8.2 Popout gated to Chromium: `injectPopoutButton()` early-returns on
  `import.meta.env.BROWSER === "firefox"`. Firefox popout never rendered (blank window + memory
  spike on pop-out); it's the single entry point so the whole flow is disabled there. esbuild
  dead-code-strips the popout button code from the Firefox bundle (verified: 0 refs in FF content.js,
  1 in Chrome).
- [x] 8.3 Built both targets (`build:chrome`, `build:firefox`); `tsc --noEmit` exit 0.
- [x] 8.4 User confirmed: Firefox WebExtensions process flat at 75MB (was climbing to GBs), no popout
  icon, everything else works. Chrome popout unaffected.

## Phase 9 — review fixes (Sonnet + CodeRabbit, parallel)
- [x] 9.1 Resize-listener leak (Sonnet major): the `_setupResize` document/window listeners were
  never removed on `destroy()`. FIXED via `AbortController` — all four listeners take `{ signal }`;
  `destroy()` calls `this.resizeAbort.abort()`. (This was the deferred follow-up; now done.)
- [x] 9.2 Popout cross-tab crosstalk (Sonnet major): `popoutSearch` broadcast reached every popout.
  FIXED — background returns the tab id on `started`; content stamps `tab` on forwarded selections;
  popout ignores selections whose `tab` ≠ its own `&tab=` param.
- [x] 9.3 Stale `--dpd-header-bg` (CodeRabbit minor): FIXED — cleared before the header branch in
  `applyTheme` so switching s4nt/vri → a plain theme falls back to the CSS default.
- Skipped (reason in review.md): same-tab multi-popout (unreachable — button hidden while popped
  out); "s4nt_light spec mismatch" (user-directed colors, approved).
- [x] 9.4 `tsc --noEmit` exit 0; Chrome + Firefox rebuilt clean; button present in Chrome (1),
  stripped in Firefox (0).

## Tooling note (for the record)
Native `/chrome` browser tools never loaded into the CLI session; self-driven CDP couldn't load the
unpacked extension (2026 Chrome disabled the `--load-extension` flag). Root cause was nailed via a
one-paste DevTools console snippet the user ran in the live popout. Keep that snippet approach for
future in-extension debugging here.

## Decisions / deviations (log)
- Popout content-side logic integrated into `content.ts` (no 2nd content script) — see spec.
- Popout page uses ES imports, not window-global reuse — see spec.
- DEVIATION: `browser.runtime.getURL` isn't on WXT's runtime type → cast `(browser.runtime as any).getURL`,
  matching the existing convention in `components/dictionary-panel.ts:628`.
- `browser.storage.session` / `browser.windows.*` typed fine under WXT 0.19 — no casts needed there.

## FINALIZED 2026-07-21
Reviewed (Sonnet + CodeRabbit, parallel) → 2 majors fixed (resize-listener leak via
AbortController; popout cross-tab crosstalk via tab-stamped forwarding), 1 minor fixed
(stale --dpd-header-bg), invalid/unreachable findings skipped with reason (see review.md).
tsc clean; Chrome + Firefox rebuilt. User-confirmed both browsers. Sibling: 20260721_wxt_s4nt_theme.
