# Plan: preview builds its button content

Spec: `kamma/threads/20261118_preview_inflection_table/spec.md`. Not tied to a GitHub issue
(audio part relates to #215).

## Architecture Decisions

- Extract the table builder to a module-level function in the existing generator file and
  call it from both the build and the preview. One copy of the HTML logic.
- No cache for the corpus word set: load, use, drop. Keeps gui2 memory flat.
- Mirror the build's rules: a table only when `pattern` is set; a missing template gives `""`.
- Audio is embedded as base64 data plus a small `Audio` shim inside the preview page. The
  webapp's `dpd.js` is not edited, so the webapp is unaffected.
- The word-list fix goes last, after the equivalence check, because it changes what the
  builder returns versus the stored tables.
- Frequency counts and family tables are deliberately not built.

## Model Strategy

| Phase | Tier | Suggested model | Reason |
|---|---|---|---|
| 1 Inflection table | Fast (workhorse) | Sonnet | Small mechanical edit with a clear test |
| 2 Frequency note | Fast (workhorse) | Sonnet | One field set, one test |
| 3 Audio | Pro | Opus | Browser audio behaviour and the shim need judgement |
| 4 Word list fix | Fast (workhorse) | Sonnet | One-line fix and a count check |
| 5 Verify | Fast (workhorse) | Sonnet | Commands and checks |

## Phase 1 — Inflection table — *Fast*

- [x] Write failing tests first in `tests/gui2/test_preview.py` (reuse `edited_copy`,
      `db_session`): (a) a new word with a real stem and pattern (read from a real db row,
      e.g. word id 7) previews with `<table class='inflection'>` and an inflected form;
      (b) an existing word with `pattern` changed to another real pattern previews the new
      pattern's heading, not the old one.
  → verify: `uv run pytest tests/gui2/test_preview.py -k inflection`, expect both to fail
    (empty or stale table). Paste the failure output here.
    RESULT: both failed before the change. `assert "<table class='inflection'>" in html` and
    `assert 'is <b>a nt</b>' in html` raised AssertionError. 2 failed, 21 deselected.
- [x] In `db/inflections/generate_inflection_tables.py` add module-level
      `make_inflection_table(i, template, tipitaka_words)` returning `(html, list)`;
      `tipitaka_words` may be `None` (no grey marking). `generate_inflection_table` calls it
      and keeps its `i.it` missing-template error branch.
  → verify: `uv run pyright db/inflections/generate_inflection_tables.py` clean; equivalence
    check in Phase 5.
- [x] In `gui2/preview.py` `render_preview`, after `_copy_of`: if `copy.pattern`, get the
      `InflectionTemplates` row inside the existing `no_autoflush` block, load the word set
      (catch `FileNotFoundError` only, then pass `None`), call the function, set
      `copy.inflections_html`. Missing template gives `""`.
  → verify: `uv run pytest tests/gui2/test_preview.py` all pass, including the existing
    `db_session.dirty` and `db_session.new` empty checks.
- [x] Time the word-set load: fresh process, one warm-up, median of 3.
  → verify: write the measured seconds here. Above 3 s: stop and ask the owner about a cache.
    RESULT: 1.26, 1.31, 1.32 s (n=3 after one warm-up, median 1.31 s, load average 1.9,
    1,135,694 words). Under 3 s, so no cache.
    Test file note: a module fixture reads the lists once, so the 20-word random test does not
    pay 1.3 s each (it took 41 s without it, 4 s with it).

## Phase 2 — Frequency note — *Fast*

- [x] Failing tests first: a new word's page contains the note and not "no matches"; an
      edited word with a stored `freq_html` keeps it and shows no note.
  → verify: run them, expect both to fail, paste the output.
    RESULT: the new-word test failed (`assert 'Not yet built' in html`). The stored-frequency test
    passed already: it guards existing behaviour, so only one test could fail first.
- [x] In `render_preview`, if the copy's `freq_html` is empty, set it to the note (one
      sentence, wording agreed with the owner at review). Check the template's frequency
      block markup so the note sits inside valid HTML.
  → verify: `uv run pytest tests/gui2/test_preview.py -k freq` passes; open the page text for
    word 7 and read the frequency box wording.
    RESULT: 25 passed. Wording: "Not yet built. The frequency is worked out when the dictionary
    is built." It follows the heading "Frequency of X and its declensions" after a line break.
    Owner can change the wording at review (constant `FREQUENCY_NOT_BUILT`).

## Phase 3 — Audio — *Pro*

- [x] Probe first, in this thread's `artifacts/`: for 3 words that have audio, read the
      three recordings with `get_audio_record` and print byte sizes and read time. Do not
      run it on the contributor server.
  → verify: write sizes and times here. If one page would exceed about 2 MB or a read takes
    over 2 s, stop and ask the owner.
    RESULT (probe: `artifacts/audio_probe.py`, words a, dhamma, akakkasa): each recording is
    1,677 to 7,149 bytes, each read 1 to 9 ms. One word's page gains under 25 KB. No stop.
- [x] Failing tests first: (a) a word with audio (id picked from the audio index, real row)
      has `data:audio` in the page and no hide rule; (b) a word with no audio keeps the hide
      rule; (c) with the audio db path pointing at a missing file, the audio reader is never called
      and the file is not created (changed 2026-11-18: no server check, owner decision); (d) a missing index leaves the page working, button
      hidden. Update `test_page_is_dark_opens_grammar_and_hides_audio` to the new rule.
  → verify: run them, expect (a) to fail now. Paste the output.
    RESULT: 4 failed, 2 passed before the change (embed, headless, missing-index and the node
    shim test failed; the no-audio test passed as a guard). `assert script` raised on None.
    The old test `test_page_is_dark_opens_grammar_and_hides_audio` asserted the hide rule on
    word 8, which has audio. It is now `test_page_is_dark_and_opens_grammar`; the hide rule
    is tested on a word with no audio.
- [x] Write `_audio_script(db_session...)` in `gui2/preview.py` (or a small new module if it
      grows): build a JS map keyed `<lemma_clean>|<gender>` with the fallback rules of
      `get_audio_record`, and a shim for `window.Audio` that turns
      `/audio/<encoded word>?gender=<g>` into the data URI (strip the trailing ` \d.*$` like
      the server). Insert it before `dpd.js` runs its clicks; drop the hide rule only when
      audio was embedded.
  → verify: `uv run pytest tests/gui2/test_preview.py` all pass. Run the JS shim logic in
    `node` on a sample map and URL, expect the data URI back for `male`, `female`, `male1`.
    RESULT: 30 passed. The node test runs the real script from the page and checks `male`,
    `female`, `male1`, `male2`, `female1`, an unknown gender, a numbered headword
    (`akakkasa%201`) and a different word (left as the server url).
- [x] Revert check: remove only the audio wiring, run the audio tests, restore in the same
      command.
  → verify: (a) fails on revert and passes after restore. Report the counts.
    RESULT: with the audio call removed, 2 failed (embed, node shim), 28 passed. The two
    guard tests pass on that revert by design, so each guard was removed on its own:
    missing-file `except` removed gives 1 failed (missing-index test).
    CHANGED 2026-11-18: the first version had a contributor-server check
    (`is_headless_server`). The owner said the server only adds new words, so all that is
    wanted is a quiet skip when the audio db is missing. That check is gone; the preview tests
    `exists()` on the db path instead. The new test `test_missing_audio_db_is_skipped_without_creating_it`
    failed before the change (reader called 3 times) and passes after; 30 passed. File restored with `cmp`, 30 passed.

## Phase 4 — Word list fix — *Fast*

- [x] Failing test first, `tests/tools/test_all_tipitaka_words.py`: a word that is in
      `sc_wordlist.json` and in no other list is in the set. Pick it from the real files.
  → verify: run it, expect it to fail now. Paste the output.
    RESULT: failed before the fix: `assert 'abbhantarajātaka' in make_all_tipitaka_word_set()`.
    New file `tests/tools/test_all_tipitaka_words.py`.
- [x] In `tools/all_tipitaka_words.py` open `pth.sc_wordlist` for `sc_wordlist`.
  → verify: the test passes; `uv run ruff check`, `ruff format`, `pyright` clean on both files.
    RESULT: test passes; ruff and pyright clean on both files.
- [x] Measure the effect without a rebuild: print the set size before and after, and the
      count of SuttaCentral words that the other three lists lack (probe in `artifacts/`).
  → verify: write the three numbers here. Note which two build scripts read the set and
    that their output changes at the next db rebuild.
    RESULT (probe `artifacts/wordlist_effect_probe.py`): set before 1,135,694 words, after
    1,143,761, so 8,067 words added. The earlier 32,796 compared the SC list with SYA alone;
    8,067 is what the other three lists lack. Of 500 sampled tables, 26 get different grey
    cells. Readers: the inflection table build and `inflections_to_headwords.py`.

## Phase 5 — Verify — *Fast*

- [x] Equivalence over real data, run against the OLD word set (before Phase 4's file edit,
      or by building the old set in the probe): for at least 300 db words with a pattern,
      compare `make_inflection_table` to the stored `inflections_html`. Probe in `artifacts/`.

  → verify: print equal and different counts. Explain every different row. Zero unexplained.
    RESULT: probe `artifacts/equivalence_probe.py`, 500 random words with a pattern (of 80,267):
    equal 500, different 0, no template 0. Run before the word-list fix.
- [x] Revert check for Phases 1 and 2: undo each preview change in turn, run its tests,
      restore in the same command.
  → verify: each set of new tests fails on its revert and passes on restore. Report counts.
    RESULT: Phase 1 reverted: 2 failed, 28 passed. Phase 2 reverted: 1 failed, 29 passed (the
    stored-frequency test is a guard and passes either way). Restored with `cmp`, 30 passed.
- [x] Lint and types on each touched file (`ruff check --fix`, `ruff format`, `pyright`;
      `--project /dev/null` for `gui2/` and `tests/`), then `just typecheck`.
  → verify: zero errors. Check `ruff format` did not rewrite unrelated lines.
    RESULT: ruff check and format clean, pyright clean on all five touched files
    (`--project /dev/null` for `gui2/` and `tests/`), `just typecheck`: 0 errors. The IDE
    showed stale errors (undefined names, unresolved flet) that the command line does not.
- [ ] Owner run (`just gui`): preview a word with audio, press play, hear it; press the
      declension or conjugation button; press frequency.
  → verify: sound plays, table shows with grey cells, frequency note reads right, the word
    saves normally afterwards. If sound is silent in the browser, record it and stop.
- [x] Phase check: `uv run pytest tests/gui2 tests/db tests/tools`.
  → verify: no new failures; note any that already failed.
    RESULT: `uv run pytest tests/gui2 tests/db tests/tools tests/audio tests/exporter
    tests/scripts tests/db_tests tests/newsletter tests/onboarding tests/test_typecheck_gate.py`:
    3342 passed, 2 failed. PRE-EXISTING — NOT CAUSED BY THIS THREAD:
    `tests/tools/test_docs_update_abbreviations.py::test_make_abbreviations_md_golden_master` and
    `tests/exporter/goldendict/test_export_help.py::test_abbrev_sample[0]`. Both read the
    abbreviations data (the latest commit changed it); neither imports a module this thread
    touched (grep: 0 files).

## Review round (DeepSeek flash via pi, thinking off; CodeRabbit per folder) — 2026-11-18

Validated against the code. Fixed:
- DeepSeek 6 (real): the frequency note also showed for a saved word with no matches
  (4,878 such words). Now only for a word not in the db. New test
  `test_existing_word_without_matches_keeps_the_webapp_text` (word 108) failed first.
- CodeRabbit: `Container[str]` became `Set[str]` (a plain string would match substrings).
- CodeRabbit (major): the autouse word-list fixture no longer errors when the lists are absent.
- CodeRabbit: the two audio tests skip when the audio db or index is not downloaded.
- CodeRabbit: the node audio test compares each voice with the real recording, and builds the
  url with `encodeURIComponent`.
- CodeRabbit (unverified, accepted): the word-list test now uses four temporary lists, so it
  runs everywhere. Reverting the fix makes it fail.

Rejected, with reasons:
- DeepSeek 1 and 2: `render_preview` writes only to a transient copy that is never added to
  the session, and never to the word the caller saves. Preview tests assert `session.new`
  and `session.dirty` stay empty. The claimed old behaviour (preview filling the live word)
  never existed.
- DeepSeek 3: a table with an empty stem still has the headword in its heading. The build
  makes the same table; the preview mirrors it by design.
- DeepSeek 4: `decodeURIComponent` undoes `encodeURIComponent` for every character.
- DeepSeek 5: the engine-per-call is in the shared audio helper, and costs milliseconds.
  Not touched.
- DeepSeek 7: true that the rebuild also changes lookup and i2h output. The spec says so;
  the i2h delta was not measured.
