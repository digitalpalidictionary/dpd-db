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
- [x] `db_tests/single/add_word_family_finder.py` — find missing word families
  - **writes DB (1)** · refs: pickle in paths.py · last run: no pyc · git: 2025-09-21 · flags: bare print only
  - verdict: **move to `fixme/`** — the workflow (bare `rich.print` prompts + raw-`input()` clipboard-regex loop, 3 unrelated detection strategies bolted into one file) is not intuitive to use and needs a redesign, not a freshen. Moved script + its `add_word_family_finder.pickle` exceptions cache to `db_tests/single/fixme/`; removed the dead `tools/paths.py` `wf_exceptions_list` entry (only that file referenced it).
  - **Redesign notes for future rewrite** (not implemented — logged for whoever picks this up):
    - Split the single file's three independent detectors into separate entry points or an explicit menu — `find_in_family_compound` (interactive, writes DB), `find_in_construction` (read-only, clipboard-regex), `find_in_lemma_1` (read-only, clipboard-regex) currently share no UI pattern and are only chained by `main()`.
    - Replace the clipboard-regex-then-bare-`input()` steps (`find_in_construction`/`find_in_lemma_1`) with the same JSON-exceptions + lettered-menu TUI pattern already standardized this thread (e.g. `test_family_compounds_have_meaning_1.py`, `test_root_family_vs_construction_prefixes.py`) — show the candidate headword's `pos`/`meaning_combo` inline instead of requiring the user to paste a regex into another tool and eyeball the DB.
    - Replace the pickle exceptions cache with JSON (project convention elsewhere) registered in `tools/paths.py`, keyed by `lemma_1` — the old `.pickle` is preserved in `fixme/` in case its accumulated exceptions are worth porting forward.
    - Consider whether `gui2`'s family-tools views (`family_root`/`family_word` editing) already cover part of this — if so, the rewrite may only need the detection logic (`build_word_family_dict`, `find_in_construction`, `find_in_lemma_1`), not a new standalone interactive shell.
  - → verify: file + pickle moved to `fixme/` ✓; `tools/paths.py` dead entry removed ✓; ruff+pyright clean on `tools/paths.py` ✓
- [x] `db_tests/single/test_antonyms.py` — missing/wrong/extra antonyms
  - **writes DB (9!)** · refs: `test_antonyms.json` in paths.py · last run: 2026-02-01 (pytest) · git: 2026-06-11 · flags: 2 FIXME (lines ~102, 161)
  - verdict: **move to `fixme/`** — user found it too complicated to even understand, let alone use safely: a `GlobalVars` class driving a nested nine-branch `check_w1`/`update_w2` state machine, nine possible DB writes per mismatch, unfixed FIXMEs (antonym match never actually verified before branching; multi-antonym case just prints a warning and does nothing), plus ~70 lines of dead commented-out alternate handlers. Moved script + `test_antonyms.json` to `db_tests/single/fixme/`; removed the dead `tools/paths.py` `antonym_dict_path` entry (only that file referenced it).
  - **Redesign notes for future rewrite** (not implemented — logged for whoever picks this up):
    - Same complaint pattern as `add_word_family_finder.py` above: one giant function branching on multiple simultaneous conditions (match/mismatch × pos-match/mismatch × has/hasn't-antonym) is hard to reason about interactively. Split into one check per condition, presented one at a time, rather than a single dense cascade.
    - Fix the FIXMEs as part of the rewrite, not as a patch to the old structure: actually verify the antonym match before branching (line ~102), and decide + implement real handling for words with multiple antonyms (line ~161) instead of a print-and-skip.
    - Standardize on the same lettered-menu + JSON-exceptions pattern used elsewhere this thread (e.g. `test_root_family_vs_construction_prefixes.py`) rather than the bespoke `u/d1/a/r/m/d2/e/p` menu, so the tool matches the muscle memory built up across the other freshened `single/` scripts.
    - Delete the dead commented-out code (`antonym_doesnt_exist`, `add_antonym_back`, `delete_antonym`, `update_w2_or_add_exceptions`) rather than carrying it into the rewrite — none of it is wired up, and it doesn't represent a design the user wants either.
  - → verify: file + json moved to `fixme/` ✓; `tools/paths.py` dead entry removed ✓; ruff+pyright clean on `tools/paths.py` ✓
- [x] `db_tests/single/test_bahubbihis.py` — bahubbīhi compound characteristics
  - **writes DB (1)** · refs: json in paths.py · last run: 2026-02-01 (pytest) · git: 2026-06-11 · flags: **5 FIXME (lines ~122–126)**, uses `tools.terminal_highlights`
  - verdict: **consolidate + move to `fixme/`**. Discovery mid-triage: `scripts/find/bahubbīhi_finder.py` (created 2026-02-26) was already a cleaner, partial rewrite of this same tool — same `GlobalVars`/`bahubbihi_dict` shape, sharing the same `test_bahubbihis.json` data file via `bahubbihi_dict_path`, but with 2 of 5 detection strategies uncommented/cleaned (noun-ending + relative-pronoun, `sa +` prefix), added skip-already-reviewed guards, and a `(q)uit` option — the other 3 strategies (adj-ending, pp-ending, taddhita `ka|ika|aka`) were dropped, not just commented out. User tested the newer script and confirmed it should replace this row's file rather than being freshened separately. Replaced `db_tests/single/test_bahubbihis.py` content with `scripts/find/bahubbīhi_finder.py`, deleted the now-duplicate `scripts/find/bahubbīhi_finder.py` (unreferenced by justfile/README/other code), then moved the consolidated file + `test_bahubbihis.json` to `db_tests/single/fixme/`. Removed the dead `tools/paths.py` `bahubbihi_dict_path` entry (only the fixme file references it now).
  - **Redesign notes for future rewrite** (not implemented — logged for whoever picks this up):
    - Even the newer/cleaner version still needs help per the user — same class of complaint as the other rows above: only 2 of the 5 documented bahubbīhi heuristics are implemented, the other 3 were quietly dropped rather than fixed.
    - When rebuilding, decide deliberately whether the dropped heuristics (adj-ending, pp-ending relative-pronoun checks; taddhita `ka/ika/aka` suffix check) are worth reviving, rather than letting them silently disappear again in a future pass.
    - Same standardization note as the other `fixme/`-bound rows: adopt the shared lettered-menu/JSON-exceptions pattern once one is settled on for this thread's rewrites, so all these tools feel consistent.
  - → verify: `scripts/find/bahubbīhi_finder.py` no longer exists ✓; consolidated file + json moved to `fixme/` ✓; `tools/paths.py` dead entry removed ✓; ruff+pyright clean on `tools/paths.py` ✓
- [x] `db_tests/single/test_bold_example_inflections.py` — bold word in examples must be a real inflection
  - **writes DB (1)** · refs: `test_bold.json` (`bold_example_path`) in paths.py · last run: 2026-03-20 (pytest) · git: 2026-06-11
  - verdict: **keep** + improve: `printer()` (the shared failure-review prompt for tests 1/2/4/5/6/8) rebuilt to the thread's standard `(e)xception`/`(q)uit`/Enter-for-next menu — previously mislabeled `(p)ass` (which actually wrote a permanent exception) and `e(x)it`; now shows the full example sentence (`example_1`/`example_2`, whichever is being tested) with the bold word rendered via `terminal_bold` so the user can see it in context instead of just the isolated clean bold word. Removed dead unused `check_username()` (and its now-unused `config_test` import) — defined, never called anywhere. Renamed the exceptions data file `test_bold.json` → `test_bold_example_inflections.json` (project convention: exceptions filename matches its script's filename) and updated `tools/paths.py`'s `bold_example_path` accordingly. Freshened: docstrings on all previously-bare functions/methods, modern type hints (`-> None`, `"GlobalVars"` forward refs), fixed a stray doubled-quote docstring typo in `test4`, renamed `get_headword`'s `id` param to `headword_id` (no builtin shadowing).
  - **Bug found live during user triage, fixed:** `counter`/`counter_total` both started at 1 instead of 0, and `printer()` displayed the count before incrementing `counter` — inflated the total by 1 and showed the last item's numerator one short (e.g. `"2 / 3"` for what should have been `"2 / 2"`). `test7`'s own separate `counter_total` increment had the same class of bug (fired unconditionally on both passes instead of only during the pass-1 tally, and never pre-incremented `counter` for its own display). Fixed both call sites to increment before display and only tally during pass 1.
  - NOTICED — NOT TOUCHING: `test7` still falls through to `test8` even after flagging a double-letter problem (both during pass-1 tallying and pass-2 when the user answers "n") — a word can get flagged under two different tests. Separate pre-existing design quirk from the numbering bug, left alone.
  - User then asked why headword id 89749 (`mukhapīḷakā`) flagged under `test8` — confirmed as a genuine data gap, not a script bug: `hw.inflections_list` is `[]` for this headword (inflections not yet generated), so any bold word for it necessarily fails every inflection-matching test and falls through to `test8`. Script logic is correct; this headword just isn't ready for this test yet.
  - → verify: ruff+pyright clean ✓; user confirmed the numbering fix and the test8 flag explanation live
- [x] `db_tests/single/test_digu.py` — numerals in compounds → compound_type digu
  - read-only · refs: json in paths.py · last run: 2026-03-20 (pytest) · git: 2026-06-11
  - verdict: **keep** + improve: `printer_pass2` menu converted from mislabeled `(p)ass`/`e(x)it` to the thread's standard `(e)xception`/`(q)uit`/Enter-for-next pattern (`update_json` already behaved as an exception write, just mislabeled). Exceptions file (`test_digu.json` → `digu_json_path`) was already correctly registered in `tools/paths.py` and already matched the script's filename — no change needed there. Fixed a latent type/runtime mismatch: `GlobalVars.json` was typed `dict[int, str]` and written with an int key (`self.json[self.i.id] = ...`) but always read back with a string key (`str(g.i.id) not in g.json`) — since JSON round-trips all keys as strings, this was silently inconsistent; retyped to `dict[str, str]` and made `update_json` write `str(self.i.id)` consistently. Corrected the module docstring, which claimed the script "change[s] the compound type to digu" — it's actually read-only; nothing writes `compound_type`. Freshened: docstrings + `-> None`/`-> bool` type hints on every previously-bare function/method.
  - → verify: ruff+pyright clean ✓; user confirmed ✓
- [x] `db_tests/single/test_hyphenations.py` — find super-long words and hyphenate
  - **writes DB (1)** · refs: `test_hyphenations.txt` scratchpad in paths.py · last run: 2026-02-21 (pytest) · git: 2026-06-11 · flags: 1 FIXME; **print strings claim to update `test_hyphenations.json` but the script uses the `.txt`** — orphaned 158 KB json + lying log messages to resolve here
  - verdict: **move to `fixme/`** — user confirmed out of date. Moved script + its `test_hyphenations.txt` scratchpad to `db_tests/single/fixme/`; removed the dead `tools/paths.py` `hyphenations_scratchpad_path` entry (only this file referenced it). Archived the genuinely orphaned `test_hyphenations.json` (158 KB, last touched 2025-05-21) to `archive/db_tests/single/` — it's a dead legacy data file from before the switch to `tools/speech_marks.json`/`SpeechMarkManager` (old flat `clean_word: single_variant` shape vs. the live `clean_word: [variants]` shape), unreferenced by any code, distinct from the still-live scratchpad `.txt`.
  - **Issues found, logged for whoever rebuilds this** (not fixed — file is going to `fixme/`, not being improved in place):
    - The 3 print messages claiming to update `"test_hyphenations.json"` (lines ~230, 239, 300 pre-move) are simply wrong — the script actually writes through `SpeechMarkManager` to `tools/speech_marks.json`. Needs correcting if/when revived.
    - Existing FIXME (module-level comment near `find_variations`): unhandled case where a word's saved hyphenation in `speech_marks.json` differs from the version found live in the DB.
    - `main()` shells out to `subprocess.Popen(["code", ...])` to open two files in VS Code on every run — an editor-specific side effect baked into a data script; worth reconsidering in a rewrite (e.g. just print the paths).
    - `process_long_words`'s menu (`number`/`m`anual/`o`k/`p`ass/e`x`it) predates this thread's standardized `(e)xception`/`(q)uit` convention — another candidate for realignment if rebuilt, though its extra actions (multi-choice, manual clipboard/editor paste-back) are more complex than a simple exception list and may not map 1:1.
  - → verify: script + scratchpad moved to `fixme/` ✓; orphaned json archived ✓; `tools/paths.py` dead entry removed ✓; ruff+pyright clean on `tools/paths.py` ✓
- [x] `db_tests/single/test_idioms.py` — component words contain correct family idiom
  - **writes DB (1)** · refs: `test_idioms.json` in paths.py · last run: 2026-02-01 (pytest) · git: 2026-06-11
  - verdict: **move to `fixme/`** — user found it too hard to understand how it works. Moved script + `test_idioms.json` to `db_tests/single/fixme/`; retargeted (not removed) `tools/paths.py`'s `idioms_exceptions_dict` to the new `fixme/` location so the file stays self-consistent and pyright-clean while parked. Issues logged inline as a `# FIXME` block at the top of the file (per updated process, see note below), not just in this plan.
  - **Process change (2026-07-12):** user asked that fixme issues be logged **inside the files themselves** going forward, not only in `plan.md` — they may not be working from this plan when they eventually revisit these scripts. Retrofitted inline `# FIXME` blocks onto the other 4 files moved to `fixme/` earlier in this session (`add_word_family_finder.py`, `test_antonyms.py`, `test_bahubbihis.py`, `test_hyphenations.py`) with the same issues already recorded in their rows above. Editing those files to add the notes meant they now "own their lint" per project rules — this exposed that fully deleting their `tools/paths.py` entries (as done in those earlier rows) left dangling `pth.xxx` references with real pyright errors. Fixed by **retargeting** those entries to their new `fixme/` paths instead of deleting them (`wf_exceptions_list`, `antonym_dict_path`, `bahubbihi_dict_path`, `hyphenations_scratchpad_path`) — same pattern now used for `idioms_exceptions_dict`. All 5 `fixme/`-parked files + `tools/paths.py` are ruff+pyright clean.
  - → verify: script + json moved to `fixme/` ✓; inline FIXME note added ✓; `tools/paths.py` retargeted (not dangling) ✓; ruff+pyright clean on all 5 fixme files + `tools/paths.py` ✓
- [x] `db_tests/single/test_maha_compounds.py` — mahā compound_type + construction
  - **writes DB (1)** · refs: `test_maha_exceptions.json` in paths.py · last run: 2026-03-20 (pytest) · git: 2026-06-11
  - verdict: **archive** — user confirmed fully superseded by gui2's inline family compound autofill. Moved script + `test_maha_exceptions.json` to `archive/db_tests/single/`; removed the now-dead `tools/paths.py` `maha_exceptions_list` entry (unlike `fixme/` rows, an archived/retired file isn't expected to run again, so no retargeting needed).
  - → verify: script + json moved to `archive/db_tests/single/` ✓; `tools/paths.py` dead entry removed ✓; ruff+pyright clean on `tools/paths.py` ✓
- [x] `db_tests/single/test_neg_compounds.py` — find negative kammadhārayas
  - **writes DB (1)** · refs: exceptions json in paths.py · last run: 2026-02-21 (pytest) · git: 2026-06-11
  - verdict: **keep** — user confirmed it works nicely. Freshened only (no behavior change): docstrings + `-> None` type hints on all previously-bare functions, `add_exception`'s `id` param renamed to `headword_id` (no builtin shadowing).
  - NOTICED — NOT TOUCHING: the `(m)anual (a)utomatic (e)xception` menu has no quit option, and the confirm step (`press x to reject or any other key to continue`) commits on literally any key besides `x`. User said it works nicely as-is; didn't touch since verdict was a plain freshen, not improve.
  - → verify: ruff+pyright clean ✓
- [x] `db_tests/single/test_sukha_dukkha_finder.py` — sukha/dukkha compounds lacking antonyms
  - 114 lines · read-only · refs: json in paths.py · last run: 2026-03-20 (pytest) · git: 2026-06-11 · flags: uses `tools.goldendict_tools`
  - verdict: **keep** — user confirmed it works fine. Freshened only (no behavior change): docstrings + type hints (`DpdHeadword`, `list[str]`, `-> bool`, `-> None`) on all previously-bare functions.
  - → verify: ruff+pyright clean ✓
- [x] `db_tests/single/test_theragatha_filler.py` — fill missing auto-added monk names in Theragāthā
  - 73 lines · read-only · refs: pickle in paths.py · last run: 2026-02-21 (pytest) · git: 2026-06-15 · flags: bare print; prior pickle read≠write bug already fixed (kamma archive)
  - verdict: **keep** + improve: converted the `done_list` store from pickle to JSON (human readable/editable) — converted the existing pickle's 17 recorded ids into `test_theragatha_filler.json`, updated `tools/paths.py`'s `theragatha_filler_path` to the new `.json` path, deleted the old pickle. Menu reformatted to this thread's standard: word shown first, then `(q)uit or Enter to continue` on its own line (was `x` to exit shown before the word, any key = continue). Freshened: docstrings + type hints on all previously-bare functions, renamed `load_pickle`/`dump_pickle` to `load_done_list`/`save_done_list`.
  - → verify: ruff+pyright clean ✓
- [x] **Phase 2 wrap:** all rows verdicted; `uv run ruff check db_tests/single/` + `uv run pyright db_tests/single/` clean; `uv run pytest tests/db_tests/` passes; justfile recipes for surviving scripts intact
  - → verify: `uv run ruff check db_tests/single/` — all checks passed ✓; `uv run pyright db_tests/single/` — 0 errors ✓; `uv run pytest tests/db_tests/` — 39 passed ✓; all 4 justfile recipes (`add_synonym_variant_single/multi/del.py`, `add_phonetic_variants.py`) point at intact files ✓

## Phase 3 — `db_tests/gui/` (formerly `db_tests_gui/`, 8 files — problem children begin)

Flet mini-app last run 2026-03-29 (>3 months). Central question at each row: retire, fold into gui2, or keep standalone.

**Directory move (2026-07-12):** user asked to relocate the whole folder from top-level `db_tests_gui/` to `db_tests/gui/`, nesting it under `db_tests/` alongside `single/` — this also brings the real tree in line with `docs/technical/project_folder_structure.md`, which never listed `db_tests_gui/` as a top-level folder at all. Moved all files (`main.py`, the 6 `add_*.py` editors, `add_antonyms_sync_dict.json`, `add_hyphenations.json`, `README.md`); updated `main.py`'s sibling imports (`db_tests_gui.xxx` → `db_tests.gui.xxx`); updated `tools/paths.py` (`add_antonyms_sync_dict` path + section comment); updated docstring mentions in `tools/goldendict_tools.py` + `tools/negative_to_positive.py`; moved `archive/db_tests_gui/` → `archive/db_tests/gui/`; added the previously-missing `gui/` + `single/` entries to `docs/technical/project_folder_structure.md`'s tree and folder-details. All references below now use the new path.

- [x] `db_tests/gui/internal_tests.py` — Flet form for editing column-rule tests
  - GUI · refs: none · last run: no pyc; git: 2025-03-24 · flags: **buttons never wired — non-functional prototype**; duplicates gui2's Tests tab (`gui2/tests_tab_view.py` + controller, backed by `DbTestManager`); `print("Next")` stub
  - verdict: **archive** — user confirmed gui2's Tests tab works nicely and this is unused elsewhere. Confirmed none of the 6 action buttons (Run/Stop/Edit/Update/Add/Delete) are wired to any handler; confirmed no code imports this module. Moved to `archive/db_tests/gui/`.
  - → verify: file moved to `archive/db_tests/gui/` ✓; no importers ✓
- [x] `db_tests/gui/main.py` — Flet sidebar dispatching the 6 add_* editors
  - GUI · `ft.app` at import · last run: no pyc; git: 2025-10-29 · flags: **3 pyright errors (lines 110, 118)**; dispatch key `"add_antonyms sync"` contains a space (fragile); commented-out dead lines
  - verdict: **keep** — fixed the 3 pyright errors: kept direct references to the `appbar`/`appbar_title`/`menu_button` objects constructed in `main()` instead of re-reading them back through the optionally-typed `page.appbar`/`page.appbar.leading`, so no behavior change, just proper typing. Sibling imports updated for the directory move (see note above).
  - NOTICED — NOT TOUCHING: the `"add_antonyms sync"` dispatch key (embedded space, inconsistent with sibling `add_fc_*` keys) and the commented-out title-bar lines — cosmetic, out of scope for "get it working."
  - → verify: ruff+pyright clean ✓ (0 errors, was 3)
- [~] `db_tests/gui/add_antonyms.py` — add missing antonyms interactively
  - **writes DB (1)** · last run: 2026-03-29 · git: 2026-06-11 · flags: **imports from `archive/db_tests/old_tests_DELETE.py`** — live dependency on an archived "DELETE" module; resolve here (inline the needed code or properly relocate it)
  - verdict: **keep** + fix. This was the one script in Phase 3 with a genuinely live (read AND write) dependency on `archive/db_tests/old_tests_DELETE.py` — its "Exception" button actually persisted to `db_tests_columns.tsv` via that archived module's `InternalTestRow`/`make_internal_tests_list`/`write_internal_tests_list`, a real landmine (file literally named "DELETE", sitting in `archive/`, silently load-bearing). Replaced with the modern, already-tested `db_tests/db_tests_manager.py::DbTestManager` (used by gui2 ×4 elsewhere) — its own `add_exception(test_name, id)` does the same job properly. Confirmed no other live code imports the old archived module (only another archived file, `archive/gui/functions_tests.py`, references it — archive-to-archive, harmless). Removed the now-dead `make_antonym_set()`/`self.fc_set` (assigned, never read — copy-paste leftover from the family_compound siblings). Fixed the module docstring, which wrongly said "Add missing family compounds and idioms" (copy-paste artifact — this script adds antonyms).
  - → verify: no imports from `archive/` remain ✓; ruff+pyright clean ✓; sibling-module import check passes ✓ — user to launch `main.py` and confirm the "Add antonyms" flow (including the Exception button) still works end-to-end
- [ ] `db_tests/gui/add_antonyms_sync.py` — antonyms from existing words; caches to `add_antonyms_sync_dict.json`
  - **writes DB (1)** · data json in paths.py · last run: 2025-12-02 · git: 2026-06-11 · flags: bare print · user: "actually the only script that really does any work here" (leaning keep)
  - verdict: ____
  - → verify: as above
- [x] `db_tests/gui/add_family_compound_neg.py` — family compounds/idioms from negative words
  - **writes DB (1)** · uses `tools.negative_to_positive` · last run: 2026-03-29 · git: 2026-03-04 · flags: no entry point (only via main.py)
  - verdict: **needs real feature work** (JSON exceptions list, currently a hardcoded `neg_exceptions = [...]` list at module level) — **spun off into a new dedicated thread** rather than done as a triage-scope freshen (see note below). This row and its two siblings are "parked pending new thread", not fully verdicted here.
  - → verify: n/a — tracked in new thread
- [x] `db_tests/gui/add_family_compound_su_dur.py` — family compounds/idioms for su/dur/sa
  - **writes DB (1)** · last run: 2026-03-29 · git: 2026-03-04
  - verdict: **needs real feature work** (same exceptions-list treatment as `_neg`; also its exceptions lookup misses the separate `family_compound empty sa` row in `db_tests_columns.tsv` even though it processes `sa`-prefixed compounds too) — spun off, see note below.
  - → verify: n/a — tracked in new thread
- [x] `db_tests/gui/add_family_compound_taddhita.py` — family compounds/idioms from taddhita
  - **writes DB (1)** · uses `tools.tsv_read_write` · last run: 2026-03-29 · git: 2026-03-04
  - verdict: **needs real feature work** (same treatment) — spun off, see note below.
  - → verify: n/a — tracked in new thread
- [x] `db_tests/gui/add_hyphenations.py` — add hyphenations; manages `speech_marks.json`
  - **writes DB (1)** · last run: 2026-03-29 · git: 2026-06-11 · flags: no module docstring; orphaned sibling `add_hyphenations.json` (22 B, no consumer) to resolve here
  - verdict: **keep** + fix crash. Root cause found live: `load_hyphenations_dict()`/`save_hyphenations_dict()` were wired to `pth.speech_marks_path` (`tools/speech_marks.json`, a different tool's data, shape `{word: [variants]}`) instead of this script's own sibling `add_hyphenations.json` (shape `{"max_length": N, "exceptions": {...}}`) — hence `KeyError: 'max_length'` on the very first run, since `speech_marks.json` has neither key. Registered a new `tools/paths.py` entry (`add_hyphenations_config_path`) pointing at `db_tests/gui/add_hyphenations.json`, rewired both methods to it, and seeded the file with the missing `"exceptions": {}` key (it only had `"max_length": 20`, so it would have crashed again one property later even with the path fixed).
  - → verify: ruff+pyright clean ✓; orphan json now has a real consumer + paths.py entry ✓ — user to confirm it runs without the KeyError
- [ ] **Phase 3 wrap:** folder's fate coherent (README matches reality; if the whole app is retired, folder archived and `tools/paths.py` entries removed)
  - → verify: `uv run ruff check db_tests/gui/` + `uv run pyright db_tests/gui/` clean (or folder gone); gui2 unaffected

**New thread spun off (2026-07-12):** the 3 `add_family_compound_*.py` scripts need a real feature — replacing ad hoc/read-only exceptions handling (a hardcoded list in `_neg`; a read-only `db_tests_columns.tsv` lookup with no write-back in `_taddhita`/`_su_dur`) with a proper writable JSON-exceptions system + UI button, consistent across all three. This is design/build work, not a freshen, so it doesn't fit this triage thread's scope — tracked in a new dedicated thread (name TBD by `/kamma:1-plan`) seeded with this session's research: the exact current mechanism in each file, the live seed data already sitting in `db_tests_columns.tsv` (`family_compound empty neg` = 17 ids vs. the hardcoded list's 9; `family_compound empty taddhita` = 32 ids; `family_compound empty su dur nir` = 3 ids **plus** a separate never-consulted `family_compound empty sa` = 3 ids that `_su_dur` should also be checking since it handles `sa`-prefixed compounds).

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

- [ ] Clear stale `__pycache__` entries for deleted/moved modules (evidence no longer needed once triage is complete): `db_tests/__pycache__` (add_family_compound_and_idiom/2, add_family_compound_neg, add_family_compound_taddhita, helpers, internal_tests, old_tests_DELETE, test_allowable_characters), `single/__pycache__` (add_synonym_multi, add_synonym_variant), `gui/__pycache__` (regenerated post-move, check for stale entries)
  - → verify: no `.pyc` without a matching live `.py`
- [ ] Add pytest coverage decided during triage (rows marked "pytest: yes") under `tests/db_tests/`, mirroring source paths
  - → verify: `uv run pytest tests/db_tests/` passes; new tests fail meaningfully if logic breaks
- [ ] Update `db_tests/README.md`, `db_tests/single/README.md`, `db_tests/gui/README.md` (already updated for the directory move, re-check for post-triage reality) to post-triage reality; check `docs/technical/project_folder_structure.md` (already updated for the directory move)
  - → verify: READMEs list only existing files/entry points
- [ ] Final sweep: `uv run ruff check db_tests && uv run pyright db_tests && uv run pytest tests/`
  - → verify: all pass; report summary table of verdicts to user (report-only — user commits)

## Review fixes (2026-07-12)

Post-commit review of `c0a2d772`/`3946bb9c`/`1f352192` found and fixed:

- [x] `tools/phonetic_changes.tsv:86` (`ñj + t` rule) lost its `exceptions` column in the `not_in_lemma` migration (6 fields vs 7) — padded to 7 columns with `x` placeholders
- [x] `tools/phonetic_change_manager.py` `_update_exception_in_tsv`: guard was still `len(cols) > 5` while writing `cols[6]` → IndexError on short rows — now `len(cols) > 6`
- [x] `test_pali_1_2_difference.py` + `test_numbering_anomalies.py`: `prompt()` returns 0 on (e)xception so the summary doesn't count excepted items; pali_1_2 prompt now shows the `q`uit option it already accepted
- [x] `test_root_family_vs_construction_prefixes.py`: `GlobalVars` DB load moved from class level (fired at import) into `__init__`
- `add_synonym_variant_multi` row: verdict recorded 2026-07-12 (**keep**) after user confirmed the `1f352192` (t)extual option works; docstring polish added
