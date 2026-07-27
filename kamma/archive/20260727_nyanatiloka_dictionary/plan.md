# Plan — Add Nyanatiloka's Buddhist Dictionary

Spec: `spec.md` in this directory. Read it first.

## Architecture Decisions

1. **Scrape once, commit static JSON — no scraper kept in the repo.** Mirrors
   DPPN (`DPPN.json` is a committed, compressed source with no in-repo
   fetch script), not Apte/MW (which re-downloads from Cologne every build
   because that upstream changes). dhammatalks.net's own footer shows the
   text was last saved 2005 per the site's own footer, and no new edition
   of the underlying book has appeared since 1980 — nothing to keep in sync.

2. **BeautifulSoup, not regex, for the HTML parse.** Real fetched markup
   (`dic3_a.htm`) contains malformed tag nesting (`</p></i>` reversed order)
   and inline `<b>` inside entry bodies unrelated to entry boundaries — a
   tolerant parser is required, matching `simsapa_combined.py`'s own
   approach to similarly messy HTML.

3. **`<p>` is the entry boundary, not `<b>` count.** 197 `<p>` blocks vs 213
   `<b>` tags on page "A" alone — 16 bolds are inline emphasis, not new
   entries. Confirmed by direct inspection, not assumed.

4. **No app change.** `prepareDictHtml` in `dpd-flutter-app` only
   special-cases `cone`/`mw`+`apte`/`cpd`; everything else renders as-is
   through `HtmlWidget`, which handles `<p>`/`<b>`/`<i>`/`<blockquote>`
   natively. Verified by reading the Dart source, same conclusion DPPN
   reached.

5. **No schema version bump.** Adding rows to `dict_entries`/`dict_meta`,
   not columns — same basis as DPPN/Apte/WordNet/PEU.

6. **Three commits, in order, only after explicit user permission:**
   submodule (`resources/other-dictionaries`) first, then `dpd-db` (mobile
   exporter block + `tools/paths.py` + docs + submodule pointer bump). No
   `dpd-flutter-app` commit is expected since no code changes there.

7. **Licensing posture: attribute, don't claim an open license.** Same
   posture already used for DPPN/CPD/MW/Apte — none of those carry a
   verified open license either, and DPD ships them with author/editor
   attribution in `dict_meta`. Flagged explicitly in spec.md as a judgment
   call, not silently assumed.

---

> **Deviation from the original plan (2026-07-27).** The spec assumed one
> consistent HTML shape (`<p><b>word</b>: definition</p>`) based on page A
> alone. Fetching all 22 pages showed the site was hand-edited across at
> least three inconsistent shapes: `<p><b>word</b>...` (page A), `<b><p>word:
> </b>...` — bold opened *before* the paragraph (page B), and
> `<p><font...><b>word</b>...` — an inline `<font>` wrapper between `<p>` and
> `<b>` (page D). The parser segments entries by locating either tag order
> (with optional `<font>`/`<a>` wrappers in between) rather than assuming a
> single shape, and additionally strips a stray alphabet-divider prefix
> (`-B-\n\nbahula-kamma` → `bahula-kamma`) that occurs when the divider's own
> `<b>` stays open into the next real entry, and drops the page-title
> "BUDDHIST DICTIONARY" pseudo-entry that the same wrapper pattern also
> matches. `<font>` tags are unwrapped throughout (no CSS classes use them).
> Final count is 1,406 entries, not the "low thousands" estimate — see
> Phase 1 task 3 below for the exact per-letter breakdown. See
> `spec.md`'s updated "Data shape" section for the corrected extraction
> rules.

## Phase 1 — Acquire and verify the source data

- [x] Fetch all 22 dhammatalks.net pages with `curl` (not `WebFetch`, which
      paraphrases through a summarizing model and won't return verbatim
      markup): `dic3_a.htm dic3_b.htm dic3_c.htm dic3_d.htm dic3_e.htm
      dic3_f.htm dic3_g.htm dic3_h.htm dic3_i.htm dic3_j.htm dic3_k.htm
      dic3_l.htm dic3_m.htm dic3_n.htm dic3_o.htm dic3_p.htm dic3_r.htm
      dic3_s.htm dic3_t.htm dic3_u.htm dic3_v.htm dic3_w-z.htm dic3_y.htm`.
      Save to a scratch directory, not the repo.

  → verify: 22 files saved, each non-trivial in size (compare against the
  99,720-byte "A" page as a sanity floor for the more populous letters).

- [x] Write a one-off parser script (scratch, not committed) that, per page:
      finds the main content `<blockquote>`, iterates its `<p>` children,
      skips the alphabet-divider row and any footer/nav `<p>`, extracts
      `word` from the first `<b>…</b>`, builds `definition_html` per the
      spec's data-shape section (strip that first bold once, unwrap `<a>`
      tags to plain text, decode HTML entities).

  → verify: ran against `dic3_a.htm` alone first, then all 22 pages once the
  parser was generalised (see deviation note below). Spot-checked the
  `anabhirati-saññā` / `Anāgāmī` malformed-nesting boundary (correctly
  resolved as two separate entries, and `Anāgāmī`'s multi-paragraph numbered
  list body is fully preserved) and multiple entries containing
  `dic2-abbrev.htm` links (correctly unwrapped to plain text, e.g. `A. IV,
  57` instead of a dead link).

- [x] Run the parser across all 22 pages, concatenate into
      `nyanatiloka.json`, record the actual total entry count here in this
      file (replacing the "low thousands, TBC" estimate in spec.md).

  **Result: 1,406 entries** (per-page: a197 b46 c84 d92 e37 f35 g23 h21 i50
  j12 k76 l24 m82 n61 o22 p122 r46 s167 t48 u52 v79 w-z17 y13).

  → verify: no duplicate headwords across letter boundaries — checked: only
  2 words repeat at all (`conception` ×2, both legitimate distinct
  sub-entries "1." and "2." within the C page, not a parse artifact; no
  cross-letter repeats). Spot-checked `questions and answers` (folded into
  `dic3_r.htm` since Q has no own page) and multiple entries from
  `dic3_w-z.htm`/`dic3_y.htm` — all correct.

---

## Phase 2 — `other-dictionaries` submodule

Working directory for this whole phase: `resources/other-dictionaries`.

- [x] Add `dictionaries/nyanatiloka/source/nyanatiloka.json`,
      `dictionaries/nyanatiloka/nyanatiloka.css`, and
      `dictionaries/nyanatiloka/README.md` (source URL, scrape date, BPS
      edition/ISBN, per spec.md).

- [x] Add `_setup_nyanatiloka_paths` to `vendor/dpd_tools/paths.py`, mirroring
      `_setup_dppn_paths` (lines 84–89).

- [x] Write `dictionaries/nyanatiloka/nyanatiloka.py`, mirroring `dppn.py`'s
      shape: load JSON, build `DictEntry` list (no synonyms), `DictInfo`
      per spec.md, `export_to_goldendict_with_pyglossary` +
      `export_to_mdict` (default `h3_header=True`).

  → verify: `uv run python -m dictionaries.nyanatiloka.nyanatiloka` produces
  `build/goldendict/nyanatiloka.zip` (208 KB) and `build/mdict/nyanatiloka.zip`
  (the mdict output is `.zip`, not `.mdx.zip` as originally guessed in
  spec.md — matches every other dictionary's actual build output, e.g.
  `dppn.zip`, `apte.zip`; corrected in spec.md) with 1,406 entries — ran
  clean, 0 errors.

- [x] Compress the new source: run `scripts/compress_sources.py`, confirm
      `dictionaries/nyanatiloka/nyanatiloka.tar.zst` is created (glob-based,
      no explicit registration needed per spec.md).

  → verify: created, 154 KB from 0.6 MB source. Deleted the source JSON and
  re-ran `decompress_sources.py` — restored correctly, 1,406 entries intact.

  **Self-caught mistake:** running the unscoped `compress_sources.py` (it
  compresses every dictionary's `source/` dir, not just the new one)
  recompressed `cpd.tar.zst`/`peu.tar.zst`/`wordnet.tar.zst` with spurious
  byte-diffs (tar embeds mtimes), and the subsequent `prepare_sources.py`
  run's live Apte/MW rebuild caused `compress_sources.py`-adjacent code to
  create `dictionaries/apte/apte.tar.zst` and `dictionaries/mw/mw.tar.zst`,
  which shouldn't exist at all — Apte/MW deliberately have no committed
  archive (they rebuild from Cologne live every time, per `apte_from_cologne.py`/
  `mw_from_cologne.py`). Reverted the three spurious binary diffs with
  `git checkout --` and deleted the two archives that shouldn't exist.
  `git status` in the submodule now shows only the intended files. This
  matches a known project rule (compress scoped, per-dictionary, never
  the blanket script) that I violated and then caught before commit.

- [x] Add `"nyanatiloka": pth.nyanatiloka_source_path` to `mobile_critical`
      in `scripts/prepare_sources.py`.

  → verify: deleted `dictionaries/nyanatiloka/source/nyanatiloka.json`, ran
  `uv run python scripts/prepare_sources.py` — exit code 0, `nyanatiloka
  0.6 MB` line present in the mobile-critical report alongside cpd/bhs/mw/
  apte/dppn.

- [x] Add a `nyanatiloka` row to the root `README.md` dictionary table.

- [x] **Scope addition (user request, 2026-07-27):** sweep every README/help/
      download-link location listing dictionaries, in both repos, not just
      the two originally planned in spec.md. Found and updated:
      - `resources/other-dictionaries/scripts/export_all.py` — the "build
        everything" orchestrator did not import/call `nyanatiloka`; added,
        since without this the new dictionary would silently never be built
        by the one-shot "build all" entry point even though `prepare_sources.py`
        and the mobile exporter were already wired up.
      - `resources/other-dictionaries/.github/workflows/build-and-release.yml`
        — the actual GitHub Release notes table (real download links users
        see); added a row.
      - `resources/other-dictionaries/README.md` — dictionary table (done
        above).
      - `dpd-db/docs/other_dicts.md` — GoldenDict table, MDict table, and a
        new description section mirroring DPPN's, plus a cross-reference
        note on the existing Simsapa section (already in Phase 3's plan,
        done ahead of schedule here since it was part of the same sweep).
      - `dpd-db/docs/index.md` — one-line mention alongside "Critical Pāli
        Dictionary" in the GoldenDict/MDict intro paragraph.
      - `dpd-flutter-app/assets/help/bibliography.tsv` — added a row
        (alphabetically, between Malalasekera and Rhys Davids), matching the
        13-column TSV shape exactly.
      - Checked and found NOT applicable (left untouched): `dict_settings_widget.dart`
        (dictionary list is driven from `dict_meta` at runtime, no hardcoded
        list to edit — confirmed by reading the file, not assumed);
        `dpd-db/README.md` and `dpd-flutter-app` screen files (no dictionary
        list present, grep hits were false positives on unrelated words like
        "adapt").

---

## Phase 3 — Mobile database and dpd-db docs

- [x] Add `nyanatiloka_source_path` / `nyanatiloka_css_path` to
      `dpd-db/tools/paths.py`, mirroring the DPPN entry there.

- [x] Add the Nyanatiloka block to `export_other_dictionaries` in
      `exporter/mobile/mobile_exporter.py`, placed immediately after the
      existing (uncommitted) Apte block, per spec.md's code shape.

  → verify: `uv run python exporter/mobile/mobile_exporter.py` ran clean
  end-to-end (full 2m38s run against real `dpd.db`), printed `1,406` for the
  Nyanatiloka step, and `sqlite3 exporter/share/dpd-mobile.db "SELECT name,
  entry_count FROM dict_meta WHERE dict_id='nyanatiloka'"` returns
  `Buddhist Dictionary: Manual of Buddhist Terms and Doctrines | 1406`.

- [x] Spot-check rendered rows in the built database: queried `Anāgāmī`
  (the malformed-nesting multi-paragraph entry) — body renders correctly
  with the full 5-item structure intact, no leftover `<a href=`/`<font>`
  tags anywhere in the 1,406 rows, no unresolved `&#...;` entities.

- [x] Add a Nyanatiloka section to `dpd-db/docs/other_dicts.md`, alongside
      DPPN's, crediting Nyanatiloka/Nyanaponika/BPS and linking
      dhammatalks.net. (Done as part of the docs sweep recorded in Phase 2.)

- [x] Phase 3 verification: load the built database in the app and search a
      known headword (e.g. `Anāgāmī`) — confirm a *Buddhist Dictionary:
      Manual of Buddhist Terms and Doctrines* card appears, text is
      readable with no raw HTML tags or dead links visible, and the
      dictionary shows up in the dictionary settings list with a working
      on/off toggle. This is the concrete check for the "no app change
      needed" claim in spec.md — confirm it holds for real data, not just
      the plain-tag theory.

  → verify: user tested on a real Android device (not desktop Linux —
  required `just android-debug-push-db` via `adb`, not the `linux-push-db`
  recipe first tried, since the running app reads its db from Android app
  storage, not `~/Documents/`). First attempt showed no results at all for
  `Anāgāmī` — investigated and found the actual cause was unrelated to any
  code: the app's live database predated even DPPN/Apte (only
  `bhs`/`cpd`/`mw` in `dict_meta`, a stale file from a much earlier session
  that had never been refreshed). Not the DPPN "capitalised headword"
  search-tier bug the user suspected — confirmed by reading that bug's
  root cause in the sibling thread (case-folding/fuzzy-key parity in
  `dict_provider.dart`/`dao.dart`/`diacritics.dart`) and finding it
  structurally can't produce "zero results in every tier," only
  misclassification between tiers. After pushing the current build via
  `adb`, user confirmed `Anāgāmī` works; tested a second entry (`dāna`,
  from the page-D `<font>`-wrapped HTML shape) and confirmed. **User
  signed off — thread ready to finalize.**

---

## Phase 4 — Review and finalise

- [x] Run the project test suite for the affected area.

  → verify: `uv run pytest tests/` — 22 failed, 5 errors (collection),
  1702 passed. **All failures are pre-existing and unrelated to this
  thread**: they trace to a *different*, concurrently in-progress kamma
  thread's uncommitted schema change (`db/models.py`/`gui2/dpd_fields.py`
  add a `meaning_1_add` column not yet present in `dpd.db`, confirmed via
  `git status` showing those files modified before this thread started —
  this repo runs multiple kamma threads against the same working tree at
  once, per `CLAUDE.md`). `tools/ipa.py` and
  `shared_data/reference/bibliography.tsv` (a different file from the
  `dpd-flutter-app` one this thread edited) are also modified by that other
  session and explain the `test_ipa.py`/bibliography golden-master
  failures. Nothing touched by this thread (`mobile_exporter.py`,
  `tools/paths.py`, `resources/other-dictionaries`) has a test file, so
  there is no regression check specific to this thread's own code — same
  caveat the DPPN/Apte thread recorded.

- [x] Hand off for `/kamma:3-review`, then apply findings.

  → verify: `review.md` exists — a Sonnet subagent ran the full review
  independently (diffed only this thread's actual files across all three
  repos, re-ran ruff/pyright/pytest, re-derived the data-quality claims by
  re-parsing `nyanatiloka.json` itself rather than trusting the prose, and
  confirmed the compress_sources.py self-correction actually held). Verdict:
  **PASSED, no blocking findings.** One minor, non-blocking note: the
  Nyanatiloka mobile-export block read its CSS unconditionally
  (`nyanatiloka_css_path.read_text()`) instead of guarding with `.exists()`
  like every sibling block (DPPN, Apte, CPD, MW). Applied the fix
  (`exporter/mobile/mobile_exporter.py`) — now matches the established
  pattern exactly; re-ran ruff/pyright, both clean. CodeRabbit could not run
  for this review (free-tier rate limit) — separately run via isolated git
  worktrees per repo afterward, see below.

- [x] **CodeRabbit review (`coderabbit review --agent`), scoped to only this
      thread's files.** The repo runs multiple concurrent kamma threads in
      the same working tree, and CodeRabbit's `--dir` flag only scopes to a
      single directory — insufficient since this thread's files span
      several directories in each of three repos, alongside unrelated
      in-progress files from other threads. Used isolated `git worktree add
      --detach HEAD` per repo (never `git stash` a shared tree), copied in
      only this thread's changed/new files, ran CodeRabbit inside each
      worktree, then removed the worktrees. Hit CodeRabbit's free-tier rate
      limit (51-minute cooldown, then cleared gradually) before all three
      finished:
      - `dpd-db` (`docs/index.md`, `docs/other_dicts.md`,
        `exporter/mobile/mobile_exporter.py`, `tools/paths.py`): **0
        findings.**
      - `resources/other-dictionaries` (the full `dictionaries/nyanatiloka/`
        dir, `vendor/dpd_tools/paths.py`, `scripts/prepare_sources.py`,
        `scripts/export_all.py`, `.github/workflows/build-and-release.yml`,
        root `README.md`): **2 minor findings, both valid, both fixed** —
        `dictionaries/nyanatiloka/README.md` asserted the source page "has
        not changed since 2005" and carries "no reuse restriction" as
        confirmed facts, when the actual evidence only supports "saved
        2005 per the site's own footer" and "no restriction text was found
        on the page" respectively. Reworded both claims to match what was
        actually verified, not overstate it.
      - `dpd-flutter-app` (`assets/help/bibliography.tsv`, `justfile`):
        **0 findings.**

- [ ] Commit, in order, **only after explicit user permission**:
  1. `resources/other-dictionaries` —
     `feat: add Nyanatiloka's Buddhist Dictionary`
  2. `dpd-db` (includes the submodule pointer bump) —
     `feat: mobile releases now include Nyanatiloka's Buddhist Dictionary`

  → verify: `git status` clean in both repos; `git submodule status` in
  `dpd-db` points at the new submodule commit.
