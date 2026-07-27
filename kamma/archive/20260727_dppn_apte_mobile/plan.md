# Plan — Add DPPN and Apte to the mobile database

Spec: `spec.md` in this directory. Read it first.

## Architecture Decisions

1. **Copy the existing per-dictionary block, don't abstract it.**
   `export_other_dictionaries` is a sequence of near-identical ~35-line blocks
   (Cone, WordNet, PEU, CPD, MW, BHS). Two more blocks fit that pattern. Factoring
   out a shared helper would touch six working blocks for no functional gain and
   is out of scope.

2. **DPPN before Apte.** DPPN is self-contained: its source is already restored
   by the existing build step, so it can be built and verified with zero
   infrastructure work. Apte needs a source-preparation change in the submodule
   first. Doing DPPN first gets a working, verifiable dictionary in the database
   before touching the build pipeline.

3. **Apte's source preparation mirrors Monier-Williams exactly.**
   `mw_from_cologne.py` exposes `build_mw_json(pth)` extracted out of its `main()`,
   and `prepare_sources.py` calls it. Apte gets `build_apte_json(pth)` in the same
   shape. This is the established sibling pattern; do not invent a new one.

4. **Apte's HTML is cleaned in the app, not the exporter.** The app's
   `_cleanMwHtml` already does exactly what Apte needs. Routing `apte` through it
   is one line and keeps the two Cologne dictionaries on one code path. Doing it
   in the exporter would fork the behaviour.

5. **No schema version bump.** Verified against commit `f0602dec`, which added
   WordNet and PEU to every release without touching `DB_SCHEMA_VERSION`.

6. **Three repos, three commits.** Submodule (`resources/other-dictionaries`)
   first, then `dpd-db` including the submodule pointer bump, then
   `dpd-flutter-app`. Do not commit anything without explicit user permission.

---

> **Deviation from the original plan (2026-07-27).** The Apte exporter block
> (Phase 3, task 1) was written in the same edit as the DPPN block, since both
> live in the same function in the same file and splitting the edit gained
> nothing. `dppn` was also added to `mobile_critical` in `prepare_sources.py`
> alongside `apte`, which the plan had not called for — it is free and makes the
> pre-build check cover every dictionary the mobile export now hard-requires.
> Verification order is unchanged: DPPN is still verified before Apte.

## Phase 1 — DPPN in the mobile database

- [x] Add the DPPN block to `export_other_dictionaries` in
      `exporter/mobile/mobile_exporter.py`, placed after the BHS block.
  - Read `pth.dppn_source_path` (a JSON list of `{"name", "entry"}`); raise
    `_missing_source_error("DPPN", g.pth.dppn_source_path)` if absent.
  - Skip any item whose `name` contains `class="Heading3"` (38 alphabet dividers).
  - `word` = text of the **first** `<b>…</b>` in `name`, stripped, `ṁ` → `ṃ`.
  - `definition_html` = `name + entry`, then remove that first `<b>…</b>`
    occurrence once, then drop a head `<span>` that contains nothing but
    whitespace and an optional full stop, then `ṁ` → `ṃ`. Keep the surrounding
    `<p>` … `</p>` intact.
  - `word_fuzzy` = `_strip_diacritics_mobile(word)`; `definition_plain` = `""`.
  - `dict_meta`: `("dppn", "Dictionary of Pāli Proper Names",
    "G. P. Malalasekera, revised by Ānandajoti Bhikkhu",
    _sanitize_css(pth.dppn_css_path.read_text(encoding="utf-8")), len(batch))`.
  - Follow the surrounding style: `pr.green_tmr(...)` before, `pr.yes(len(batch))` after.

  → verify: `uv run python exporter/mobile/mobile_exporter.py` completes and the
  DPPN step prints `13604`.

- [x] Verify the DPPN rows in the built database.
      **Done 2026-07-27.** All four checks passed. Note: the built database is at
      `exporter/share/dpd-mobile.db`, not `exporter/mobile/`.

  → verify: against `exporter/mobile/dpd-mobile.db`, all four must hold —
  (a) `SELECT name, entry_count FROM dict_meta WHERE dict_id='dppn'` →
  `Dictionary of Pāli Proper Names | 13604`;
  (b) `SELECT definition_html FROM dict_entries WHERE dict_id='dppn' AND word='Akataññujātaka'`
  starts with `<p><span class="Head"> (` , contains `Ja 90`, and does **not**
  contain `<b>Akataññujātaka</b>`;
  (c) `SELECT definition_html FROM dict_entries WHERE dict_id='dppn' AND word='Akatti'`
  has no leading stray `.` before `See`;
  (d) `SELECT COUNT(*) FROM dict_entries WHERE dict_id='dppn' AND (word LIKE '%ṁ%' OR word IN ('A-An','Ā','Kh','Mahā'))` → `0`.

- [ ] Phase 1 verification: load the database in the app and search a proper name.

  → verify: search `Anāthapiṇḍika`; a card titled *Dictionary of Pāli Proper Names*
  appears, the headword is shown once (not twice), the entry text is readable
  with no raw HTML tags visible, and the dictionary appears in the dictionary
  settings list with a working on/off toggle.

---

## Phase 2 — Apte source preparation (submodule)

Working directory for this whole phase: `resources/other-dictionaries`.

- [x] Extract `build_apte_json(pth: RepoPaths) -> list[DictEntry]` from
      `dictionaries/apte/apte_from_cologne.py::main`, mirroring
      `dictionaries/mw/mw_from_cologne.py::build_mw_json` (lines 18–47) —
      download, load, build entries, write `pth.apte_json_path`, return the
      entries. `main()` then calls it and keeps only the `DictInfo` /
      `DictVariables` / export calls. Behaviour must be unchanged.

  → verify: `uv run python -m dictionaries.apte.apte_from_cologne` still writes
  `source/apte.json` with 34,277 entries and still produces
  `build/goldendict/apte.zip` and `build/mdict/apte.mdx.zip`.

- [x] Call `build_apte_json(pth)` from `scripts/prepare_sources.py` next to the
      existing `build_mw_json(pth)` call, and add both
      `"apte": pth.apte_json_path` and `"dppn": pth.dppn_source_path` to the
      `mobile_critical` dict.

  → verify: delete `dictionaries/apte/source/apte.json`, run
  `uv run python scripts/prepare_sources.py`, expect exit code 0, an `apte` line
  in the mobile-critical report showing ~39 MB, and the file recreated.

---

## Phase 3 — Apte in the mobile database

- [x] Add the Apte block to `export_other_dictionaries` in
      `exporter/mobile/mobile_exporter.py`, placed after the DPPN block, copying
      the Monier-Williams block's structure.
  - Read `pth.apte_source_json_path` (list of `{"word", "definition_html", …}`);
    raise `_missing_source_error("Apte", g.pth.apte_source_json_path)` if absent.
  - `word` = `entry["word"]`; `definition_html` = `entry["definition_html"]`
    unchanged (the document wrapper is stripped in the app, as it is for MW);
    `word_fuzzy` = `_strip_diacritics_mobile(word)`; `definition_plain` = `""`.
  - `dict_meta`: `("apte", "Apte Practical Sanskrit-English Dictionary, 1890",
    "Vaman Shivram Apte",
    _sanitize_css(pth.apte_css_path.read_text(encoding="utf-8")), len(batch))`.

  → verify: `uv run python exporter/mobile/mobile_exporter.py` completes, the
  Apte step prints `34277`, and
  `SELECT name, entry_count FROM dict_meta WHERE dict_id='apte'` →
  `Apte Practical Sanskrit-English Dictionary, 1890 | 34277`.

- [x] In `dpd-flutter-app`, route `apte` through the existing Monier-Williams
      cleaning in `lib/widgets/dict_html_card.dart::prepareDictHtml` —
      change `if (dictId == 'mw')` to also match `apte`. Nothing else.

  → verify: `flutter analyze` clean; then in the app search `aṃhati` — an
  *Apte Practical Sanskrit-English Dictionary, 1890* card appears with no
  visible `<!DOCTYPE`, no `(H1)` marker, italic/coloured styling matching the
  Monier-Williams card, and a tappable reference tooltip.

- [x] Phase 3 verification: full mobile export from clean sources.
      **Done 2026-07-27.** `prepare_sources.py` exit 0, all five mobile-critical
      files present (cpd 29.3 MB, bhs 8.5 MB, mw 200.2 MB, apte 40.7 MB,
      dppn 7.0 MB). Export exit 0 in 2:40 with counts: wordnet 111,198 /
      peu 203,865 / cpd 29,734 / mw 194,084 / bhs 17,836 / **dppn 13,604** /
      **apte 34,277**. Mobile db 1089.6 MB, **zip 243.0 MB** (built without
      `--cone`, matching CI; the previously observed 272 MB zip included Cone).

  → verify: `cd resources/other-dictionaries && uv run python scripts/prepare_sources.py`
  then `uv run python exporter/mobile/mobile_exporter.py` from the repo root —
  both exit 0, `SELECT dict_id, entry_count FROM dict_meta ORDER BY dict_id`
  lists all eight dictionaries (`apte, bhs, cpd, dppn, mw, peu, wordnet` plus
  `cone` if built with `--cone`) with non-zero counts, and the reported zip size
  is recorded here for comparison against the previous 272 MB.

---

## Phase 4 — Case-insensitive exact dictionary match (added mid-thread)

Added at the user's request after manual testing. Full diagnosis in `spec.md`
under "Added mid-thread". All work is in `dpd-flutter-app`.

- [x] Benchmark the candidate queries against the real 604,000-row
      `dict_entries` table before writing any code — the user required proof
      that the airtight query costs no more time than the current one.
      Each strategy timed in its own fresh process; median and p95 over 20
      iterations after 3 warmups; `EXPLAIN QUERY PLAN` captured for each.

  → verify: results table recorded below, with a plain verdict on whether any
  correct case-insensitive strategy is measurably slower than the current
  `word = ?`.

  **Results (2026-07-27, moderate system load, gaps span 3 orders of
  magnitude so the load does not affect the conclusion):**

  | Strategy | Query plan | Median | Correct |
  | --- | --- | --- | --- |
  | A `word = ?` (current) | **full scan** | 85–121 ms | ✗ misses capitals |
  | `lower(word) = ?` | full scan | 135–149 ms | ✗ (empirically dropped `Ṭhakuraka`) |
  | B `word_fuzzy = ?` | full scan | 87–128 ms | ✓ |
  | C loop `dict_id=? AND word_fuzzy=?` ×7 | index seek | 0.014–0.235 ms | ✓ |
  | D `word_fuzzy=? AND dict_id IN (…)` | index seek | 0.009–0.55 ms | ✓ |
  | E existing fuzzy `LIKE 'key%'` (baseline) | full scan | 0.06–98 ms | — |

  **Verdict:** the airtight fix costs nothing. `EXPLAIN QUERY PLAN` confirmed
  the crux — strategy A was *already* full-scanning, because `word` alone
  cannot seek `idx_dict_entries_word (dict_id, word)` without `dict_id`.
  Supplying `dict_id` makes C and D index seeks, 400×–5000× faster than the
  query they replace. Candidate superset stays tiny (worst case 58 rows for
  `Tissa`), so the Dart-side comparison is negligible. **Chose D** — one query
  instead of seven, same speed.

- [x] Add a case-insensitive exact lookup to `DictDao` in
      `lib/database/dao.dart`, using whichever strategy the benchmark supports.
      It takes the fuzzy key, fetches the candidate superset, and returns only
      rows where `row.word.toLowerCase() == query.toLowerCase()` (Dart's
      `toLowerCase`, which folds accented capitals; SQLite's does not).
      Leave `searchDictPartial` and `searchDictFuzzy` alone.

  → verify: `flutter analyze` clean.

- [x] Call it from `_dictRawResultsProvider` in
      `lib/providers/dict_provider.dart` in place of
      `dao.searchDictExact(query.toLowerCase())`, passing the same fuzzy key
      already computed for the fuzzy search. Ensure rows promoted to exact are
      excluded from the partial and fuzzy tiers, as `fromRows` already does via
      `excludedFromFuzzy` — extend that exclusion to `partial` if the exact row
      also appears there.

  → verify: in the app, each of these lands in the **exact** tier, not partial
  or fuzzy — `anāthapiṇḍika`, `Anāthapiṇḍika`, `AKATTI`, `tissa`, and an
  accented-capital name (`ānanda`, `ñāṇamoli`). Confirm `dhamma` and other
  ordinary lowercase searches are unchanged, and that no entry now appears in
  two tiers at once.

- [x] Add a unit test for the case-insensitive matching logic.
      Data logic only — the project forbids UI tests for this app.

  → verify: `flutter test` passes, including a case covering an accented
  capital. **Done 2026-07-27** — 7 new cases in `test/database/dao_test.dart`;
  full app suite green.

  **Second deviation:** two existing fixtures in
  `test/providers/dict_provider_test.dart` hard-coded `wordFuzzy: 'buddha'`,
  a value the exporter would never produce (`_strip_diacritics_mobile`
  collapses the aspirate and the doubled consonant, giving `buda`). The old
  `word = ?` lookup never read that column, so the wrong value went unnoticed.
  The new lookup does read it, and those two tests failed. Fixed by computing
  the fixture value with `stripDiacritics` instead of hard-coding it — the
  fixtures now match what the real database contains.

## Phase 4b — Fuzzy-key parity regression (found in review)

The independent audit caught a **critical regression introduced by Phase 4**.
CodeRabbit did not catch it (0 findings on the same files).

**The defect.** `searchDictExact` builds its key with Dart's `stripDiacritics`
and matches it against the stored `word_fuzzy`, which the Python exporter
generates. The two were not equivalent: Python NFD-decomposes and drops every
Unicode combining mark, while Dart used a closed 25-entry map covering the Pāḷi
set only. Every Sanskrit letter was absent.

Measured against the shipped database: **78,000 rows, 12% of the table** —
~34% of Monier-Williams, ~24% of Apte, ~26% of BHS. Apte is a Sanskrit
dictionary, so a quarter of the dictionary this thread ships would have been
demoted from exact to partial on day one. DPPN has zero affected rows, which is
exactly why manual testing passed.

| word | stored key | Dart produced | result |
| --- | --- | --- | --- |
| `aṃśa` | `amsa` | `amśa` | no exact match |
| `ṛṣi` | `rsi` | `ṛṣi` | no exact match |
| `akaniṣṭha` | `akanista` | `akaniṣta` | no exact match |

- [x] Derive the missing characters from the real data rather than guessing —
      22 distinct characters, led by `ś` (37,806), `ṣ` (34,454), `ṛ` (19,604).
- [x] Add them to `_diacriticMap` in `lib/utils/diacritics.dart`, plus a
      combining-mark range check so decomposed input folds too.
- [x] Document the parity requirement in the function's doc comment, naming the
      exporter function that must stay in sync.

  → verify: ported the patched Dart algorithm to Python and ran it against every
  row of the built database — **606,004 rows, 0 mismatches**. Cone was absent
  from that build (another session rebuilt the db without `--cone`), so it was
  checked separately from its source: **37,395 keys, 0 mismatches**. Parity now
  holds for all 643,399 headwords across all eight dictionaries.

- [x] Add `test/utils/diacritics_test.dart` pinning the expectations to the
      values actually stored in the database, with the Sanskrit cases called out
      as a regression guard.

**Lesson for `kamma/lessons.md`:** when Dart-side and Python-side
implementations of the same transform must agree, verify parity across the whole
real dataset, not with a handful of examples. The examples chosen by hand were
all Pāḷi, and Pāḷi was the one subset that already worked.

## Phase 4c — DPPN head line moves into the displayed title (user request)

Manual review showed the head-line residue reading badly at the start of the
body: 437 entries began `, `, 94 began `. `, one began `.. `. User chose to move
that material into the displayed title instead of stripping or keeping it inline.

**Decided against a database change.** `definition_plain` is declared but read
nowhere in the app and is `""` for every dictionary, so it was available — but
naming a display title "plain definition" is misleading, and any new column
would force a schema bump and a full re-download for every user. The head span
is already in the stored HTML, so the app can do this alone. Works on databases
already built; no rebuild needed.

- [x] `dppnDisplayTitle(word, html)` in `lib/widgets/dict_html_card.dart` reads
      the `<span class="Head">` residue, strips tags, collapses whitespace and a
      doubled full stop, and joins it to the headword — directly when it starts
      with punctuation, with a space otherwise. A span holding only punctuation
      is dropped, leaving the bare word.
- [x] `prepareDictHtml` removes that span from the body for `dppn`.
- [x] The card titles DPPN entries with it; every other dictionary is untouched.

  → verify: `test/widgets/dppn_title_test.dart`, fixtures copied verbatim from
  `definition_html` in the built database. Renders as
  `Ajitajana, Abhitatta.` / `Atthakaraṇasutta. (v.l. Aṭṭakaraṇasutta).` /
  `Akataññujātaka (Ja 90).` / `Anāthapiṇḍika 01.`, with bodies no longer
  starting with stray punctuation.

## Phase 5 — Review and finalise

- [x] Run the project test suite for the affected area.
      **Done 2026-07-27.** `uv run pytest tests/ -q` → 1,719 passed, 1 failed,
      17 deselected in 70s. The single failure is
      `tests/tools/test_docs_update_bibliography.py::test_make_bibliography_md_matches_golden_master`
      — a stale golden-master fixture missing two Oberlies 2019 grammar volumes
      that have since been added to the database. Unrelated to this thread
      (no shared code path); pre-existing drift, left alone.

  → verify: `uv run pytest tests/` passes with no new failures (note: there are
  no existing mobile-exporter tests; this is a regression check on everything else).

- [x] Hand off for `/kamma:3-review`, then apply findings.

  → verify: `review.md` exists in this thread directory with no unresolved
  blocking findings. **Done 2026-07-27.** CodeRabbit (3 scopes, 0 findings; a
  4th rate-limited) plus an independent audit (5 findings, one critical). All
  resolved; three items deliberately deferred and recorded. Three lessons added
  to `kamma/lessons.md`.

**Cross-session note (2026-07-27).** A parallel session is working in the same
two repos. Do not stage: `justfile`, `pyproject.toml`, `uv.lock`,
`tools/compound_type_manager.tsv`, or any `kamma/threads/` directory other than
this one. `assets/help/bibliography.tsv` in the app now holds *both* this
thread's Malalasekera row and the other thread's Nyanatiloka row — user decided
**that file is left out of this thread's commit** and the other thread carries
both rows.

- [ ] Commit, in order, **only after explicit user permission**:
  1. `resources/other-dictionaries` — `refactor: extract build_apte_json for the mobile build`
  2. `dpd-db` (includes the submodule pointer bump) —
     `feat: mobile releases now include Pāli Proper Names and Apte Sanskrit dictionaries`
  3. `dpd-flutter-app` — `fix: Apte Sanskrit entries now render like Monier-Williams`

  → verify: `git status` clean in all three repos; `git submodule status` in
  `dpd-db` points at the new submodule commit.
