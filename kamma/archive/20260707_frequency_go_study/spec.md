# Spec: Study go_modules/frequency for optimization (#157)

## Goal

Study `go_modules/frequency/` (the frequency-table generator that fills
`freq_html` and `freq_data` on all ~89k headwords) and produce
benchmark-proven suggestions for:

1. speed
2. memory
3. readability & maintainability

This is a **study thread** — the deliverable is a findings report with
measured evidence, presented for discussion. No production code changes
until the user picks which suggestions to implement. Part of the #157
refactoring series; do not comment on or close the issue.

## Scale facts (measured)

- 89,144 headwords, 964 idioms skipped, avg ~20 inflections per word
  (plus the api/ca/eva/iti list ≈ ~40 word-forms per headword).
- Corpus file-freq JSONs loaded at init: cst 71MB (217 files, 2.96M
  entries), bjt 40MB (285 files, 1.72M), sya 41MB (115 files, 1.73M),
  sc 19MB (**7,288 files**, 0.87M) — 171MB JSON total.
- `freqFinder` iterates sections × files × word-forms:
  ~7,905 file visits × ~40 forms ≈ 316k map lookups per headword,
  ≈ 25 billion lookups per run. Sections are far fewer: 49+39+30+19 = 137.
- Output written back: 654MB `freq_html` + 61MB `freq_data`;
  `updateDb` deletes the whole `dpd_headwords` table and re-inserts
  every row with GORM `CreateInBatches`.

## Hypotheses to prove or kill with benchmarks

- H1 **freqFinder aggregation**: merging per-file freq maps into
  per-*section* maps once at load turns 316k lookups/headword into
  ~5.5k — the dominant speed win. Must produce identical freq lists.
- H2 **Template waste**: `templ.Clone()` per headword is unnecessary
  (`text/template` Execute is goroutine-safe); `CleanWhiteSpace`
  recompiles its regex on every call and regex-scans every rendered
  row when the template could be minified once at load. Must produce
  byte-identical HTML.
- H3 **Double JSON parse**: `tools.ReadJson*` runs `json.Valid` (full
  parse) then `json.Unmarshal` (second parse) on 171MB — dropping the
  pre-validation roughly halves load time.
- H4 **DB write**: delete-table + GORM re-insert of full rows (multi-GB
  table) is slower than a plain prepared `UPDATE ... SET freq_html=?,
  freq_data=? WHERE id=?` in one transaction; UPDATE also removes the
  need to load all columns (enables SELECT of only needed columns →
  memory win) and removes the risk window where the table is empty.
- H5 **Memory**: section-aggregated maps hold fewer entries (union per
  section) than 7,905 per-file maps → lower heap than current.

## Discovered during study (2026-07-07)

- **SYA data bug**: `file_maps/sya_file_map.json` lists files as
  `canon/01_Vinaya_Mahaavi_1.txt` but `sya_file_freq.json` keys are
  `Canonical/01-Mahavibhanga-1.txt` — zero intersection. Every SYA cell
  in every published frequency table is silently 0 (verified in live
  `dpd.db`). Needs a decision: fix the file map or regenerate the freq
  JSONs.

## Method

- Benchmarks live in a temporary `study_test.go` (package main, uses the
  real loaded globals) inside `go_modules/frequency/` — deleted or kept
  per discussion outcome.
- Full-run baseline measured in a sandbox dir (symlinked `shared_data`,
  throwaway copy of `dpd.db`) with `/usr/bin/time -v` — never against
  the live db.
- Every speed claim verified for output equivalence (identical freq
  lists / byte-identical HTML) before being reported.
- (added during study) A combined end-to-end prototype run, gated
  behind `PROTO=1` in the harness, measures all fixes together and is
  md5-compared against the live db's freq columns.

## Implementation phase (added 2026-07-07, user-approved)

After discussion the user approved implementing everything. Scope:

1. Rewrite `main.go`: corpus struct replacing the 8 globals + `init()`;
   section-aggregated freq maps; column-select load; shared pre-minified
   template (no per-row Clone, no per-row CleanWhiteSpace); prepared
   `UPDATE` of the two freq columns instead of DELETE + reinsert;
   unified `DpdBaseDir` path joining.
2. Simplify `gradient.go` to an arithmetic loop with **exactly**
   preserved semantics (incl. the min-offset quirk — behavior change is
   a separate decision); prove equivalence by brute force over the
   full (min, max, value) domain before deleting the old code.
3. Drop the `json.Valid` pre-parse from `tools/json.go` helpers,
   preserving panic-on-invalid behavior via the Unmarshal error.
4. `setup/`: optional corpus arg (`go run ./go_modules/frequency/setup
   sya`) so the SYA fix doesn't force a full 4-corpus rescan; remove
   dead `writeFileList`.
5. Delete stale `shared_data/frequency/*(copy).json` (not git-tracked).
6. Delete `study_test.go` once final verification passes.

Acceptance: sandbox end-to-end run of the new binary against a fresh
db copy produces md5-identical `(id, freq_html, freq_data)` to the
live db; `go vet` and `go build ./go_modules/...` clean.

The SYA data regeneration itself is run by the user
(`go run ./go_modules/frequency/setup sya`), after which SYA columns
become non-zero — that output is intentionally NOT part of the
md5-identical acceptance check (it must be run only after this
implementation is verified).

## Out of scope

- `setup/` corpus-scanning rewrite beyond the arg + dead-code removal.
- Changing gradient bucketing behavior (min-offset quirk) — flagged
  for a future decision, semantics preserved for now.
