# Plan: move `variant` → `var_text`

**Thread:** 20260725_variant_to_var_text
**Spec:** `spec.md` in this folder
**Verified against disk + live `dpd.db`:** 2026-07-25

## User decisions (resolved — no open questions)

1. **Scope** — move the data AND remove the field from gui2. Do NOT drop the
   column from `db/models.py`; add a TODO reminder there instead. The user drops
   it at their next db-model change.
2. **Directionality** — literal move, no reciprocal backfill.

## Phase 1 — migration script

- [x] 1.1 Write `scripts/fix/variant_to_var_text.py`.
  - Module docstring stating what it does, that it is one-off, and that it must
    not be run with gui2 open.
  - `ProjectPaths().dpd_db_path` → `get_db_session`. No hardcoded `"dpd.db"`.
  - Query `db.query(DpdHeadword).filter(DpdHeadword.variant != "").all()`.
  - Per row, snapshot `hw.variant_list` first (the loop mutates `hw.variant`),
    then for each token call
    `assign_relationship(hw, token, "var_text")` from `tools.synonym_variant`.
  - Report with `tools.printer` (`pr.green_title`, `pr.summary`) — rows touched,
    tokens moved.
  - Single `db.commit()` at the end.
  - `--dry-run` flag that reports without committing, so the user can inspect
    first.
  - → verify: `uv run ruff check --fix`, `ruff format`, `pyright` clean on the file.

- [x] 1.2 Capture the pre-state for verification: row count with non-empty
  `variant`, total variant tokens, total var_text tokens, and a per-row
  `id → expected union set` map written to the scratchpad.
  - → verify: numbers match the spec table (2,450 rows / 2,865 tokens / 799
    var_text rows). If they differ, something wrote to the db — stop and re-check.

- [x] 1.3 Run `--dry-run` and eyeball a sample of the 74 both-populated rows.
  - → verify: each shows the correct union, Pāḷi-sorted, comma-space joined.

**CHECKPOINT — user must confirm gui2 is closed before 1.4.**

- [x] 1.4 Run the migration for real.
  - → verify: `select count(*) from dpd_headwords where variant != ''` = 0.

- [x] 1.5 Verify against the 1.2 snapshot: every row's post `var_text` set equals
  the expected union. No token lost, none invented.
  - → verify: script-level set comparison, zero mismatches.

- [x] 1.5b **Added mid-thread (user decision, 2026-07-25).** 26 rows had `var_text`
  values that were not Pāḷi-sorted — pre-existing hand-entered values that never
  went through `assign_relationship`. None were touched by the migration. User
  asked for them to be normalised, so `normalise_var_text()` was added to the
  same script as a second pass. Both passes are idempotent, so the script was
  simply re-run.
  - → verify: whole-table check — 3,176 rows with `var_text`, 0 render
    violations, 0 rows with `variant`. Done.

- [x] 1.6 `just backup`, then confirm `db/backup_tsv/dpd_headwords_part_*.tsv`
  changed and the `variant` column is empty throughout.
  - → verify: all 89,273 TSV rows have an empty `variant` column; id 1128
    (`ajajjita`) reads `var_text='ajaddhuka, jaddhuka'`. Done.
  - **NOTE:** `just backup` auto-commits the three TSVs as `"pali update"`
    (`git_commit()` in `backup_dpd_headwords_and_roots.py:148`). This is the
    repo's built-in data-update habit, not something this thread chose. It stages
    an explicit file list (the `dpd_headwords_part_*` / `dpd_roots_part_*` globs)
    so no concurrent thread's work was swept in, and it does not push. Commit
    `b85ec0a7`.

## Phase 2 — remove `variant` from gui2

- [x] 2.1 `gui2/dpd_fields.py`
  - Remove `FieldConfig("variant", ...)` (lines 257–261).
  - Delete `variant_field_change` (1310) and `variant_blur` (1459).
  - Delete `synonym_variant_check` (1427) entirely — its only job was keeping
    `synonym` and `variant` disjoint, which is meaningless once `variant` is gone.
  - `synonym_field_change` (1305) then does nothing but `clean_pali_field`, so
    delete it too and point `FieldConfig("synonym", on_change=...)` straight at
    `self.clean_pali_field`.
  - `_compute_and_write_synonyms` (1357–1361): drop the block that filters synonym
    candidates against the `variant` field value.
  - `transfer_add_value` (654–663): drop `"variant"` from the `current` dict and
    write back only `synonym` / `var_phonetic` / `var_text`.
    **This one is a live crash risk, not cosmetic:** `assign_relationship_dict`
    always returns a `"variant"` key, and the existing write-back loop does
    `self.get_field(name).value = value`. `get_field` returns `""` for an unknown
    name, so `"".value = ...` would raise `AttributeError` the moment a user
    accepted a suggestion. Must be fixed in the same commit as the field removal.
    (`assign_relationship_dict` reads `fields.get("variant")`, so omitting the key
    on the way in is safe.)
  - → verify: `rg -n "\bvariant\b" gui2/dpd_fields.py` returns only
    `var_phonetic` / phonetic-variant wording, no DB-field references.

- [x] 2.2 `gui2/dpd_fields_lists.py` — remove `"variant"` from `ALL`,
  `ROOT_FIELDS`, `COMPOUND_FIELDS`, `WORD_FIELDS`, `NO_SPLIT_LIST`, and from the
  numbered docstring at the top (renumbering entries 38+).
  - `SUTTA_FIELDS` and `PASS1_FIELDS` do not list it — leave them.
  - → verify: `rg -n "variant" gui2/dpd_fields_lists.py` shows only
    `var_phonetic` / `var_text`.

- [x] 2.3 Sweep the rest of gui2 for any other reference to the DB field.
  - → verify: `rg -rn "\bvariant\b" gui2/ --glob '!*.pyc'` — every remaining hit is
    `var_phonetic`, `var_text`, sandhi variants, or `gui2/variants.py`
    (variant *readings*, unrelated `Lookup` pipeline).

- [x] 2.4 Lint gate on both touched files: `uv run ruff check --fix`,
  `uv run ruff format`, `uv run pyright`. `gui2/` is pyright-excluded but NOT
  ruff-excluded, so pre-existing ruff violations in these files must be fixed too
  (per CLAUDE.md: touch a file = own its lint).
  - → verify: all clean.

## Phase 3 — model reminder + docs

- [x] 3.1 `db/models.py:1184` — add a `TODO` comment on the `variant` column:
  data migrated to `var_text` on 2026-07-25, column now always empty, drop it at
  the next db-model change.
  - → verify: `ruff check` / `ruff format` / `pyright` clean on `db/models.py`.

- [x] 3.2 `docs/technical/dpd_headwords_table.md` (lines 153–159) — mark `variant`
  and `variant_list` as deprecated/empty, and drop the now-wrong "(currently
  unused)" note from `var_text`.
  - → verify: reads correctly against the new reality.

## Phase 4 — validation

- [x] 4.1 Run the `db_tests` column rule `"variant: not empty, move"`.
  - → verify: zero rows flagged.

- [x] 4.2 Run the project test suite for the affected areas:
  `uv run pytest tests/db_tests/ tests/tools/ tests/exporter/goldendict/`
  plus anything touching these columns.
  - → verify: no new failures vs. the pre-change baseline.

- [x] 4.3 Full-suite smoke run (`uv run pytest tests/`) before handoff, per the
  kamma smoke gate.
  - → verify: no new failures.

- [ ] 4.4 **User does a real interactive gui2 session** — open pass2, load a word
  that had a `variant`, confirm the field is gone, confirm `synonym`,
  `var_phonetic` and `var_text` all still edit and save, and specifically test an
  `_add` transfer button (the 2.1 crash risk).
  - → verify: user confirms.

## Notes

- Nothing in this thread touches `Lookup.variant` or `db/variants/`.
- `tools/synonym_variant.py` keeps its `variant` handling. It costs nothing and
  it keeps clearing the column if anything ever refills it before the column is
  dropped.
- Files expected to change: `scripts/fix/variant_to_var_text.py` (new),
  `gui2/dpd_fields.py`, `gui2/dpd_fields_lists.py`, `db/models.py`,
  `docs/technical/dpd_headwords_table.md`,
  `db/backup_tsv/dpd_headwords_part_*.tsv`.
- Concurrent kamma threads share this working tree — stage by explicit file list
  at commit time, never `git add -A`.
