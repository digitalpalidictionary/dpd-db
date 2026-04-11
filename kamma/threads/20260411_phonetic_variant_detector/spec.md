# Phonetic Variant Detector — Spec

## Issue Reference
Closes part 1 of [#144](https://github.com/digitalpalidictionary/dpd-db/issues/144). Parts 2 (exporter wiring) and 3 (delete legacy `variant` column) are explicitly deferred to separate threads.

## Overview
Build a standalone phonetic variant detection toolkit under a new `scripts/variants/` directory. The toolkit reads the current `dpd.db`, identifies candidate phonetic variant pairs, and writes them to a TSV report next to the script for human review. It does not modify the database, the exporters, or any existing data.

## Current State Context (snapshot 2026-04-11)
- `dpd_headwords` already has three columns: legacy `variant` (≈6,376 rows populated), `var_phonetic` (≈69 rows), `var_text` (≈166 rows). The split is half-done in the schema but not in the data.
- `gui2/dpd_fields.py` already exposes `var_phonetic` and `var_text` as editable fields (lines 261–262). The legacy `variant` field is still present and edited via `variant_blur`.
- `db_tests/single/add_phonetic_variants.py` already does one of the four requested detection techniques (grouping headwords by `construction_clean` + `pos` and printing groups with >1 distinct `lemma_clean`). It is print-only and uses `rich`.
- `tools/phonetic_change_manager.py` manages a different feature (`phonetic` column, construction-time sound changes like `va > uva`). It is NOT reused here.
- `db/variants/` handles textual variant readings from CST/BJT/SC/SYA books via `Lookup.variant`. It is a completely separate pipeline and stays untouched.
- `Levenshtein` 0.27.1 is already installed via `uv`.
- `docs/technical/dpd_headwords_table.md` currently labels `var_phonetic` and `var_text` as "(currently unused)". Do not update these docs in this thread — data population is a later thread.

## What It Should Do
1. Provide `scripts/variants/find_phonetic_variants.py` which, when run, writes `scripts/variants/phonetic_variant_candidates.tsv` with one row per candidate pair.
2. Implement four detection techniques behind a shared `PhoneticVariantDetector` class in `scripts/variants/phonetic_variant_detector.py`:
   - **Same-construction grouping** — port of `db_tests/single/add_phonetic_variants.py` (group by `(construction_clean, pos)`).
   - **Handwritten substitution rules** — a Python literal list in `scripts/variants/phonetic_rules.py` (e↔aya, ṃ↔ṅ, t↔ṭ, h↔"", ā↔a, …). Applied bidirectionally.
   - **Levenshtein proximity** — pairs with distance 1–2, same first char, scoped to same `family_word` / `family_root` to cut false positives.
   - **Reuse** — the same-construction grouping above IS the reuse of `add_phonetic_variants.py`.
3. For each candidate pair emit the columns: `lemma_1`, `candidate_lemma_1`, `rule`, `construction_clean`, `pos`, `meaning_1`, `var_phonetic`, `var_text`, `variant`.
4. Expose reusable pure functions and dataclasses so later threads can import them from the GUI or exporters without re-running the CLI.
5. Ship `tests/scripts/variants/test_phonetic_variant_detector.py` covering each rule class plus a combined `detect_all` test. Tests use `types.SimpleNamespace` stand-ins (no SQLAlchemy session needed).

## Constraints
- Python 3.13, managed with `uv`. Modern type hints (`list[...]`, `dict[...]`, `|` unions).
- `pathlib.Path` for file paths. `icecream.ic` for debug. No `sys.path` hacks.
- Do NOT modify `db/models.py`, `db/variants/`, any exporter, `gui2/`, or existing `variant` / `var_phonetic` / `var_text` data.
- Reuse `tools.db_helpers.get_db_session`, `tools.paths.ProjectPaths`, `DpdHeadword.construction_clean`, `DpdHeadword.lemma_clean`, `tools.printer.printer`.
- The executing agent does NOT run `find_phonetic_variants.py` during implementation (user runs scripts per global `CLAUDE.md`). Tests use in-memory fakes only.
- Add `scripts/variants/phonetic_variant_candidates.tsv` to `.gitignore` (or confirm an existing glob already covers it) so review output doesn't accidentally get committed.

## How We'll Know It's Done
- `uv run pytest tests/scripts/variants/ -q` passes.
- `uv run ruff check scripts/variants/ tests/scripts/variants/` is clean.
- When the user runs the script, `scripts/variants/phonetic_variant_candidates.tsv` appears and contains known pairs present in the current DB: `karīyati/kayirati`, `jayati/jeti`, `nahāta/nhāta`, `gāmaṇi/gāmaṇī`, `akaṭa/akata`, `akathaṃkathī/akathaṅkathī`.
- `git status` shows code changes limited to `scripts/variants/`, `tests/scripts/variants/`, `.gitignore`, and `kamma/threads/...`.

## What's Not Included
- No migration of the ≈6,376 legacy `variant` rows into `var_phonetic`/`var_text`.
- No writes to `var_phonetic` or `var_text`.
- No exporter, template, GUI, or `db/models.py` changes.
- No deletion of the `variant` column.
- No changes to `db/variants/` (CST/BJT/SC/SYA textual-reading pipeline).
- No update to `docs/technical/dpd_headwords_table.md`.
