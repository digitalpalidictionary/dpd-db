# Plan — ProjectPaths audit & migration (#157)

## Phase 0 — Audit (research) ✅
- [x] Find every ad-hoc file open across the codebase
- [x] Classify into CASE 1 / 2 / 3 (`audit_table.md`)

## Phase 1 — Policy ✅
- [x] Agreed committed-rule + 3-tier scheme (see spec.md)
- [x] Reclassify table, mark git-tracked vs untracked

## Phase 2 — Low-hanging fruit (unambiguous)   ✅ (B2.1–B2.8 done; lint+pyright green; prompt-toolkit dep added w/ approval, pandas synced)
Reuse-existing-attr + clear tracked Tier-1 + Tier-2 temp anchoring. New attrs are
appended in-section; the single alphabetical sort happens in Phase 4.
- [x] B2.1 — `exporter/kobo/kobo.py`: add `kobo_css_path` + `kobo_templates_dir` (tracked)
- [x] B2.2 — `tools/ai_manager.py`: add `ai_models_json_path` (tracked), lazy pp
- [x] B2.3 — `scripts/fix/verb_finder.py`: `dpd.db`→`dpd_db_path`, `temp/verb_finder`→`temp_dir/`
- [x] B2.4 — `scripts/find/sn_samyutta_mismatch_finder.py`: `dpd.db`→attr, temp anchor
- [x] B2.5 — `scripts/find/variants_process.py`: `dpd.db`→attr
- [x] B2.6 — vagga_codes (`shared.py`/`runner.py`/`kn_suggestions.py`): hardcoded
      `db/backup_tsv/sutta_info.tsv`→`sutta_info_tsv_path`, `temp`→`temp_dir`
- [x] B2.7 — other Tier-2 temp scratch: `suffix_counter`, `sanskrit_export`,
      `deconstruction_finder`, `db/variants/variants_modules.py`, `tools/bjt.py`
- [x] B2.8 — clear tracked Tier-1: `apple_dictionary.py` (no change — already share_dir-derived),
      `scripts/fix/fix_synonym_entries.py` (tracked json)

## Phase 3 — Ambiguous, one-by-one (user decisions 2026-06-15)
- [x] `config.ini` → LEAVE. User: "sits in root, always and forever." Not in pp.
- [x] `resources/**` → OUT OF SCOPE entirely (user). Drops the DPR external-path case too.
- [x] `conductor/**` → DON'T TOUCH (will be archived later). Drops README template case.
- [x] `db_tests/single/test_theragatha_filler.py` — was reading nonexistent
      `tests/tests/theragatha_filler` & writing `tests/test_theragatha_filler` (latent bug).
      Repointed both to pp `theragatha_filler_path` =
      `db_tests/single/test_theragatha_filler.pickle`; moved the canonical 101 B data
      file there. ⚠ FLAG: stray `tests/test_theragatha_filler` (36 B, newer, DIFFERENT
      content) left in place — user to reconcile/delete.
- [x] `db_tests/single/test_family_compounds.py` — repointed bare `"family_compound_exceptions"`
      → pp `family_compound_exceptions_path` = `db_tests/single/test_family_compounds.pickle`.
      NOTE: file is never written and doesn't exist → exceptions set always empty (dormant).
- [ ] DECIDE: broader `db_tests/single` rename sweep ("same with anything else…name py+data
      the same, diff extensions"). Mismatched pairs need confirmation — see below.
- [x] B done: added `suttas_dpd_dir` (14 `scripts/suttas/dpd/*.py` repointed), `most_common_missing_words_tsv_path`.
      ⚠ FLAG: `kn9-thi.py` writes `kn8-thi.tsv` (pre-existing filename typo) — preserved as-is.
- [x] Renamed dead pickle `add_word_family_exceptions` → `add_word_family_finder.pickle`
      (matches `add_word_family_finder.py`); `wf_exceptions_list` attr updated. JSON data files
      left as-is (user: jsons in use, pickles old/dead).
- [ ] OPTIONAL (A): `apple_dictionary_xml_path` (already pp-derived via share_dir). Likely leave.
- [ ] `cst_book_translator.tsv` — reader uses `__file__`-relative; only writer hardcodes (tracked). Still open.

## Phase 4 — tools/paths.py cleanup (user-directed 2026-06-15) ✅
- [x] **Existence check** — `path_existence_report.md`. 310→ checked; 74 missing.
- [x] **"does any script use it" test** (user's rule) — 61 dead / 13 used.
- [x] **Deleted 48 dead attrs** (47 dead-non-resources + dormant `family_compound_exceptions_path`).
      Consumer `test_family_compounds.py::load_exceptions` → `return set()` (was dormant: file
      never existed → always empty). `pickle` import dropped.
- [x] **Repointed 5** `shared_data/help/` → `shared_data/reference/` (rename fallout) — now exist.
- [x] **Kept** (used or by-design-absent): pali_word/root (base-name for `_part_*.tsv` glob),
      translit temp json, typst_lite_abbreviations, + 14 `resources/**` dead (OUT OF SCOPE).
- [x] **Regenerated paths.py**: alphabetised, dir-grouped comment headings (81 sections),
      string template-name constants in own final section. Generator + integrity check
      (286 survivors, 0 missing/extra/value-diff). `Optional`→`| None` already done.
- [x] **Convention pass**: removed all `ProjectPaths(create_dirs=False)` and inline
      `ProjectPaths().X` I introduced → `pth = ProjectPaths()` then `pth.X` (project convention).
- [x] Gate: ruff+pyright clean on all touched files; `pytest tests/` 2234 passed.

## ⚠ Flags for user (decisions/oddities surfaced, NOT acted on)
- `kn9-thi.py` writes `kn8-thi.tsv` (pre-existing kn8/kn9 filename typo) — preserved.
- stray `tests/test_theragatha_filler` (36B, newer, DIFFERENT content vs kept 101B copy) — reconcile/delete.
- `family_compound_exceptions` mechanism was fully dormant; deleted per user. Revert easily if wrong.
- 14 `resources/**` pp attrs are dead but left untouched (out of scope).

## Phase 5 — Path(__file__) elimination (user: "not a single hacky Path(__file__)")
- [x] Swept project (excl tests, per user "leave the tests"; archive/resources out of scope).
- [x] Production Path(__file__) removed → ProjectPaths/Gui2Paths attrs (8 new pp attrs +
      `pass2_x_manager_py_path` on Gui2Paths; paths.py re-sorted, integrity 294 ok):
      cst_book_translator (reader+writer), compile_vaggas, extract_cone/cpd, audio trim/delete,
      exporter/analysis/paths.py (ANALYSIS_DIR), gui2 pass2 hot-reload.
- [x] apple_dictionary: NO issue — already `pth.share_dir`-derived, no Path(__file__). Left.
- [x] Lint debt dragged in by touched files: fixed mechanically (chmod EXE001, PLW1510
      `check=False`, SIM102, SIM118); 10 deliberate blind-except → `# noqa: BLE001` per user
      (overrode the no-noqa rule for intentional catch-alls; behavior-preserving).
- [x] Gate green (ruff+pyright); `pytest tests/` 2234 passed; import smoke (no cycles).
- LEFT (user "leave the tests"): 45 test files — 43 co-located `Path(__file__).parent/fixture`
  (idiomatic) + 2 `parents[3]` repo-root (technically breach CLAUDE.md no-traversal; left per user).

## Phase 6 — Review-surfaced fixes (2026-06-15)
Independent review (opencode + subagent) found the original `open(`-focused audit missed
`get_db_session(Path("dpd.db"))` / db-path-constant patterns. Comprehensive re-sweep + fixes:
- [x] `scripts/add/vagga_codes/dhp_m2.py` — `sutta_info_tsv_path` + `dpd_db_path` (missed sibling)
- [x] `tools/proofreader.py` — `proofreader_tsv_path` + `dpd_db_path`
- [x] `scripts/fix/variant_cleaner.py` — `dpd_db_path`
- [x] `scripts/export/db_filter_export.py` — `dpd_db_path` + temp output anchored; pandas `.loc` pyright fix
- [x] `tools/meaning_construction.py` — `dpd_db_path` (`__main__`)
- [x] `db_tests/db_tests_manager.py` — `dpd_db_path` (`main()`)
- [x] `scripts/tutorial/quick_start.py` — `dpd_db_path` (7th miss, beyond the 6 flagged)
- [x] `tools/script_runner.py` — `os.path.exists("dpd.db")` → `pth.dpd_db_path.exists()`
- LEFT per user: `scripts/onboarding/*` + `scripts/bash/initial_build_db.py` (bootstrap, pre-setup),
  `tools/version.py` ("dpd.db" is a label, not a path).
- Incidental lint in touched files: chmod EXE001, pandas `.loc`; deliberate `except Exception`
  catch-alls + local-wall-clock `datetime.now()` → `# noqa: BLE001` / `# noqa: DTZ005` (per user policy).
- [x] Gate green; `pytest tests/` 2234 passed; zero `dpd.db` literals remain in production (excl bootstrap/label).

## Resolved / no-op
- A: `apple_dictionary_xml_path` — no change needed (already share_dir-derived).
- `create_dirs` param now type-hinted (`create_dirs: bool = True`) per review nit.

## Phase 5 — Verify & finish
- [ ] ruff + pyright on every touched file; run related tests (`uv run pytest`)
- [ ] Review, then finalize
