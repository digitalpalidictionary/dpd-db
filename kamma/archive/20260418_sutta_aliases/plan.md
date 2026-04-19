# Plan: Sutta Name Aliasing

Branch: `feature/sutta-aliases`

## Phase 1 — Branch

- [x] Create branch `feature/sutta-aliases` from `main`.
  → verify: `git branch --show-current` returns `feature/sutta-aliases`.

## Phase 2 — Cleaning function

- [x] Add `tools/sutta_name_cleaning.py` with:
  - `clean_sc_sutta(s: str) -> str`
  - `clean_bjt_sutta(s: str) -> str`
  Both: trim whitespace, strip a single trailing `ṃ`, return empty string
  for empty input. `clean_bjt_sutta` additionally strips leading `^\d+\.\s*`.
  → verify: `uv run pytest tests/tools/test_sutta_name_cleaning.py` passes
  cases for: trailing ṃ, no ṃ, empty, leading "12. ", "5.Foo",
  whitespace-only, mid-string ṃ untouched.

- [x] Add `tests/tools/test_sutta_name_cleaning.py` covering the cases above.
  → verify: `uv run pytest tests/tools/test_sutta_name_cleaning.py -v` shows
  all named cases passing.

## Phase 3 — Candidate-finder script (manual tool)

- [x] Add `db/suttas/find_sutta_alias_candidates.py`:
  - Loads all `SuttaInfo` rows and all `DpdHeadword.lemma_1` values into a set.
  - For each row, computes cleaned candidates from `sc_sutta` and `bjt_sutta`.
  - Collects existing aliases across all rows for collision checks.
  - For each candidate emits one TSV row with status:
    `ok | missing_headword | collides_with_dpd_sutta | collides_with_existing_alias | duplicate_in_row`.
  - Writes `temp/sutta_alias_candidates.tsv` with columns:
    `dpd_sutta | source | raw | cleaned | status | note`.
  - Prints summary counts per status using `tools.printer`.
  → verify: `uv run python db/suttas/find_sutta_alias_candidates.py` runs to
  completion; TSV exists with expected header; status counts printed; spot-check
  10 rows manually for sane output.

- [x] **STOP for user review.** The user inspects `temp/sutta_alias_candidates.tsv`,
  copies approved aliases into the Google Sheet's `dpd_sutta_var` column
  (`;`-separated), and re-runs `uv run python db/suttas/suttas_update.py` to pull
  them back into the DB.
  → verify: USER confirms at least one row in `SuttaInfo` now has a multi-value
  `dpd_sutta_var` containing a valid alias.

## Phase 4 — Resolver changes

- [x] **Audit `sutta_info_count`** at `db/models.py:757` before changing it.
  Grep for callsites; the function queries `SuttaInfo` but filters on
  `DpdHeadword.lemma_1` with no explicit join — semantics are unclear.
  Document what it actually returns, then decide whether to keep its
  count semantics (alias-aware) or simplify to `1 if self.su else 0`.
  → verify: a one-paragraph note added inline to this plan recording the
  decision and the callsites found.

  **Decision note (2026-04-18):** `sutta_info_count` has zero external callsites
  (grep confirmed — only the definition in `db/models.py`). The current query
  crosses `SuttaInfo` with `DpdHeadword` without a JOIN, producing incorrect
  semantics. Since `su` will be alias-aware after this phase, simplify to
  `1 if self.su else 0`.

- [x] Replace `DpdHeadword.su` relationship at `db/models.py:948` with a
  `cached_property` that returns the canonical `SuttaInfo` for `self.lemma_1`,
  matching either `dpd_sutta == lemma_1` or `lemma_1` ∈
  `dpd_sutta_var.split(";")`. Use a module-level `lru_cache`'d loader returning
  `dict[str, SuttaInfo]` keyed by every name (canonical + alias) for O(1) lookup.
  → verify: in a Python REPL, fetch (a) a canonical sutta headword, (b) a
  variant headword whose name was added in Phase 3 — both return a `SuttaInfo`
  with the same `dpd_sutta`.

- [x] Update `tools/cache_load.py:14` `load_sutta_info_set`: include canonical
  names AND every `;`-split alias from `dpd_sutta_var` (rows where
  `dpd_code != ""`).
  → verify: in a REPL, `load_sutta_info_set()` size > the previous baseline
  count of canonical names; sample of 5 known aliases confirmed present.

- [x] Update `db/models.py:757` `sutta_info_count` to use the alias-aware
  loader (or simplify to `1 if self.su else 0`, since `su` now resolves
  multi-name).
  → verify: returns 1 for both canonical and variant headwords with valid
  aliases; returns 0 for unrelated headwords.

## Phase 5 — Integration check

- [x] Run `uv run python db/suttas/suttas_update.py` end-to-end.
  → verify: no errors; `SuttaInfo` re-populated from sheet; aliases preserved.

- [x] Run `uv run python db/suttas/suttas_to_lookup.py`.
  → verify: no errors.

- [x] Run `uv run pytest tests/` (full suite).
  → verify: no new failures vs `main`.

- [ ] Manual webapp spot-check (USER): start the webapp, visit a variant
  headword whose alias was added, confirm the sutta tab renders with the
  canonical sutta's CST/SC/BJT content.
  → verify: USER confirms tab content matches the canonical sutta's data.
