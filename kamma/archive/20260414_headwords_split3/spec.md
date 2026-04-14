---
thread: 20260414_headwords_split3
type: chore
---

## Overview
Split dpd_headwords TSV backup from 2 parts into 3, and fix a header bug between backup and rebuild scripts.

## Context
- ~88,746 headword entries. Fields like `example_1` contain embedded newlines, so `wc -l` is misleading.
- Current `chunk_size=50,000` rows produces 2 parts: part_001 at 61 MB (over GitHub's 50 MB warning), part_002 at 48 MB.
- Backup: `db/backup_tsv/backup_dpd_headwords_and_roots.py`
- Rebuild: `scripts/build/db_rebuild_from_tsv.py`

## What it should do
1. Set `chunk_size=30,000` rows → 3 parts of ~36 MB each, all under GitHub's 50 MB threshold.
2. Write TSV headers to ALL part files, not just part_001.
3. Update rebuild to read headers from ALL parts (currently skips first line of non-first parts, which drops the first data row since those parts have no header).

## Assumptions
- ~30,000 rows × ~1.23 KB/row ≈ 37 MB per part — well under 50 MB.
- Rebuild already uses `glob("dpd_headwords_part_*.tsv")` so it handles any number of parts automatically.

## Constraints
- Do not re-run the backup script — user handles execution.

## How we'll know it's done
- `split_tsv_file()` uses `chunk_size=30,000` and writes header to every part.
- `read_tsv_files()` reads header from every part instead of skipping.

## What's not included
- Changing dpd_roots split behavior (already small, no issue).
- Actually running the backup.
