# Plan: Remove ORM mutation in grammar_to_lookup.py

**Thread:** 20250608_grammar_close_db_rollback
**GitHub:** #157

## Phase 1: Refactor

- [x] Refactor `modify_pos` to return `dict[int, str]` instead of mutating ORM objects
- [x] Update `generate_grammar_data` to accept and use the pos_override dict
- [x] Remove `GlobalVars.close_db()`, `GlobalVars.commit_db()`, and the `g.close_db()` call in `main()`
- [x] Update tests to match new signatures
- [x] Run pre-commit gate
