# Implementation Plan: SN Peyyala Numbering Fix

## Phase 1: Fix Data in sn_peyyalas

- [x] Task: Fix SN30 entries (lines 37-39)
- [x] Task: Fix SN33 entry (line 54)
- [x] Task: Add SN24 entries (after line 34, in the sn3 section)
    - [ ] Add `(24, "1. Vātasuttaṃ", 19, 44)` for vagga 2
    - [ ] Add `(24, "1. Navātasuttaṃ", 45, 70)` for vagga 3
    - [ ] Add `(24, "1. Navātasuttaṃ", 71, 96)` for vagga 4

- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Restructure Branch Logic

- [x] Task: Merge the two subhead branches (lines 739-763) into one
    - [ ] Remove the separate hyphen/no-hyphen branches
    - [ ] Check peyyalas first for ALL subheads starting with a digit
    - [ ] Fall through to normal single-sutta counting only if no peyyala matched AND no hyphen in text
    - [ ] See spec.md for exact code

- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Verify

- [x] Task: Run linting and formatting
- [x] Task: Run full test suite
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
