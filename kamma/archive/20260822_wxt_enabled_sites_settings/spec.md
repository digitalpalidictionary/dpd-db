# Spec: Enabled-sites list in extension settings

**Thread:** 20260822_wxt_enabled_sites_settings
**Date:** 2026-08-22
**Area:** `exporter/wxt_extension/`
**GitHub issue:** none — user-reported via support question. Do NOT write to the tracker.
**Status:** Specced, not started.

> Self-contained: a fresh agent with zero conversational context can execute
> from this spec + plan.md.

## Origin

A user asked whether DPD can be made to work on an arbitrary webpage. Their
concrete case: the extension activates on `s.4nt.org` and `lucid24.org`, but
not on their **local copies** of those same sites.

The behaviour they hit is not a bug — the mechanism already exists — but it is
completely invisible, and unreachable for the site you're actually stuck on.

## Current behaviour (verified in code, 2026-08-22)

- The content script is registered with `matches: ['<all_urls>']`
  (`entrypoints/content.ts:13`), so it is *permitted* on any http/https page.
  **No new permissions or manifest changes are needed for this thread.**
- Whether it *initialises* is gated in `content.ts:248-259`:
  - `storage.local['state_' + hostname] === "ON"` → `init()`
  - `=== "OFF"` → stay dormant (explicit user opt-out)
  - key absent → `init()` only if `isAutoDomain(hostname) && !isExcludedDomain(hostname)`
- `AUTO_DOMAINS` (`utils/domains.ts:1-12`) is a hardcoded list of 11 trusted
  domains. `lucid24.org` is **not** on it — so the user's working `lucid24.org`
  is a stored `state_lucid24.org = "ON"` from a past toolbar click.
- The toolbar click handler (`entrypoints/background.ts`) flips
  `state_<hostname>` and messages the content script.
- **The storage key is hostname only** — no port, no path, no scheme. So
  `localhost:3000` and `localhost:8080` share one entry; `localhost` and
  `127.0.0.1` are two separate entries.
- `file://` pages are blocked by the browser itself, independent of all of the
  above, until "Allow access to file URLs" is enabled for the extension.

## The problem

1. **Invisible.** The only feedback that a site is enabled is the toolbar icon's
   colour. There is no list, no way to audit, no way to remove an entry.
2. **Unreachable where it matters.** The settings dropdown lives *inside* the
   dictionary panel (`components/dictionary-panel.ts:978`), and the panel only
   renders on sites that are already ON. So an in-panel "enable the current
   site" control is a guaranteed no-op — by the time you can see it, the site is
   already enabled. **This is why "just add the current site" was rejected.**

## Solution

Add an **Enabled Sites** section at the bottom of the existing settings
dropdown, with three parts:

1. **A list** of every site the user has switched on.
2. **An `×` per row** to remove that site.
3. **A text box + Add button** taking an **exact site name** — no wildcards, no
   patterns. Typing `localhost` while sitting on SuttaCentral enables the local
   copy for next visit. This is what actually answers the user's question.

### Why exact-name entry and not wildcards

An exact name writes the *same* `state_<hostname>` key the toolbar click already
writes, so it needs **zero new matching logic** and touches no hot path. A
wildcard would require a pattern matcher wired into both the content-script gate
and the background icon-state logic, and belongs on a proper options page rather
than a 220px scrolling dropdown. Explicitly out of scope; see Non-goals.

## Requirements

### R1 — List enabled sites
- Enumerate `storage.local` and collect keys matching `state_<hostname>` whose
  value is `"ON"`. Sort alphabetically by hostname.
- **Built-in auto-domains never appear, whatever their stored state** (revised
  during review — see review.md finding 3). The list is user-added sites only.
  A built-in site with an explicit `"ON"` entry would otherwise show a row whose
  `×` clears the entry but leaves the site running on its default — a button
  that looks like it worked and changed nothing. Filtered via
  `isDefaultOnDomain`, shared with the content script so the two cannot drift.
- Empty state: a short line such as *"No sites added yet."* — never an empty box.

### R2 — Remove a site
- `×` removes the `state_<hostname>` key entirely (not set to `"OFF"`).
  Removal restores default behaviour, which is correct for both cases: a normal
  site reverts to off, an auto-domain reverts to auto-on.
- **Removing the site you are currently on must tear the panel down.**
  ⚠️ `content.ts:240-246` only tears down on `newValue === "OFF"`. On key
  *removal* `newValue` is `undefined`, so the existing listener will NOT fire.
  It must be extended to also tear down when the key is removed and the hostname
  is not an active auto-domain.

### R3 — Add a site by exact name
- Text input + Add button. Accept forgiving input and normalise to a bare
  hostname before storing, because the storage key is hostname-only:
  - `https://localhost:3000/foo` → `localhost`
  - `LocalHost` → `localhost`
  - `  example.com  ` → `example.com`
- Reject empty/whitespace-only input and anything that does not normalise to a
  plausible hostname. Show an inline message; do not write a junk key.
- Adding a site already in the list is a no-op, not a duplicate row.
- Writes `state_<normalised> = "ON"`. If the normalised name equals the current
  hostname, the panel is already open — no action needed beyond the list update.
- The list re-renders immediately after add or remove, without reopening the
  dropdown.

### R4 — Placement
- Bottom of the existing settings dropdown, below the last toggle, separated by
  a divider and a small heading.
- Must not break the dropdown's existing `maxHeight: 400px` / `overflowY: auto`
  scroll behaviour, and must inherit the theme variables like the rows above it.

### R5 — Scroll affordance (added mid-thread, 2026-08-22)
**Not in the original scope.** Added after the first manual test: with eleven
toggle rows already present, the new section sits below the dropdown's 400px
fold and there was no cue that anything existed down there. The user missed it
entirely, which makes the feature undiscoverable in exactly the way the feature
was meant to fix.

- Show a chevron pinned to the bottom edge of the dropdown while it is scrolled
  above the bottom.
- Hide it once the bottom is reached, and never show it when the content fits.
- It must not intercept clicks intended for the row beneath it.
- It must re-measure after the sites list paints, since the list is rendered
  asynchronously and the scrollable height is not final on the first tick.

**Known limitation:** this treats the symptom. The dropdown is overloaded, and
the site list is unreachable from precisely the situation it exists to fix — a
site where the dictionary is not running. A standalone extension options page is
the real answer; deliberately deferred, not forgotten. See Non-goals.

## Non-goals

- Wildcard or pattern matching of any kind.
- A dedicated options page.
- Changing `AUTO_DOMAINS`, or adding `lucid24.org` to it.
- Any `file://` handling, detection, or prompt.
- Touching the legacy extension (already archived in this thread's companion
  chore — see "Related work").
- Editing the theme-per-site or popout-per-site storage keys. Removing a site
  clears only its on/off entry; a remembered theme for that site is harmless.

## Affected files

- `exporter/wxt_extension/components/dictionary-panel.ts` — settings dropdown
  markup (`_toggleSettingsDropdown`) + handlers (`_setupSettingsEventListeners`).
- `exporter/wxt_extension/entrypoints/content.ts` — teardown on key removal (R2).
- `exporter/wxt_extension/utils/domains.ts` — new `normalizeHostname` helper,
  placed here so it is unit-testable alongside the existing domain helpers.
- `exporter/wxt_extension/tests/utils/domains.test.ts` — cases for the helper.

## Verification

- `npm run compile` (tsc --noEmit) clean.
- `npm run test` (vitest) green, including new `normalizeHostname` cases.
- `npm run build:chrome` succeeds.
- **Manual, required — this is UI in a browser and cannot be proven headless:**
  1. On an enabled site, open settings → the site appears in the list.
  2. Add `localhost` by name → it appears; visit a local server on that
     hostname → DPD activates.
  3. `×` a site you are not on → gone from the list; visiting it does nothing.
  4. `×` the site you *are* on → panel disappears immediately (R2 teardown).
  5. Reopen the browser → the list survives.

## Related work

The legacy `exporter/chrome_extension/` was archived to
`archive/exporter/chrome_extension/` on 2026-08-22 before this thread's
implementation, after confirming nothing outside its own folder referenced it
(no build script, task-runner recipe, or CI workflow). The stale `.gitignore`
entry and both `docs/technical/project_folder_structure.md` references were
removed with it. All work in this thread targets the WXT extension only.

## Confidence

**8/10.** The mechanism is read and verified rather than assumed, and the change
is additive UI over storage keys that already exist. The one genuine trap is R2
— the existing teardown listener does not handle key removal, and missing it
would produce a panel that stays open on a site the user just removed.
