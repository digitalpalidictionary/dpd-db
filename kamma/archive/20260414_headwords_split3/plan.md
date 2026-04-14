---
thread: 20260414_headwords_split3
---

## Phase 1: Fix backup script

- [x] Change `chunk_size` default to 30,000 in `split_tsv_file()` — `db/backup_tsv/backup_dpd_headwords_and_roots.py:29`
  → verify: function signature confirms `chunk_size: int = 30000` ✓

- [x] Write header to ALL parts — remove the `if i == 0` guard
  → verify: header written unconditionally at line 53 ✓

## Phase 2: Fix rebuild script

- [x] Update `read_tsv_files()` in `scripts/build/db_rebuild_from_tsv.py` — read columns from every file's first line
  → verify: no skip branch; `columns = next(csvreader)` for every file at line 101 ✓

## Phase 3: Review
- [x] Read both scripts end-to-end and confirmed consistency
  → verify: backup writes headers to all parts, rebuild reads headers from all parts, chunk_size=30,000 ✓
