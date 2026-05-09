# Add (p)honetic-all-pairwise choice to cluster prompt

## Overview
In `db_tests/single/add_synonym_variant_multi.py`, the cluster prompt only offers `(s)ynonym all pairwise`. Some clusters are not synonyms but phonetic variants of each other (e.g. `ḍiṇḍima ↔ dindima ↔ dendima` "drum"). Add a `(p)` choice that writes `var_phonetic` pairwise across all members.

## What it should do
- Add a `(p)` option to the `prompt_clusters` choice prompt.
- On `p`, iterate every unique pair in the cluster and call `assign_relationship(..., "var_phonetic")` both directions.
- Skip pairs already preserved as `var_text` (mirror of how `(s)` preserves `var_phonetic`).
- No-op pairs already bidirectional in `var_phonetic`.
- Existing `synonym` pairs get overwritten to `var_phonetic` (assign_relationship enforces exclusivity — same convention as `prompt_pairs` `(p)honetic`).
- Commit at the end of the cluster, like `(s)`.

## Constraints
- No new helpers, no new imports. Reuse `assign_relationship`, `split_field`.
- Do not touch detection logic or `_all_pairs_related` — phonetic-resolved clusters are already filtered out.

## How we'll know it's done
- `uv run ruff check db_tests/single/add_synonym_variant_multi.py` passes.
- The new prompt string lists `(p)honetic all pairwise`.
- User runs the script on a phonetic-variant cluster and confirms the var_phonetic field is populated bidirectionally for all members.

## What's not included
- Single-pair `prompt_pairs` is unchanged — already has `(p)`.
- No tests added; this is interactive CLI.
