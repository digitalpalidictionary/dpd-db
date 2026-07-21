# Review — wxt_s4nt_theme

- **Reviewers:** Sonnet subagent + CodeRabbit (shared pass with the popout thread; same working tree).
- **Date:** 2026-07-21

## Verification
- `npx tsc --noEmit` exit 0; both browser builds exit 0.
- Built artifacts contain `s4nt_light`/`s4nt_dark` + header-bar vars (content.js and popout chunk).
- User-confirmed live on s.4nt.org: panel auto-matches the site's light/dark (via its own
  `data-theme` attr, read by `isDark()`); dropdown lists both entries; popout inherits the theme.

## Findings & resolution
| # | Severity | Source | Finding | Resolution |
|---|----------|--------|---------|------------|
| 1 | minor | CodeRabbit | `--dpd-header-bg` left stale when switching from s4nt to a non-header theme. | **FIXED** in `applyTheme` (shared with popout thread) — cleared before the header branch. |
| 2 | major | Sonnet | `s4nt_light` colors differ from the handoff table (`primary/headerBg/headerText`). | **SKIPPED (invalid).** User explicitly directed the change after seeing v1: header de-brown'd to `#efe8db`, `primary` → gold `#c8a060` so buttons match the dark theme's gold-with-black-text. The handoff table's browns are superseded by that instruction; colors are user-approved. |

The `s4nt` header branch (fires for explicit keys and auto-detect), the `s4nt_dark` entry in the
dark-mode check, and the dropdown entries were all reviewed clean and mirror the `vri` pattern.

## Verdict
PASSED — user-approved live; the one valid finding fixed; the "spec mismatch" is a deliberate,
approved user override, not a defect.
