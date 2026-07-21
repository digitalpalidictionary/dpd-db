# Review — chrome_ext_popout (final)

- **Reviewers:** independent Sonnet subagent (zero-context) + CodeRabbit CLI (`--base main
  --type uncommitted --dir exporter/wxt_extension`) run in parallel, plus live browser testing
  by the user (Chrome + Firefox) and CDP-console diagnosis.
- **Date:** 2026-07-21

## Verification evidence
- `npx tsc --noEmit` exit 0; `npm run build:chrome` + `build:firefox` exit 0.
- Chrome content.js contains the popout button (1 ref); Firefox build dead-code-strips it (0 refs).
- User-confirmed live: resize/persist/min-width/stuck-recovery, middle-dot, tooltips, popout
  open/pop-in/dismiss, page→popout forwarding, theme match — all working in Chrome. Firefox:
  WebExtensions process flat at 75MB (was climbing to GBs before the observer fix), no popout,
  everything else working.

## Findings & resolution (both review passes reconciled)
| # | Severity | Source | Finding | Resolution |
|---|----------|--------|---------|------------|
| 1 | major | Sonnet | Resize listeners (`_setupResize`) added per panel construction, never removed in `destroy()` → leak across destroy→init cycles. | **FIXED.** `AbortController` field; all document/window resize listeners take `{ signal }`; `destroy()` aborts it. |
| 2 | major | Sonnet | `popoutSearch` is a broadcast with no tab scoping → two popped-out tabs cross-feed each other. | **FIXED.** Background returns tab id on `started`; content stamps `tab` on forwarded selections; popout ignores mismatched `tab` (its own `&tab=` param). |
| 3 | minor | CodeRabbit | `--dpd-header-bg` not cleared when switching s4nt/vri → default/DPR/SC (stale header color). | **FIXED.** `removeProperty("--dpd-header-bg")` before the header branch; vri/s4nt re-set it. |
| 4 | (earlier) | Sonnet r1 | Pop-in before popout learned its window id → dismiss instead of restore. | **FIXED earlier** (bg falls back to `sender.tab?.windowId`). |
| 5 | (earlier) | Sonnet r1 | `poppedOut`/`dpd-popped-out` not reset on `destroy`. | **FIXED earlier.** |
| 6 | major | CodeRabbit | No guard against multiple popouts per source tab. | **SKIPPED (unreachable).** The pop-out button lives in the panel, which is `display:none` while popped out, so it can't be reclicked. Documented as a known edge. |
| 7 | major | Sonnet | `s4nt_light` colors don't match the handoff table. | **SKIPPED (invalid).** The user explicitly directed these colors (de-brown the header, gold+black buttons like dark). Handoff table is superseded by user instruction; themes are user-approved. |
| 8 | minor/nit | both | Debounce timer may fire one `applyTheme("auto")` after destroy (no-ops); `dpdReset`→`destroy` send ordering; Firefox ships dormant popout bytes. | **ACCEPTED.** All harmless; documented. |

## Known follow-up for the owner (deferred, out of minimal scope)
- The memory-critical leaks are fixed (theme observer + resize listeners). No remaining unbounded
  accumulation identified.

## Verdict
PASSED — all blocking/major findings fixed or validly skipped; rebuilt clean; user-confirmed in
both browsers.
