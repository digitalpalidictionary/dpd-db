# Plan — s.4nt.org theme (executed per handoff.md)

Implemented alongside `20260721_chrome_ext_popout` (same working tree, same agent — no
concurrency conflict). All paths under `exporter/wxt_extension/`.

- [x] Step 1 — `types/extension.d.ts`: added `headerBg?`, `headerText?` to `Theme`.
- [x] Step 2a — `utils/themes.ts`: added `s4nt_light` + `s4nt_dark` to `THEMES` (colors per
  handoff table; `niggahita: true` = ṁ default, per user).
- [x] Step 2b — `detectTheme()`: `s.4nt.org` → `isDark() ? "s4nt_dark" : "s4nt_light"`
  (site sets `data-theme` on `<html>`, which `isDark()` already reads → auto works).
- [x] Step 2c — `applyTheme()`: `s4nt_dark` added to `isDarkTheme`; new `s4nt` header-bar
  branch (mirrors `vri`) sets `--dpd-header-bg`/`--dpd-header-text` for explicit keys and auto.
- [x] Step 3 — `components/dictionary-panel.ts`: added the two `s4nt_*` entries to the theme dropdown.

## Verify
- [x] `npx tsc --noEmit` exit 0; `npm run build` exit 0.
- [x] Built artifacts contain `s4nt_light`/`s4nt_dark` + header-bar vars (content.js and popout chunk).
- [x] User live test on `https://s.4nt.org/...`: panel auto-matches light/dark; dropdown shows both
  entries; popout (Chrome) inherits the theme. Light theme refined after first look: header
  de-brown'd to `#efe8db` w/ dark text, `primary` → `#c8a060` (gold) so buttons match the dark
  theme's gold-with-black-text (auto-contrast via `getContrastText`). Both themes user-approved.

## Note
This thread's fix is what makes the popout theme work correctly (the popout receives the resolved
`s4nt_*` key). The popout thread's Phase 6 JSON-copy hack was reverted in favour of this.

## FINALIZED 2026-07-21
Reviewed with the popout thread. s4nt_light/s4nt_dark shipped; colors user-approved (light theme
refined per user away from the handoff browns). One valid finding (stale header-bg) fixed. See review.md.
