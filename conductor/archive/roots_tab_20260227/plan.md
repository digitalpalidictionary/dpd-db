# Plan: GUI2 Roots Tab

## Phase 1: Database Layer — Root CRUD Methods

- [x] Task 1.1: Write Tests for Root CRUD Methods
  - [ ] Create `tests/test_roots_db.py`
  - [ ] Test `get_all_root_keys_sorted()` returns sorted list of root keys
  - [ ] Test `get_root_by_key()` returns correct `DpdRoot` or `None`
  - [ ] Test `add_root_to_db()` inserts a new root
  - [ ] Test `update_root_in_db()` updates fields including primary key rename
  - [ ] Test primary key rename cascades to `DpdHeadword.root_key`
  - [ ] Test `delete_root_in_db()` removes a root
  - [ ] Run tests — confirm RED (failing)

- [x] Task 1.2: Implement Root CRUD Methods in `database_manager.py`
  - [ ] `get_all_root_keys_sorted()` — query all root keys, sort by `pali_sort_key`
  - [ ] `get_root_by_key(root_key: str) -> DpdRoot | None`
  - [ ] `add_root_to_db(root: DpdRoot) -> tuple[bool, str]`
  - [ ] `update_root_in_db(original_key: str, root: DpdRoot) -> tuple[bool, str]` — handles PK rename + cascade
  - [ ] `delete_root_in_db(root_key: str) -> tuple[bool, str]`
  - [ ] `get_root_headword_count(root_key: str) -> int` — for delete warning
  - [ ] Run tests — confirm GREEN (passing)
  - [ ] Lint and format with `ruff`

- [x] Task 1.3: Conductor - User Manual Verification 'Database Layer' (Protocol in workflow.md)

## Phase 2: Roots Tab View — UI Implementation

- [x] Task 2.1: Create `gui2/roots_tab_view.py`
  - [ ] Class `RootsTabView(ft.Column)` with top/middle/bottom sections
  - [ ] Top section: root selector dropdown, Load/New/Clear buttons, message field
  - [ ] Middle section: scrollable column with grouped field rows
    - Root Info group: root, root_in_comps, root_has_verb, root_group, root_sign, root_meaning, root_example
    - Sanskrit group: sanskrit_root, sanskrit_root_meaning, sanskrit_root_class
    - Dhātupāṭha group: dhatupatha_num, dhatupatha_root, dhatupatha_pali, dhatupatha_english
    - Dhātumañjūsa group: dhatumanjusa_num, dhatumanjusa_root, dhatumanjusa_pali, dhatumanjusa_english
    - Saddanīti group: dhatumala_root, dhatumala_pali, dhatumala_english
    - Pāṇini group: panini_root, panini_sanskrit, panini_english
    - Other group: note (multiline), matrix_test
  - [ ] Bottom section: Save to DB button, Delete button (red hover)
  - [ ] Helper methods: `_make_field()`, `_make_row()`, `_make_group_header()`

- [x] Task 2.2: Implement Load/Save/New/Delete/Clear Logic
  - [ ] `_load_root()` — populate fields from DpdRoot
  - [ ] `_save_root()` — read fields, detect new vs update, call DB methods, √ auto-prefix for new
  - [ ] `_new_root()` — clear fields, set mode to new
  - [ ] `_delete_root()` — confirm with headword count warning, delete, refresh dropdown
  - [ ] `_clear_all()` — reset all fields
  - [ ] `_refresh_dropdown()` — reload root keys after mutations
  - [ ] Snackbar feedback via `show_global_snackbar()`

- [x] Task 2.3: Register Tab in `gui2/main.py`
  - [ ] Import `RootsTabView`
  - [ ] Create instance in `App.__init__()`
  - [ ] Add `ft.Tab(text="Roots", content=self.roots_view)` to tabs list

- [x] Task 2.4: Lint, Format, and Verify
  - [ ] Run `ruff check --fix` and `ruff format` on all changed files
  - [ ] Run full test suite to confirm no regressions

- [x] Task 2.5: Conductor - User Manual Verification 'Roots Tab View' (Protocol in workflow.md)

## Phase 3: Documentation

- [x] Task 3.1: Update Documentation
  - [ ] Update `docs/` with Roots tab feature documentation if applicable
  - [ ] Update folder README if gui2 structure changed

- [x] Task 3.2: Conductor - User Manual Verification 'Documentation' (Protocol in workflow.md)
