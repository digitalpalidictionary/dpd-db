## Phase 1: Fix "Add spelling" bottleneck

- [x] **1.1** Add `_skip_spell_check` flag to `DpdMeaningField.__init__`
  → verify: flag exists, initialized to False

- [x] **1.2** Rewrite `_handle_add_to_dict_submit` to:
  - Add word to dictionary
  - Clear the input field
  - Remove the added word from existing error_text (string manipulation, no spell re-check)
  - Set skip flag before focusing meaning field
  → verify: read code, confirm no `check_sentence` call in the add flow

- [x] **1.3** Add `_remove_word_from_spell_errors(word)` method that parses the "word: suggestions" error format and filters out the added word
  → verify: read code, confirm it handles both single-error and multi-error cases

- [x] **1.4** Update `_handle_on_focus` to check and reset `_skip_spell_check` flag, skipping spell check when set
  → verify: read code, confirm the flag is checked before `_handle_spell_check`

- [x] **1.5** Reduce redundant `page.update()` calls — `update_message` already calls `page.update()`, so removed the extra one
  → verify: read code, confirm only one `page.update()` path in the add flow

- [ ] **1.6** Phase verification: user tests "Add spelling" flow
  → verify: user confirms speed improvement and remaining errors still display correctly
