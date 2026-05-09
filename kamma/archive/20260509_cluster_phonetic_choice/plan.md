# Plan

## Architecture Decisions
- Mirror the existing `(s)` block exactly — same shape, just swap the target field and the "preserve" check. Keeps the two branches visually parallel for future readers.
- Use `var_text` as the "preserve" field for `(p)` (symmetric to `var_phonetic` being preserved by `(s)`).

## Phase 1 — implementation
- [x] Update prompt string to include `(p)honetic all pairwise`.
  → verify: prompt line in `prompt_clusters` reads new label.
- [x] Add `elif choice == "p":` block mirroring `(s)`.
  → verify: `uv run ruff check db_tests/single/add_synonym_variant_multi.py` passes.
- [x] Phase verify: ruff clean.
