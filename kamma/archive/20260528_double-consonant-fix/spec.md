# Spec: Double-consonant hyphen cleanup

## Overview
Find and fix the pattern `-x-x` (hyphen, consonant, hyphen, same consonant) in
the database, replacing it with `-xx`. Scope: `example_1`, `example_2`, and
`commentary` columns of `dpd_headwords`. Same consonant only; single Pāḷi
letters only (no aspirate-as-unit handling).

## What it should do
- Stage 1 (dry run): scan the three columns, list every match with id, lemma,
  column, old text, and new text. No DB writes.
- Stage 2 (apply): after user approves the dry-run output, run the same matcher
  with a y/n commit prompt, mirroring the convention in
  `scripts/fix/character_replacer.py`.

## Assumptions & uncertainties
- Consonant set: k g c j ñ ṭ ḍ ṇ ṅ t d n p b m y r l v s h ḷ (lowercase).
  Regex is case-insensitive.
- Pattern `-([consonant])-\1`, replaced with `-\1\1`.
- Global replacement per field.

## Constraints
- Match `scripts/fix/character_replacer.py` style.
- Modern type hints, `Path` from pathlib, no sys.path hacks.

## How we'll know it's done
- Dry-run prints all matches with id, lemma, column, before/after.
- After approval, same script applies changes when user types `y`.
- `uv run ruff check` on the new file passes.

## What's not included
- Other columns, aspirates as units, mixed-consonant pairs, CLI flags.
