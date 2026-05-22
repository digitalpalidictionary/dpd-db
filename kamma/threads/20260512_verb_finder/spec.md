# Spec: verb_finder (exploratory)

## GitHub issue
(none provided)

## Overview
Add `scripts/fix/verb_finder.py` — an exploratory, read-only diagnostic script that audits consistency between present-tense verbs (`pos='pr'`) and the derived forms (`pp`, `ptp`, `prp`, `abs`, `ger`, `inf`) that reference them in the `grammar` and `derived_from` columns. Goal: produce TSV reports + terminal summary so we can see how many entries deviate from the rule "if a pr verb exists in the dictionary, derived forms must point at the verb; otherwise they must point at the family_root."

## What it should do
1. Iterate `dpd_headwords`, build an index of all `pos='pr'` entries keyed by `(family_root, root_key)` → list of pr lemmas. Also produce the inverse: lemma → (family_root, root_key).
2. Identify and report every `(family_root, root_key)` pair (across the whole db) that has zero pr entries.
3. Iterate all derived forms (`pp`, `prp`, `ptp`, `abs`, `ger`, `inf`), parse the `grammar` column, and bucket each entry:
   - **ok_verb_present**: grammar says "<pos> of <verb>" (or "<pos> of na <verb>") and <verb> exists as pr → no change.
   - **would_change_to_root**: grammar says "<pos> of <verb>" (or "of na <verb>") but <verb> is NOT in the db as pr → propose change to "<pos> of <root_key>" (preserving "na " if present).
   - **would_change_to_verb**: grammar says "<pos> of √root" and a pr verb exists for that (family_root, root_key) → propose change to "<pos> of <verb>". If exactly one matches the root base, propose it; if multiple, mark **ambiguous** with all candidates listed.
   - **special_verb**: the `verb` column is non-empty (caus, pass, intens, desid, deno, impers, combos) OR grammar contains "caus of"/"pass of"/"intens of"/"desid of"/"deno of"/"impers of". Detect only — no proposed fix.
4. Also report mismatches between `derived_from` and what `grammar` references (since both should agree per user's note).
5. No writes to the db. Write TSV reports under `temp/verb_finder/` and print a colored summary via `tools.printer`.

## Assumptions & uncertainties
- "Present tense verb" = strictly `pos='pr'`. Other finite-tense pos (aor, fut, imp, opt, perf, imperf, cond, ve) are not pr verbs for this script.
- `pos='cs'` is NOT causative (it's the "case suffix" entries with `verb` column markers); causatives are detected via the `verb` column and grammar text.
- "Match on the root base" means: when grammar says "X of √root", a pr verb's `root_key` must equal that root. The `family_root` (with prefixes) on the pp/ptp may or may not match the pr's `family_root`; we'll record both views in the ambiguous bucket so we can see how often pure root_key match still narrows to a single candidate.
- `derived_from` is treated as authoritative for the verb the entry refers to; grammar text parsing uses regex on the canonical patterns observed in the data (`"<pos> of <verb>"`, `"<pos> of na <verb>"`, `"<pos> of √<root>"`, optionally with trailing ", in comps" / ", irreg" / "??" etc.).
- Grammar strings can have suffixes like ", in comps" or " ??" — strip these when parsing then preserve in the proposed replacement.
- For "pp of na <verb>" (negative compounds): the inner verb is the pr verb to check. Treat it identically to the positive form — if inner verb exists as pr, ok; if not, change to "pp of na √root".

## Constraints
- Read-only. No db writes, no file modifications outside `temp/verb_finder/`.
- Modern type hints, `Path` from pathlib, `from icecream import ic` if needed, `tools.printer` for output, `tools.db_helpers.get_db_session`.
- No `sys.path` hacks.

## How we'll know it's done
- `uv run scripts/fix/verb_finder.py` runs to completion with no errors.
- `temp/verb_finder/` contains: `pr_verb_index.tsv`, `roots_without_pr.tsv`, `would_change_to_root.tsv`, `would_change_to_verb.tsv`, `ambiguous.tsv`, `special_verbs.tsv`, `unparsed.tsv`, `grammar_derived_from_mismatch.tsv`.
- Terminal summary shows counts per bucket.
- Spot-check confirms: ruṭṭha → `would_change_to_root` (russati not in dict), rusita → `ok_verb_present` (roseti exists), akkanta → `ok_verb_present`.

## What's not included
- No writes to the db. No corrections applied. No GUI changes. No new tests beyond a quick verification.
- Causative/passive/intensive/desiderative/denominative handling is detection-only; rewrite rules for them are out of scope for this pass.
