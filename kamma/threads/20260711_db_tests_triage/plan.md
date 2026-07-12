# Plan: db_tests triage & refresh

**GitHub issue:** #157
**Spec:** `spec.md` in this folder

## Architecture Decisions

- **No pre-made verdicts.** Each file's fate is decided at its task, after the user runs it. The plan stores the evidence so no file starts from scratch.
- **Verdict menu:** `keep` (as-is + standard freshen) · `freshen` (standard freshen only) · `improve` (real logic/UX work, scoped at the row) · `archive` (move to `archive/db_tests/`, remove stale refs) · `delete` — or any bespoke mix.
- **Standard freshen (constant, applies to every surviving file):** module + function docstrings; modern type hints; `uv run ruff check --fix` + `uv run ruff format` + `uv run pyright` clean; minor obvious fixes (bare `print` → `tools.printer` where sensible, `Dict`→`dict`, dead commented code out).
- **Ordering is motivational:** low-hanging fruit (orphans, tiny files, quick verdicts) first; problem children (big files, live library, Flet app) later.
- **Pytest:** where a surviving file has importable pure logic, add a test under `tests/db_tests/...` mirroring the source path (existing pattern: `tests/db_tests/test_db_tests_manager.py`, `tests/db_tests/single/test_add_phonetic_variants.py`). Decided per row.
- **Archive convention:** `archive/db_tests/` (already exists). Also remove the file's `tools/paths.py` entries, justfile recipes, and data files, or archive data alongside.
- **Evidence preserved here:** "last run" = newest `__pycache__` `.pyc` mtime (snapshot 2026-07-11, before any re-runs); "(pytest)" = the `.pyc` was created by a direct pytest run over the folder. **No `.pyc` ≠ unused** — direct `python file.py` runs leave no cache. "git" = last non-data-update commit date where known, else last commit touching the file.

## Verdict legend for rows

Each file task: user runs it → reports → verdict recorded on the `verdict:` line → agent implements → tick.

---

## Phase 1 — Orphaned `single/` scripts (12 files, low-hanging fruit)

Referenced by nothing (no justfile, no live import, no paths.py data) — but several ran as manual one-offs in 2026, so orphaned ≠ unused. Likely fast verdicts.

- [x] `db_tests/single/test_su_kammadharaya.py` — words starting with *su* should be kammadhāraya
  - 33 lines, tiny · read-only · refs: none · last run: 2026-02-21 (pytest) · git: 2025-12-18 · flags: bare print
  - verdict: **keep** + improve: added exceptions JSON (`test_su_kammadharaya.json`) with 7 legitimate non-kammadhāraya su- words (sīdha, suggahitaggāhī, suṭṭhu, sudaṃ 2, sulabhati, subuddhasāsana, subhāveti). Freshened: docstrings, type hints, printer, path registered in tools/paths.py.
  - → verify: verdict implemented; ruff+pyright clean on file ✓
- [x] `db_tests/single/test_numbering_anomalies.py` — anomalies in headword numbering
  - read-only · refs: none · last run: 2026-02-21 (pytest) · git: 2025-12-18 · flags: bare print, no printer
  - verdict: **keep** + improve: added exceptions JSON (`test_numbering_anomalies.json`), (e)xception/(q)uit TUI, path registered in tools/paths.py. Freshened: docstrings, type hints, printer, GlobalVars class.
  - → verify: ruff+pyright clean ✓
- [x] `db_tests/single/test_phonetic_change_sk_ri.py` — phonetic changes from Sanskrit ṛ
  - read-only · refs: none · last run: 2026-02-21 (pytest) · git: 2025-12-18 · flags: bare print
  - verdict: **move to `fixme/`** — unused, moved to `db_tests/single/fixme/test_phonetic_change_sk_ri.py` for later revisit
  - → verify: file moved ✓
- [x] `db_tests/single/test_pali_1_2_difference.py` — is lemma_1 ≈ lemma_2 (difflib)
  - read-only · refs: none · last run: 2026-02-21 (pytest) · git: 2025-10-29 · flags: ~~filename typo fixed~~, bare print, uses `tools.pos.INDECLINABLES`
  - verdict: **keep** + improve: renamed `difefrence`→`difference`; added exceptions JSON (`test_pali_1_2_difference.json`) with 10 pre-seeded IDs; interactive one-by-one display (id, lemma_1, lemma_2, stem, pattern); clipboard copy lemma_1; (e)xception TUI; path registered in tools/paths.py. Freshened: docstrings, type hints, printer, GlobalVars class.
  - → verify: ruff+pyright clean ✓; filename fixed ✓
- [x] `db_tests/single/test_family_compounds_equals_family_idiom.py` — docstring admits it's a "quick starter template"
  - **writes DB (1 commit)** · refs: none · last run: 2026-02-01 (pytest) · git: 2025-12-18 · flags: leftover scaffold, not a real test
  - verdict: **freshen** — docstrings, type hints, printer, extracted functions, ruff+pyright clean. Logic unchanged.
  - → verify: ruff+pyright clean ✓
- [x] `db_tests/single/test_family_compounds_have_meaning_1.py` — family compounds must have meaning_1 + headword
  - read-only · refs: none · last run: 2026-02-01 (pytest) · git: 2025-09-21 · flags: bare print
  - verdict: **keep** + improve: added exceptions JSON, (e)/(q) TUI, fixed display labels (family compound / no meaning_1), dark_orange colors. Freshened: docstrings, type hints, printer, GlobalVars class.
  - → verify: ruff+pyright clean ✓
- [x] `db_tests/single/test_family_compounds.py` — find missing compound families
  - read-only · refs: none · last run: 2026-02-01 (pytest) · git: 2026-06-15 · flags: `load_exceptions()` returns empty `set()` — exceptions file was removed, function dormant
  - verdict: **move to `fixme/`** — clipboard-SQL workflow is unmanageable. Future: inline DB queries or gui2 Tests tab integration.
  - → verify: file moved ✓
- [x] `db_tests/single/test_example_dupes.py` — duplicate examples in example_1/2 (SequenceMatcher)
  - **writes DB (2)** · refs: none · last run: 2026-02-01 (pytest) · git: 2025-10-29 · flags: bare print
  - verdict: **keep** + improve: JSON config (`threshold` + `exceptions`), (e)xception/(d)elete/(s)wap/(q)uit TUI, path registered. Freshened: docstrings, type hints, printer. Original display formatting preserved.
  - → verify: ruff+pyright clean ✓
- [ ] `db_tests/single/test_gram_in_last_position.py` — grammatical terms must be in last position
  - **writes DB (2)** · refs: none · last run: 2026-03-20 (pytest) · git: 2026-03-13 · flags: uses `sqlalchemy.or_`, `tools.printer` present
  - verdict: ____
  - → verify: as above
- [x] `db_tests/single/test_root_family_vs_construction_prefixes.py` — root-family prefix == construction prefixes?
  - 192 lines · **writes DB (2)** · refs: none · last run: 2026-02-21 (pytest) · git: 2025-10-29 · flags: ~~2 pyright errors~~ fixed, bare print
  - verdict: **keep** + improve: exceptions JSON, (e)xception/(r)oot/(c)onstruction/(q)uit TUI, title, root_base display, path registered. Freshened: `| None` types (removed `typing.Optional`), pyright errors fixed (`or ""` guard).
  - → verify: ruff+pyright clean ✓
- [x] `db_tests/single/test_allowable_characters.py` — allowable characters per field, flags illegal chars
  - read-only · refs: only `archive/gui/gui_main.py` (dead) · last run: 2026-02-01 (pytest) · git: 2026-05-30 · flags: 2 FIXME, imports `tools.pali_alphabet`/`configger`/`unicode_char`; note a similarly-named old copy's pycs sit in `db_tests/__pycache__`
  - verdict: **keep** + improve: single-pass speedup (~10×), title, 7 allowlist fixes (ṣ in meaning, + in meaning, - in sutta, ?/= in link, ? in sanskrit, trans/example skip without meaning_1). Freshened: docstrings, type hints.
  - → verify: ruff+pyright clean ✓; runs in ~12s ✓
- [x] `db_tests/single/add_compound_type.py` — interactively set compound_type via `CompoundTypeManager`
  - no direct commit (manager may) · refs: none · last run: no pyc (direct-run leaves none) · git: 2026-02-10 · flags: bare print
  - verdict: **archive** — better version in gui2 now. Moved to `archive/db_tests/single/`.
  - → verify: file moved ✓

- [x] **Phase 1 wrap:** all 12 rows have verdicts

## Phase 2 — Active `single/` scripts (17 files: justfile-wired or paths.py-backed)

In active use (ran Mar–May 2026). Verdicts likely `freshen`/`improve`. Watch: most write the DB.

- [x] `db_tests/single/add_phonetic_changes.py` — find missing/wrong phonetic changes per TSV criteria
  - **writes DB (1)** · refs: `just test-phonetic` (`python -m`) · last run: 2026-03-29 · git: 2026-06-11 · flags: ~~5 FIXME → 2~~
  - verdict: **keep** + improve: (q)uit TUI, title + DB loading status via printer, `without`→`not_in_constr` + `not_in_lemma` in TSV/manager, precompute+index speedup (75s→2s), type hints, docstrings. Freshened: ruff+pyright clean.
  - → verify: ruff+pyright clean ✓; `just test-phonetic` still works ✓
- [x] `db_tests/single/add_phonetic_changes_vowels.py` — missing/wrong vowel sandhi per TSV
  - **writes DB (1)** · refs: data TSV in paths.py; no justfile entry · last run: no pyc · git: 2026-03-13 · flags: consider justfile entry if kept
  - verdict: **move to `fixme/`** — not working
  - → verify: file moved ✓
- [x] `db_tests/single/add_phonetic_variants.py` — find & add phonetic variant pairs
  - **writes DB (4)** · refs: `just add-variants-phonetic`; exceptions json in paths.py; **has pytest** (`tests/db_tests/single/test_add_phonetic_variants.py`, 436 lines) · last run: 2026-05-09 · git: 2026-06-11 · flags: clean
  - verdict: **keep** — already clean, works well
  - → verify: no changes needed ✓
- [x] `db_tests/single/add_synonym_variant_single.py` — synonyms sharing one meaning + same signature
  - **writes DB (3)** · refs: `just add-synonyms-single`; imports from `add_synonym_variant_multi` · last run: 2026-05-07 · git: 2026-05-09
  - verdict: **keep** — already clean, works well
  - → verify: no changes needed ✓
- [x] `db_tests/single/add_synonym_variant_multi.py` — synonyms sharing 2+ meanings + same pos/grammar
  - **writes DB (5)** · refs: `just add-synonyms-multi`; imported by `_single` and `_del` · last run: 2026-05-11 · git: 2026-06-11 · flags: shared helper module — API used by siblings
  - verdict: **keep** — user confirmed working well, including the `(t)extual all pairwise` option added in `1f352192`. Final polish: one-line docstrings added to `_pair_key`, `_general_key`, `_entry_label`, `_format_fields`, `_show_result`, `main`.
  - → verify: ruff+pyright clean ✓
- [x] `db_tests/single/add_synonym_variant_del.py` — review likely-wrong synonym pairs, delete/reassign
  - **writes DB (3)** · refs: `just add-synonyms-del`; json in paths.py · last run: 2026-05-11 · git: 2026-06-11 · flags: unused `_is_valid_synonym` kept intentionally as documented revert path — leave
  - verdict: **keep** + improve, extensive session fixing false-positive "wrong synonym" flags found live during user triage:
    - `_plausibly_valid_synonym`: added shared non-empty `family_word` as an alternate validity signal alongside meaning overlap (catches declension siblings like `imasmā`/`asmā`, same family_word `ima`, whose wording differs)
    - added `_has_reciprocal_synonym`: a candidate already listing hw_a's lemma_clean back is treated as valid even without meaning/family_word overlap (`assācariya`/`sārathi 2`)
    - `find_wrong_synonym_pairs` now skips hw_a entries with no `meaning_1` and candidates with no `meaning_1` (incomplete entries shouldn't drive flags)
    - for `pos == "pron"` only: added a `family_inflections` union (per `family_word`, unioning `inflections_list` across every member) — only a family's "primary" headword (e.g. `ima 1.1`) carries the full generated declension paradigm; individual declined-form headwords (`imehi`, `imasmā`) have trivial self-only inflection lists, so contracted spellings that never got their own headword (`ehi`, `amhā`) are validated against the family union instead of a same-lemma_clean homonym search. Restricted to pronouns since every other pos always resolves to a real headword.
    - added `_meaning_overlap` helper; when a syn_clean has exactly one total candidate (no ambiguity to resolve), an overlapping meaning is valid regardless of pos_class — the pos_class restriction exists only to disambiguate between multiple candidates (`cicciṭa` masc ↔ `ciṭiciṭi` ind, `todaka` masc ↔ `tudanta` prp, identical/overlapping meanings, unrelated pos)
    - `find_wrong_synonym_pairs`/`prompt_wrong_pairs` restructured to emit **one row per (hw_a, syn_clean)** instead of one row per candidate homonym — an ambiguous lemma_clean with several non-plausible homonyms (e.g. `amhā` → both a `pr` and a `fem` headword) is one underlying decision, not several; added `_choose_target` for the rare case a multi-candidate group needs (s)/(t) to pick a specific target
    - added missing `(p)honetic` action (assign `var_phonetic`) — the menu previously only had `(s)ynonym`/`(t)extual`/`(d)elete`, with no way to reclassify a flagged pair as a phonetic variant (`uttarikaraṇīya`/`uttariṃkaraṇīya`, nasalized sandhi variant)
    - `tools/synonym_variant.py`: added `IND_SANDHI_POS = {"ind", "sandhi"}` to the shared `pos_class()` grouping (used by `_multi`/`_single`/`_del`) so `ind`/`sandhi` pos are treated as one class, fixing cross-pos false flags there too
  - → verify: ruff+pyright clean on `add_synonym_variant_del.py` and `tools/synonym_variant.py` ✓; user confirmed each fix live against real flagged rows during interactive triage
  - NOTICED — NOT TOUCHING: `uv run pytest tests/` smoke run at row wrap shows 3 pre-existing failures unrelated to this row's scope — `tests/db/families/test_family_root.py::test_compile_rf_html`, `::test_make_anki_data`, `tests/exporter/txt/test_export_txt.py::TestMakeWordEntry::test_branch1_with_root_and_extras_id10`. `dpd.db` is gitignored/mutable and these assert against specific live-data snapshots (e.g. headword id 10 `meaning_1` wording); neither `add_synonym_variant_del.py` nor `tools/synonym_variant.py` touches `meaning_1`/family_root/export html, so this is DB-content drift, not a regression from this row. Matches the known brittle-golden-master pattern already logged in memory.
- [ ] `db_tests/single/add_word_family_finder.py` — find missing word families
  - **writes DB (1)** · refs: pickle in paths.py · last run: no pyc · git: 2025-09-21 · flags: bare print only
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_antonyms.py` — missing/wrong/extra antonyms
  - **writes DB (9!)** · refs: `test_antonyms.json` in paths.py · last run: 2026-02-01 (pytest) · git: 2026-06-11 · flags: 2 FIXME (lines ~102, 161)
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_bahubbihis.py` — bahubbīhi compound characteristics
  - **writes DB (1)** · refs: json in paths.py · last run: 2026-02-01 (pytest) · git: 2026-06-11 · flags: **5 FIXME (lines ~122–126)**, uses `tools.terminal_highlights`
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_bold_example_inflections.py` — bold word in examples must be a real inflection
  - **writes DB (1)** · refs: `test_bold.json` (`bold_example_path`) in paths.py · last run: 2026-03-20 (pytest) · git: 2026-06-11
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_digu.py` — numerals in compounds → compound_type digu
  - read-only · refs: json in paths.py · last run: 2026-03-20 (pytest) · git: 2026-06-11
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_hyphenations.py` — find super-long words and hyphenate
  - **writes DB (1)** · refs: `test_hyphenations.txt` scratchpad in paths.py · last run: 2026-02-21 (pytest) · git: 2026-06-11 · flags: 1 FIXME; **print strings claim to update `test_hyphenations.json` but the script uses the `.txt`** — orphaned 158 KB json + lying log messages to resolve here
  - verdict: ____
  - → verify: as above; json orphan resolved (deleted/archived/rewired) and print messages truthful
- [ ] `db_tests/single/test_idioms.py` — component words contain correct family idiom
  - **writes DB (1)** · refs: `test_idioms.json` in paths.py · last run: 2026-02-01 (pytest) · git: 2026-06-11
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_maha_compounds.py` — mahā compound_type + construction
  - **writes DB (1)** · refs: `test_maha_exceptions.json` in paths.py · last run: 2026-03-20 (pytest) · git: 2026-06-11
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_neg_compounds.py` — find negative kammadhārayas
  - **writes DB (1)** · refs: exceptions json in paths.py · last run: 2026-02-21 (pytest) · git: 2026-06-11
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_sukha_dukkha_finder.py` — sukha/dukkha compounds lacking antonyms
  - 114 lines · read-only · refs: json in paths.py · last run: 2026-03-20 (pytest) · git: 2026-06-11 · flags: uses `tools.goldendict_tools`
  - verdict: ____
  - → verify: as above
- [ ] `db_tests/single/test_theragatha_filler.py` — fill missing auto-added monk names in Theragāthā
  - 73 lines · read-only · refs: pickle in paths.py · last run: 2026-02-21 (pytest) · git: 2026-06-15 · flags: bare print; prior pickle read≠write bug already fixed (kamma archive)
  - verdict: ____
  - → verify: as above
- [ ] **Phase 2 wrap:** all rows verdicted; `uv run ruff check db_tests/single/` + `uv run pyright db_tests/single/` clean; `uv run pytest tests/db_tests/` passes; justfile recipes for surviving scripts intact
  - → verify: commands pass

## Phase 3 — `db_tests_gui/` (8 files — problem children begin)

Flet mini-app last run 2026-03-29 (>3 months). Central question at each row: retire, fold into gui2, or keep standalone.

- [ ] `db_tests_gui/internal_tests.py` — Flet form for editing column-rule tests
  - GUI · refs: none · last run: no pyc; git: 2025-03-24 · flags: **buttons never wired — non-functional prototype**; duplicates gui2's Tests tab (`gui2/tests_tab_view.py` + controller, backed by `DbTestManager`); `print("Next")` stub
  - verdict: ____ (probably doesn't even need a run — user confirms)
  - → verify: verdict implemented
- [ ] `db_tests_gui/main.py` — Flet sidebar dispatching the 6 add_* editors
  - GUI · `ft.app` at import · last run: no pyc; git: 2025-10-29 · flags: **3 pyright errors (lines 110, 118)**; dispatch key `"add_antonyms sync"` contains a space (fragile); commented-out dead lines
  - verdict: ____
  - → verify: verdict implemented; pyright errors resolved
- [ ] `db_tests_gui/add_antonyms.py` — add missing antonyms interactively
  - **writes DB (1)** · last run: 2026-03-29 · git: 2026-06-11 · flags: **imports from `archive/db_tests/old_tests_DELETE.py`** — live dependency on an archived "DELETE" module; resolve here (inline the needed code or properly relocate it)
  - verdict: ____
  - → verify: no imports from `archive/` remain; ruff+pyright clean
- [ ] `db_tests_gui/add_antonyms_sync.py` — antonyms from existing words; caches to `add_antonyms_sync_dict.json`
  - **writes DB (1)** · data json in paths.py · last run: 2025-12-02 · git: 2026-06-11 · flags: bare print
  - verdict: ____
  - → verify: as above
- [ ] `db_tests_gui/add_family_compound_neg.py` — family compounds/idioms from negative words
  - **writes DB (1)** · uses `tools.negative_to_positive` · last run: 2026-03-29 · git: 2026-03-04 · flags: no entry point (only via main.py)
  - verdict: ____
  - → verify: as above
- [ ] `db_tests_gui/add_family_compound_su_dur.py` — family compounds/idioms for su/dur/sa
  - **writes DB (1)** · last run: 2026-03-29 · git: 2026-03-04
  - verdict: ____
  - → verify: as above
- [ ] `db_tests_gui/add_family_compound_taddhita.py` — family compounds/idioms from taddhita
  - **writes DB (1)** · uses `tools.tsv_read_write` · last run: 2026-03-29 · git: 2026-03-04
  - verdict: ____
  - → verify: as above
- [ ] `db_tests_gui/add_hyphenations.py` — add hyphenations; manages `speech_marks.json`
  - **writes DB (1)** · last run: 2026-03-29 · git: 2026-06-11 · flags: no module docstring; orphaned sibling `add_hyphenations.json` (22 B, no consumer) to resolve here
  - verdict: ____
  - → verify: as above; orphan json resolved
- [ ] **Phase 3 wrap:** folder's fate coherent (README matches reality; if the whole app is retired, folder archived and `tools/paths.py` entries removed)
  - → verify: `uv run ruff check db_tests_gui/` + `uv run pyright db_tests_gui/` clean (or folder gone); gui2 unaffected

## Phase 4 — Top-level `db_tests/` (2 files, known-live problem children)

> ⚠️ **MODEL NOTE:** Phases 1–3 run fine on Sonnet 5 (mechanical, well-scoped edits). For this phase — latent "possibly unbound" bugs in ~1,150 dense lines and API-preserving changes to `DbTestManager` — switch to a stronger model (Opus 4.8) if the current model's analysis feels shallow or it misjudges the unbound-variable fixes.

- [ ] `db_tests/db_tests_relationships.py` — large battery of cross-word relationship checks
  - ~1,153 lines · read-only (pyperclip) · refs: `just db-test` · last run: no pyc (direct-run) · git: 2026-03-27 · flags: **3 FIXME "possibly unbound" latent bugs (lines ~934, 971, 1048)**; old `typing.Dict`/`Optional`; messy design-notes header with typos ("generting", "fucntions")
  - verdict: ____ (likely improve: fix unbound bugs, modernize hints, tidy header)
  - → verify: `just db-test` runs to completion; ruff+pyright clean; FIXMEs resolved
- [ ] `db_tests/db_tests_manager.py` — `DbTestManager`: loads/checks/runs/saves the column-rule TSV
  - shared library · writes the TSV (not the DB) · refs: gui2 ×4 + `tests/db_tests/test_db_tests_manager.py` (158 lines) · last run: 2026-06-16 (live via gui2) · git: 2026-06-15 · flags: mixes bare rich `print("[red]...")` with `pr.red(...)`; `main()` is a hardcoded id=112 smoke demo
  - verdict: ____ (constraint: gui2-facing API must not break)
  - → verify: `uv run pytest tests/db_tests/` passes; gui2 Tests tab still imports cleanly (`uv run python -c "from gui2.toolkit import ..."` or equivalent import check)
- [ ] **Phase 4 wrap:** `uv run ruff check db_tests/` + `uv run pyright db_tests/` clean; `uv run pytest tests/` passes
  - → verify: commands pass

## Phase 5 — Cross-cutting cleanup & wrap-up

- [ ] Clear stale `__pycache__` entries for deleted/moved modules (evidence no longer needed once triage is complete): `db_tests/__pycache__` (add_family_compound_and_idiom/2, add_family_compound_neg, add_family_compound_taddhita, helpers, internal_tests, old_tests_DELETE, test_allowable_characters), `single/__pycache__` (add_synonym_multi, add_synonym_variant), `db_tests_gui/__pycache__` (db_tests_gui)
  - → verify: no `.pyc` without a matching live `.py`
- [ ] Add pytest coverage decided during triage (rows marked "pytest: yes") under `tests/db_tests/`, mirroring source paths
  - → verify: `uv run pytest tests/db_tests/` passes; new tests fail meaningfully if logic breaks
- [ ] Update `db_tests/README.md`, `db_tests/single/README.md`, `db_tests_gui/README.md` to post-triage reality; check `docs/technical/project_folder_structure.md`
  - → verify: READMEs list only existing files/entry points
- [ ] Final sweep: `uv run ruff check db_tests db_tests_gui && uv run pyright db_tests db_tests_gui && uv run pytest tests/`
  - → verify: all pass; report summary table of verdicts to user (report-only — user commits)

## Review fixes (2026-07-12)

Post-commit review of `c0a2d772`/`3946bb9c`/`1f352192` found and fixed:

- [x] `tools/phonetic_changes.tsv:86` (`ñj + t` rule) lost its `exceptions` column in the `not_in_lemma` migration (6 fields vs 7) — padded to 7 columns with `x` placeholders
- [x] `tools/phonetic_change_manager.py` `_update_exception_in_tsv`: guard was still `len(cols) > 5` while writing `cols[6]` → IndexError on short rows — now `len(cols) > 6`
- [x] `test_pali_1_2_difference.py` + `test_numbering_anomalies.py`: `prompt()` returns 0 on (e)xception so the summary doesn't count excepted items; pali_1_2 prompt now shows the `q`uit option it already accepted
- [x] `test_root_family_vs_construction_prefixes.py`: `GlobalVars` DB load moved from class level (fired at import) into `__init__`
- `add_synonym_variant_multi` row: verdict recorded 2026-07-12 (**keep**) after user confirmed the `1f352192` (t)extual option works; docstring polish added
