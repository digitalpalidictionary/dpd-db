# ProjectPaths Audit — ad-hoc file opens

Issue #157 task: **"Add all Path() to `ProjectPaths`"**

Audit of every Python `open()` (and csv/pickle/json/config read) that uses a
**hardcoded literal path** instead of a `tools/paths.py::ProjectPaths` attribute
(or `gui2/paths.py::Gui2Paths` for gui2).

Scope searched: `db/ db_tests/ db_tests_gui/ audio/ exporter/ gui2/ scripts/ tools/ conductor/`
(excluded: `archive/`, `**/archive/**`, `.venv/`, `resources/`, `tests/`, `tools/writemdict/` vendored).

## Classification legend
- **CASE 1** — genuine persistent project file/dir → needs a `ProjectPaths` attribute + replace the open.
- **CASE 2** — temp/throwaway, OR opens a passed-in arg/variable, OR f-string derived from an existing pp dir attr → fine as-is (no action).
- **CASE 3** — ambiguous → needs a human decision before acting.

> Note: the bulk of the codebase is already compliant — most `open()`s are CASE 2
> (already use `pth.*` / `Gui2Paths`, or open a variable/parameter). Only CASE 1 and
> CASE 3 below are actionable. Each CASE 1 row is **first-pass** and must be re-verified
> in context during its batch before editing.

## Reclassification — committed-rule (agreed 2026-06-15)
Deciding line: **committed/tracked ⇒ Tier 1 named attr**; uncommitted single-file scratch ⇒
Tier 2 (anchor to `pth.temp_dir`); external/separate-tooling ⇒ Tier 3 (leave). Git facts:
- `temp/` is **gitignored** → every `temp/*` fixed-name file = **Tier 2** (dir-anchor), not a new attr.
- `scripts/suttas/dpd/*.tsv` = **untracked**, write-only → not 12 attrs; one dir attr or leave (ambiguous).
- **Tracked (→ Tier 1):** `tools/cst_book_translator.tsv`, `exporter/kobo/templates/kobo.css`,
  `tools/ai_models.json`, `scripts/fix/fix_synonym_entries.json`.
- **Untracked but core/ambiguous (→ Phase 3 one-by-one):** `config.ini` (gitignored, but project input),
  `db_tests/single/family_compound_exceptions`, bjt `index.json`, webapp `processed_logs`.
- Build artifacts under `exporter/share/*` follow the existing convention → Tier 1 even if untracked
  (e.g. apple-dict `Dictionary.xml`).
See `plan.md` for the resulting batch order.

---

## CASE 1 — needs a ProjectPaths attribute (actionable)

### Batch A — `tools/` core (low-level, verify import safety)
| file:line | path opened | mode | purpose | proposed attr |
|---|---|---|---|---|
| tools/configger.py:13, 237 | `config.ini` | r/w | read+write project config | `config_ini_path` ⚠ configger is very low-level — check for import cycle with paths.py |
| tools/ai_manager.py:22 | `tools/ai_models.json` | r | AI model config | `ai_models_json_path` |
| tools/bjt.py:222 | `temp/{books}.text` | w | dump BJT book text | `temp_dir`-derived (maybe CASE 2 — temp scratch) |

### Batch B — `exporter/`
| file:line | path opened | mode | purpose | proposed attr |
|---|---|---|---|---|
| exporter/kobo/kobo.py:34 | `exporter/kobo/templates/kobo.css` | r | kobo template CSS | `kobo_css_path` |
| exporter/apple_dictionary/apple_dictionary.py:268 | `<share>/apple_dictionary/Dictionary.xml` | w | Apple Dict XML out | `apple_dictionary_xml_path` (base derived from share_dir already) |
| exporter/webapp/scripts/process_logs.py:96 | `processed_logs` (cwd) | wb | pickled log analysis | `webapp_processed_logs_path` |

### Batch C — `db/` + `audio/`
| file:line | path opened | mode | purpose | proposed attr |
|---|---|---|---|---|
| db/variants/variants_modules.py:51 | `temp/variants.json` | w | dump extracted variants | `variants_json_path` (temp-based — could be CASE 2) |
| db/suttas/dv_catalogue_suttas.py:22 | download temp file | wb | staging dl of DV catalogue | use `temp_dir`; verify if `dv_catalogue_suttas_tsv_path` is the real target |
| audio/db_create.py:215 | `<audio/db>/dpd_audio_index_{version}.tsv` | w | versioned audio index | `dpd_audio_index_versioned_tsv_path` (unversioned `dpd_audio_index_tsv_path` exists) |

### Batch D — `scripts/` finders & builders writing to `temp/`
| file:line | path opened | mode | purpose | proposed attr |
|---|---|---|---|---|
| scripts/build/generate_books_tsv.py:347 | `tools/cst_book_translator.tsv` | w | book translator map (read elsewhere via __file__) | `cst_book_translator_tsv_path` |
| scripts/build/transliterate_bjt.py:116 | `<bjt_dir>/index.json` | w | BJT index | `bjt_index_json_path` |
| scripts/find/deconstruction_finder.py:16 | `temp/deconstruction_finder.csv` | w | finder output | temp-scratch — likely CASE 2 |
| scripts/find/sn_samyutta_mismatch_finder.py:20 | `temp/sn_samyutta_mismatch.tsv` | w | finder output | temp-scratch — likely CASE 2 |
| scripts/info/suffix_counter.py:63,69 | `temp/suffixes_sorted.tsv`, `temp/suffix_counts.tsv` | w | counter output | temp-scratch — likely CASE 2 |
| scripts/export/sanskrit_export.py:56,63 | `temp/DPD Pāḷi Sanskrit.txt/.tsv` | w | sanskrit export | temp-scratch — likely CASE 2 |
| scripts/fix/verb_finder.py:18,19 | `dpd.db`, `temp/verb_finder` | r/mkdir | db + output dir | use `dpd_db_path`; output temp-scratch |
| scripts/add/vagga_codes/shared.py:13,14 | `db/backup_tsv/sutta_info.tsv`, `temp` | r | sutta info + out dir | use existing `sutta_info_tsv_path` + `temp_dir` |
| scripts/add/vagga_codes/kn_suggestions.py:22,23 | `db/backup_tsv/sutta_info.tsv`, `temp/vagga_codes_suggestions.tsv` | r/w | same | use `sutta_info_tsv_path`; output temp-scratch |
| scripts/fix/fix_synonym_entries.py:20 | `<script-sibling>/fix_synonym_entries.json` | r/w | fix data store | `fix_synonym_entries_json_path` |

### Batch E — `scripts/` hardcoded `dpd.db` session opens (should use `dpd_db_path`)
| file:line | note |
|---|---|
| scripts/fix/verb_finder.py:18 | `get_db_session(Path("dpd.db"))` → `pth.dpd_db_path` |
| scripts/add/vagga_codes/runner.py:51 | same |
| scripts/find/sn_samyutta_mismatch_finder.py:24 | same |
| scripts/find/variants_process.py:313 | same |
> Verify each: confirm it's literally `"dpd.db"` and not already a pp attr.

### Batch F — `db_tests/`
| file:line | path opened | mode | purpose | proposed attr |
|---|---|---|---|---|
| db_tests/single/test_family_compounds.py:66 | `family_compound_exceptions` (cwd-relative pickle) | rb/wb | exceptions pickle | `family_compound_exceptions_pickle_path` |
| db_tests/single/test_theragatha_filler.py:58,63 | `tests/tests/theragatha_filler`, `tests/test_theragatha_filler` | rb/wb | progress pickle (note: read & write paths DIFFER — likely a bug) | `theragatha_filler_pickle_path` |

---

## CASE 3 — ambiguous, needs decision

| file(s) | path | why ambiguous |
|---|---|---|
| scripts/suttas/dpd/*.py (≈12 files: an, dn, mn, sn, kn3-ud, kn4-iti, kn5-snp, kn6-vv, kn7-pv, kn8-th, kn9-thi, kn14-ja) | `scripts/suttas/dpd/<book>.tsv` | one-off sutta-extraction scripts writing a fixed-name TSV next to themselves. Persistent-ish but script-local. Worth ~12 pp lines, or leave as script-local? |
| scripts/suttas/dpr/an_vaggas.py:18, an_nipatas.py:12 | `../../2_Resources/Code/digitalpalireader/.../listam.js` | reads an **external** path OUTSIDE the repo (a sibling checkout). pp uses repo-relative base_dir — does this belong in pp at all? |
| scripts/find/most_common_missing_word_finder.py:198 | `scripts/find/most_common_missing_words.tsv` | output written next to script, not temp/. Persistent reference list or ephemeral? |
| conductor/tests/test_readme_standards.py:16 | `conductor/templates/DIR_README_TEMPLATE.md` | `conductor/` is separate scaffolding tooling with its own tests — in scope for dpd-db ProjectPaths at all? |
| **temp/ fixed-name outputs** (Batches A,C,D above marked "temp-scratch") | various `temp/*.tsv/.csv/.json` | KEY DECISION: a fixed-name file under `temp/` that a human inspects after a run — CASE 1 (give it a pp attr) or CASE 2 (leave as scratch)? Resolving this reclassifies ~8 rows. |

---

## CASE 2 — already compliant / no action (summary counts)
- **gui2/** — fully compliant (all via `Gui2Paths` or `ProjectPaths`, or atomic `.tmp` writes). 0 actionable.
- **tools/tsv_read_write.py, unpickle.py, script_runner.py, mdict_exporter.py** — generic helpers opening a passed-in `file_path` arg. Correct by design.
- **db/inflections/, db/lookup/** — all via `pth.*` (incl. `.with_suffix()` batch variants). Compliant.
- **db_tests/single/** (most) + **db_tests_gui/** — all via `pth.*`. Compliant.
- **scripts/suttas/** TSV reads of CST/BJT/SC — derived from existing pp dir attrs. Compliant.
- **exporter/analysis/** — uses a local `ensure_analysis_dirs()` runtime dir helper (ephemeral), not pp. Compliant by intent.
