# Plan — Sutta filter button on pass2_add tab

## Architecture Decisions
- Reuse the existing filter RadioGroup + `dpd_fields.filter_fields(...)`
  pipeline. No new component or controller.
- Keep prefill logic inline in the filter-change handler — too small to
  warrant extraction.
- Keep `SUTTA_FIELDS` next to existing `COMPOUND_FIELDS` etc. for parity.
- Sutta filter is sticky across `clear_all_fields`; all other filters still
  reset to "all" (per user's explicit instruction). Implemented inline in
  `clear_all_fields` rather than as a generic mechanism.

## Phase 1 — Add SUTTA_FIELDS list
- [x] Edit `gui2/dpd_fields_lists.py`: add `SUTTA_FIELDS` after
  `COMPOUND_FIELDS`. (User trimmed list further during implementation —
  final list is the authoritative one.)

## Phase 2 — Wire the Sutta radio + filter
- [x] Imported `SUTTA_FIELDS` in `gui2/pass2_add_view.py`.
- [x] Added `ft.Radio(value="sutta", label="Sutta")` between Compound and Word.
- [x] Added `sutta` branch in `_handle_filter_change` with prefill of
  `source_1` and `commentary` to `-` (only when empty).

## Phase 3 — Sutta-only stickiness across clear
- [x] In `clear_all_fields`, only reset `_filter_radios.value = "all"` if the
  current filter is not "sutta". When sutta, re-prefill source_1/commentary
  and re-apply `filter_fields(SUTTA_FIELDS)` after the rebuild.

## Phase 4 — User smoke
- [x] User confirmed the Sutta filter behaves correctly across consecutive
  word loads and that other filters still reset to All as before.
