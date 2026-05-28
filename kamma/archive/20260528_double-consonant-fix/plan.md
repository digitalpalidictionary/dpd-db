# Plan

## Architecture Decisions
- Single script `scripts/fix/double_consonant_replacer.py`. Stage 1 = run and
  type `n`; Stage 2 = run and type `y`. Matches `character_replacer.py`.
- Regex compiled once at module level.

## Phase 1: Dry-run matcher
- [ ] Create `scripts/fix/double_consonant_replacer.py`
  → verify: `uv run ruff check scripts/fix/double_consonant_replacer.py` passes
