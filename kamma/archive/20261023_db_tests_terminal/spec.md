# Spec: Turn the six db_tests GUI tools into terminal scripts

**Thread:** 20261023_db_tests_terminal
**Date:** 2026-10-23
**GitHub issue:** none given. Commits use `#157` (the db_tests tidy-up) unless the user says otherwise. This is an assumption.

> Self-contained: this spec and `plan.md` hold everything a fresh agent needs.

## Overview

`db_tests/gui/` is a Flet app with a side menu and six review tools. The user finds it
unusably slow, especially "add antonyms sync": the terminal prints the next answer at
once, but the window takes a very long time to show it. The user decided (2026-10-23)
to drop the GUI. Each tool becomes a separate terminal script in `db_tests/single/`,
in the style of the existing interactive scripts there (for example
`test_digu.py`: `pr` printer, `rich` print, `input()`, `pr.tic()/toc()`,
`if __name__ == "__main__": main()`). Same logic, same answers, same data files, no GUI.

Nothing connects the six tools except the menu in `gui/main.py`. **Each script stands
alone. No shared helper module.** Some copy-paste between scripts is accepted on purpose.

## What it should do

Six new scripts (plus six JSON files) in `db_tests/single/`, each runnable as `uv run python -m db_tests.single.<name>`:

| New script | Replaces | Selects | Proposes | Writes on commit | Exception stored in |
|---|---|---|---|---|---|
| `add_antonyms.py` | `gui/add_antonyms.py` | `meaning_1` and `neg` and no `antonym`, not excepted; sorted by `pali_sort_key(lemma_1)` | `make_positive(i)` | `antonym` | `add_antonyms.json` |
| `add_antonyms_sync.py` | `gui/add_antonyms_sync.py` | each headword with an `antonym`; its antonym's twin (same `lemma_clean` and `pos`) that lacks the reverse link | the twin's antonyms plus the source's `lemma_clean`, Pāḷi-sorted | twin's `antonym` | `add_antonyms_sync_dict.json` (source id → excepted twin ids) |
| `add_family_compound_neg.py` | `gui/add_family_compound_neg.py` | `meaning_1`, no `family_compound`, `neg`, `pos` not sandhi/idiom, not excepted | `make_positive(i)` | `family_compound` and `family_idioms` | `add_family_compound_neg.json` |
| `add_family_compound_su_dur.py` | `gui/add_family_compound_su_dur.py` | `meaning_1`, `pos` not sandhi/idiom, no `family_compound`, `construction` starts with su/dur/sa/nir; sorted by `pali_sort_key` | name, "of/from" target, or `lemma_clean` | `family_compound` and `family_idioms` | `add_family_compound_su_dur.json` |
| `add_family_compound_taddhita.py` | `gui/add_family_compound_taddhita.py` | `meaning_1`, `derivative == "taddhita"`, no `family_compound`, not excepted | same as su_dur | same | `add_family_compound_taddhita.json` |
| `add_hyphenations.py` | `gui/add_hyphenations.py` | long dirty hyphenated words grouped by clean word | the single dirty form, or the user's pick | exceptions in `add_hyphenations.json`; replaces the variants in `example_1`, `example_2`, `commentary` | `add_hyphenations.json` |

**Prompt rule (the four review scripts and sync):** the screen shows the item and the proposed value, then one prompt.
Enter commits the proposed value. Typing other text commits that text. `e` = add exception, `p` = pass,
`q` = quit. When nothing is proposed, Enter passes (the GUI also did nothing on an empty commit).
The letters `e`, `p`, `q` are reserved. No Pāḷi value is one letter.

**Screen layout (user rule, 2026-10-23): follow the other tests in `single/`.** Read from `test_digu.py`, `test_verb_grammar_sync.py`, `test_sukha_dukkha_finder.py` and `tools/printer.py`:
- `pr.tic()` first, `pr.toc()` last, `main()` plus `if __name__ == "__main__"`.
- **Heading:** `pr.yellow_title("<lowercase phrase saying what the test finds>")`, printed once. The phrases:

| Script | Heading text |
|---|---|
| `add_antonyms` | `find negative words with no antonym` |
| `add_antonyms_sync` | `find antonyms linked on one side only` |
| `add_family_compound_neg` | `find negative words with no family compound` |
| `add_family_compound_su_dur` | `find su dur sa nir words with no family compound` |
| `add_family_compound_taddhita` | `find taddhita words with no family compound` |
| `add_hyphenations` | `find long hyphenated words and choose one spelling` |

- **Item fields:** `pr.summary("<field>", value)` lines (id, lemma, pos, meaning, proposed value), as `test_digu.py` does. A counter line `12 / 340` before them.
- **Options line, the house style:** print with `end=""`, then `input()`. Yellow letter, white rest of the word: `[yellow]e[white]xception [yellow]p[white]ass [yellow]q[white]uit or Enter to commit: `. Hyphenations: `[yellow]1[white]-9 pick, [yellow]p[white]ass [yellow]q[white]uit: `.
- Confirmation lines use `[green]` for a write (`committed`, `exception added`) like `test_longest_compound_parts.py` (`[green]saved`).
- No new colours, no panels, no shared code. Each script copies the pattern.

**Prompt rule detail:** the proposed value appears as a `pr.summary("proposed", ...)` line. Enter commits it; typed text commits that text instead. (`input()` cannot pre-fill, so the proposed value is shown, not editable in place.)

**Hyphenations prompt:** show the clean word and the numbered dirty words. A number picks that
dirty word. Other text is the choice. With exactly one dirty word, Enter picks it. `p` or an
empty answer passes. `q` quits. After the last item, lower `max_length` by one, reload and
continue (same as the GUI), but stop at `max_length` 1 without saving 0 (the GUI looped forever; review found a saved 0 floods the next run).

**Behaviour kept:** open GoldenDict on the proposed word (`tools.goldendict_tools.open_in_goldendict`);
re-read the JSON before adding an exception in the four JSON-based scripts; `pyperclip` copy of ids when a hyphenation replace finds nothing.

**Behaviour changed on purpose:**
- `add_antonyms`: the live "words starting with what you type" list cannot work in a prompt.
  Show the 20 shortest matching words for the proposed value once, per item.
- `add_antonyms_sync`: remove the `print("source", source)` for every source (10,040 prints per run).
- `add_antonyms_sync` **bug fix (verified 2026-10-23):** `dest.antonym_list` is a `cached_property`
  and does not refresh after `commit()`. In a scratch in-memory db, after `antonym = "a, b"` and
  `commit()` the list still read `['a']`. A second commit to the same twin would therefore drop
  the first. Build the proposal from the `dest.antonym` string instead.
- `add_antonyms_sync` (user, 2026-10-23): no history list (`update_history` removed). The proposed antonyms print on their own line in bold cyan, last before the prompt.
- **Prompt change (user, 2026-10-23), all six scripts:** `c` commits the proposed value, Enter passes, other typed text commits that text. `c`, `e`, `p`, `q` are reserved. In hyphenations, Enter always passes (no auto-pick of a single dirty word) and the commit message names the chosen spelling.
- **Hyphenations auto-approve (user, 2026-10-23):** a word with exactly one marked form in the text, with or without the plain word, and no approved spelling yet is approved without a prompt and saved. The plain form is left in the text, as pressing the number did before (a single dirty word that equals the choice replaces nothing). It is prompted only for two differently marked forms. The count of auto-approved words prints each time the list loads.
- **Hyphenations bug fix (found 2026-10-23, `nevasaññānāsaññāyatanasaṃyojane`):** the list showed only hyphenated forms, so a word with a hyphenated and an apostrophe-only form looked like one option, and picking it replaced nothing. Now the list shows every marked form (hyphen or apostrophe). An approved word also comes back when a long marked form, hyphenated or not, differs from the approved spelling. The plain word never counts as a different form.
- **Hyphenations manual edit pause (user, 2026-10-23):** when a pick makes 0 replacements, the script prints the word's forms plainly, one per line (no id, field or tags), then a line, then waits for one key. (First built with raw db text; the user rejected it.) Cause found: the replace cannot match a form that has a bold tag inside it (e.g. headword 1768 commentary `sarīran</b>'ti-ādigāthāyo`). The clipboard copy of ids stays.
- **Hyphenations bold-tag pause (user, 2026-10-23, replaces an upfront skip the user rejected):** the prompt is always shown. After a pick, if a form that was NOT chosen has a bold tag inside it in the db text, the replace cannot reach it, so the script prints the forms plainly, one per line, a line, then waits for one key. A tagged form that is the chosen one needs no edit. Example: `guḷhavessantaraguḷhaummagga...` has tagged rows only in the hyphenated form.
- **Highlight (user, 2026-10-23):** in `add_antonyms_sync`, the two meaning lines print in bold magenta, the proposed antonyms in bold cyan. This overrides "no new colours".
- **Hyphenations integration (user, 2026-10-23, "maximum integration"):** the script and the speech marks file (`tools/speech_marks.json`, a cache rebuilt from db text) must agree.
  - After any commit, the script calls `SpeechMarkManager().regenerate_from_db()` once on exit (quit or end), so rejected spellings leave the file at once.
  - An approved word is skipped only when every hyphenated form in the text equals the approved spelling. A different form brings the word back, and the approved spelling is added to the numbered list.
- `add_hyphenations`: the `time.sleep(2)` pauses go. Messages print at once.

**Data files (user rule, 2026-10-23):** each test has its own Python file and its own JSON file,
with exactly the same name and a different suffix: `add_antonyms_sync.py` + `add_antonyms_sync.json`,
`add_hyphenations.py` + `add_hyphenations.json`, and so on, all in `db_tests/single/`.
- `gui/add_antonyms_sync_dict.json` moves to `db_tests/single/add_antonyms_sync.json` (a rename; plain `mv`, it has uncommitted edits that must survive).
- `gui/add_hyphenations.json` moves to `db_tests/single/add_hyphenations.json` (same name).
- Update `tools/paths.py` (`add_antonyms_sync_dict`, `add_hyphenations_config_path`, and the `# db_tests/gui` comment). Keep the attribute names; change the paths.
- **DECIDED (user, 2026-10-23, option B):** the other four tests (`add_antonyms`, `add_family_compound_neg`, `_su_dur`, `_taddhita`) keep their exceptions in their own JSON file, `<name>.json`, a sorted list of headword ids, e.g. `[4, 9, 19]`. They stop using `DbTestManager.add_exception` and the TSV.
  - **Consequence the user accepted:** the TSV rows in `db_tests/db_tests_columns.tsv` stay as they are (gui2's Tests tab still reads them). A word excepted in a terminal script is not excepted there, so gui2 flags it again.
  - **Seed, so answers stay the same:** create each JSON file once from the ids now in the TSV `exceptions` column (read 2026-10-23): `antonym: empty` (2,773 characters), `family_compound empty neg` (104), `family_compound empty taddhita` (227), and for su_dur the union of `family_compound empty su dur nir` (3 ids) and `family_compound empty sa` (3 ids). Read the live file when seeding; do not copy these numbers. After seeding, the scripts never read the TSV.
  - su_dur no longer splits exceptions by `sa ` prefix: one list in `add_family_compound_su_dur.json`. Its selection still uses the construction regex.
  - Write the JSON sorted ascending, with `ensure_ascii=False`, so a regeneration never reorders the file.
  - The `DbTestManager` import goes from all four scripts. Re-read the exceptions from the JSON before each add (another run may have written it).

**Remove** `db_tests/gui/` (`main.py`, `README.md`, the six scripts, `__pycache__`).

**Update references (sweep done 2026-10-23, `rg --hidden`, excluding `.git`, `graphify-out`, `kamma/archive`):**
- `justfile` line 68: recipe `db-tests-gui` becomes six recipes.
- `db_tests/run_all_tests.py`: drop `LAST_MODULE = "db_tests.gui.main"` and the docstring words about the Flet gui. The six scripts are picked up by its `single/*.py` glob.
- `db_tests/README.md` line 17 ("Interactive editors ... in `gui/`").
- `docs/technical/project_folder_structure.md`: tree line 19 and bullet line 108.
- Docstrings: `db_tests/db_tests_manager.py` line 5, `tools/goldendict_tools.py` line 2, `tools/negative_to_positive.py` line 2.

## Assumptions & uncertainties

- Verified by reading: every behaviour in the table above, from the six GUI sources.
- Verified by run: the stale `cached_property` after commit (scratch in-memory db).
- Verified by run: ORM load of 64,112 rows takes 2.2 s; only 25 sync candidates remain today. So the terminal version is fast.
- **Not verified:** the exact cause of the GUI slowness. It was not found. It does not matter for this thread, because the GUI goes.
- Assumed: `run_all_tests.py` running the new scripts in its sequence (each waits on prompts) is fine, as for the other interactive scripts in `single/`.
- Assumed: no outside code imports `db_tests.gui` (sweep found none besides the files above).

## Constraints

- Project rules: modern type hints, `Path`, `icecream` for debug, no `sys.path` hacks. Run `ruff check --fix`, `ruff format`, `pyright` on every touched file. Run `just typecheck` before finishing.
- Never run git commands. The user commits.
- Never run `git stash`/`restore`/`checkout --`. Other threads share the tree.
- Do not run exception paths against the real JSON files in tests. Never edit `db_tests_columns.tsv`.

## How we'll know it's done

- Six scripts exist in `db_tests/single/`, each starts and shows its first item (or "nothing to do") without Flet imports.
- `rg --hidden -n "db_tests[./]gui|import flet" db_tests` finds nothing. `db_tests/gui/` is gone.
- A test shows the sync fix: two sources for one twin leave both lemmas in the twin's `antonym`. Reverting the fix fails that test.
- `ruff`, `pyright` clean on all six; `just typecheck` clean; `uv run pytest tests/db_tests tests/tools` passes.
- The user runs one script live and confirms the answers match the old GUI.

## What's not included

- No speed work on the sync load (64k ORM objects). It takes seconds.
- No shared helper, base class or common prompt module.
- No change to `gui2`, the TSV file, or the two existing JSON formats.
- No GitHub writes.
