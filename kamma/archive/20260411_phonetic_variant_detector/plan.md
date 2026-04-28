# Phonetic Variant Detector — Plan

## Issue Reference
Part 1 of [#144](https://github.com/digitalpalidictionary/dpd-db/issues/144).

## Phase 1 — Scaffold + rule data
- [x] 1.1 Create `scripts/variants/`. Check `scripts/find/` first — if siblings have no `__init__.py`, do not add one here either. (No `__init__.py` added; siblings don't have one.)
- [x] 1.2 Create `scripts/variants/phonetic_rules.py` with typed `PHONETIC_RULES: list[tuple[str, str]]` containing at least: `("e","aya")`, `("o","ava")`, `("ā","a")`, `("ī","i")`, `("ū","u")`, `("ṃ","ṅ")`, `("t","ṭ")`, `("d","ḍ")`, `("n","ṇ")`, `("l","ḷ")`, `("h","")`, `("nh","h")`, `("y","")`, `("v","")`. Also `SAME_FIRST_CHAR_LEVENSHTEIN_THRESHOLD: int = 2`. Module docstring documents that rules are applied bidirectionally.
- [x] 1.3 Phase verification: `uv run ruff check scripts/variants/phonetic_rules.py`. (Covered by Phase 2.6 sweep.)

## Phase 2 — Detection engine
- [x] 2.1 Create `scripts/variants/phonetic_variant_detector.py`. Define `@dataclass PhoneticVariantCandidate` with fields `lemma_1`, `candidate_lemma_1`, `rule`, `construction_clean`, `pos`, `meaning_1`, `var_phonetic`, `var_text`, `variant`. Define `class PhoneticVariantDetector` whose `__init__(self, headwords)` pre-builds `_by_lemma_clean: dict[str, list]`, `_by_construction_pos: dict[tuple[str, str], list]`, `_by_family: dict[str, list]` (key = `family_word or family_root`).
- [x] 2.2 `detect_same_construction()` — port grouping logic from `db_tests/single/add_phonetic_variants.py` (lines 72–91). Group by `(construction_clean, pos)`, require ≥2 distinct `lemma_clean`, emit one candidate per ordered pair inside each group with rule `"same_construction"`. Skip groups where `construction_clean` is empty.
- [x] 2.3 `detect_by_rules()` — for each headword A and each rule `(x, y)` in `PHONETIC_RULES`, produce candidate strings by replacing every `x` with `y` AND every `y` with `x` in `A.lemma_clean`. If a candidate resolves via `_by_lemma_clean` to a different existing headword B, emit with rule `f"rule:{x}<->{y}"`. Dedup A→B pairs within this method only (not across methods).
- [x] 2.4 `detect_by_levenshtein()` — for each A with non-empty `family_word` or `family_root`, iterate siblings B in `_by_family[key]`. Skip if `A.lemma_clean[0] != B.lemma_clean[0]`. Compute `Levenshtein.distance(A.lemma_clean, B.lemma_clean)`. Emit when `0 < distance <= SAME_FIRST_CHAR_LEVENSHTEIN_THRESHOLD`. Rule tag `f"levenshtein:{distance}"`.
- [x] 2.5 `detect_all()` — call the three detectors in order, concatenate results, return without cross-method dedup.
- [x] 2.6 Phase verification: `uv run ruff check scripts/variants/`. All checks passed.

## Phase 3 — Runner script + TSV output + .gitignore
- [x] 3.1 Create `scripts/variants/find_phonetic_variants.py`:
  - Shebang `#!/usr/bin/env python3` + docstring referencing #144.
  - `main()` uses `ProjectPaths().dpd_db_path`, opens session via `get_db_session`, queries `db_session.query(DpdHeadword).all()`, instantiates the detector, calls `detect_all()`, and writes the TSV.
  - TSV path: `Path(__file__).parent / "phonetic_variant_candidates.tsv"` (sits next to the script, no dependency on `ProjectPaths.temp_dir`).
  - Use `csv.writer` with `delimiter="\t"`, `quoting=csv.QUOTE_MINIMAL`.
  - Header row: `lemma_1`, `candidate_lemma_1`, `rule`, `construction_clean`, `pos`, `meaning_1`, `var_phonetic`, `var_text`, `variant`.
  - Use `from tools.printer import printer as pr` for status (`pr.tic()`, `pr.yellow_title(...)`, `pr.green_title(...)`, `pr.toc()`), matching `scripts/find/` sibling style.
- [x] 3.2 Read the repo root `.gitignore`. If no existing glob already excludes `scripts/variants/phonetic_variant_candidates.tsv`, append an entry for it. (Added next to `scripts/find/most_common_missing_words*.tsv` entries.)
- [x] 3.3 Phase verification: `uv run ruff check scripts/variants/find_phonetic_variants.py`. DO NOT execute the runner. Runner imported only (`from scripts.variants.find_phonetic_variants import main, OUTPUT_TSV, TSV_HEADER`) — no database execution.

## Phase 4 — Tests
- [x] 4.1 Create `tests/scripts/variants/` (add `__init__.py` only if sibling test dirs do — check `tests/scripts/find/`). No `__init__.py` needed — siblings don't have one.
- [x] 4.2 Build fakes with `types.SimpleNamespace` exposing: `lemma_1`, `lemma_clean`, `pos`, `construction_clean`, `family_word`, `family_root`, `meaning_1`, `var_phonetic`, `var_text`, `variant`. No SQLAlchemy session involved.
- [x] 4.3 Tests to add (each a separate `def test_*`):
  - `test_same_construction_groups_pairs` — two fakes with identical `(construction_clean, pos)` but different `lemma_clean` produce a candidate; a loner does not.
  - `test_rule_e_aya_matches_known_pair` — `jayati` ↔ `jeti` matches rule `rule:e<->aya`.
  - `test_rule_ṃ_ṅ_matches_known_pair` — `akathaṃkathī` ↔ `akathaṅkathī`.
  - `test_rule_t_ṭ_matches_known_pair` — `akaṭa` ↔ `akata`.
  - `test_levenshtein_within_family` — two fakes in same `family_word` with distance 1 match.
  - `test_levenshtein_ignores_different_first_char` — distance 1 but different first char is skipped.
  - `test_levenshtein_ignores_different_family` — distance 1 across different families is skipped.
  - `test_detect_all_returns_candidates_from_all_methods` — combined dataset triggers each detector; assert at least one candidate tagged per rule source.
- [x] 4.4 Phase verification: `uv run pytest tests/scripts/variants/ -q` → 9 passed in 0.05s. `uv run ruff check scripts/variants/ tests/scripts/variants/` → all checks passed.

## Phase 5 — Final cross-check
- [x] 5.1 `git status` — diff is scoped to `.gitignore`, `scripts/variants/`, `tests/scripts/variants/`, `kamma/threads/20260411_phonetic_variant_detector/`. Pre-existing dirty files (`gui2/data/pass2_exceptions.json`, `kamma/kammika.queue.json`) are unrelated to this thread.
- [x] 5.2 `uv run ruff check scripts/variants/ tests/scripts/variants/` — clean.
- [x] 5.3 Re-read `plan.md`, confirm every `[ ]` is `[x]` or has an explicit note. (Done in this edit.)

## Critical Files
- **New:**
  - `scripts/variants/phonetic_rules.py`
  - `scripts/variants/phonetic_variant_detector.py`
  - `scripts/variants/find_phonetic_variants.py`
  - `tests/scripts/variants/test_phonetic_variant_detector.py`
- **Modified:** `.gitignore` (one line, only if needed).
- **Read-only refs:** `db/models.py` (DpdHeadword columns), `db_tests/single/add_phonetic_variants.py` (grouping logic to port), `tools/paths.py`, `tools/db_helpers.py`, `tools/printer.py`.

## End-to-end Verification
1. `uv run pytest tests/scripts/variants/ -q` — passes cleanly.
2. `uv run ruff check scripts/variants/ tests/scripts/variants/` — clean.
3. **User smoke-test:** `uv run python scripts/variants/find_phonetic_variants.py` → `scripts/variants/phonetic_variant_candidates.tsv` appears and contains rows for `karīyati/kayirati`, `jayati/jeti`, `nahāta/nhāta`, `akaṭa/akata`.
4. `git status` diff scoped as in 5.1.
