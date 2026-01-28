# Plan: Diacritic-Insensitive Pāḷi Search Dropdown

**Phase 1: Backend Data Generation**
- [x] Task: Create `scripts/generate_search_index.py`.
- [x] Task: Aggregate unique `lemma_clean` from `dpd_headwords`.
- [x] Task: Aggregate unique `root_no_sign` from `dpd_roots`.
- [x] Task: Aggregate unique `root_family_clean` from `family_root`.
- [x] Task: Build a dictionary mapping ASCII-normalized versions of these terms to their original Unicode versions.
- [x] Task: Save the result as `exporter/webapp/static/search_index.json`.
- [x] Task: Conductor - User Manual Verification 'Backend Data Generation' (Protocol in workflow.md)

**Phase 2: Frontend Implementation**
- [x] Task: Update `app.js` to fetch `search_index.json` in the background.
- [x] Task: Implement a diacritic-stripping function in Javascript.
- [x] Task: Create a debounced input listener for the search box.
- [x] Task: Implement the dropdown UI and visibility logic with scrolling support.
- [x] Task: Conductor - User Manual Verification 'Frontend Implementation' (Protocol in workflow.md)

**Phase 3: Interaction and Navigation**
- [x] Task: Implement keyboard navigation (ArrowUp/Down) for the dropdown.
- [x] Task: Implement selection logic (Enter or Click) to populate the search box and trigger search.
- [x] Task: Ensure the dropdown closes when clicking outside or pressing Escape.
- [x] Task: Conductor - User Manual Verification 'Interaction and Navigation' (Protocol in workflow.md)

**Phase 4: Optimization**
- [x] Task: Verify the JSON payload size and optimize if necessary.
- [x] Task: Test UI responsiveness with the combined dataset (~100k+ entries).
- [x] Task: Conductor - User Manual Verification 'Optimization' (Protocol in workflow.md)
