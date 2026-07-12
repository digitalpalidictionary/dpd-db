# Plan: tools/ folder cleanup (#157)

## Phase 0 — audit
- [x] Import sweep of all tools modules grouped by repo area (`rg --hidden`)
- [x] Direct-run reference sweep (justfile, CI workflows, scripts/bash)
- [x] Content inspection of zero/low-reference files
- [x] Write spec with delete/move/keep classification
- [x] User approval with rulings: keep bjt_source_sutta_example, tpr_codes_gen
      (+json), logo in tools; add tests + docstrings to scope

## Phase 1 — delete dead files
- [x] Delete the 10 files listed in spec Phase 1
      → verified: `rg --hidden` sweep clean; full pytest 1471 passed

## Phase 2 — move the two orphan scripts
- [x] Move gatha_cleaner.py → scripts/fix/, missing_meanings.py → scripts/find/
- [x] ruff + pyright on both moved files — fixed 6 pre-existing pyright errors
      (None-guards, raw regex string); BUG FOUND+FIXED: find_missing_meanings()
      ignored its `level` parameter (hardcoded level=1)
      → verified: full pytest 1471 passed

## Phase 3 — docstrings
- [x] Added module docstring to all 33 kept tools files missing one (3 parallel
      agents + 2 by hand). Also fixed pre-existing pyright errors in
      goldendict_path.py (return type Path | None + None-safe config_read) and
      sinhala_tools.py (str annotation); corrected wrong `Path | str` annotation
      in goldendict_exporter.py:322
      → verified: ruff check/format + pyright 0 errors on all touched files

## Phase 4 — tests (lock outputs before refactor)
- [x] 27 new test files in tests/tools/ covering all previously-untested
      pure-function modules (5 agents; first batch died on session limit and
      was relaunched on sonnet). All modules testable without db — nothing skipped.
- [x] Suspected bugs locked + reported: uposatha_day NoSectionError uncaught;
      clean_sentence mutates global pali_alphabet + no-op replaces; pos.py
      "var" in INDECLINABLES but not POS; find_stem_pattern dead branches
      → verified: full suite 1730 passed at phase end

## Phase 4b — move INTO tools (user request)
- [x] gui2 clean_example family (6 funcs) → tools/example_cleaning.py;
      updated importers in gui2 ×2, exporter/analysis ×2, scripts/fix ×1;
      tests consolidated into tests/tools/test_example_cleaning.py
      → verified: lint clean, 242 tests pass, no stale-import sweep hits

## Phase 5 — cleanup
- [x] Dead-function removals (each verified zero-caller, incl. docs/kamma):
      configger: config_test_section, print_config_settings ·
      cst_sc_text_sets: extract_sutta_from_file, make_cst_text_set_sutta,
      make_cst_text_list_sutta, make_cst_text_set_from_file,
      make_cst_text_list_from_file, make_sc_text_list, make_other_pali_texts_set ·
      fast_api_utils: request_bold_def_server · sinhala_tools: si_grammar +
      gram_dict · superscripter: superscripter_html · tarballer:
      extract_tarball_to_paths · tokenizer: split_words_keep_dash +
      remove_dirty_characters_keep_dash · tsv_read_write: append_tsv_list,
      read_tsv_as_dict_with_different_key · bjt: save_bjṭ_text ·
      lemma_traditional: make_lemma_trad_si. Corresponding new tests removed.
      KEPT: tipitaka_db.sqlite_engine_connect (live @event.listens_for hook).
- [x] ruff + ruff format + pyright clean over ALL tools/*.py (ex writemdict);
      fixed niggahitas E712, modernized stray List/Set hints
- [x] Pre-existing pyright fixes: goldendict_path (Path | None),
      goldendict_exporter:322 (wrong Path | str annotation), sinhala_tools,
      missing_meanings (None guards; BUG: ignored level param — fixed)
      → verified: full `uv run pytest tests/` 1721 passed

## Follow-ups (user rulings 2026-07-12)
- [x] Bug 2 FIXED: clean_sentence now builds the letter set from a local copy
      of pali_alphabet (user: "work on a copy"); dead no-op text.replace lines
      removed; test fixture replaced with a no-mutation assertion
- [x] Bug 3 WONTFIX per user: uposatha_day NoSectionError fallback not needed
      (locked test documents current behaviour)
- [x] Repaired pre-existing test break at HEAD: commit 1f352192 (parallel
      db_tests thread) renamed without→not_in_constr in phonetic_change_manager
      but left tests/tools/test_phonetic_change_manager.py asserting the old
      key — fixtures and assertions updated to new schema (+not_in_lemma)

## Wrap-up
- [x] docs/technical/project_folder_structure.md — no change needed (no
      folder-level changes); tools/README.md generic, no stale refs
- [x] Review: two parallel sonnet subagents (CodeRabbit + kamma review-phase
      audit) — see review.md. Verdict PASS. 3 more CodeRabbit fixes applied
      (niggahitas type hint, gatha_cleaner type hints/docstring/typing,
      missing_meanings cumulative-level bug + type hints). One item flagged
      out of scope: tools/sanskrit_translit.py HK/SLP1 mapping looks swapped —
      not fixed, needs its own deliberate PR.
- [x] Full suite 1722 passed, 16 deselected. Committed as 5875fdc0 (this
      thread's files only — parallel db_tests_triage thread's uncommitted
      files excluded).

## Follow-up: sanskrit_translit HK/SLP1 fix (user sign-off 2026-07-12)
- [x] Fixed tools/sanskrit_translit.py hk_translit swapped S/z mapping
      (z: ś, S: ṣ — matches standard HK convention and the T/D/N retroflex
      capitalization pattern). Confirmed hk_translit has zero production
      callers (test-only); slp1_translit (the one exporter/mobile actually
      uses) was already correct and untouched — zero live output change.
- [x] Updated tests/tools/test_sanskrit_translit.py's two locked-buggy-behaviour
      cases to correct expected values (kRSNa -> kṛṣṇa; zaTkoNa case replaced
      with zrI -> śrī to properly exercise the z->ś mapping)
- [x] Lint/pyright clean; full suite 1722 passed, 16 deselected
- [ ] Commit as its own follow-up commit
