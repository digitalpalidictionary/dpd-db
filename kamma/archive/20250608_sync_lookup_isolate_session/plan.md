# Plan: Isolate `sync_lookup_column` session

**Thread:** 20250608_sync_lookup_isolate_session  
**GitHub:** #157

## Analysis

After discussion, the `expunge_all()` call was added as a precaution for a memory problem that never actually existed. Removing it eliminates the `DetachedInstanceError` entirely — no session isolation needed.

## Tasks

- [x] Remove `db_session.expunge_all()` from `tools/lookup_sync.py`
- [x] Revert call-order workaround in `db/families/family_root.py` (`update_lookup_table` before `generate_root_info_html`)
- [x] Verify `tests/tools/test_lookup_sync.py` (9 tests pass)
- [x] Pre-commit checks pass (ruff, pyright)
