# Spec — Daily ePitaka DPD update (local only)

## Overview
The ePitaka app (Flutter, repo `~/MyFiles/3_Active/epitaka`, upstream
`dhammanana/epitaka_app`) shows DPD from its own SQLite file,
`dpd-dictionary.db`. The upstream maintainer builds that file privately
(no builder exists in any public repo or branch — searched 2026-10-06) and
uploads it to a GitHub release. The copy on this machine was downloaded
in mid-July 2026, but its data is DPD as of 2026-05-01 (max headword id
89412; matches the backup TSVs in commit `babe7108` row for row).

Goal: every normal dpd-db build refreshes the local ePitaka
`dpd-dictionary.db` from the live `dpd.db`, replicating the existing file's
data subset and HTML exactly, so the app is ready to use with today's data
the next time it opens. Local only, not for public release.

## Current state (verified 2026-10-06 by reading the files read-only)

**Live file:** `/home/bodhirasa/.local/share/com.dn.epitaka/dpd-dictionary.db`
(folder from the app id `com.dn.epitaka`; the app also records the folder in
`~/.local/share/epitaka_db_path`). WAL mode; the app keeps it open while
running.

**Tables in the existing file:**
- `dpd_headwords(id INTEGER PRIMARY KEY, lemma_1, meaning_html, antonym,
  synonym, stem, pattern)` + index `idx_dpd_headwords_lemma_1` — 89,617 rows:
  88,864 headwords + 753 roots.
- `dpd_lookup(lookup_key, headwords, deconstructor)` + indexes
  `idx_dpd_lookup_key` and `idx_dpd_lookup_lookup_key` — 1,281,838 rows, i.e.
  every row of `dpd.db` `lookup` (live now: 1,282,717), including ~89k rows
  with neither headwords nor deconstructor.
  - `headwords`: JSON int list of `dpd_headwords.id` (headword ids, plus root
    ids for root keys, e.g. `acc` → `[927, 89413, 89414]`, `√acc` →
    `[89413, 89414]`), NULL when empty.
  - `deconstructor`: JSON string list, NULL when empty.
- `sqlean_define` (empty) — origin unknown, not read by the app.
- `dpd_lookup_norm_v2(src_rowid INTEGER PRIMARY KEY, norm, lookup_key)` +
  index `dpd_lookup_norm_v2_idx` — the app's diacritic-folded search table
  (see below). Not DPD data.

**`meaning_html`, headwords** (`<details class='dpd-meaning'>`):
`<summary>` = `<i>pos</i>` + meaning (meaning_1 bold, then meaning_2, then
`(lit. meaning_lit)`) + `[construction summary]`; then
`<div class='dpd-meaning-detail'>` with, when present, `dpd-grammar`,
`dpd-sanskrit`, `dpd-root`, `dpd-compound`, `dpd-example` (example_1 only)
divs, each `<b>Label:</b> value`. Uses single-quoted attributes.
Samples: `dhamma 1.01` (id 34626), `abhikkanta 1` (7553), `akakkasa` (7),
`akukkukata` (220, meaning_2 only, not bold), `kusala 1` (22620).

**`meaning_html`, roots** (`<details class='dpd-root-meaning'>`): summary
`<b>√root</b> meaning [skt. …]`; detail divs `dpd-root-group`,
`dpd-root-example`, `dpd-dhatupatha`, `dpd-dhatumanjusa`, `dpd-root-count`,
optional `dpd-root-note`, then `<p class='heading underlined'>` and
`<table class='family'>` (rows: lemma with superscript homonym number, pos,
meaning, degree-of-completion mark in `<span class="gray">` — double quotes
there). Root ids start at (max headword id at build time + 1): 89413–90165
in the existing file, apparently in plain (not Pāḷi) sort order of the root
key. Live `dpd.db` headword ids now run to 90214, so root ids must be
assigned after the current max.

**`antonym`, `synonym`, `stem`, `pattern`:** straight copies of the
`dpd_headwords` columns. The app selects them but never shows them.

**How the app reads it** (`lib/core/database/dpd_dictionary_database.dart`):
exact `lookup_key` match, then folded match through `dpd_lookup_norm_v2`,
then headwords `WHERE id IN (...)`. Optional `epd` lookup column supported,
absent in the file — not added here.

**The search table (`dpd_lookup_norm_v2`):** on every launch the app checks
it in a background isolate (`ensureNormTable`). It only rebuilds from zero if
the norm table has more rows or a higher rowid than `dpd_lookup`; otherwise
it tops up missing rowids. So a replaced `dpd_lookup` of equal or larger size
can keep stale norm rows. A missing table is built at launch (the tool's
comment: 10–20 min on a slow dual-core machine; not measured here), during
which folded search is off. The repo's own `tool/build_dpd_norm.dart`
(imports `package:sqlite3` and the app's `dpd_dictionary_database.dart`;
runs under plain `dart`, verified 2026-10-06) runs the identical
`ensureNormTable` code from the command line: `dart run tool/build_dpd_norm.dart <db>` from the epitaka repo.
`dart` is at `~/flutter/3.29.2/bin/dart`.

**App update path:** none. The app downloads the file only when missing and
never reads the manifest's `updated` date. In-memory caches mean a restart
is needed after a swap.

**TPR comparison:** `exporter/tpr/tpr_exporter.py` writes into the local TPR
db at `[tpr] db_path` with DROP/CREATE. It only runs on uposatha days or with
`[tpr] make_beta = yes`. The ePitaka export is independent of that gate.

## What it should do
1. New exporter `exporter/epitaka/epitaka_exporter.py`, added to the
   exporter list in `scripts/bash/makedict.py` after the TPR line, plus a
   `just export-epitaka` recipe next to `export-tpr`.
2. Gated by `[exporter] make_epitaka` (default `no` in `DEFAULT_CONFIG`; set
   `yes` in this machine's `config.ini`). Not added to any profile, so it
   stays on through quick and full builds.
3. New config section `[epitaka]`:
   - `db_path` = `/home/bodhirasa/.local/share/com.dn.epitaka/dpd-dictionary.db`
   - `repo_path` = `/home/bodhirasa/MyFiles/3_Active/epitaka`
   Defaults empty. If `db_path` is empty or its folder is missing: print a
   red message and exit before loading the db.
4. Build a fresh `dpd-dictionary.db` in `exporter/epitaka/output/` (that
   folder gitignored) with exactly the tables, columns, indexes, NULL
   conventions and HTML described above, from the live `dpd.db`.
5. Pre-build the search table on that output file by running
   `dart run tool/build_dpd_norm.dart <output db>` in `repo_path`. If
   `repo_path` is empty, or `dart` is missing, or the tool fails: print the
   error in red, skip the prebuild, and still install (the app then builds
   it at launch).
6. Install the output into `db_path` through SQLite's backup API (Python
   `sqlite3.Connection.backup`), not a file copy, so the destination's WAL is
   handled correctly. Added 2026-10-06 after review (user request): if
   ePitaka is running (process name `epitaka`, `/usr/bin/epitaka`), close it
   (SIGTERM, wait up to 30 s) right before the install, then reopen it
   through its registered launcher (`gtk-launch epitaka`, desktop entry
   `/usr/share/applications/epitaka.desktop`). Reopen only if it was running.
   If it does not close in time, skip the install with a red message — the
   backup would otherwise wait forever on the app's write lock (review
   finding).

## Assumptions & uncertainties
- The HTML rules above come from reading samples; the exact rules (summary
  bracket text, Root line, which example, family table markup, root id
  order, roots' Example field) are not yet proven. Proof = byte-identical
  `meaning_html` for every headword whose source fields have not changed
  since July (Phase 1 measures this; every mismatch class is read).
- Whether the app tolerates the backup API swapping the file under an open
  connection without a restart: assumed it needs a restart; not tested.
- Norm prebuild time on this machine: not measured. Measured in Phase 2.
- Whether `dart run` in the epitaka repo needs `pub get` first:
  `.dart_tool/package_config.json` exists now, so assumed not.
- `sqlean_define` is not reproduced (empty, unread by the app).

## Constraints
- Read `dpd.db` only. No ORM mutation.
- Never write to the ePitaka repo or its git state; only run its tool.
- Do not touch the other files in the ePitaka folder (`epitaka.db`,
  `app_data.db`, `dpd-mobile.db`, etc.).
- Before the first install, back up the existing live file (it is the only
  copy of the upstream build on this machine) via the backup API into
  `exporter/epitaka/output/baseline_dpd-dictionary.db`; never overwrite that
  baseline afterwards.
- Python conventions: modern type hints, `Path`, `tools.printer`, no
  `sys.path` hacks; ruff + pyright + pyrefly clean.

## How we'll know it's done
- Parity check: HTML rendered from the 2026-05-01 data (the data the
  baseline was built from) is byte-identical to the baseline; differences
  between today's output and the baseline are explained as data change.
  Roots and lookup rows compared the same way.
- One real makedict run (by the user) updates the live file; the app opens
  with no search-table rebuild, finds a word added since July, and folded
  search (e.g. typing without diacritics) works at once.
- Unit tests for the HTML builders and the config gate pass.

## What's not included
- Public release zip, upload, or manifest changes.
- Any change to the ePitaka app (update button, showing extra fields).
- New fields (`epd`, etc.), display improvements, other dictionaries —
  parked as thread `20261006_epitaka_dpd_improvements`.
- Changing the TPR exporter.
