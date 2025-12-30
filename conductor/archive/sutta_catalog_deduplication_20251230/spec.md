# Specification: Sutta Catalog Deduplication

## Overview
Improve the DV catalogue sutta import process in `db/suttas/dv_catalogue_suttas.py` to:
1. Sort sutta entries naturally (e.g., AN1.2 before AN1.10)
2. Remove consecutive duplicate entries that have identical summary, key_excerpt1, and key_excerpt2 fields

## Problem Statement
The current `read_dv_catalogue()` function:
- Does not sort sutta codes naturally, resulting in alphabetical ordering (AN1.10 before AN1.2)
- Does not filter out consecutive duplicate entries that appear in the TSV file
- This can lead to duplicate data or incorrect ordering in the database

## Functional Requirements

### FR1: Natural Sorting
- Sutta codes must be sorted using natural sort order (natsort)
- Sorting should handle mixed alphanumeric codes with numbers, letters, and hyphens
- Example: AN1.1, AN1.2, AN1.10, AN1.11 (not AN1.1, AN1.10, AN1.11, AN1.2)

### FR2: Consecutive Duplicate Removal
- Remove entries where ALL of the following are identical to the previous entry:
  - summary
  - key_excerpt1
  - key_excerpt2
- Only consecutive duplicates should be removed (non-consecutive entries with same content are kept)
- The first occurrence of a duplicate sequence is retained
- Empty/NaN values in any of the three fields should NOT trigger duplicate removal

### FR3: Processing Order
- TSV file must be read first
- Data must be sorted by sutta code using natsort
- Consecutive duplicates must be removed after sorting
- Existing `drop_duplicates(subset=["suttacode"])` logic remains unchanged

## Non-Functional Requirements

### NFR1: Performance
- Processing should complete within 10 seconds for typical file sizes (~10,000 entries)

### NFR2: Data Integrity
- No data loss should occur for unique entries
- All required fields (suttacode) must remain after processing

### NFR3: Error Handling
- Gracefully handle missing or invalid columns
- Log number of duplicates removed for transparency

## Acceptance Criteria

1. Given a TSV with sutta codes [AN1.10, AN1.2, AN1.1], the output order is [AN1.1, AN1.2, AN1.10]
2. Given consecutive entries with identical summary/key_excerpt1/key_excerpt2, only the first is retained
3. Non-consecutive entries with identical content are both retained
4. Empty/NaN values in comparison fields prevent duplicate detection for those entries
5. The total number of entries removed is logged
6. All existing functionality (download, database update) continues to work

## Out of Scope
- Modifying the existing `drop_duplicates(subset=["suttacode"])` logic
- Handling duplicates that are not consecutive
- Removing duplicates based on sutta code alone (outside current scope)
- UI changes or user-facing features
