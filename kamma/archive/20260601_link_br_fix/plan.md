# Plan

## Architecture Decision
Fix at the source of the mutation, not the templates: remove `"link"` from the
newline→`<br>` conversion lists. The `link_list` property already does the
correct splitting; the field simply must not be pre-mangled. Simplest possible
fix — no template changes, no model changes.

## Phase 1: Fix conversion lists
- [x] Remove `"link"` from `string_columns` in `exporter/webapp/data_classes.py`
  → verify: file no longer lists `"link"`; ruff clean
- [x] Remove `"link"` from `attrs` in `exporter/goldendict/data_classes.py`
  → verify: file no longer lists `"link"`; ruff clean
- [x] Phase verify: `uv run ruff check` both files pass; webapp confirmed working
  by user; link-relevant headword tests pass
