# Plan: Diacritic-Insensitive Pāḷi Search Dropdown

**Phase 1: Backend Data Generation**
- [ ] Task: Create `scripts/generate_search_index.py`.
- [ ] Task: Aggregate unique `lemma_clean` from `dpd_headwords`.
- [ ] Task: Aggregate unique `root_no_sign` from `dpd_roots`.
- [ ] Task: Aggregate unique `root_family_clean` from `family_root`.
- [ ] Task: Build a dictionary mapping ASCII-normalized versions of these terms to their original Unicode versions.
- [ ] Task: Save the result as `exporter/webapp/static/search_index.json`.
- [ ] Task: Conductor - User Manual Verification 'Backend Data Generation' (Protocol in workflow.md)

**Phase 2: Frontend Implementation**
- [ ] Task: Update `app.js` to fetch `search_index.json` in the background.
- [ ] Task: Implement a diacritic-stripping function in Javascript.
- [ ] Task: Create a debounced input listener for the search box.
- [ ] Task: Implement the dropdown UI and visibility logic with scrolling support.
- [ ] Task: Conductor - User Manual Verification 'Frontend Implementation' (Protocol in workflow.md)

**Phase 3: Interaction and Navigation**
- [ ] Task: Implement keyboard navigation (ArrowUp/Down) for the dropdown.
- [ ] Task: Implement selection logic (Enter or Click) to populate the search box and trigger search.
- [ ] Task: Ensure the dropdown closes when clicking outside or pressing Escape.
- [ ] Task: Conductor - User Manual Verification 'Interaction and Navigation' (Protocol in workflow.md)

**Phase 4: Optimization**
- [ ] Task: Verify the JSON payload size and optimize if necessary.
- [ ] Task: Test UI responsiveness with the combined dataset (~100k+ entries).
- [ ] Task: Conductor - User Manual Verification 'Optimization' (Protocol in workflow.md)
