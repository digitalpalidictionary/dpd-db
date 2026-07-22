# Review — popout_never_minimize (final)

- **Reviewers:** independent zero-context general-purpose subagent (reviewed Change A
  + Change B adversarially) + my own inline review, plus live browser testing by the
  user. (A first review subagent died on an API connection error and was relaunched.)
- **Date:** 2026-07-22

## Verification evidence
- `npm run compile` (tsc --noEmit) exit 0; `npm run build:chrome` exit 0 (multiple runs).
- Constructor-caller + `settings.minimized` sweeps: only the popout passes the flag;
  in-page panel path byte-identical.
- User-confirmed live: popout renders full-size with the `minimized` setting saved on
  (not a blank/30px strip); word double-click triggers a lookup; drag-select enabled.

## Findings & resolution
| # | Severity | Source | Finding | Resolution |
|---|----------|--------|---------|------------|
| 1 | — | subagent | Change A (never-minimize guard) correct and complete; every minimized render path (class toggle, 30px width, positioning, storage load, settings toggle, maximize btn) funnels through the single gated `minimized` local; #254 observer now a true safety net; no timing hole. | **PASS.** No change needed. |
| 2 | medium | subagent | Change B restored only double-click; **drag-select-to-search was still dead** in the popout — shared `handleMouseUp` (`utils.ts:178`) early-returns for any target inside `#dict-panel-25445` (an in-page copy guard). Contradicted the stated intent. | **FIXED (user decision, option A).** Popout sets `window.dpdIsPopout`; guard becomes `if (!window.dpdIsPopout && target.closest('#dict-panel-25445')) return;`. In-page untouched. |
| 3 | minor | subagent | Popout "Minimize" settings toggle still writes `settingsMinimized` to shared storage (visually inert in popout). | **ACCEPTED / deferred.** Pre-existing; strictly improved vs before (previously it also broke the popout). Noted as out-of-scope follow-up in spec. |

## Scope note
- A word-clickability fix (`addListenersToTextElements()` in the popout) was folded in
  mid-thread after the user found words weren't clickable during verification. Git
  confirmed this was a **pre-existing gap** in the popout (never wired since #253),
  **not** caused by the minimize change.
- A separate host-CSS-leak regression on s.4nt.org surfaced during the same session; it
  was fixed as a direct quick-fix in the extension CSS bundle and its durable
  namespace-rename follow-up parked as spec `20260722_namespace_jump_class`. Both are
  outside this thread.

## Verdict
PASSED — Change A clean; Change B's one real finding fixed per user decision; rebuilt
clean; user-confirmed live. Not committed (user commits at the end).
