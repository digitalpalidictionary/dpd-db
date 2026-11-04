# Pass1 Auto: better prompt and better context — plan

Spec: `kamma/threads/20261104_pass1_auto_prompt/spec.md`. Read it first; it lists the verified facts, file paths and data shapes.

## Architecture Decisions

- **One context builder, used by both the test and gui2.** A new module `gui2/pass1_context.py` holds the sentence picker (SC first, then ePitaka, cap 3), the PEU lookup and the new prompt builder. The test harness imports it, so what is tested is what ships. It takes plain inputs (word, book key, SC segments, related entries) and returns the prompt text plus the chosen sentences — no Flet, no controller state.
- **ePitaka and PEU are optional readers.** `tools/epitaka_sentences.py` opens both ePitaka files read-only (`sqlite3.connect("file:...?mode=ro", uri=True)`), loads one CST book's sentences at a time into a `word -> [(pali, english)]` dict, same shape idea as `SuttaCentralSource.word_dict`. PEU is loaded once from `peu_dump.json` with `json.load`. Missing files → empty results, no error. Paths go in `tools/paths.py` next to `tipitaka_translation_db_path` / `peu_source_path`.
- **Old prompt stays callable.** The current `compile_prompt` text is moved verbatim into `gui2/pass1_context.py` as `build_old_prompt` for the test only; gui2 switches to the new builder only in Phase 5, after the verdict.
- **Test harness is throwaway** and lives in `artifacts/eval/` (not in `scripts/`), with its raw outputs, so results stay next to the spec that explains them.
- **Not abstracted:** no plugin system for "dictionaries". PEU is one function. A second dictionary later gets a second function.
- **New books** are plain `SuttaCentralSource` entries with `pali_path=None, english_path=None`, like the commentary books; their sentences come from ePitaka.

## Model Strategy

Fast = Sonnet. Pro = Opus. Target models (receive the prompts) = DeepSeek flash via DeepSeek API only (owner, 2026-11-04: no GLM test).

| Phase | Tier | Reason |
|---|---|---|
| 1 — Context sources and word sets | Fast | Readers, counts, word sampling: mechanical code and queries. |
| 2 — New prompt design | Pro | Judgement on Pāḷi grammar rules, prompt wording, worked example. |
| 3 — Run the test | Fast | Send ~200 calls, save raw answers, score. |
| 4 — Analysis and verdict | Pro | Read results field by field, build spot-check page, decide with owner. |
| 5 — Ship in gui2 (only if better) | Fast | Wire builder into controller, add books, tests, save K-set answers. |
| 6 — Final checks | Fast | Lint, types, tests, one real run. |

## Phase 1 — Context sources and word sets — *Fast*

- [x] 1.1 Check the DeepSeek model id. **(DeepSeek done. Z.ai dropped from the test, owner 2026-11-04.)** Use `AIManager`'s deepseek provider client (OpenAI-compatible) to list models from the DeepSeek API, without printing the key. If a 4.1 flash id exists, update the `deepseek` entry in `tools/ai_models.json`; record the id used in `artifacts/results.md`.
  → verify: one 1-line test request to the chosen id and to zai `glm-5.3-flash` returns non-empty content; paste the model id and the status messages into `artifacts/results.md`.
- [x] 1.2 Add `epitaka_db_path`, `epitaka_en_db_path` (`~/.local/share/com.dn.epitaka/epitaka.db`, `epitaka_en.db`) and `peu_json_path`-style entry for `peu_dump.json` to `tools/paths.py` (check the existing `peu_json_path` name first; it points at a build file, so use a new name such as `peu_source_json_path`).
  → verify: `uv run pyright tools/paths.py` clean; the three paths `.exists()` on this machine.
- [x] 1.3 Write `tools/epitaka_sentences.py`: `epitaka_word_dict(cst_files: list[str]) -> dict[str, list[tuple[str, str]]]` — map CST file stems (e.g. `s0506m.mul`) to ePitaka `book_id`s via `books.vri_id`, join `sentences` Pāḷi + English on `(book_id, para_id, line_id)`, clean each Pāḷi sentence with `clean_machine`, index every word. Read-only connections; empty dict if files missing. Plus `peu_entries(word: str, limit: int = 2) -> list[str]`: exact match, else cut 1/2/3 letters off the end and take headwords that start with the rest and are at most 3 letters longer (sorted keys + `bisect`), first cut with a hit wins, closest length first.
  → verify: new tests in `tests/tools/test_epitaka_sentences.py` (missing file → `{}`/`[]`; a fixture db built from 3 real rows copied from `epitaka.db` Vv; a PEU fixture of 3 real entries); `uv run pytest tests/tools/test_epitaka_sentences.py` passes.
- [x] 1.4 Measure coverage on the target books (Vv kn6, Pv kn7, Ap kn10+kn11, Bv kn12, Cp kn13): for the missing words (current `is_missing` rules, using `DatabaseManager` as the controller does), count how many get ≥1 ePitaka sentence and ≥1 PEU entry. Print 20 random PEU matches (word, cut used, headword found) and read them all; if short stems give wrong headwords, add a minimum stem length and re-measure.
  → verify: a coverage table (book, missing words, % with sentence, % with PEU) in `artifacts/results.md`, plus the 20 printed PEU samples with a right/wrong mark.
- [x] 1.5 Pick the word sets into `artifacts/eval/words.json`:
  - Set G: 50 words in `dpd.db` (lookup has headwords) with a saved `temp/prompts/pass1/{word}_prompt` and `_response`; prefer verse books; about 25 whose saved prompt had no sentence. Store the gold headword id(s).
  - Set K: 50 missing words, 8–9 per target book (Vv, Pv, Ap-i, Ap-ii, Bv, Cp), random with a fixed seed.
  → verify: `words.json` has 50 + 50 entries; print the per-book and with/without-sentence counts into `artifacts/results.md`. If fewer than 50 G words exist, record the real number and fill from other books.
- [x] 1.6 Phase check: `uv run ruff check`, `uv run ruff format`, `uv run pyright` on every touched file; `uv run pytest tests/tools/test_epitaka_sentences.py`.
  → verify: all clean; pytest: `9 passed in 0.19s` (ruff, ruff format, pyright clean on `tools/paths.py`, `tools/epitaka_sentences.py`, and the test file with `--project /dev/null`).

## Phase 2 — New prompt design — *Pro*

⚠️ MODEL SWITCH REQUIRED (Pro tier): prompt wording and Pāḷi grammar rules need judgement.

- [x] 2.1 Move the current `compile_prompt` text verbatim into `gui2/pass1_context.py::build_old_prompt(word, sentences, related)`.
  → verify: for 3 G words, `build_old_prompt` output equals the saved `_prompt` file text when fed the same sentences and related entries parsed from that file (diff empty, or only the related-entries lines if the db changed since).
- [x] 2.2 Write `build_new_prompt(word, book_name, sentences, related, peu)` per spec "What it should do" 1–4: book name, up to 3 sentence pairs, PEU block with its caveat, related entries as JSON objects, exact keys, one worked example answer taken from a real DPD entry of a common verse-book word, corrected field rules, and a short system prompt constant. Related entries for a G word must exclude its gold headword ids (leak guard) — the builder takes an `exclude_ids` argument.
  Also in the module (needed by the test harness, so built now): `choose_sentences` (SC first, then ePitaka, no duplicates, cap 3), `related_entry_dict` (one headword in the answer's JSON shape, plus its id), and `load_allowed_values(db_session)` (owner, 2026-11-04: lists of real dictionary values for `pos`, `pattern`, `root_sign`, `root_key`). Fixed text first, word context last (prompt caching). Unit tests in `tests/gui2/test_pass1_context.py`.
  → verify: print the full new prompt for 3 G words and 3 K words to `artifacts/eval/sample_prompts.md`; read all six; confirm none contains its own gold `lemma_1` in the related block; record the prompt length in tokens (approx chars/4) old vs new.
- [x] 2.3 Dry run: send the new prompt for 5 K words to DeepSeek flash. **Done: 5 of 5 valid after one rule fix, see `artifacts/results.md`. Z.ai dropped (owner, 2026-11-04).**
  → verify: all 10 answers parse as JSON with exactly the expected keys; fix the prompt if not, then rerun the 10.

## Phase 3 — Run the test — *Fast*

⚠️ MODEL SWITCH REQUIRED (Fast tier): mechanical execution resumes.

- [x] 3.1 Write `artifacts/eval/run.py`: for every word in `words.json`, for old and new prompt, on `deepseek` / `deepseek-v4-flash`, call `AIManager.request(provider_preference=..., model=...)` (same system prompt as each version uses), save raw text to `artifacts/eval/raw/{set}/{model}/{version}/{word}.txt`. Skip files that already exist, so a rerun resumes. G-word old prompts are the saved `_prompt` text verbatim; K-word old prompts come from `build_old_prompt` with today's SC sentences and related entries.
  → verify: run on 2 words first; 4 raw files appear; then the full run; count = 200 files (or list the failures with their error text).
- [x] 3.2 Write `artifacts/eval/score.py`: parse each answer (strip code fences, `json.loads`); for G words score the 8 fields of the spec against the best-matching gold headword; also score the saved historic `_response`. Output `artifacts/eval/scores.csv` and a summary table.
  → verify: hand-check the scores of 3 words against their raw answers and db rows; paste the summary table (model × version × field, JSON-valid rate) into `artifacts/results.md`.

## Phase 4 — Analysis and verdict — *Pro*

⚠️ MODEL SWITCH REQUIRED (Pro tier): judging results and deciding.

- [x] 4.1 Read the score table against the spec's four "genuinely better" rules. For every field that dropped, read the answers that lost and name the cause.
  → verify: `artifacts/results.md` has a pass/fail line per rule with the numbers.
- [x] 4.2 Build the spot-check page `artifacts/spot_check.html` (static, local file): 20 words (10 G, 10 K), each showing the sentences sent, old answer, new answer, dictionary entry for G words.
  → verify: open the file and check all 20 words render with all columns.
- [x] 4.3 Owner verdict. Hand the owner the page; record the verdict and any notes in `artifacts/results.md`. If the verdict or rules say "not better", stop here: Phase 5 is skipped, Phase 6 runs only on Phase 1–2 files, and `results.md` states why.
  → verify: verdict line present in `artifacts/results.md`.

## Phase 5 — Ship in gui2 (only if better) — *Fast*

⚠️ MODEL SWITCH REQUIRED (Fast tier): mechanical execution resumes.

- [x] 5.1 Add books `vv` (kn6), `pv` (kn7), `ap` (kn10, kn11), `bv` (kn12) to `gui2/books.py::sutta_central_books` with no SC folders, `is_commentary=False`. Check every reader of `sutta_central_books` (`rg -n sutta_central_books --hidden`) still copes with a book that has no SC data (the commentary books already do).
  → verify: `uv run pytest tests/gui2` passes; the Pass1Auto book dropdown lists the four new books (`uv run pytest tests/gui2/test_pass1_auto_controller.py`). **Done: `tests/gui2` + epitaka tests 674 passed. Pass2 Pre's book list also shows the four books (shared dict); they have no SC data, same as the commentary books.**
- [x] 5.2 In `gui2/pass1_auto_controller.py`, replace `compile_prompt`'s text with `build_new_prompt`, choose sentences through the context builder (SC first, ePitaka, cap 3), pass the new system prompt in `send_prompt`, and fill `example_1/2`, `translation_1/2` from the chosen sentences. Keep the saving of `_prompt`/`_response` files. Load the ePitaka word dict once per book run, in the same thread step as `find_missing_words_in_cst`.
  → verify: new tests in `tests/gui2/test_pass1_auto_controller.py`: SC sentences come before ePitaka; never more than 3; ePitaka missing → SC only, no error; PEU missing → no PEU block; `example_1` equals the first chosen sentence. `uv run pytest tests/gui2/test_pass1_auto_controller.py` passes. **Done. Also fixed a pre-existing pyright error in `send_prompt` (`ai_response` possibly unbound) with a `last_error` variable. `load_prompt_context` loads allowed values and the ePitaka dict once per run; text mode has no ePitaka.**
- [x] 5.3a Retire every old `gui2/data/pass1_auto_*.json` (spec item 8) by moving them into the backup folder `gui2/data/pass1_auto_retired/20261104/`. Never delete them (owner, 2026-11-04: keep as backups to compare). Record the file list and per-file answer counts in `artifacts/results.md` before moving. Only after 5.2 has shipped the new prompt.
  → verify: `ls gui2/data/pass1_auto_*.json` lists none of the 18 old files; the backup folder holds all 18 with the same answer counts and identical bytes (`sha256sum` before/after); `rg -n pass1_auto_retired --hidden gui2` shows no code reads the folder. **Update (owner, 2026-11-04, during review): the backup folder is local only; `.gitignore` ignores `gui2/data/pass1_auto_retired/`.**
- [x] 5.3b Track the Pass1 Auto files in git (spec item 9). Owner decided 2026-11-04: Pass1 Auto runs only on the laptop; the files reach the server through git (spec item 9). **Open point decided (owner, 2026-11-04, spec item 9):** the server never edits the tracked files; each contributor has a removals list `pass1_auto_removed_{username}.json` in `DPD_GUI2_DATA_DIR`. Steps: (1) untrack nothing, change the `.gitignore` rule for `gui2/data/pass1_auto_*.json` so the live files are tracked (the backup folder stays ignored, see 5.3a), but keep `pass1_auto_removed_*.json` ignored; (2) add `pass1_auto_removed_path` to `Gui2Paths.for_user`; (3) `Pass1FileManager` takes the removals path: for a contributor `read` returns the tracked file minus the removed words, and `remove` writes to the list, never the tracked file; user "1" is unchanged; (4) read every add path in `gui2/pass1_add_controller.py` and make sure each successful add from a book writes the removal, so a contributor never sees a word already added; the owner commits.
  → verify: `git check-ignore -v gui2/data/pass1_auto_cp.json gui2/data/pass1_auto_retired/20261104/pass1_auto_cp.json` prints nothing; the removals file is still ignored; new tests: a contributor's removals path is under `DPD_GUI2_DATA_DIR` (`tests/gui2/test_paths.py`); for a contributor, `read` hides removed words and `remove` leaves the tracked file byte-identical; a word added then removed never reappears, also after the tracked file gains new words. **Done. `.gitignore` now ignores `pass1_auto_removed_*.json` and (my addition) `pass1_auto_text.json`, the pasted-text scratch slot, so it is not tracked either. `Pass1FileManager.remove` is the one removal path; for a contributor `write`/`update` raise `PermissionError`. Add path checked: `remove_word_and_save_json` runs after every successful commit and skips only when `word_in_text` is empty (a history word, not from a book). `tests/gui2` + epitaka tests: 685 passed.**
- [x] 5.3c Remove `"Pass1Auto"` from `BASE_TABS` in `gui2/contributor_tabs.py` (owner, 2026-11-04). Read how `gui2/main.py` `_view(2)` builds a view for a hidden tab first: Pass1 Add gets its controller from it, so it must still work for a contributor.
  → verify: `tests/gui2/test_contributor_tabs.py` updated to the new tab list (an intended change, not a weakened check) and passing; a new test shows a contributor's Pass1 Add still gets a Pass1 Auto controller while the Pass1Auto tab is not visible. **Done. Also changed the server start tab in `gui2/main.py` from 2 to 3 (Pass1Add), else `_visible.index(2)` raises; `test_main.py` server tests moved to the new tab positions (intended change). `uv run pytest tests/gui2` 666 passed. `gui2/main.py` shows 24 pyright errors under `--project /dev/null`; all are on lines this thread did not touch (flet typing, `profiler`).**
- [x] 5.3 Save the kept K-set answers (DeepSeek's new answers) into `pass1_auto_{book}.json` via `Pass1FileManager.update`, with `example_*`/`translation_*` added as the controller does and the `[provider: model]` comment prefix. Never overwrite an existing key.
  → verify: before/after key counts of each touched file printed into `artifacts/results.md`; existing keys unchanged (compare JSON before/after for old keys).
- [x] 5.4 Real run: hand the owner `cd <repo> && just gui`, Pass1Auto, book `vv`, stop after 3 words.
  → verify: the three newest `temp/prompts/pass1/*_prompt` files contain ePitaka sentences and a PEU block where one exists. **Done 2026-11-04: owner ran several words on `vv` ("very fast"). The five newest prompts show book name, sentences (two words show a second sentence from ePitaka), a PEU block where PEU has the word (paṭhamapīṭhavimānaṃ, suvatthe), and no PEU block where it has none.**

## Phase 6 — Final checks — *Fast*

- [x] 6.1 `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright` on every touched `tools/` file; `uv run pyright --project /dev/null` on touched `gui2/` and `tests/` files.
  → verify: all clean. **Done: ruff check, ruff format, pyright (tools files, and gui2/tests files with `--project /dev/null`) all clean on every touched file except `gui2/main.py`, which keeps 24 pre-existing pyright errors on lines this thread did not touch.**
- [x] 6.2 `just typecheck` and `uv run pytest tests/gui2 tests/tools/test_epitaka_sentences.py`.
  → verify: both pass; paste summary lines here. **`just typecheck`: 0 errors. `uv run pytest tests`: 2925 passed, 1 failed, 12 deselected. The failure is `tests/scripts/server_contrib/test_maintenance_window.py::TestHappyPath::test_status_file_reports_a_failure_and_its_reason` (status file says `problems: 0`). It passes when its file runs alone (20 passed). PRE-EXISTING? — NOT CAUSED BY THIS THREAD (unverified against a clean tree): it only fails in the full run; this thread touches nothing the test reads.**
- [x] 6.3 Update `kamma/tech.md` with the two new optional sources (ePitaka, PEU) and where they live; `graphify update .` then prune old snapshots.
  → verify: `tech.md` diff shows the note; only one `graphify-out/20*` snapshot remains.
