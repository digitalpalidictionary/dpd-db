# Spec: Popout never enters minimized state (defense-in-depth)

**Thread:** 20260722_popout_never_minimize
**Date:** 2026-07-22
**GitHub issue:** #253 (Browser extension updates) — do NOT write to the tracker; report only.
**Status:** Confirmed direction

> **Self-contained:** this spec + plan.md capture the whole decision trail so a
> fresh agent with zero conversational context can execute from these two files.

## Background (how we got here)

PR #254 fixed a bug where the detached popout window froze on dark-themed sites:
an unconditional `classList.remove('dpd-minimized')` inside a `MutationObserver`
re-fired the observer (removing an absent token still rewrites the `class`
attribute), producing an infinite microtask loop, tripped by `applyTheme()`
toggling the `dark-mode` class. #254 replaced it with a guarded observer that
only removes the class when present and disconnects while removing. Merged.

While auditing #254, an independent verification pass found that my original
"the width CSS overrides make minimized inert in the popout" reasoning was
**wrong**, even though the no-visible-bug outcome happened to hold. The real
picture:

- `.dpd-minimized` does far more than change width. `chrome-extension.css:645-657`
  sets `display: none !important` on `.dpd-content`, `.dpd-search-box`,
  `.dpd-footer`, `.dpd-title`, `.dpd-nav-group`, `.dpd-status-text`, etc. The
  popout imports this stylesheet (`popout/main.ts` → `chrome-extension.css`).
- The popout's `#dict-panel-25445 { width: 100% !important }` and
  `#dict-panel-25445.dpd-minimized { width: 100% !important }`
  (`popout/index.html:23,35`) only override **width**. They do nothing about the
  `display:none` child-hiding rules.
- Worse, `index.html:35`'s `width:100% !important` has **equal** specificity to
  `chrome-extension.css:548`'s `width:30px !important` (both `.dpd-minimized`,
  both `!important`), so the winner is cascade-order-dependent; WXT injects the
  imported stylesheet after the inline `<style>`, so `30px` can actually win.

**Therefore:** if the `dpd-minimized` class is ever present on the panel at paint
time in the popout, the popout renders broken — a narrow strip showing only the
logo + settings/maximize buttons, no content, no search box. The class IS added
by `_applySettings` (`dictionary-panel.ts:218`) whenever a user's saved
`settingsMinimized` is `true`, because the popout reuses the same
`DictionaryPanel` component.

**What actually prevents the bug today:** the PR #254 `MutationObserver` alone —
it strips the class on a microtask before first paint (the class is added only
after an `await` in `_loadInitialSettings`, and the observer is registered
synchronously before that resolves). This is a **single point of failure**. If
the observer regressed, or the class were ever added before the observer
registered, the popout would break visibly for saved-minimized users.

## Goal

Make the popout **never enter minimized state at the source**, so the #254
observer becomes a genuine safety net rather than the sole load-bearing
mechanism. The popout is a real OS window sized by its frame; the minimized
"sliver" concept does not apply there at all.

## Decisions (do not relitigate)

1. **Fix at the source in the shared component**, gated by an explicit flag —
   not by DOM-sniffing "am I in the popout". Add an optional `neverMinimize`
   flag to `DictionaryPanel`; the popout constructs the panel with it set.
2. **Compute an effective-minimized in `_applySettings`** as
   `this.neverMinimize ? false : this.settings.minimized`, and use that for the
   class toggle, the width branch, and the positioning branch. This makes the
   guarantee hold for BOTH the load path and any runtime toggle, without
   mutating stored settings (`settings.minimized` may still reflect storage —
   harmless).
3. **Keep the #254 observer.** It stays as belt-and-suspenders and is already
   merged/verified. Removing it is out of scope and would reduce defense.
4. **Behaviour for the in-page content-script panel is unchanged** — it
   constructs `DictionaryPanel` with no flag, so `neverMinimize` defaults to
   `false` and every existing minimized code path is byte-identical.

## Out of scope (follow-ups, do NOT do here)

- Hiding / removing the inert "Minimize Panel" settings toggle in the popout
  (verification noted it's effectively dead UI in the popout — toggling it
  reverts immediately). Separate change; only do it if the user asks.
- Any change to the #254 observer itself.

## Added mid-thread (2026-07-22): popout words not clickable

Discovered during the user's manual verification: double-click / select-to-search
on words **inside the popout's own results** never worked. Traced and confirmed
via git that this is **pre-existing and unrelated to the minimize change** — the
popout entrypoint (`popout/main.ts`) has never called `addListenersToTextElements()`
(the `document.body` `dblclick`/drag-select delegation in `utils.ts:211` that calls
`handleSelectedWord`). The in-page content script wires it in `init()`
(`content.ts:162`); the popout was simply missing the equivalent call. Not caused
by the `dpd-minimized` class (the popout content is unminimized in both the pre-
and post-change states).

**Fix:** `popout/main.ts` now imports and calls `addListenersToTextElements()`
after panel setup, routing word clicks through the popout's own
`handleSelectedWord`. Folded into this thread because it is popout-scoped and
surfaced during this thread's verification; it is a distinct concern from the
minimize guard.

This restores **both double-click and drag-select-to-search** in the popout.
The shared `handleMouseUp` (`utils.ts:178`) early-returns for any target inside
`#dict-panel-25445` — an intentional in-page guard (there the panel is chrome and
you drag-select to copy, while the searchable text is the host page outside the
panel). In the popout the whole result is inside the panel, so that guard would
block drag-select.

**Decision (2026-07-22): enable drag-select-to-search in the popout (option A).**
`popout/main.ts` sets `window.dpdIsPopout = true`; the guard becomes
`if (!window.dpdIsPopout && target.closest('#dict-panel-25445')) return;`. In-page
behaviour is untouched (the flag is only ever set in the popout's own window).
The accepted trade — in the popout a drag-highlight fires a search instead of a
plain copy — was judged a non-issue: the popout is a lookup window, the handler
only fires on a real drag (>5px), and any accidental search is recoverable with
the back button.

## Files

- `exporter/wxt_extension/components/dictionary-panel.ts` — add `neverMinimize`
  field + optional constructor param; compute effective-minimized in
  `_applySettings`.
- `exporter/wxt_extension/entrypoints/popout/main.ts` — pass
  `{ neverMinimize: true }`; set `window.dpdIsPopout = true`; import + call
  `addListenersToTextElements()`.
- `exporter/wxt_extension/utils/utils.ts` — `handleMouseUp` panel guard is now
  bypassed when `window.dpdIsPopout` is set, so drag-select searches in the popout.

## Verification

- `npm run compile` (tsc --noEmit) clean.
- `npm run build:chrome` builds.
- Manual (user-confirmed 2026-07-22): with a saved `settingsMinimized: true`, the
  popout renders full-size (not a blank/30px strip) and words are clickable.
- Manual (pending): drag-select a word/phrase in the popout results triggers a
  lookup; in-page sidebar drag-select still copies (does NOT search).
