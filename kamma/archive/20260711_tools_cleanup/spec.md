# Spec: tools/ folder cleanup and refactor (#157)

## Goal
`tools/` is supposed to hold modules used globally across the project. Audit found
~97 py files (~26.7k LOC), 2 subpackages, 9 data files. Most are genuine shared
tools; a minority are dead files or standalone scripts that belong in `scripts/`.

Phases:
1. delete dead files
2. move the two true orphan scripts to `scripts/`
3. proper module docstrings for every kept file that lacks one
4. tests locking current outputs of kept modules (regression safety net)
5. light cleanup/refactor of what remains — no output changes unless an actual bug is found

## Audit method
- Sweep 1: `rg --hidden` for `from tools.X import` / `import tools.X` across the
  whole repo, grouped by area (db, exporter, gui2, scripts, tests, archive, …).
- Sweep 2: `rg --hidden` for direct-run path references (`tools/X.py`) in
  justfile, `.github/workflows/`, `scripts/bash/`.
- Content inspection of every zero/low-reference file.

## User rulings (2026-07-11)
- `bjt_source_sutta_example.py` stays in tools — right place, just unused.
- `tpr_codes_gen.py` stays in tools with `tpr_codes.json` — a .py and its .json
  are NEVER separated.
- `logo.py` stays — anything invoked by another module stays in tools.
- Tests must lock outputs before refactoring.
- Every file gets a proper docstring.

## Phase 1 — delete (approved; no live reference anywhere outside archive/)
| file | LOC | evidence |
|---|---|---|
| `dprint.py` | 30 | debug printer for obsolete `i.pali_root.*` attrs; zero refs |
| `time_log.py` | 94 | only importer is `archive/db/deconstructor/sandhi_splitter.py` |
| `unpickle.py` | 11 | zero refs |
| `fuzzy_search_regex.py` | 23 | zero refs; superseded by `fuzzy_tools.py` (used by gui2) |
| `link_generator.py` | 359 | zero refs |
| `hex_decoder.py` | 11 | zero refs; `__main__` demo only |
| `addition_class.py` | 93 | only archive (old gui) imports; live `scripts/add/add_additions_to_db.py` doesn't use it |
| `all_words_in_dpd.py` | 54 | only archive import |
| `add_encoding_declaration.sh` | 50 | one-off sed mass-edit script, zero refs |
| `writemdict/writemdict old.py` | — | dead copy inside vendored package |

## Phase 2 — move to scripts/ (approved; standalone, zero invokers of any kind)
| file | destination |
|---|---|
| `gatha_cleaner.py` | `scripts/fix/` |
| `missing_meanings.py` | `scripts/find/` |

NOT moved: `bjt_source_sutta_example.py`, `tpr_codes_gen.py`, `logo.py` (user
rulings above); `version.py`, `rss_feed.py`, `docs_update_*.py`,
`docs_changelog_and_release_notes.py`, `uposatha_day.py`, `css_manager.py`
(wired into justfile/CI/exporters).

## Phase 3 — docstrings
Add a proper module docstring (what it is, what uses it) to every kept tools
file missing one (~33 files: the ai_* family, utils, zip_up, version, translit,
tokenizer, tipitaka_db, spelling, sinhala_tools, goldendict_tools, fuzzy_tools,
fast_api_utils, exporter_functions, uposatha_day, unicode_char, etc.).

## Phase 4 — tests
Existing coverage in `tests/tools/`: ai_* family, configger, css_manager,
cst_book_translator, cst_source, deconstructed_words, docs_*, goldendict_exporter,
lookup_sync, phonetic_change_manager, proofreader, rss_feed, speech_marks,
sutta_codes, sutta_name_cleaning, tokenizer, utils, variants_manager,
compound_type_manager.

Add targeted behaviour tests (NOT frozen golden-masters) for untested kept
modules, prioritising pure-function modules whose output the cleanup could
silently change: pali_sort_key, pali_alphabet, clean_machine, sort_naturally,
niggahitas, superscripter, meaning_construction, date_and_time, tsv_read_write,
first_letter, diacritics_cleaner, fuzzy_tools, list_deduper,
negative_to_positive, unicode_char, sinhala_tools, translit, sanskrit_translit,
ipa, uposatha_day, degree_of_completion, lemma_traditional, headwords_clean_set,
db_search_string, clean_sentence, pos, zip_up, hex-free utils.
DB/IO/network-heavy modules (tipitaka_db, bold_definitions_search, cache_load,
tarballer, script_runner, goldendict_tools, fast_api_utils…) get light
structural tests only where meaningful — no live-db fixtures invented.

## Phase 4b — move INTO tools (user request 2026-07-11)
Audit of production cross-area imports found gui2 text-cleaning functions used
by exporters/scripts. Moved `clean_speech_marks`, `clean_text`,
`clean_commentary`, `remove_brackets`, `remove_bold_tags`, `clean_example` from
`gui2/dpd_fields_functions.py` to new `tools/example_cleaning.py`; updated
importers (gui2 ×2, exporter/analysis ×2, scripts/fix ×1); tests relocated to
`tests/tools/test_example_cleaning.py`. `book_codes` in gui2 noted as a weaker
optional candidate — not moved.

## Phase 5 — cleanup of what remains
- ruff check/format + pyright pass over every kept `tools/*.py`; fix real issues.
- Dead-function sweep inside kept modules (zero-caller functions removed,
  verified individually).
- Modern type hints / Path where trivially missing, per project rules.
- Constraint: byte-identical behaviour — no output changes unless an actual bug
  is found, and any bug found is reported before fixing.
- Out of scope: restructuring into subpackages (e.g. `tools/ai/`), touching
  `writemdict/` internals (vendored, pre-commit-excluded), moving
  single-consumer library modules.
