# Pass1 Auto: better prompt and better context — spec

## Overview

Pass1 Auto (gui2 tab "Pass1Auto", `gui2/pass1_auto_controller.py`) finds every word in a book that is not yet in DPD, sends one AI prompt per word, and saves the JSON answer to `gui2/data/pass1_auto_{book}.json`. Pass1 Add later shows each answer to the editor, who corrects it and adds it to `dpd.db`. On add, the word is removed from the pass1_auto file.

This thread builds a better prompt and better context for that AI call, tests it against the current system, and only ships it if the test shows it is genuinely better. The owner's view: almost anything will beat the current prompt, so the test must show *where* it is better and catch any field that gets worse.

Target books for the test, and the next books to process (ePitaka names): Vimānavatthupāḷi, Petavatthupāḷi, TherāpadānapāḷiPaṭhamo, TherāpadānapāḷiDutiyo, Buddhavaṃsapāḷi, Cariyāpiṭakapāḷi.

Target models (the models the owner will actually use): DeepSeek flash through the DeepSeek API directly (owner said "4.1 flash"; `tools/ai_models.json` lists `deepseek` / `deepseek-v4-flash`, so the exact API model id must be checked). **Owner, 2026-11-04: "We don't need a test with GLM. Deepseek is enough."** Z.ai `glm-5.3-flash` is dropped from the test.

## Current behaviour (verified by reading the code and data on 2026-11-04)

- **Book list** — `gui2/books.py::sutta_central_books`. Each book has CST book codes plus optional SuttaCentral (SC) Pāḷi and English folders. Vv, Pv, Ap, Bv are **not** in the list; Cp is (`"cp"`, kn13, SC Sujato English).
- **Word list** — CST words of the book (`make_cst_text_list`) plus SC words, filtered by `is_missing()`.
- **Sentences** — only from SC (`SuttaCentralSource.word_dict`). CST-only words get `[]`. All four commentary books (`kva`, `dhpa`, `jaa`, `dna`) have no SC folders, so every word from them is sent with an empty "Sentences" section. SC words send *every* sentence they occur in (sometimes dozens).
- **SC coverage of the target books** — `resources/sc-data/sc_bilara_data/root/pli/ms/sutta/kn/` has `vv`, `pv`, `bv`, `cp`, `tha-ap`, `thi-ap` (Pāḷi). The Sujato English folder has only `cp` of these. So SC gives no English for Vv, Pv, Ap, Bv.
- **Related entries** — `DatabaseManager.get_related_dict_entries`: looks up the word's deconstructor splits (first 2) in `lookup`, and lists every headword of each part as one text line. A word with no deconstruction gets no related entries.
- **Prompt** — one fixed f-string in `compile_prompt`: word, sentences, related entries, then field rules for 14 fields. No worked example of a finished entry, no book name, no list of valid patterns or roots. System prompt is "Follow the instructions very carefully."
- **Answer handling** — `update_auto_processed`: strips code fences, `json.loads`, prefixes `comment` with `[provider: model]`, adds `example_1/translation_1`, `example_2/translation_2` from the first two SC sentences, saves.
- **Saved history** — every prompt and answer is written to `temp/prompts/pass1/{word}_prompt` and `{word}_response`. 47,863 files there (≈24k pairs), newest 2026-11-01.
- **Models** — `tools/ai_models.json` default list: zai `glm-5.3-flash`, deepseek `deepseek-v4-flash`, deepseek `deepseek-v4-pro`, openrouter `deepseek/deepseek-v4.1-flash`, others.
- **Pass1 Auto is also a contributor tab** (`gui2/contributor_tabs.py` `BASE_TABS`), so it can run on the contributor server, where the ePitaka files do not exist.

## New context sources (verified 2026-11-04)

- **ePitaka** (`~/.local/share/com.dn.epitaka/`, the installed ePitaka app's data):
  - `epitaka.db` table `sentences(book_id, para_id, line_id, ..., pali)` — 1,283,680 Pāḷi sentences, uses `ṃ`. Table `books(book_id, vri_id, book_name, category, ...)`; `vri_id` is the CST file stem, e.g. `Vv`=`s0506m.mul`, `Pv`=`s0507m.mul`, `Ap-i`=`s0510m1.mul`, `Ap-ii` and `Ap-iii`=`s0510m2.mul`, `Bv`=`s0511m.mul`, `Cp`=`s0512m.mul`. Categories: Mūla, Aṭṭhakathā, Ṭīkā, Añña.
  - `epitaka_en.db` table `sentences(book_id, para_id, line_id, translation, translation_confidence, confidence_note)` — 1,278,940 rows, only 20 with empty translation. Same key as the Pāḷi table.
  - Sentence counts in the target books: Vv 2255, Pv 1843, Ap-i 10187, Ap-ii 4460, Bv 2212, Cp 843.
- **PEU — Pali English Ultimate** (owner's request, 2026-11-04): `resources/other-dictionaries/dictionaries/peu/source/peu_dump.json` (path `ProjectPaths.peu_source_path` points at the `.js` twin `peu_dump.js`; the exporter parses that with `exporter/mobile/mobile_exporter.py::_load_peu_dump`). 203,865 headwords in the `.json` (counted 2026-11-04), keys are stems/lemmas (`abaddhamukha`, `dasaakkosavatthu`), not inflected forms. Each value starts with the split and the gender, e.g. `'[Dasa1+agghanaka] (ti) CL=0 10 - Blue - 10 Kyats ...'`, `'[Abaddha+gāmasīmā] (thī) CL=8 village sīma hall ...'`. Gender codes seen: `pu` masc, `na` nt, `thī` fem, `ti` adjective (three genders). About 80% human translated, the rest machine translated (`docs/other_dicts.md`), so meanings are a hint, not a source. The source folder is local to the `other-dictionaries` submodule and may be absent on other machines.
- **Tipitaka translation db** (`resources/tipitaka_translation_db/tipitaka-translation-data.db`, `tools/tipitaka_db.py`): one table per CST file, *paragraph* level, Pāḷi as HTML plus English. Covers the same CST books but per paragraph, so it is not used in this thread (see "Not included").

## What it should do

1. **Sentences for every word.** For each word, send up to **3** sentence pairs (Pāḷi + English): SC sentences first (they have a human translation), then ePitaka sentences from the same CST book(s), matched by the cleaned word form. Prefer different sentences (no duplicates). If the ePitaka files are missing (contributor server), fall back silently to SC-only, as today.
2. **PEU entries.** For each word, find up to 2 PEU entries by the owner's rule: remove the inflected ending and match everything except the last few letters. Concretely: try the exact word first; then cut 1, 2, then 3 letters off the end, and take PEU headwords that start with what is left and are at most 3 letters longer than it. Stop at the first cut that finds a hit; among hits, prefer the one closest in length to the word. A sorted key list with `bisect` makes the prefix search fast. The cut limit (3) is checked in Phase 1. Send each as `headword: [split] (gender) meaning`, trimmed to about 300 characters, with `CL=…` removed. Tell the model that PEU is a guide for the split and gender, and that its English is partly machine translated. If the PEU file is missing, skip it silently.
3. **`example_1/2` and `translation_1/2`** come from the same chosen sentences, so ePitaka sentences also fill them.
4. **A better prompt.** Final wording is decided in the design phase and measured, but the candidate changes are:
   - book name and text type (e.g. verse, Apadāna) in the prompt;
   - related entries shown in the same JSON shape as the expected answer, so the model copies the style;
   - one complete worked example answer, and the exact JSON keys;
   - fix the wrong or unclear rules in the current text (typos, "absolutes adverbs", contradictions);
   - a short system prompt that states the job;
   - **lists of the real dictionary values** for every field with a fixed set (owner, 2026-11-04: "in case of doubt, you can always include the list of real dictionary values for any field, pick one"): `pos` (30), `pattern` (153), `root_sign` (66), `root_key` (753, each with its meaning, about 16k characters). Read from `dpd.db` at run time, not hard-coded, so they follow the dictionary;
   - all fixed text (rules, worked example, value lists) comes **first** and the word's own context **last**, so the provider prompt caches (DeepSeek's among them) can reuse the long fixed part between calls.
   Each candidate stays only if the test does not show it hurting a field.
5. **New books** Vv, Pv, Ap (Ap-i + Ap-ii, CST kn10 + kn11), Bv added to the pass1 book list, so they can be auto-processed.
6. **Test before shipping** — see "How we'll know it's done".
7. **Keep the good results** — if the new system wins, the new answers for the test words from the target books are saved into their `pass1_auto_{book}.json` files, so that work is not wasted.
8. **Retire all old Pass1 Auto answers** (owner's request, 2026-11-04) — once the new prompt and context ship in gui2, every existing `gui2/data/pass1_auto_*.json` made by the old prompt is retired, so the editor no longer works from old-prompt answers. Only if the new system wins; it runs before item 7, so the kept K-set answers go into fresh files.
   - What exists today (counted 2026-11-04): 18 files, about 20,100 answers — `dhpa` 9588, `nidd1&2` 3983, `jaa` 3400, `ja` 1493, `vin5` 667, `cp` 646, `dhp` 236, `th` 36, `thi` 17, `an` 9, `text` 9, `iti` 5, `snp` 5, and five empty files (`dn`, `mn`, `sn`, `ud`, `vin3&4`).
   - None of these files is tracked by git, so deleting one cannot be undone.
   - Side effect: `is_missing()` skips every word that has an answer in its book's file. After retiring, those words count as missing again, and the next Pass1 Auto run on that book processes them with the new prompt. That is the intended effect, but it costs one AI call per word (about 20,100 calls if every book is re-run).
   - Method (owner's decision, 2026-11-04): **never delete them.** Move the files into a backup folder, `gui2/data/pass1_auto_retired/20261104/`, which Pass1 Add and Pass1 Auto never read. They stay there as backups so old and new answers can be compared later.
9. **Track the Pass1 Auto files in git** (owner's request, 2026-11-04) — commit, from now on, the new `pass1_auto_*.json` files, so the contributor server has them. **Changed (owner, 2026-11-04, during review): the retired backups stay local only and are not committed** (`.gitignore` ignores `gui2/data/pass1_auto_retired/`; 17 MB of old-prompt drafts would stay in git history forever). The owner commits; the agent only changes `.gitignore` (line 106 today: `gui2/data/pass1_auto_*.json`).
   - Size: the 18 files total 17 MB (`dhpa` alone 8 MB).
   - **Open problem (found 2026-11-04, decide before Phase 5):** `Pass1FileManager` writes to `Gui2Paths.gui2_data_path`, which is the repo's `gui2/data` for every user. `Gui2Paths.for_user` sends many per-user files to `DPD_GUI2_DATA_DIR` (outside the repo) "so a pull never meets a local copy of a file that main tracks", but not the Pass1 Auto files. So on the server, once these files are tracked, a contributor's Pass1 Auto run or Pass1 Add (which removes a word on add) edits a tracked file, and the nightly `git pull --ff-only` in `scripts/server_contrib/maintenance_window.py` meets local changes. Pass1 Auto files are also not in the delivered file list (`tools/contrib_entry.py`), so server-made answers never come back to the laptop. Options to put to the owner: (a) server reads the tracked files but writes its own per-user copy in `DPD_GUI2_DATA_DIR`; (b) track only the retired backups, not the live files; (c) accept the conflict and handle it in the maintenance window.
   - **Decided (owner, 2026-11-04):** the owner runs all Pass1 Auto on the laptop and shares the files with the server through git. Reason: the server has no ePitaka files, so a server run would send no sentences for Vv, Pv, Ap and Bv. Contributors do Pass1 Add on the server; the owner edits the final versions on the laptop, and only those go into `dpd.db`.
   - **Still open, decide before Phase 5:** (1) a contributor's Pass1 Add removes the word from the Pass1 Auto file, which is now tracked, so the nightly `git pull --ff-only` meets a local change. The server needs to record its removals somewhere untracked (per user, in `DPD_GUI2_DATA_DIR`), as option (a). (2) ~~Whether the Pass1Auto tab stays in the contributor tabs~~ **Decided (owner, 2026-11-04): "definitely this server should not have Pass1 Auto tab."** Remove `"Pass1Auto"` from `BASE_TABS` in `gui2/contributor_tabs.py`. Pass1 Add still needs the Pass1 Auto *controller* (it reads the drafts and removes a word on add): `gui2/main.py` builds Pass1 Add with `self._view(2).controller`, so the hidden Pass1 Auto view must still be constructible for a contributor, only not shown.

   - **Decided (owner, 2026-11-04): the server never edits the tracked Pass1 Auto files.** One contributor works on one book. The contributor's view of a book = the tracked file minus a per-user list of finished words. Pass1 Add writes each removal to that list, stored as `pass1_auto_removed_{username}.json` (`{book: [word, ...]}`) in `DPD_GUI2_DATA_DIR`, like the other per-user files in `Gui2Paths.for_user`. `Pass1FileManager.read` applies the list for a contributor; the laptop (user "1") is unchanged. The laptop does not need the list: finished entries reach it as the contributor's additions, and once they are in `dpd.db` its own `is_missing()` skips the words. Words added to a tracked file later reach the contributor at once. **Owner condition:** a contributor must never see a word they have already added, so every successful add from a book must write the removal (check the add paths in `pass1_add_controller.py`, including the case where `word_in_text` is empty).

## Test design

Two word sets, 100 words in total. Every word is run with the **old prompt** and the **new prompt**, on DeepSeek flash (`deepseek-v4-flash`): 2 calls per word, about 200 calls.

- **Set G (gold), 50 words** — words now in `dpd.db` that have a saved old answer in `temp/prompts/pass1/`. Prefer words from the verse books closest to the targets (`cp`, `th`, `thi`, `ja`, `dhp`, `snp`), and include about half that had **no** sentence in their old prompt, since that is where the change matters most.
  - Reference 1, "what ended up in pass1auto": the saved old answer, plus the old prompt re-sent to each target model (the saved prompt text verbatim, so the model is fixed but the context is what the old system really sent).
  - Reference 2, "what ended up in the dictionary": the `dpd_headwords` row. If the word form maps to several headwords, score against the best-matching one (same rule for old and new).
  - **Leak guard:** when building the new prompt for a gold word, the word's own headword(s) must be removed from related entries, or the model is handed the answer.
  - Auto score: exact match after trimming spaces on `lemma_1` (vs lemma without homonym number), `pos`, `root_key`, `family_root`, `family_compound`, `construction`, `stem`, `pattern`; plus the rate of valid JSON.
- **Set K (keep), 50 words** — words still missing from DPD, about 8–9 each from Vv, Pv, Ap-i, Ap-ii, Bv, Cp. Reference 1 is the old prompt run now (Cp words may also have a real old answer in `pass1_auto_cp.json`). There is no dictionary entry yet, so these are judged by the owner.
- **Spot check** — one side-by-side page of 20 words (10 from G, 10 from K): sentences sent, old answer, new answer, and the dictionary entry where it exists. The owner reads meanings and grammar.

"Genuinely better" means all of these:
- on Set G, the new prompt's total field-match score is higher than the old one on DeepSeek flash;
- no single field drops by more than 5 percentage points;
- valid-JSON rate is not lower;
- the owner prefers the new answers in the spot check.

## Assumptions & uncertainties

- **Assumption:** the ePitaka files stay at `~/.local/share/com.dn.epitaka/`, and opening them read-only (`mode=ro`) while the ePitaka app may be running is safe. The path goes in `tools/paths.py`; code treats the files as optional.
- **Assumption:** the owner's "Therāpadānapāḷi" twice means ePitaka's Ap-i and Ap-ii. Therīapadāna (Ap-iii) is not a target, but it shares CST file `s0510m2` with Ap-ii, so its words come in with kn11 anyway.
- **Unverified:** how many gold words exist. Phase 1 counts them. If fewer than 50 suit, fill from other books with saved answers.
- **Unverified:** the DeepSeek API model id for "4.1 flash". Phase 1 lists the API's models and updates `tools/ai_models.json` if needed.
- **Checked (1.4):** PEU finds an entry for 51–60% of missing words in the target books. Short stems often give wrong headwords but are only 12% of hits; no minimum stem length (owner: most words are long compounds). See `artifacts/results.md`.
- **Checked (1.4):** ePitaka words are cleaned exactly like `make_cst_text_list` (round brackets removed, `clean_machine`, hyphen parts); 96–100% of missing words find a sentence.
- **Uncertain:** the new books' SC Pāḷi folders (`vv`, `pv`, `bv`, `tha-ap`, `thi-ap`) add nothing that CST + ePitaka lack, so the new book entries use no SC folders. If an SC word not in CST matters, revisit.
- The pass/fail thresholds above are the planner's proposal.

## Constraints

- No `dpd.db` writes in the test. The test reads `dpd.db`, ePitaka and saved prompt files only.
- Never overwrite the existing `pass1_auto_*.json` entries during the test. Phase 5 retires the old files (item 8), then adds the kept K-set answers through `Pass1FileManager.update`.
- Contributor server must keep working without ePitaka.
- Test scripts and results live in this thread's `artifacts/`, not in the repo's code folders.
- API keys come from `config.ini` via the existing `AIManager`; never print them.
- Project lint/type rules (ruff, ruff format, pyright, `just typecheck`) apply to every touched code file.

## How we'll know it's done

- A results table in `artifacts/results.md`: per model, per prompt version, per field, match rate on Set G, plus JSON-valid rate and context coverage (how many words got 0/1/2/3 sentences, old vs new).
- The spot-check page, and the owner's verdict recorded in `artifacts/results.md`.
- If better: Pass1 Auto in gui2 uses the new context and prompt; Vv, Pv, Ap, Bv are in the book list; all old `pass1_auto_*.json` files are retired; K-set answers are saved; tests in `tests/gui2/test_pass1_auto_controller.py` cover sentence selection (SC first, cap 3, ePitaka missing) and the leak-free prompt build; one real Pass1 Auto run on a target book in gui2 shows sentences in the saved prompt.
- If not better: nothing in gui2 changes, and `artifacts/results.md` says why.

## What's not included

- The tipitaka translation db (paragraph level). ePitaka covers the same books per sentence. Can be a fallback in a later thread.
- Dictionaries other than PEU (Cone, CPD, PTS and others in `other-dictionaries`). If PEU helps, the same slot can take another dictionary in a later test.
- Commentary glosses (e.g. Vv-a explaining a Vv word). Likely useful for verse books; a follow-up test.
- Changes to Pass1 Add, to the retry logic, or to the JSON file locking.
- A weekly improvement cycle (owner, 2026-11-04: contributors will use these books heavily in the coming weeks and months). Planned as a separate kamma loop thread after this one ships: each week, compare the AI drafts with the owner's final entries field by field, propose one rule change, test it on the fixed Set G, and keep it only if it wins and the owner approves. Its first cycle closes a gap found 2026-11-04: a contributor's addition (`additions_*.json`) carries the contributor's entry but not the AI draft it started from, and the processed log keeps only the final version, so draft and final cannot be compared yet. The draft, with its model and prompt version, must travel with the addition.
- Re-running Pass1 Auto on the books whose old answers are retired. Retiring makes those words pending again; the owner re-runs each book in gui2 when wanted.
