# Plan: Tipiṭaka Pāḷi Reader (TPR) Links

- [x] Phase 1: Data Extraction & Loading
    - [x] Task: Extract unique `sutta_shortcut` from TPR DB and save to `resources/tpr/tpr_codes.json`
    - [x] Task: Implement `load_tpr_codes_set` in `tools/cache_load.py`
    - [x] Task: Conductor - User Manual Verification 'Data Extraction & Loading' (Protocol in workflow.md)

- [x] Phase 2: Core Logic & Testing
    - [x] Task: Write tests for `SuttaInfo.has_tpr` in `tests/test_tpr_links.py` (Red Phase)
    - [x] Task: Implement `has_tpr` property in `db/models.py` (Green Phase)
    - [x] Task: Conductor - User Manual Verification 'Core Logic & Testing' (Protocol in workflow.md)

- [x] Phase 3: UI Integration
    - [x] Task: Update section heading and add TPR link row in `exporter/webapp/templates/dpd_headword.html`
    - [x] Task: Conductor - User Manual Verification 'UI Integration' (Protocol in workflow.md)

- [ ] Phase 4: GoldenDict Integration
    - [ ] Task: Update section heading and add TPR link row in the relevant GoldenDict template (file name TBD after refactor)
    - [ ] Task: Conductor - User Manual Verification 'GoldenDict Integration' (Protocol in workflow.md)
