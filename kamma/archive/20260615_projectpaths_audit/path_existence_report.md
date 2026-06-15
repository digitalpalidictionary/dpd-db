# ProjectPaths existence report (2026-06-15)

Method: `ProjectPaths(create_dirs=False)`, checked `.exists()` on every `Path` attr from cwd = repo root.
**310 Path attrs · 236 exist · 74 MISSING.** (24 non-Path str attrs = webapp template name constants, not checked.)
Evidence only — no fixes applied. Decisions are the user's.

---

## A. STALE — `shared_data/help/` → `shared_data/reference/` rename (commit 4207a36f)
Files EXIST under the new `reference/` dir; pp attrs still say `help/`.
| pp attr | pp points to | actual file |
|---|---|---|
| abbreviations_tsv_path | shared_data/help/abbreviations.tsv | shared_data/reference/abbreviations.tsv ✓ |
| abbreviations_other_tsv_path | shared_data/help/abbreviations_other.tsv | shared_data/reference/abbreviations_other.tsv ✓ |
| bibliography_tsv_path | shared_data/help/bibliography.tsv | shared_data/reference/bibliography.tsv ✓ |
| help_tsv_path | shared_data/help/help.tsv | shared_data/reference/help.tsv ✓ |
| thanks_tsv_path | shared_data/help/thanks.tsv | shared_data/reference/thanks.tsv ✓ |

## B. STALE — template `.html` → `.jinja` conversion (equivalent file EXISTS, extension fix)
| pp attr | pp .html | actual .jinja |
|---|---|---|
| dpd_header_templ_path | …/dpd_header.html | dpd_header.jinja ✓ |
| dpd_header_plain_templ_path | …/dpd_header_plain.html | dpd_header_plain.jinja ✓ |
| spelling_templ_path | …/dpd_spelling_mistake.html | dpd_spelling_mistake.jinja ✓ |
| variant_templ_path | …/dpd_variant_reading.html | dpd_variant_reading.jinja ✓ |
| abbrev_templ_path | …/help_abbrev.html | help_abbrev.jinja ✓ |
| epd_templ_path | …/epd.html | epd.jinja ✓ |
| help_templ_path | …/help_help.html | help_help.jinja ✓ |
| root_header_templ_path | …/root_header.html | root_header.jinja ✓ |
| deconstructor_header_templ_path | exporter/deconstructor/deconstructor_header.html | deconstructor_header.jinja ✓ |
| grammar_dict_header_templ_path | exporter/grammar_dict/grammar_dict_header.html | grammar_dict_header.jinja ✓ |
| ebook_* (10 attrs) | exporter/kindle/templates/ebook_*.html | ebook_*.jinja ✓ (all 10) |

## C. STALE — `db/backup_tsv/` single file → split into `_part_NNN.tsv`
| pp attr | pp points to | actual |
|---|---|---|
| pali_word_path | db/backup_tsv/dpd_headwords.tsv | dpd_headwords_part_001/002/003.tsv |
| pali_root_path | db/backup_tsv/dpd_roots.tsv | dpd_roots_part_001.tsv |
> ⚠ Core source paths. The single-file no longer exists; backup is now chunked.

## D. ⚠ GONE — no `.html` AND no `.jinja` equivalent, BUT pp attr still referenced in exporter code
Build artifacts in `exporter/share/` exist (pipeline ran), yet these templates are absent.
Needs your knowledge — were they consolidated into `dpd_headword.jinja` / `dpd_root.jinja`?
| pp attr | missing file | still referenced in (non-paths.py) |
|---|---|---|
| button_box_templ_path | dpd_button_box.html | 1 file |
| dpd_definition_templ_path | dpd_definition.html | 2 files |
| example_templ_path | dpd_example.html | 2 files |
| family_compound_templ_path | dpd_family_compound.html | 1 file |
| family_idiom_templ_path | dpd_family_idiom.html | ? |
| family_root_templ_path | dpd_family_root.html | ? |
| family_set_templ_path | dpd_family_set.html | ? |
| family_word_templ_path | dpd_family_word.html | ? |
| feedback_templ_path | dpd_feedback.html | ? |
| frequency_templ_path | dpd_frequency.html | 1 file |
| grammar_templ_path | dpd_grammar.html | 2 files |
| inflection_templ_path | dpd_inflection.html | 1 file |
| sutta_info_templ_path | dpd_sutta_info.html | 1 file |
| root_button_templ_path | root_buttons.html | ? |
| root_definition_templ_path | root_definition.html | ? |
| root_families_templ_path | root_families.html | ? |
| root_info_templ_path | root_info.html | ? |
| root_matrix_templ_path | root_matrix.html | ? |
| buttons_js_path | exporter/goldendict/javascript/buttons.js | ? |

## E. DEAD — already `# FIXME delete these` in paths.py
| pp attr | missing |
|---|---|
| complete_word_templ_path | exporter/templates_jinja/dpd_complete_word.html (parent gone) |
| jinja_templates_dir | exporter/templates_jinja/ (gone) |
| templates_dir | exporter/templates/ (gone) |
| typst_data_path | exporter/pdf/typst_data.typ (only typst_data_lite.typ exists) |

## F. OUTPUT absent despite pipeline run (parent OK — likely regenerate-flag-gated or stale)
| pp attr | missing |
|---|---|
| additions_pickle_path | shared_data/additions |
| inflection_templates_pickle_path | shared_data/inflection_templates |
| inflections_from_translit_json_path | shared_data/inflections_from_translit.json |
| inflections_to_translit_json_path | shared_data/inflections_to_translit.json |
| lookup_from_translit_path | shared_data/lookup_from_translit.json |
| lookup_to_translit_path | shared_data/lookup_to_translit.json |
| typst_lite_abbreviations_path | exporter/share/abbreviations.pdf |

## G. NEW attr added this session, never written (dormant)
| family_compound_exceptions_path | db_tests/single/test_family_compounds.pickle | test always falls back to empty set |

## H. EXTERNAL legacy (parent dir missing, outside repo)
| old_dpd_full_path | ../csvs/dpd-full.csv |
| old_roots_csv_path | ../csvs/roots.csv |

## I. resources/** — OUT OF SCOPE per user (not actioned), listed for completeness
14 missing under `resources/other-dictionaries/build/**` (bhs/cone/cpd/dppn/dpr/mw/peu/simsapa/sin_eng_sin/vri/whitney json, vri_gd, vri_mdict) + `…/dictionaries/vri/source/vri.csv`.

---

# VERDICT — "does any script use the path?" (user's test, 2026-06-15)
Usage scan over 5850 source files (py/go/js/jinja/html/toml; excl archive, __pycache__, paths.py).
**61 of 74 missing attrs are referenced by NO script → truly dead. 13 still consumed.**

## STILL USED (13) — keep; fix the path where stale
| attr | verdict | action |
|---|---|---|
| abbreviations_tsv_path | USED (6 files), stale `help/`→`reference/` | repoint to `shared_data/reference/` |
| abbreviations_other_tsv_path | USED (2), stale help/ | repoint to reference/ |
| bibliography_tsv_path | USED (4), stale help/ | repoint to reference/ |
| help_tsv_path | USED (2), stale help/ | repoint to reference/ |
| thanks_tsv_path | USED (4), stale help/ | repoint to reference/ |
| pali_word_path | USED (2) as BASE NAME — `_part_*.tsv` glob/split (by design) | LEAVE, base never exists |
| pali_root_path | USED (2), same base-name pattern | LEAVE |
| inflections_from_translit_json_path | USED (1) — runtime temp | LEAVE (genuine temp) |
| inflections_to_translit_json_path | USED (1) — runtime temp | LEAVE |
| lookup_from_translit_path | USED (1) — runtime temp | LEAVE |
| lookup_to_translit_path | USED (1) — runtime temp | LEAVE |
| typst_lite_abbreviations_path | USED (1) — build output | LEAVE (regenerated) |
| family_compound_exceptions_path | USED (1) — added this session, dormant | user said DEL → see below |

## DEAD — referenced by NO script (61) → candidates for deletion from paths.py
Confirmed root causes:
- **Templates (B/D):** exporters now load templates BY NAME via jinja `FileSystemLoader`
  (`exporter/jinja2_env.py`), not via `*_templ_path` attrs. All goldendict/kindle/root/epd/help
  template attrs + `buttons_js_path` are superseded.
- **E FIXME block:** `complete_word_templ_path`, `jinja_templates_dir`, `templates_dir`, `typst_data_path`.
- **F pickles:** `additions_pickle_path`, `inflection_templates_pickle_path` — referenced nowhere.
- **H external:** `old_dpd_full_path`, `old_roots_csv_path`.
- **resources/** (I): bhs/cone/cpd/dppn/dpr/mw/peu/simsapa/sin_eng_sin/vri/whitney json + vri_gd/vri_mdict/vri_source.

Full dead list (61): abbrev_templ_path, additions_pickle_path, bhs_json_path, button_box_templ_path,
buttons_js_path, complete_word_templ_path, cone_json_path, cpd_json_path, deconstructor_header_templ_path,
dpd_definition_templ_path, dpd_header_plain_templ_path, dpd_header_templ_path, dppn_json, dpr_json_path,
ebook_abbrev_entry_templ_path, ebook_content_opf_templ_path, ebook_deconstructor_templ_path,
ebook_entry_templ_path, ebook_epd_entry_templ_path, ebook_epd_letter_templ_path, ebook_example_templ_path,
ebook_grammar_templ_path, ebook_letter_templ_path, ebook_title_page_templ_path, epd_templ_path,
example_templ_path, family_compound_templ_path, family_idiom_templ_path, family_root_templ_path,
family_set_templ_path, family_word_templ_path, feedback_templ_path, frequency_templ_path,
grammar_dict_header_templ_path, grammar_templ_path, help_templ_path, inflection_templ_path,
inflection_templates_pickle_path, jinja_templates_dir, mw_json_path, old_dpd_full_path, old_roots_csv_path,
peu_json_path, root_button_templ_path, root_definition_templ_path, root_families_templ_path,
root_header_templ_path, root_info_templ_path, root_matrix_templ_path, simsapa_json_path,
sin_eng_sin_json_path, spelling_templ_path, sutta_info_templ_path, templates_dir, typst_data_path,
variant_templ_path, vri_gd_path, vri_json_path, vri_mdict_path, vri_source_path, whitney_json_path.

NOTE: the resources/** entries among the dead list are OUT OF SCOPE per user — leave them.
