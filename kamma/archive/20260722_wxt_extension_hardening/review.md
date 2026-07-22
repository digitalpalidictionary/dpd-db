## Thread
- **ID:** 20260722_wxt_extension_hardening
- **Objective:** Harden the DPD WXT browser extension after the #253 popout / s.4nt.org work (correctness, popout lifecycle, CSS, UX, hygiene).

## Files Changed
- `entrypoints/background.ts` — `fetchData` `!response.ok` gate; popout geometry persistence (`onBoundsChanged`); removed noisy per-message logs; EOF newline.
- `entrypoints/content.ts` — delegate search to shared helper; storage.onChanged already host-keyed; fixed stale `started` comment.
- `entrypoints/popout/main.ts` — use shared `searchWord`; live theme sync; tightened host-scoped message guard (type-check + require host match).
- `utils/search.ts` (new) — shared `searchWord` (GoldenDict pref, offline, fetch, success/empty/error fallback, monotonic race guard).
- `components/dictionary-panel.ts` — restore `settingsGoldenDict` (was never loaded); hide Minimize/Panel-side/GoldenDict rows in popout; PAUK Society dropdown; s.4nt.org niggahita default; pop-out info note.
- `assets/styles/chrome-extension.css` — removed dead `.button` rules.
- `vitest.config.ts` + `tests/utils/*.test.ts` (new) — Vitest (WxtVitest + happy-dom); 19 tests.
- `spec.md` — refreshed to match current behaviour.

## Findings
Three independent reviews (CodeRabbit, external agent, fresh zero-context subagent). De-duplicated:

| # | Severity | Location | What | Disposition |
|---|----------|----------|------|-------------|
| 1 | ~~major~~→none | dictionary-panel.ts openInGoldenDict | popout `goldendict://` "destroys window" | Rejected — live-tested working; external-protocol handoff, not navigation. Fallback-on-error is intended parity (spec item 2). |
| 2 | minor | popout/main.ts:123 | validate msg.q/msg.theme are strings | Fixed |
| 3 | minor | popout/main.ts:123 | require host match when sourceHost set | Fixed (folded into #2) |
| 4 | minor | utils/search.ts | no searchWord tests | Fixed — added 6 tests (race, status, offline, GoldenDict) |
| 5 | minor | background.ts geometry | off-screen restore risk | Accepted residual — a clamp needs `system.display` perm (spec forbids); Chrome clamps `windows.create`. |
| 6 | nit | content.ts:125 | stale started/tabId comment | Fixed |
| 7 | nit | background.ts EOF | missing newline | Fixed |
| 8 | nit | plan.md/spec.md | stale "not started" header | Fixed |
| — | minor | openPopout | focus-existing-popout ignores new q | Out of scope — #257 residue; noted for follow-up. |

## Fixes Applied
Tightened popout message guard (#2/#3); added `tests/utils/search.test.ts` (#4); fixed stale comment (#6); EOF newline (#7); thread header status (#8).

## Test Evidence
- `npm run compile` (tsc --noEmit) → pass
- `npm run test` → 19/19 pass (4 files)
- `npm run build:chrome` → pass
- `npm run build:firefox` → pass

## Verdict
PASSED
- Review date: 2026-07-22
- Reviewer: Claude (consolidated: CodeRabbit + external agent + independent subagent)
