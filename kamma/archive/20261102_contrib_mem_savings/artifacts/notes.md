# Phase 0 notes (2026-11-02)

## (a) and (b) The 59 `DpdHeadword` columns: bytes and load state
Source: read-only query on `dpd.db` (`mode=ro`), `pragma table_info(dpd_headwords)`. Deferred list from `gui2/database_manager.py:190-196` (`defer(...)` options inside `load_corpus`, lines 181-204).

59 columns, 89774 rows, total 1195.4 MB, loaded 124.3 MB, deferred 1071.0 MB

| # | Column | Bytes (MB) | load_corpus today |
|---|---|---|---|
| 1 | freq_html | 694.87 | deferred |
| 2 | inflections_html | 265.00 | deferred |
| 3 | freq_data | 61.92 | loaded |
| 4 | inflections_sinhala | 47.42 | deferred |
| 5 | inflections_thai | 39.03 | deferred |
| 6 | inflections_devanagari | 24.73 | deferred |
| 7 | inflections | 24.70 | loaded |
| 8 | example_1 | 8.11 | loaded |
| 9 | commentary | 3.29 | loaded |
| 10 | inflections_api_ca_eva_iti | 3.05 | loaded |
| 11 | meaning_1 | 2.31 | loaded |
| 12 | example_2 | 1.99 | loaded |
| 13 | created_at | 1.71 | loaded |
| 14 | construction | 1.40 | loaded |
| 15 | meaning_2 | 1.25 | loaded |
| 16 | sanskrit | 1.22 | loaded |
| 17 | updated_at | 1.14 | loaded |
| 18 | grammar | 1.13 | loaded |
| 19 | sutta_1 | 1.12 | loaded |
| 20 | lemma_1 | 1.01 | loaded |
| 21 | lemma_2 | 0.98 | loaded |
| 22 | stem | 0.76 | loaded |
| 23 | compound_construction | 0.59 | loaded |
| 24 | family_compound | 0.57 | loaded |
| 25 | meaning_lit | 0.54 | loaded |
| 26 | compound_type | 0.45 | loaded |
| 27 | id | 0.44 | loaded |
| 28 | pattern | 0.42 | loaded |
| 29 | root_base | 0.39 | loaded |
| 30 | synonym | 0.34 | loaded |
| 31 | source_1 | 0.31 | loaded |
| 32 | family_set | 0.28 | loaded |
| 33 | derived_from | 0.28 | loaded |
| 34 | pos | 0.27 | loaded |
| 35 | sutta_2 | 0.26 | loaded |
| 36 | family_root | 0.25 | loaded |
| 37 | phonetic | 0.24 | loaded |
| 38 | origin | 0.23 | loaded |
| 39 | root_key | 0.18 | loaded |
| 40 | family_idioms | 0.15 | loaded |
| 41 | notes | 0.15 | loaded |
| 42 | derivative | 0.12 | loaded |
| 43 | var_phonetic | 0.12 | loaded |
| 44 | ebt_count | 0.12 | loaded |
| 45 | antonym | 0.11 | loaded |
| 46 | source_2 | 0.08 | loaded |
| 47 | trans | 0.07 | loaded |
| 48 | plus_case | 0.06 | loaded |
| 49 | root_sign | 0.06 | loaded |
| 50 | suffix | 0.06 | loaded |
| 51 | var_text | 0.04 | loaded |
| 52 | family_word | 0.03 | loaded |
| 53 | verb | 0.02 | loaded |
| 54 | link | 0.02 | loaded |
| 55 | neg | 0.01 | loaded |
| 56 | cognate | 0.01 | loaded |
| 57 | non_ia | 0.00 | loaded |
| 58 | non_root_in_comps | 0.00 | loaded |
| 59 | variant | 0.00 | loaded |

The text actually loaded (124.3 MB) is about a tenth of the 676.4 MB the corpus step costs (`contrib_mem_measure/artifacts/laptop_tables.md`). The rest is Python object overhead.

## (c) `SearchType` values
`SearchType = Literal["EXACT", "STARTS_WITH", "CONTAINS", "REGEX"]` (`tools/wordfinder_manager.py:14`). Default is `STARTS_WITH` (`:95`). The search loops over every file and calls `list(self.cst_file_freq[file].keys())` each time (`:102-103`).

## (d) Columns `inflections_list_all` reads
`inflections` and `inflections_api_ca_eva_iti`, split on commas and joined into one list (`db/models.py:1477-1481`). It is a `cached_property` (`db/models.py:1476`), so each list stays on its object. `make_inflections_lists` also reads `meaning_1` (`gui2/database_manager.py:358-360`). So the direct query for L2 needs three columns: `inflections`, `inflections_api_ca_eva_iti`, `meaning_1`. The lists contain `""` when a column is empty (project note), so the direct query must drop empty strings the same way the set does: today's set keeps `""` as a member.

## (e) Callers of `load_corpus` and of the corpus list
- `gui2/database_manager.py:351` `make_inflections_lists`; `:408` `make_pass2_lists`; `:435` `make_compound_components_map`; `:797` `get_relationship_detector`.
- `gui2/tests_tab_controller.py:287,853` (Tests tab; not in a contributor's tab list, `gui2/contributor_tabs.py:9-11`).
- `gui2/database_manager.py:824-827` builds its own private load for the detector rebuild, not `load_corpus`. This is a second place that loads headwords after a write. Check it in task 1.1: if a contributor save triggers it, a slim corpus must cover it as well.
- No other reader of the corpus list in `gui2/` or `tools/` (`rg -n "load_corpus\(|_db_entries" gui2 tools --type py`).

## Contributor path summary
Tabs: Pass1Auto and Pass1Add (`gui2/contributor_tabs.py:9`). Corpus readers on that path: `make_inflections_lists` (Pass1Auto `gui2/pass1_auto_controller.py:120,198`; Pass1Add `gui2/pass1_add_view.py:229`) and the detector (`gui2/dpd_fields.py:1367,1408`). The one reader of `all_inflections` is `gui2/pass1_auto_controller.py:273`.

## Drift (task 0.2)
Re-read every line the spec cites. Corrected in `spec.md` and `plan.md`:
- `gui2/contributor_tabs.py:8-10` is `:9-11`.
- `tools/synonym_variant.py:890` is `:889` (`self._headwords = list(headwords)`).
- `tools/synonym_variant.py:350-358` is `:351-358`.
Everything else matched. `git status --porcelain gui2 tools db tests` printed nothing (no uncommitted change in the code folders).

## Finding: a second corpus after "refresh DB" (not in the spec at first)
- A contributor's save goes to JSON files, not the database (`gui2/save_router.py:38-52`: `is_not_primary()` branch writes additions and corrections). So `add_word_to_db` and `update_word_in_db` do not run for a contributor, and the detector rebuild worker (`gui2/database_manager.py:800-847`, a private full headword load) is not triggered by a contributor save.
- Pass1Add has a "refresh DB" click handler: `new_db_session()` then `mark_corpus_stale()` (`gui2/pass1_add_view.py:243-246`). The next `load_corpus()` (any call to `make_inflections_lists`, `gui2/pass1_auto_controller.py:120,198`) builds a second full corpus. The detector keeps its own reference to the first rows (`tools/synonym_variant.py:889`), so both may stay in memory. Not measured: variant `corpus_reload` in the plan measures it.

## Result of batch 1 and what it changed (2026-11-02)
- `columns_no_sets.md`: with the inflection-set consumer left out (the L5 case), the detector needs 15 columns plus `id`, and none of them is an inflection column.
- Hypotheses disproved by batch 1 (`laptop.jsonl`, 57 rows): L2 direct sets (276.2 MB against 234.3 MB for today's step), L4 interned word finder (201.8 MB against 172.1 MB), "refresh DB builds a second corpus" (+172.5 MB, not +677 MB).
- Whole-build totals that held: `contributor_today` 1,386.3 MB (the earlier staircase: 1,385.6 MB); `warm_today` 1,114.3 MB; the inflection sets cost 272.0 MB in the whole build (`contributor_today` − `warm_today`).
