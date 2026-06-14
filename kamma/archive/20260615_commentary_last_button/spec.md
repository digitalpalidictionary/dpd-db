# Spec: Commentary field "Last" button

## Context
In gui2, the example fields (`DpdExampleField`, `gui2/dpd_fields_examples.py`) automatically
stash their value on blur and let the user restore it with a **Last** button. The stash is
persisted to `gui2/data/example_stash.json` via `ExampleStashManager`.

The commentary field (`DpdCommentaryField`, `gui2/dpd_fields_commentary.py`) has no such feature.

## Requirement
1. The commentary field should automatically save its current value every time the field
   loses focus (its on-blur state), persisted like the example stash.
2. Add a **Last** button to the right of the existing **Clear** button in the commentary
   field's search row. Clicking it restores the last saved commentary value.

## Notes / Decisions
- Reuse `ExampleStashManager` for persistence (same `example_stash.json` file), adding a
  dedicated `last_commentary` property/setter that does **not** strip `<b>` tags (commentary
  legitimately contains bold tags, unlike the example stash which strips them).
- Save only when the commentary value is non-empty, mirroring the example field behaviour
  (clearing then blurring must not wipe the restorable value).
- In the example field the save fires from the bold-field blur; the commentary field has no
  always-visible bold field, so saving is wired directly to the commentary text field's
  `on_blur` — this is what reliably fires "every time the field loses focus".
- The `_handle_last_control_blur` on-blur (auto-hide tools + hyphen handling) moves from the
  **Clear** button to the new rightmost **Last** button to keep "last control" semantics.

## Out of scope
- Any change to the example fields.
- Any change to pass1/pass2 controllers beyond the commentary field component.
