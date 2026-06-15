## Thread
- **ID:** 20260615_projectpaths_audit
- **Objective:** Eliminate hardcoded paths — route every project file open through ProjectPaths (#157)

## Files Changed
- `tools/paths.py` — 48 dead attrs deleted, 5 help→reference repointed, ~10 new attrs, alphabetized (294 survivors)
- `gui2/paths.py` — added `pass2_x_manager_py_path`
- `exporter/analysis/paths.py` — `ANALYSIS_DIR` now from `pth.analysis_dir`, no `Path(__file__)`
- `tools/cst_book_translator.py` — `_TSV_PATH` from pp, no `Path(__file__)`
- `scripts/suttas/vaggas/compile_vaggas.py` — output from `pth.compile_vaggas_tsv_path`
- `scripts/extractor/extract_cone.py` — output from `pth.extract_cone_tsv_path`
- `scripts/extractor/extract_cpd.py` — output from `pth.extract_cpd_tsv_path`
- `exporter/kobo/kobo.py` — templates + CSS from `pth.kobo_templates_dir` / `pth.kobo_css_path`
- `tools/ai_manager.py` — lazy `pth.ai_models_json_path`
- `scripts/build/generate_books_tsv.py` — writes to `pth.cst_book_translator_tsv_path`
- `scripts/find/most_common_missing_word_finder.py` — `pth.most_common_missing_words_tsv_path`
- `scripts/fix/fix_synonym_entries.py` — `pth.fix_synonym_entries_json_path`
- `scripts/fix/verb_finder.py` — `pth.dpd_db_path` + `pth.temp_dir / "verb_finder"`
- `scripts/find/sn_samyutta_mismatch_finder.py` — `pth.dpd_db_path` + temp anchor
- `scripts/find/variants_process.py` — `pth.dpd_db_path`
- `scripts/find/sanskrit_export.py` — pp usage for temp outputs
- `scripts/add/vagga_codes/{shared,runner,kn_suggestions,apply}.py` — `pth.sutta_info_tsv_path` + temp anchors
- 14× `scripts/suttas/dpd/*.py` — all use `pth.suttas_dpd_dir` / `{book}.tsv`
- `db_tests/single/test_theragatha_filler.py` — read/write unified to `pth.theragatha_filler_path` (latent bug fixed)
- `db_tests/single/test_family_compounds.py` — `load_exceptions()` returns `set()`, dormant pickle deleted
- `db_tests/single/add_word_family_finder.py` — `pth.wf_exceptions_list` (renamed attr)
- `db/variants/variants_modules.py` — `pth.variants_json_path`
- `db/lookup/help_abbrev_add_to_lookup.py` — `pth.help_tsv_path` (now reference/)
- `audio/error_check/{trim_audio,delete_silent_files}.py` — pp attrs, no `Path(__file__)`
- `gui2/pass2_pre_{controller,view,file_manager,new_word_manager}.py` — Gui2Paths usage
- 7× `exporter/analysis/*.py` — `ensure_analysis_dirs()` from `pth.analysis_dir`

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `scripts/add/vagga_codes/dhp_m2.py:20,54` | Hardcoded `Path("db/backup_tsv/sutta_info.tsv")` and `Path("dpd.db")` | Sister files were all updated; this was missed | Use `pth.sutta_info_tsv_path` and `pth.dpd_db_path` |
| 2 | minor | `tools/proofreader.py:88-89` | Hardcoded `"dpd.db"` and `"tools/proofreader.tsv"` | Both `dpd_db_path` and `proofreader_tsv_path` exist in pp | Use pp attrs |
| 3 | minor | `scripts/fix/variant_cleaner.py:97` | `Path("dpd.db")`, no ProjectPaths import | Missed by audit | Import pp, use `pth.dpd_db_path` |
| 4 | minor | `scripts/export/db_filter_export.py:40` | `db_path = "dpd.db"`, no pp import | Missed by audit | Import pp, use `pth.dpd_db_path` |
| 5 | minor | `tools/meaning_construction.py:139` | `Path("dpd.db")` under `__main__` | Minor; `__main__`-only usage. Missed by audit | Use `pth.dpd_db_path` |
| 6 | minor | `db_tests/db_tests_manager.py:405` | `Path("dpd.db")` under `__main__` | Test runner in db_tests/, not tests/. Missed by audit | Use `pth.dpd_db_path` |
| 7 | nit | `kamma/threads/.../plan.md` | B2.3–B2.8 remain unchecked `[ ]` despite being done in code | Plan out of sync | Update checkmarks |
| 8 | nit | `scripts/suttas/dpd/kn9-thi.py:15` | Now writes to `kn9-thi.tsv` (was `kn8-thi.tsv` typo) | Plan said "preserved as-is"; fix is correct but unacknowledged | Update plan to note the fix |

## Fixes Applied
None (review-only; no code changes requested).

## Test Evidence
- `uv run ruff check tools/paths.py gui2/paths.py exporter/analysis/paths.py` → PASS (0 errors)
- `uv run pyright tools/paths.py gui2/paths.py exporter/analysis/paths.py` → PASS (0 errors, 0 warnings)
- `uv run pytest tests/` (per plan phase 5) → PASS (2234 passed)
- Import smoke: no cycles detected
- `grep "shared_data/help" --include="*.py" -r .` → ZERO matches (rename clean)
- `grep "Path(__file__)" --include="*.py" -r .` → only in tests/ archive/ resources/ conductor/ (all out of scope)
- `grep "create_dirs=False" --include="*.py" -r .` → only in tests/ and resources/ (out of scope)

## Verdict
PASSED
- Review date: 2026-06-15
- Reviewer: opencode (AI)
- 0 blocking, 0 major, 6 minor (auxiliary scripts), 2 nit (plan docs)
- Core refactor is thorough: 294 pp attrs, alphabetized, all production `Path(__file__)` eliminated, 48 dead attrs deleted, lint/pyright green, 2234 tests pass
- Ready for `/kamma:4-finalize`
---
# Independent Review (subagent, 2026-06-15)

## Files Changed
48 paths touched. Core: `tools/paths.py` (993-line regenerate — 325→294 attrs, 47 dead removed, 16 new, alphabetised within 86 dir-grouped sections), `gui2/paths.py` (+`pass2_x_manager_py_path`), `pyproject.toml`/`uv.lock` (+`prompt-toolkit>=3.0.52`). Consumers across `scripts/suttas/dpd/*` (14), `scripts/{add,find,fix,info,export,extractor,build}`, `db/variants/*`, `audio/error_check/*`, `tools/{ai_manager,bjt,cst_book_translator}.py`, `exporter/{kobo,analysis}`. Data: `add_word_family_exceptions`→`add_word_family_finder.pickle`, theragatha pickle→`db_tests/single/test_theragatha_filler.pickle`, two stray copies deleted. 9 files `100644→100755` (ruff EXE001).

## Findings

| # | Severity | Location | What | Why | Fix |
|---|---|---|---|---|---|
| 1 | nit | `scripts/suttas/dpd/kn9-thi.py:15` | Output filename changed `kn8-thi.tsv`→`kn9-thi.tsv` | plan.md (line 42/66) claims the pre-existing kn8/kn9 typo was "preserved as-is", but the diff actually *corrects* it. Behaviour change vs documented intent. The fix is correct, but the plan flag is now stale/inaccurate. | Confirm with user the rename is wanted (it looks right); update plan.md flag. No code change needed. |
| 2 | nit | `db_tests/single/test_family_compounds.py:62` | `load_exceptions()` now `return set()`; `pickle` import dropped | Dead-code removal of a dormant mechanism (file never existed → always empty set). Behaviour-preserving. Function is now a trivial stub — fine, but slightly odd to keep. | Accept; easily reverted if the exceptions feature is revived. |
| 3 | nit | `tools/paths.py:719` | `create_dirs=True` param has no type hint | CLAUDE.md asks for type hints on all touched code; `base_dir: Path \| None` is hinted but `create_dirs` is bare. Pre-existing, file was fully rewritten. | `create_dirs: bool = True`. Minor; not blocking. |

No blocking or major findings.

## Verifications performed (all PASS)
- **No dangling attr refs:** computed attr-name set HEAD (325) vs working tree (294); 47 truly removed. Grepped every removed name as `.<attr>` across all production `.py` (excl tests/db_tests/archive/venv/kamma) — **zero references**. `family_compound_exceptions_path` has zero refs anywhere (consumer rewritten). No consumer breaks.
- **Repointed `help/`→`reference/`:** all 5 files (`abbreviations.tsv`, `abbreviations_other.tsv`, `bibliography.tsv`, `help.tsv`, `thanks.tsv`) exist under `shared_data/reference/`; `shared_data/help/` is gone; **no stale `shared_data/help` literal** anywhere.
- **Renamed data files:** `add_word_family_finder.pickle` (2706 B) + `test_theragatha_filler.pickle` (101 B) exist; no consumer references old names; stray `tests/test_theragatha_filler` (the flagged 36 B mismatch) **deleted**. theragatha read≠write latent bug fixed (both fns now use `theragatha_filler_path`); `pyperclip.copy(str(i.id))` correctness fix.
- **Convention:** no inline `ProjectPaths().X` or `ProjectPaths(create_dirs=False)` introduced — the 3 diff hits are all deletions (`-`). New attrs all consumed (`pass2_x_manager_py_path`, `suttas_dpd_dir`, etc.). Module-level `pth=ProjectPaths()` in suttas scripts is pre-existing, not new.
- **`Path(__file__)`:** none in production. All remaining `__file__` is in `tests/` or `resources/` (both out of scope, tests exempt per user).
- **`# noqa`:** exactly 10, all `BLE001` on `except Exception` catch-alls (genuine deliberate broad catches) — accepted per prompt. No other noqa types.
- **`prompt-toolkit` dep:** actually imported (`scripts/fix/fix_synonym_entries.py`). Justified.
- **Alphabetisation:** all 86 sections internally sorted (0 unsorted); sections dir-grouped in path order.

## Test Evidence
- `uv run ruff check <44 changed .py>` → **All checks passed!**
- `uv run ruff format --check <42 non-gui2>` → **42 already formatted**
- `uv run pyright <42 non-gui2 changed>` → **0 errors, 0 warnings** (gui2 pyright-excluded per pyproject)
- `uv run python -c "import tools.paths, gui2.paths; ..."` → **ok**, new attrs resolve, no import cycle
- `uv run pytest tests/ -q` → **2234 passed, 16 deselected in 46.89s**

## Verdict
**PASSED.** The migration is behaviour-preserving and well-verified: no still-referenced attr was deleted, repoints/renames are consistent and their files exist, the latent theragatha read≠write bug was fixed, lint+pyright+2234 tests are green. Only three nits, none blocking — the most notable (Finding #1) is a *correct* filename fix whose plan.md flag is now inaccurate (says "preserved" when it was actually fixed); worth a one-line plan note and user confirmation. Residual gaps: `db_tests/single/*` scripts and the two `tests/.../parents[3]` repo-root traversals were intentionally left untested/unchanged per user scope; data-writing script paths (suttas `.tsv`, cst_book_translator writer) verified by static path only, not by running the scripts (not run per project rules).

---
# Review Resolution (2026-06-15)

## Fixes applied after review
- **7 confirmed minor findings** (hardcoded `dpd.db`/paths missed by the original `open(`-only audit) fixed → ProjectPaths attrs: `dhp_m2.py`, `proofreader.py`, `variant_cleaner.py`, `db_filter_export.py`, `meaning_construction.py`, `db_tests_manager.py`, plus a **7th** (`scripts/tutorial/quick_start.py`) found by a wider re-sweep.
- `tools/script_runner.py` — `os.path.exists("dpd.db")` → `pth.dpd_db_path.exists()` (per user).
- Review nits: `create_dirs: bool = True` type hint added; plan.md B2.3–B2.8 + kn9 note synced.
- `db_filter_export.py` — pandas pyright cleared via `.loc[mask]`; hardcoded `temp/` output anchored to `pth.temp_dir`.
- Incidental lint in touched peripheral files: chmod (EXE001); deliberate `except Exception` catch-alls and local-wall-clock `datetime.now()` → `# noqa: BLE001` / `# noqa: DTZ005` (user-approved policy for intentional cases).

## Left per user decision
- `scripts/onboarding/{contributor_setup,contributor_update}.py`, `scripts/bash/initial_build_db.py` — bootstrap/pre-setup, leave.
- `tools/version.py:71` — `"dpd.db"` is a summary label, not a path. Not a finding.
- 45 test files (`Path(__file__).parent / fixture`, 2× `parents[3]`) — left; tests out of scope.

## Final gate
- `uv run ruff check` (all touched) → pass; `ruff format --check` → clean
- `uv run pyright` (non-gui2 touched) → 0 errors (gui2 pyright-excluded per pyproject)
- `uv run pytest tests/` → **2234 passed, 16 deselected**
- Project-wide: zero `get_db_session(Path("dpd.db"))` / `db_path="dpd.db"` in production (excl bootstrap/label)

## Final Verdict: PASSED — ready for /kamma:4-finalize
All findings from both reviews resolved or consciously deferred by the user. Reviewer: Claude (with independent subagent + opencode cross-review).
