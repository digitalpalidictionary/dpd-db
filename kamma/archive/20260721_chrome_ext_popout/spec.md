# Spec — chrome_ext_popout: port fork fixes + popout into WXT source

## Overview
An external contributor (frankksutta) forked the *built* v1.0.4 DPD browser
extension, fixed several bugs, and added a "popout window" feature. Because he
believed no source project existed, he patched the vendored minified bundle and
sent a PR-seed fork + `PATCH-NOTES.md`.

The real WXT/TypeScript source **does** exist in this monorepo at
`exporter/wxt_extension/`. This thread ports his seven changes cleanly into that
source so DPD ships them from its own build, and gets it building locally.

Fork: `frankksutta/dpd-chrome-ext-popout` (his own kamma thread archived there at
`kamma/archive/20260721_dpdx_resize_popout/`). His diagnoses were independently
verified against our source — all seven hold up; four are pre-existing bugs in the
shipped extension.

## The changes (verified against `exporter/wxt_extension/`)

1. **Resize did nothing (root cause: CSS var shadowing).** `chrome-extension.css`
   declares `--dpd-panel-width: 33.33vw` on BOTH `html.dpd-active` (line 15) and
   `#dict-panel-25445` (line 6). The drag JS writes the var on `<html>`; the
   panel's own declaration shadows the inherited value, so only `body` padding
   (the page) follows the drag, never the panel. **Fix:** delete the panel-local
   declaration; keep the one on `html.dpd-active` as the single source of truth.

2. **Width didn't persist across reloads (latent, exposed by fix 1).**
   `DictionaryPanel._loadInitialSettings` applies the stored `settingsPanelWidth`
   to the `<html>` var but never primes `this.savedWidth`; `_applySettings()` then
   `removeProperty`s it because `savedWidth` is `""`. **Fix:** also set
   `this.savedWidth = result.settingsPanelWidth` when present.

3. **Panel draggable unreadably narrow.** Drag floor is `width > 200`
   (`_setupResize`). **Fix:** bump to `340`, and add a CSS `min-width: 340px` on
   the non-minimized panel, scoped behind `@media (min-width: 1020px)` so on narrow
   viewports (where default 33vw < 340px) it never overlaps page content (dev's
   refinement, retained).

4. **Resize could get stuck** if a `mouseup` was missed (over an iframe, outside
   the window, on alt-tab). **Fix:** rewrite `_setupResize` — transparent
   full-viewport overlay during drag (captures mousemove over iframes), self-heal
   when `mousemove` fires with `buttons === 0`, and stop on Escape / window blur.

5. **Middle-dot compounds unresolved.** `cleanWord`'s `PUNCTUATION_REGEX`
   (`utils/utils.ts`) doesn't strip morpheme interpuncts, so `uju·vi·pacc·a·nīka·vādā`
   is searched literally. **Fix:** add `· ‧ ∙ ⋅ ・` (U+00B7/2027/2219/22C5/30FB) to
   the regex. `expandSelectionToWord`'s `stopChars` already omits `·`, so
   double-click keeps the dotted compound as one token before cleaning — no change
   there.

6. **New feature — popout window (Bitwarden-style).** A pop-out button detaches the
   dictionary into its own browser window; a pop-in button (⤡) returns it to the
   page; closing the popout with the window X turns DPD off on that page; while
   popped out the page reclaims full width and page word-selections drive the
   popout. Needs no new manifest permissions (`storage.session` is under `storage`;
   `windows.create/remove` need none in MV3).

7. **Tooltips never appeared (pre-existing).** In `chrome-extension.css` the hide
   rule is ID-scoped `#dict-panel-25445 .dpd-tooltip .dpd-tooltip-text`
   (specificity 1,2,0) while the reveal rule `.dpd-tooltip:hover .dpd-tooltip-text`
   is unscoped (0,3,0), so hide always wins. **Fix:** scope the `:hover` rule with
   the same ID → (1,3,0) beats (1,2,0).

## Key porting decisions (differ from the fork, by design)
The fork's structure was constrained by "cannot touch the minified bundle." Since
we own the source, we take the cleaner WXT-idiomatic path:

- **Popout content-side logic is integrated into `entrypoints/content.ts`**, not a
  second appended content script. This removes the fork's content-script *ordering*
  dependency and its `window.handleSelectedWord` monkey-patch: the `poppedOut`
  branch lives directly in the existing `handleSelectedWord`, and the pop-out button
  is injected right after the panel is created in `init()`.
- **The popout window is a real WXT HTML entrypoint** (`entrypoints/popout/`) whose
  `main.ts` imports `DictionaryPanel`, `applyTheme`, `cleanWord`, and the CSS via ES
  imports — instead of the fork's "load content.js and read window globals" hack.
- **Background handlers go into the existing `onMessage` listener** in
  `entrypoints/background.ts` (plus one `windows.onRemoved` listener), reusing
  `updateIcon(tabId, "OFF")` for the dismiss path.

## Message protocol (unchanged from fork)
- content → bg: `{action:"openPopout", q}` ; `{action:"popIn", win}`
- content → popout page: `{action:"popoutSearch", q}` (runtime broadcast; bg ignores)
- bg → content: `{action:"dpdHidePanel"}` / `{action:"dpdShowPanel"}` / `{action:"dpdReset"}`
- session storage: `popout_win_<winId>` → sourceTabId ; `popout_pin_<winId>` → pop-in flag
- popout window X (no pin flag) → dismiss (reset + destroy + state OFF + gray icon);
  pop-in button (pin flag) → restore in-page panel.

## Assumptions & uncertainties
- WXT outputs `entrypoints/popout/index.html` as `popout.html`; `getURL("popout.html")`
  resolves it. (Verify at build.)
- `browser.storage.session` and `browser.windows.*` are typed in WXT's `browser`
  polyfill. (Verify with the build/typecheck.)
- Opening an own extension page via `windows.create` needs no `web_accessible_resources`
  entry. Existing WAR already lists `*.css` for host-page content CSS.

## How we'll know it's done
- `npm run build` (in `exporter/wxt_extension/`) succeeds; load `.output/chrome-mv3/`
  unpacked.
- Resize drags the panel (not the page); width persists on reload; can't drag below
  340px; minimize still collapses.
- Middle-dot compound lookup works (typed + selection).
- Tooltips show on header buttons.
- Pop-out opens its own window and searches; page reclaims width; page selections
  drive the popout; pop-in restores; window-X turns DPD off on the page.

## Out of scope
- Reconstructing/altering the fork; Web Store publishing; any change to search
  results, themes, audio, or unrelated features.
