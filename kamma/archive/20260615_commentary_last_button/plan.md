# Plan: Commentary field "Last" button

## Tasks

- [x] 1. Add `last_commentary` property/setter to `ExampleStashManager`
      (`gui2/example_stash_manager.py`) — stores/reads commentary text under a
      `last_commentary` key without stripping `<b>` tags.

- [x] 2. In `DpdCommentaryField` (`gui2/dpd_fields_commentary.py`):
      - import and construct an `ExampleStashManager`
      - wire the commentary text field's `on_blur` to save the current value
        (delegating to any externally passed `on_blur`)
      - add a **Last** button to the right of **Clear** in `_search_row` with a
        click handler that restores the saved value
      - move `_handle_last_control_blur` on-blur from **Clear** to **Last**

- [x] 3. Lint + run related tests — ruff clean, 28 gui2 tests pass, stash
      round-trip verified (bold tags preserved, persists across instances).

## Checkpoint
- [ ] Manual verification by user in the GUI.
