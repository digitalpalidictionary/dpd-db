## Thread
- **ID:** 20260823_ati_prefix_to_compound
- **Objective:** Convert `ati-` prefix headwords that were incorrectly recorded as root derivations into compounds, matching the ~200-word existing db convention.

## Files Changed
- `scripts/fix/ati_prefix_to_compound.py` — the migration tool (generate/apply, TSV round-trip)
- `.gitignore` — added `scripts/fix/ati_prefix_to_compound.tsv` (disposable working artifact, same pattern as sibling `scripts/find`/`scripts/extractor` tsvs)
- `kamma/threads/20260823_ati_prefix_to_compound/spec.md`, `plan.md` — thread docs
- `dpd.db` — 87 headwords converted by the script; 3 more (`accokaṭṭha`, `atibhārita`, `accāsanne`) fixed by hand by the user after the tool declined them (no resolvable base)
- `db/backup_tsv/dpd_headwords_part_00{1,2,3}.tsv` — already committed separately by `just backup`'s own auto-commit (`00ff91ea`, "pali update")

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `ati_prefix_to_compound.py` `read_existing`/`build_rows` | A row blocked on a previous run stayed `do=n` forever even after the editor supplied a valid `base` on regenerate | Silent stuck-declined row | Fixed: track whether a row's only line was the `(none)` placeholder; auto-restore `do=y` only in that case |
| 2 | info, resolved | `nātikhīṇaṃ` `grammar` clause names `atitikhiṇa`, not the row's own `khīṇa`-based `derived_from` | Looked like leftover inconsistency | User confirmed intentional: the case-form clause records the word's last actual prior form, not necessarily the compound's base — no fix needed |
| 3 | doc-only | `spec.md` field table says `pos`/`pattern` unchanged | Mid-thread instruction changed pp/ptp compounds to `pos=adj` | Not a code bug; recorded as an approved deviation in `plan.md` rather than rewriting `spec.md` |

Two CodeRabbit findings on files outside this thread's scope (`scripts/fix/verb_finder.py`, `scripts/fix/verb_grammar_fixer.py`) were left untouched — different, unrelated work in the same working tree.

## Fixes Applied
- `read_existing`/`build_rows` auto-unblock logic (finding 1), verified independently by a second review pass reading the fixed code.
- One gemination bug (`ati + ṭṭhāna`, `ati + kkhaya` → `ati + ṭhāna`, `ati + khaya`) found and fixed before the real apply, via a self-test that reproduces already-correct db rows.

## Test Evidence
- `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright` on `ati_prefix_to_compound.py` — clean throughout.
- Self-test rebuilding known-correct existing rows (`atitaruṇa`, `atibahu`, `nātiucca`, `nātibahu`, `aticiraṃ`, `atijotitā`, `atigambhīraṃ`) and diffing against the live db — exact match, run repeatedly through the whole thread.
- `apply --dry-run` cross-checked mechanically against the TSV: 87 words / 902 field edits in the TSV matched 87/902 printed by the dry-run exactly, before the real apply.
- `uv run pytest tests/` — 1771 passed, 0 failed, both before and after the real apply.
- Post-apply: `generate` re-run finds 0 remaining `ati`-family candidates — all 90 words (87 by script + 3 by hand) are converted.
- Independent subagent review (fresh context, own db queries) — verified the CodeRabbit fix, spot-checked ~25 of 87 applied rows against the Proposal logic by hand.

## Not Verified
- The independent reviewer spot-checked roughly 25 of the 87 script-applied rows in depth; the rest were checked only via the mechanical dry-run/TSV cross-check and the self-test set, not row-by-row by a human or a second agent.
- The 3 hand-fixed rows (`accokaṭṭha`, `atibhārita`, `accāsanne`) were not reviewed by the tooling at all — they were edited outside the script's path, verified only by the post-fix `generate` finding them no longer selected.
- `db_tests/run_all_tests.py` (the project's dedicated data-integrity checker) is an interactive TTY tool (`input()`/"press any key") and could not be run headlessly in this session — it exited on EOF before completing its first sub-check, with no output relevant to the 90 words touched. `pytest tests/` (1771 passed) is the evidence actually gathered; the interactive db_tests pass is left for the user to run themselves if they want it.

## Verdict
PASSED
- Review date: 2026-08-25
- Reviewer: Claude (same session, implementation + independent subagent + CodeRabbit)
