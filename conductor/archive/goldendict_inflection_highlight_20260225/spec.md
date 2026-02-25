# Spec: GoldenDict — Highlight Searched Word in Inflection Table

**Issue:** [#165](https://github.com/digitalpalidictionary/dpd-db/issues/165)
**Track ID:** `goldendict_inflection_highlight_20260225`
**Type:** Enhancement

---

## Overview

When a user looks up an inflected Pāḷi form in GoldenDict or GoldenDict-NG (e.g., searching for "dhammassa"), the dictionary finds the headword entry ("dhamma") and displays the full declension table. Currently, the searched form is not visually distinguished inside the table — the user must scan every cell to find which form they actually looked up.

This feature reads the searched word from the GoldenDict URL query string and uses it to automatically highlight the matching cell(s) in the inflection table with a yellow background when the table is displayed.

---

## Technical Context

### GoldenDict-NG DOM & URL Structure

GoldenDict-NG (QtWebEngine) loads dictionary articles at a custom URL scheme:

```
gdlookup://localhost/?word=dhammassa&group=1&...
```

The searched word is available in JavaScript via `window.location.search`:

```js
const params = new URLSearchParams(window.location.search);
const word = params.get("word");
```

**Important:** `document.title` is **not** the searched word. GoldenDict-NG does NOT override the HTML `<title>` tag — it remains "Digital Pāḷi Dictionary". The classic GoldenDict docs suggested `document.title`, but this does not apply to GoldenDict-NG's QtWebEngine implementation (confirmed by reading `articleview.cc`: `currentWord` is stored in C++ only and never injected into the page).

### Inflection Table

- **Inflection HTML** is pre-built at database-build time in `db/inflections/generate_inflection_tables.py` and stored in `DpdHeadword.inflections_html`. It is a `<table class='inflection'>` with `<td>` cells containing text formatted as `stem<b>ending</b>`, with multiple forms within a cell separated by `<br>`.
- The inflection table `<div>` starts **hidden** (`class="dpd content hidden"`) and is revealed when the user clicks the conjugation/declension button. DOM manipulation on hidden elements is valid — the highlight will be present when the table is subsequently revealed.

### Existing Infrastructure

- The CSS class **`.inflection-highlight`** already exists in `identity/css/dpd.css` and `identity/css/dpd-css-and-fonts.css` (the GoldenDict CSS file). **No CSS changes are required.**
- The webapp's `exporter/webapp/static/app.js` already implements the identical `highlightInflections(searchTerm)` pattern. This track ports that logic to `main.js`.

---

## Functional Requirements

1. **FR-1 — Highlight on Load:** On `DOMContentLoaded`, JavaScript reads the `word` parameter from `window.location.search` (via `URLSearchParams`) and uses it as the search term to highlight matching cells in `table.inflection`.

2. **FR-2 — Cell Matching:** For each `<td>` in `table.inflection`, split `innerHTML` by `<br>` tags. For each fragment, extract plain-text via a temporary element's `textContent`. If the plain text exactly matches the search term, wrap that fragment in `<span class="inflection-highlight">` with the plain text as content.

3. **FR-3 — Guard Clause:** If no `word` param exists in the URL (e.g., in a plain browser context), return early without error.

4. **FR-4 — Works on Hidden Tables:** Highlighting is applied at DOM ready time, before the button is clicked. The highlight must be visible when the table is subsequently revealed.

5. **FR-5 — No Python Changes:** No changes to inflection generation, database schema, Jinja templates, or CSS files.

---

## Acceptance Criteria

- [ ] AC-1: When GoldenDict-NG looks up an inflected form (e.g., "dhammassa"), the matching cell in the declension table is highlighted yellow when the declension panel is opened.
- [ ] AC-2: When GoldenDict-NG looks up a lemma directly (e.g., "dhamma"), the nominative singular cell is highlighted.
- [ ] AC-3: When multiple forms in the same cell match (rare edge case), all matching fragments within that cell are highlighted.
- [ ] AC-4: If no cell matches the searched term, no error is thrown and no visual change occurs.
- [ ] AC-5: The bold stem/ending formatting within a highlighted cell is replaced by the plain-text span (acceptable UX trade-off, matching webapp behaviour).
- [ ] AC-6: Opening the article in a regular browser (no `word` param in URL) produces no errors and no spurious highlighting.

---

## Out of Scope

- Highlighting in the webapp (already implemented).
- Highlighting in MDict, Kindle, Kobo, or other exporters.
- Modifying the inflection HTML generation in Python.
- Adding CSS — `.inflection-highlight` already exists.
- Fuzzy/partial matching of the search term.
- Using mark.js (GoldenDict-NG bundles it for FTS, but it is not available in DPD article pages; the existing `innerHTML`-based approach is sufficient).
