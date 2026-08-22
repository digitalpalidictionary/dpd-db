# Review: Enabled-sites list in extension settings

**Thread:** 20260822_wxt_enabled_sites_settings
**Date:** 2026-08-22
**Reviewer:** agent self-review of the full diff, read from `git diff` rather
than from memory of what was written.

## Scope reviewed

Four changed files in `exporter/wxt_extension/`:

- `utils/domains.ts` — new `normalizeHostname`
- `entrypoints/content.ts` — teardown on key removal
- `components/dictionary-panel.ts` — settings section, list render, add/remove
  handlers, scroll hint
- `tests/utils/domains.test.ts` — 8 new cases

Plus the committed chore: legacy extension moved to `archive/exporter/`.

## Findings

### 1. Trailing-dot hostnames — FIXED during review
A fully-qualified name with a trailing dot (`example.com.`) survives URL
parsing and would have been stored verbatim. `window.location.hostname` never
carries that dot, so the entry could never match the site it was added for — a
silent dud with no error and no feedback. Now stripped, with a test, and `.`
alone correctly returns null rather than an empty key.

### 2. Dropdown close-on-outside-click vs. the × button — checked, no defect
The dropdown closes when a click lands outside it. The `×` handler is `async`
and awaits storage before re-rendering, so the row is still attached to the DOM
while the click event bubbles to the document listener. The containment check
therefore passes and the dropdown stays open. Same reasoning holds for Add.
Order-dependent but correct; noted here because a future refactor making the
handler synchronous would break it.

### 3. Behaviour preservation in the storage listener — verified
The rewritten condition was checked case by case against the original:
`"OFF"` → teardown (unchanged), `"ON"` → falls through to the popout check
(unchanged), key removed → new teardown path. The `isExcludedDomain` /
`isAutoDomain` pair was hoisted into `defaultsOn` and now serves both the
listener and the initial state read — same expression, same operands.

### 4. Junk entries are possible but harmless — accepted, not fixed
Typing a bare number or an intranet-style single word produces a storable
hostname. These are legitimate host shapes (`localhost` is one), so rejecting
them would break the main use case. A junk entry does nothing except sit in the
list, where the user can remove it with the `×`. Not worth guarding.

### 5. Overloaded dropdown — recorded, deliberately not fixed
The scroll hint (R5) treats a symptom. The site list is unreachable from the
one situation it exists to serve: a site where the dictionary is not running.
A standalone extension options page is the correct fix. Out of scope by
agreement; recorded in spec.md R5 so it is not silently forgotten.

## Verification — what actually ran, and what did not

**Automated (all clean):**
- `npm run compile` (tsc --noEmit)
- `npm run test` — 28 passed, up from a 20-test baseline confirmed green before
  any edits
- `npm run build:chrome`
- Presence of the new section confirmed in the built content-script bundle, not
  just in source

**Manual — partially covered.** The user loaded the build and confirmed the
settings section is present and findable after the scroll hint was added, and
declared the result satisfactory. That covers spec.md verification step 1 and
the R5 affordance.

**Not confirmed by observation:** steps 2–5 — adding a site by name and seeing
it activate on a later visit; removing a site you are not on; removing the site
you *are* on and watching the panel disappear; and persistence across a
restart. Step 4 is the one that matters, because it exercises the teardown
change (finding 3), which is the only place in this diff where a silent bug
could hide. The logic was traced by hand and the reasoning is recorded above,
but it has not been watched happening in a browser.

## External review

Two independent passes run in parallel at wrap-up: **CodeRabbit CLI**
(`--base main --type uncommitted --dir exporter/wxt_extension`) and an
**independent agent review**. Worth noting for future threads: CodeRabbit
returned 1 finding, the agent returned 5 and read `background.ts` for
cross-file desync that CodeRabbit did not surface. Both independently found
finding 6 below — a genuine defect neither the author nor a single reviewer had
caught.

### 6. Add did not activate already-open tabs of that site — FIXED
Found by **both** reviewers. `_addEnabledSite` wrote the state key but sent no
message, and the content script's listener only ever tore down; it had no
branch that brought a panel up. Adding a site while a tab of it was already
open did nothing visible until a manual reload, with no cue one was needed.
This was a gap introduced by this feature: the toolbar path (the only prior
ON-transition) always paired its write with an explicit init message.
Fixed by calling `init()` on an ON-transition in the storage listener —
verified safe because `init()` opens with `if (panel) return`, so the existing
toolbar path cannot double-initialise.

### 7. Underscore hostnames rejected — FIXED
`internal_wiki` and similar container/intranet hosts are reported verbatim by
`location.hostname`, but the validation regex excluded `_`, permanently
blocking them from being added. Underscore allowed; test added.

### 8. `×` on a built-in site looked like it worked and did nothing — FIXED
A built-in auto-domain carrying an explicit `"ON"` entry (reachable by toggling
it off then on) appeared in the list. Its `×` cleared the entry, which reverted
the site to its default — which is on. Row vanished, nothing changed.
Resolved per the user's call: **built-in sites are excluded from the list
entirely, whatever their stored state.** The list means user-added sites only;
built-ins stay the toolbar icon's business. Implemented as a shared
`isDefaultOnDomain` helper now used by both the panel and the content script,
so the two definitions cannot drift apart.

### Cleared by the independent reviewer
No XSS (hostnames set via `textContent`); no listener accumulation across
repeated dropdown opens (fresh node each time, `.onclick` overwrites rather
than stacking); `normalizeHostname` correct for scheme/port/path stripping,
trailing dot, IPv6 bracket form, and `localhost` vs `127.0.0.1`; and removing
the current non-built-in site does tear the panel down.

### Accepted, not fixed
Toolbar icon colour is not refreshed for a tab whose site is added or removed
from this list; it self-heals on the next navigation or tab switch. Cosmetic.

## Final verification

`npm run compile` clean · `npm run test` 29 passed · `npm run build:chrome`
clean. Re-run after every fix above, not just once at the end.

## Outcome

Finalized. Residual risk unchanged and still recorded: the live teardown path
and the new cross-tab init path have been reasoned through and type-checked but
not watched in a browser. The options-page design debt (R5) stands as the known
follow-up.
