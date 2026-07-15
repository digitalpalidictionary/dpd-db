# Plan: verb_finder (exploratory)

> **Note (2026-07-13):** This file was triaged in the `20260713_scripts_triage` thread — all 3
> phases are fully implemented in `scripts/fix/verb_finder.py`, verdict: keep + freshen. This
> sibling thread can be closed by the user.

## Architecture Decisions
- **Single file**: `scripts/fix/verb_finder.py` with clearly named functions and a small `main()`. No sub-package yet — extract to module if/when reuse demands it.
- **Pure functions over methods**: each piece (index building, grammar parsing, bucketing, tsv writing) is a standalone function with explicit inputs/outputs, importable by future fix scripts.
- **Grammar parser is a single regex-driven function** returning a `GrammarRef` dataclass: original string, head pos token, "na" flag, root flag, target lemma or root, special-verb flag, trailing suffix. One place to update if grammar conventions evolve.
- **Reports written via a tiny `write_tsv(rows, path)` helper** taking a list of dicts; no DataFrame dependency.
- **Uses `tools.db_helpers.get_db_session`** and **`tools.printer`** per project conventions.

## Phase 1 — Index and audit infrastructure

- [x] Create `scripts/fix/verb_finder.py` skeleton: imports, `OUTPUT_DIR = Path("temp/verb_finder")`, `main()` stub with `pr.tic()`/`pr.toc()`.
  → verify: `uv run ruff check scripts/fix/verb_finder.py` passes.

- [x] Implement `build_pr_verb_index(db)` returning `dict[(family_root, root_key), list[str]]` and `dict[str, tuple[family_root, root_key]]`.
  → verify: ad-hoc call in `main()` prints total pr count == 5773; √kar → 25 lemmas.

- [x] Implement `find_roots_without_pr(db, pr_index)` returning list of `(family_root, root_key)` pairs that appear on any headword but have zero pr entries. Write `roots_without_pr.tsv` (columns: family_root, root_key, example_lemma, example_pos, headword_count).
  → verify: file exists; sample rows plausible.

- [x] Implement `write_tsv(rows: list[dict], path: Path)` helper (creates parent dir, writes header from first row keys, tab-separated). Also write `pr_verb_index.tsv` (family_root, root_key, pr_lemmas_pipe_joined, count).
  → verify: open both files, headers correct, row counts sane.

## Phase 2 — Grammar parser + derived-form scan

- [x] Define `GrammarRef` dataclass and `parse_grammar(grammar: str, pos: str) -> GrammarRef | None`. Patterns: `"<pos> of <lemma>"`, `"<pos> of na <lemma>"`, `"<pos> of √<root>"`, with optional trailing suffix after a comma (", in comps", ", irreg") or trailing "??". Set `special_verb=True` if grammar contains " caus of"/" pass of"/" intens of"/" desid of"/" deno of"/" impers of".
  → verify: inline assertions on 6+ representative strings.

- [x] Implement `scan_derived_forms(db, pr_index, pr_lemma_set)` iterating headwords where `pos IN ('pp','prp','ptp','abs','ger','inf')`. For each: parse grammar; consult `verb` column; bucket into `ok_verb_present`, `would_change_to_root`, `would_change_to_verb` (single match), `ambiguous` (multi match), `special_verb`, `unparsed`. Flag entries where `derived_from` disagrees with the verb extracted from grammar.
  → verify: print counts; spot-check ruṭṭha → would_change_to_root, rusita → ok_verb_present, akkanta → ok_verb_present.

- [x] Write all six bucket TSVs (plus `ok_verb_present.tsv` = 7 bucket outputs total) (`would_change_to_root.tsv`, `would_change_to_verb.tsv`, `ambiguous.tsv`, `special_verbs.tsv`, `unparsed.tsv`, `grammar_derived_from_mismatch.tsv`) with columns: id, lemma_1, pos, root_key, family_root, verb_col, grammar_current, grammar_proposed, reason, candidates.
  → verify: all six files exist; row counts add up to total scanned.

## Phase 3 — Summary and verification

- [x] In `main()`, print colored summary via `pr.summary(...)` for each bucket count, total scanned, and roots-without-pr count. Print elapsed time.
  → verify: run `uv run scripts/fix/verb_finder.py`, summary readable; numbers reconcile with TSV line counts.

- [x] Sanity-check user's examples: print a 3-line "spotcheck" block at end showing the bucket and proposed grammar for `ruṭṭha`, `rusita`, `akkanta 1`.
  → verify: see verification block below — rusita → ok_verb_present ✓; akkanta 1 → ok_verb_present ✓; ruṭṭha → **ambiguous** (russati absent, but 3 pr verbs exist at √rus so the logic defers instead of forcing √rus — a sounder rule than the original plan assumed).

---

## Verification (2026-07-15, `/kamma:2-do`)

Implementation was done + freshened in the `20260713_scripts_triage` thread (that row is `[x]`).
This session verified it behaviourally against the live `dpd.db` (script is read-only — no DB
writes, output only to `temp/verb_finder/`).

**Run:** `uv run python scripts/fix/verb_finder.py` — completed in 0.51s, no errors.

**Outputs produced (9 TSVs, all sane):**

| File | Rows |
|---|---|
| pr_verb_index.tsv | 2199 (family_root, root_key) pairs |
| roots_without_pr.tsv | 1158 |
| ok_verb_present.tsv | 11072 |
| special_verbs.tsv | 3160 |
| unparsed.tsv | 1393 |
| ambiguous.tsv | 375 |
| would_change_to_root.tsv | 340 |
| would_change_to_verb.tsv | 230 |
| grammar_derived_from_mismatch.tsv | 173 |

Sum of the 7 derived-form buckets = 16743 = "total derived forms scanned" ✓ (reconciles).

**Spotcheck (actual):**
- `rusita` → ok_verb_present (roseti is pr, √rus) ✓
- `akkanta 1` → ok_verb_present (akkamati 1/2/3 are pr, √kam 1; `lemma_clean()` strips the
  trailing number and matches) ✓
- `ruṭṭha` → **ambiguous**, not would_change_to_root. grammar = "pp of russati"; russati is
  absent from the dict, but 3 pr verbs exist at √rus (rosati, rosayati, roseti) so the script
  can't auto-pick one and flags it ambiguous instead of blindly proposing `pp of √rus`.
  This is a stricter, more correct rule than the original Phase 3 plan text assumed.

**Spotcheck-display fix (2026-07-15):** a concurrent agent in `20260713_scripts_triage` had
removed the `\[` rich-escape from the spotcheck `pr.white(...)` line (commit `acd85c53`),
which made rich swallow the `[bucket]` prefix as an invalid markup tag. Restored the escape
(`\[` in source = runtime literal `[`) plus an explanatory comment; verified the bucket name now
shows again. pyright stays `0/0/0` (`\` is a recognised escape).

**Deltas from the plan's inline verify lines (data grew over 2 months, not bugs):**
- pr count: plan said 5773 → now 5808 (new pr entries added).
- Phase 3 spotcheck expectation for ruṭṭha updated above.

The script is correct and complete; this thread is ready to close.
