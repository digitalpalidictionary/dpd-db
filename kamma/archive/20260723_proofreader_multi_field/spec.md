# Spec — Proofreader: extend to meaning_lit and meaning_2

Issue: #196

## Goal
The AI proofreader (`tools/proofreader.py`) currently proofreads only `meaning_1`.
Extend it to also proofread:
1. `meaning_lit` — the literal gloss of `meaning_1`.
2. `meaning_2` — but **only** for headwords where `meaning_1` is empty (meaning_2
   is then the primary meaning).

Each pass keeps the existing incremental behaviour: only re-check entries whose
source text changed since the last run, so nothing is re-proofread needlessly.

## Decisions (confirmed with user)
- **One file per field.** `tools/proofreader.tsv` (meaning_1) is untouched. Add
  `tools/proofreader_meaning_lit.tsv` and `tools/proofreader_meaning_2.tsv`, each
  with its own `*_checked.json` incremental cache and its own `FileLock`.
- **gui2: one PRead button cycles all.** The existing PRead button drains the
  three queues in priority order (meaning_1 → meaning_lit → meaning_2). Each row
  loads into its own add-field via the generic `update_add_fields`.
- **meaning_2 scope:** only `meaning_1 == "" AND meaning_2 != ""`.

## meaning_lit awareness
`meaning_lit` is a deliberately literal rendering of `meaning_1` and is often
non-idiomatic English *by design*. The prompt for the meaning_lit pass must:
- include the entry's `meaning_1` as read-only context, and
- explicitly instruct the model NOT to make the literal gloss more idiomatic —
  only fix genuine spelling/grammar typos, same bar as meaning_1.

## Non-goals
- No new gui buttons; the single PRead button is reused.
- No change to the meaning_1 prompt, file, or cache semantics.
- No DB writes from the CLI — it only produces the correction queues; the human
  applies them through gui2 (unchanged flow).

## Shared-file safety (unchanged pattern)
Both the CLI and gui2 read/write these TSVs. Each file keeps the existing
`FileLock` + reload-fresh-under-lock-then-mutate-then-save discipline, per field.

## Acceptance
- `just proofread` runs all three passes; re-runs skip unchanged entries.
- gui2 PRead loads a meaning_1, meaning_lit, or meaning_2 correction into the
  correct add-field.
- meaning_2 pass never surfaces an entry that has a non-empty meaning_1.
- meaning_lit prompt contains the meaning_1 context and the "do not make idiomatic"
  instruction.
- `ruff`, `pyright`, and the proofreader test suite pass.
