# Plan: GoldenDict — Highlight Searched Word in Inflection Table

**Track ID:** `goldendict_inflection_highlight_20260225`
**Issue:** #165

---

## Phase 1: Implement Inflection Highlighting in main.js

### Task 1.1: Add `highlightInflections` to `main.js`
- [x] Sub-task: Open `exporter/goldendict/javascript/main.js`.
- [x] Sub-task: Add `highlightInflections(searchTerm)` function after the existing `loadData()` function. Logic:
  1. Guard: if `!searchTerm` return immediately.
  2. Normalize: create a temporary `div`, set `textContent = searchTerm`, read back `textContent` to normalize HTML entities.
  3. Query all `table.inflection td` cells.
  4. For each cell: split `innerHTML` by `/<br\s*\/?>/i`, map each fragment through a temp element to get `textContent`, compare to normalizedSearch. On match, wrap in `<span class="inflection-highlight">` with plain text as content, set `modified = true`.
  5. If `modified`, rejoin fragments with `<br>` and write back to `cell.innerHTML`.
- [x] Sub-task: In the existing `DOMContentLoaded` callback, after the `loadData()` call, add:
  ```js
  const gdParams = new URLSearchParams(window.location.search);
  const gdWord = gdParams.get("word");
  if (gdWord) {
    highlightInflections(gdWord.trim());
  }
  ```
- [x] Sub-task: Confirm no JS syntax errors by reviewing the diff.

### Task 1.2: Manual Verification
- [x] Sub-task: Export/rebuild the GoldenDict dictionary, or test with the existing build if JS files are loaded at runtime.
- [x] Sub-task: In GoldenDict-NG, search for an inflected form (e.g., "dhammassa"). Open the declension panel. Confirm the "dhammassa" cell is highlighted yellow.
- [x] Sub-task: Search for a lemma (e.g., "dhamma"). Open the declension panel. Confirm the nominative singular cell is highlighted.
- [x] Sub-task: Open the exported HTML in a plain browser (no `word` param). Confirm no errors in console and no spurious highlighting.

- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

---

## Phase 2: Documentation and Cleanup

### Task 2.1: Update exporter README
- [x] Sub-task: Open or create `exporter/goldendict/README.md`.
- [x] Sub-task: Add a note: the inflection highlight feature reads `?word=` from the GoldenDict URL query string via `URLSearchParams` and applies `.inflection-highlight` CSS to matching cells in `table.inflection`.

### Task 2.2: Notify user for commit
- [x] Sub-task: List changed files: `exporter/goldendict/javascript/main.js`, `exporter/goldendict/README.md`.
- [x] Sub-task: Propose commit message: `feat(goldendict): highlight searched word in inflection table #165`

- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)
