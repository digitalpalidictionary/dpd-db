# Spec: GUI2 Roots Tab

## Overview
Add a new "Roots" tab to the gui2 application that provides a full CRUD editor for the `dpd_roots` table. This mirrors the functionality of the Pass2Add tab for `dpd_headwords`, but is simpler — all field logic is built directly into `roots_tab_view.py` (no separate fields module needed).

## Functional Requirements

### FR-1: Root Selection
- Searchable dropdown (`ft.Dropdown` with `editable=True, enable_filter=True`) containing all 754+ root keys, sorted by `pali_sort_key`.
- On selection/submit, load all root fields into the editor.
- Dropdown refreshes after add/save/delete operations.

### FR-2: Field Editor
- All editable `DpdRoot` columns displayed in a scrollable middle section.
- Fields grouped horizontally where space allows (window width ~1375px).
- **Excluded columns:** `root_info`, `root_matrix`, `created_at`, `updated_at` (generated/auto-managed).
- Field groups:
  - **Root Info:** root, root_in_comps, root_has_verb, root_group, root_sign, root_meaning, root_example
  - **Sanskrit:** sanskrit_root, sanskrit_root_meaning, sanskrit_root_class
  - **Dhātupāṭha:** dhatupatha_num, dhatupatha_root, dhatupatha_pali, dhatupatha_english
  - **Dhātumañjūsa:** dhatumanjusa_num, dhatumanjusa_root, dhatumanjusa_pali, dhatumanjusa_english
  - **Saddanīti (Dhātumālā):** dhatumala_root, dhatumala_pali, dhatumala_english
  - **Pāṇini:** panini_root, panini_sanskrit, panini_english
  - **Other:** note (multiline), matrix_test

### FR-3: Save (Commit to DB)
- Directly commit changes to the database (no test gate).
- For existing roots: update in-place, including primary key rename if `root` field changed (cascade update `DpdHeadword.root_key` references).
- For new roots: insert new row.
- Auto-prefix `√` when creating new roots.
- Show success/error feedback via snackbar.

### FR-4: New Root
- Clear all fields for fresh entry.
- Auto-prefix `√` to the root key field.

### FR-5: Delete Root
- Delete button with red hover styling (matching Pass2Add pattern).
- Show warning about number of headwords referencing this root.
- Require explicit confirmation before deletion.

### FR-6: Clear All
- Reset all fields and deselect the current root.

## Non-Functional Requirements
- Match existing gui2 styling (colors, borders, fonts, spacing).
- Follow existing code patterns (ft.Column subclass, top/middle/bottom sections).
- Use `show_global_snackbar()` for user feedback.

## Acceptance Criteria
- [ ] Roots tab appears in the gui2 tab bar
- [ ] All roots loadable from searchable dropdown
- [ ] All 25 editable fields displayed and editable
- [ ] Save persists changes to database
- [ ] Primary key rename cascades to DpdHeadword.root_key
- [ ] New root creation works with √ auto-prefix
- [ ] Delete works with red warning and headword count
- [ ] Dropdown refreshes after save/delete/new operations

## Out of Scope
- Root data integrity tests (to be added later)
- `root_info` and `root_matrix` display/editing
- Undo/redo functionality
