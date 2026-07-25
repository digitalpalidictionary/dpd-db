# Review: move `variant` → `var_text`

**Thread:** 20260725_variant_to_var_text
**Reviewed:** 2026-07-25
**Outcome:** PASS (one acceptance criterion unverified — see below)

## Verification performed

| Check | Result |
|---|---|
| `variant` non-empty rows in db | 0 |
| `variant` non-empty rows in backup TSVs (89,273 rows) | 0 |
| Per-row union vs pre-migration snapshot (2,449 rows) | 0 mismatches |
| Collateral change to `synonym` | 0 rows |
| Collateral change to `var_phonetic` | 0 rows |
| `var_text` render violations, whole table (3,176 rows) | 0 |
| Row arithmetic 801 + 2,449 − 74 = 3,176 | matches |
| Full test suite | 1,720 passed, 17 deselected |
| `ruff check` / `ruff format` / `pyright` on touched files | clean |

Spot-check of the merge path: id 1128 `ajajjita` had `variant='jaddhuka'`,
`var_text='ajaddhuka'` → now `var_text='ajaddhuka, jaddhuka'`, correctly ordered,
confirmed in both db and TSV.

## Findings

**1 — latent crash fixed (major, found during implementation).**
`transfer_add_value` in `gui2/dpd_fields.py` built a dict including `"variant"`,
passed it to `assign_relationship_dict`, and wrote every returned key back with
`self.get_field(name).value = value`. `get_field` returns `""` for an unknown
name, so once the `variant` field was removed this would have raised
`AttributeError` the first time a user accepted a synonym / var_phonetic /
var_text suggestion. Rewritten to write back an explicit three-field tuple.
This was not a pre-existing bug — it was created by the field removal and caught
before it shipped.

**2 — 26 unsorted `var_text` values (minor, out of original scope).**
Pre-existing hand-entered values that never passed through
`assign_relationship`. Surfaced by a whole-table render check. User approved
normalising them; done as a second idempotent pass in the same script.
Spec and plan updated to record the scope change.

**3 — `just backup` auto-commits (informational, not a defect).**
`git_commit()` at `db/backup_tsv/backup_dpd_headwords_and_roots.py:148` commits
the backup TSVs as `"pali update"` on every run. Commit `b85ec0a7`. It stages an
explicit glob of the `dpd_headwords_part_*` / `dpd_roots_part_*` files only, so
no concurrent thread's work was captured, and it does not push. Reported to the
user, who has a standing rule against unrequested commits.

**4 — dead `variant` tests left behind (major, found by user after review).**
Removing the gui2 field meant `make_dpd_headword_from_dict` no longer set
`variant`, so a gui2-built `DpdHeadword` had `variant = None` (SQLAlchemy column
defaults apply on INSERT, not instantiation). The `"newline in variant"` rule
then did `re.search(pattern, None)` → `TypeError` on every "run tests" click in
pass2. `variant` was the *only* column left None by this path, confirmed by
enumerating the mapper columns against a gui2-built headword.

First attempt at a fix coerced `None → ""` in
`db_tests_manager.error_test_each_single_row`. **The user correctly rejected
this.** It converted a loud, accurate crash into silently wrong test results — a
"does not contain" rule would spuriously pass, an "is empty" rule would
spuriously fire — for any test referencing a column the headword doesn't carry.
The crash was the right behaviour; the dead tests were the defect. That change
was fully reverted (`db_tests_manager.py` is untouched in the final diff).

Proper fix — deleted every dead `variant` test:
- `db_tests_columns.tsv`: rows `"newline in variant"` and
  `"variant: not empty, move"`
- `db_tests_relationships.py`: `variant_equals_lemma_1()`,
  `synonym_equals_variant()`, both registry entries, and `DpdHeadword.variant`
  from the `load_only` column list
- `test_allowable_characters.py`: the `("variant", ...)` check
- `add_phonetic_variants.py`: `variant` from the `_format_fields` display

Verified: the gui2 "run tests" path now completes with `db_tests_manager.py`
unmodified, returning only the 5 legitimate empty-headword failures.

**Process note:** writing `db_tests_columns.tsv` with `Path.write_text` stripped
its CRLF line endings and rewrote all 550 lines, which would have buried a
concurrent thread's 6-row edit in noise. Caught via `git diff --stat` and
restored byte-wise. That file is CRLF — read and write it as bytes.

**No blocking issues.**

## Unverified

Acceptance criterion 5 — a real interactive gui2 session confirming the field is
gone and the `_add` transfer buttons still work — was **not performed**. The user
declined it ("i'm sure its fine"). Finding 1 is exactly the class of bug that
check was designed to catch; it was found by reading rather than by running, and
the fix is straightforward, but it has not been exercised at runtime. Worth two
minutes the next time gui2 is opened.

## Not done (deliberate, per spec)

- `variant` column still on the model — user drops it at their next model change;
  TODO left at `db/models.py:1184`.
- Exporter and template `variant` branches left in place — all guarded on
  non-empty, so they now render nothing. They come out with the column.
- No reciprocal backfill of one-way links.
- 1,159 dead `variant` links (target is not a headword) migrated as-is into
  `var_text`. Cleaning them belongs to `scripts/fix/variant_cleaner.py`, a
  separate thread.
