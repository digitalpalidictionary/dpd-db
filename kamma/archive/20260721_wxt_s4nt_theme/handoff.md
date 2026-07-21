# Handoff: add s.4nt.org theme (light + dark) to the WXT extension

## Goal
Add a light and dark theme matching **https://s.4nt.org** to the DPD cross-browser extension in `exporter/wxt_extension/`. The extension already has a theme system (SuttaCentral, VRI, DPR, etc.); this just adds one more site.

## ⚠️ Concurrency warning
Another agent (thread `20260721_chrome_ext_popout`) currently has these files **dirty in the shared working tree**: `components/dictionary-panel.ts`, `assets/styles/chrome-extension.css`, `entrypoints/background.ts`, `entrypoints/content.ts`, `utils/utils.ts`, and an untracked `entrypoints/popout/`.
- **Steps 1 & 2 below touch `utils/themes.ts` and `types/extension.d.ts` — files they are NOT touching. Do these freely.**
- **Step 3 touches `components/dictionary-panel.ts` (theirs). Keep it to the single 2-line insertion described. Do not `git stash`, do not reformat the file, stage only by explicit filename.**

## How the theme system works (already investigated)
All in `exporter/wxt_extension/utils/themes.ts`:
- `THEMES` map — each entry: `bg/text/primary/border` (+ optional `accent/font/fontSize/niggahita/bgImage`).
- `detectTheme()` — maps `window.location.href` → a theme key.
- `applyTheme(key)` — writes `--dpd-*` CSS vars onto `#dict-panel-25445`.
- `isDark()` already checks `<html data-theme="dark">`. **s.4nt.org sets exactly `data-theme="dark"`/`"light"` on `documentElement`, so auto-detection works with no extra plumbing.**

## Exact colors (pulled from the live s.4nt.org inline CSS — do NOT guess)
| field | Light (`:root`) | Dark (`[data-theme="dark"]`) |
|---|---|---|
| bg | `#faf8f4` | `#1a1612` |
| text | `#1a1612` | `#e8dfc8` |
| primary / accent | `#5c3d1e` | `#c8a060` |
| border | `#ddd6c8` | `#3a3028` |
| header bar bg | `#5c3d1e` | `#241c10` |
| header text | `#f5ede0` | `#e8d8b8` |
| font | `Georgia, serif` | `Georgia, serif` |

s.4nt.org uses **ṁ** (niggahita dot-above), so `niggahita: true`.

## Changes

### Step 1 — `types/extension.d.ts`
The `Theme` interface (starts line 21) has no way to express a distinct header bar. Add two optional fields:
```ts
    headerBg?: string;
    headerText?: string;
```

### Step 2 — `utils/themes.ts` (3 edits)

**2a. Add to the `THEMES` object** (after the `paauksociety` entry, ~line 198):
```ts
  s4nt_light: {
    name: "s.4nt.org",
    bg: "#faf8f4",
    text: "#1a1612",
    primary: "#5c3d1e",
    border: "#ddd6c8",
    headerBg: "#5c3d1e",
    headerText: "#f5ede0",
    font: "Georgia, serif",
    niggahita: true
  },
  s4nt_dark: {
    name: "s.4nt.org Dark",
    bg: "#1a1612",
    text: "#e8dfc8",
    primary: "#c8a060",
    border: "#3a3028",
    headerBg: "#241c10",
    headerText: "#e8d8b8",
    font: "Georgia, serif",
    niggahita: true
  }
```

**2b. In `detectTheme()`** (~line 335), add before the final `return "auto"`:
```ts
  if (url.includes("s.4nt.org")) return isDark() ? "s4nt_dark" : "s4nt_light";
```

**2c. In `applyTheme()`:**
- Add `s4nt_dark` to the `isDarkTheme` check (~line 433):
  ```ts
  const isDarkTheme = themeKey === "dpd_dark" || themeKey === "suttacentral_dark" || themeKey === "tbw_dark" || themeKey === "s4nt_dark" ||
                      (themeKey === "auto" && isDark());
  ```
- In the header `if/else if` chain (~lines 446–465), add an `s4nt` branch that sets the header bar colors (mirror the existing `vri` branch). It must fire for the explicit keys AND for auto-detect. Insert it as an `else if` before the final `else { ...--dpd-header-text... }`:
  ```ts
  } else if (themeKey === "s4nt_light" || themeKey === "s4nt_dark" ||
             (themeKey === "auto" && (detectTheme() === "s4nt_light" || detectTheme() === "s4nt_dark"))) {
    panelEl.style.setProperty("--dpd-header-bg", theme.headerBg || theme.bg);
    panelEl.style.setProperty("--dpd-header-text", theme.headerText || theme.text);
  } else {
  ```

### Step 3 — `components/dictionary-panel.ts` (the shared file — minimal edit)
In the theme dropdown `options` array (~lines 913–923), add two entries after the `tipitakalk` line:
```ts
      { key: "s4nt_light", name: "s.4nt.org" },
      { key: "s4nt_dark", name: "s.4nt.org Dark" },
```
Auto-detection works without this; these entries only let the user manually pick the theme on other sites. If coordination with the other agent is a problem, this step can be deferred.

## Verify
- Typecheck: from `exporter/wxt_extension/`, run `npx tsc --noEmit` (or the project's wxt/lint typecheck) — the new `Theme` fields and entries must compile clean.
- Trace `applyTheme("s4nt_light")` and `("s4nt_dark")`: confirm `--dpd-bg`, `--dpd-text`, `--dpd-primary`, `--dpd-border`, `--dpd-header-bg`, `--dpd-header-text` all get the table values, and the header bar gets its own color.
- Live test (user does this): load extension on `https://s.4nt.org/an/an1/index.html`, toggle the site between light/dark, confirm the panel auto-matches, and confirm both entries show in the theme dropdown.

## Reference files
- Theme logic: `exporter/wxt_extension/utils/themes.ts`
- Theme type: `exporter/wxt_extension/types/extension.d.ts`
- Dropdown + panel: `exporter/wxt_extension/components/dictionary-panel.ts`
- Header CSS var consumer: `assets/styles/chrome-extension.css` line 90 (`--dpd-header-bg, var(--dpd-bg)`) — no edit needed.
