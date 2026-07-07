# Findings: go_modules/frequency optimization study (#157)

All numbers measured on this machine (22 cores), sandbox dir with a
throwaway copy of `dpd.db`, never the live db. Load average ~2 during
runs, so treat absolute times as ±10%; the ratios are the story.
Benchmark harness: `go_modules/frequency/study_test.go` (temporary
study artifact, delete or keep per discussion).

## Headline

| | baseline | prototype (all fixes) | factor |
|---|---|---|---|
| wall time | 3m49s | **15.9s** | 14× |
| CPU time | 2797s | ~35s | 80× |
| peak RSS | 6.65 GB | **2.4 GB** | 2.8× |

Output verified **byte-identical**: md5 of `(id, freq_html, freq_data)`
over all 89,144 rows matches the live db exactly.

## Bug found on the way: SYA is all zeros in production

`file_maps/sya_file_map.json` names files `canon/01_Vinaya_Mahaavi_1.txt`
but `shared_data/frequency/sya_file_freq.json` keys are
`Canonical/01-Mahavibhanga-1.txt` — intersection is **empty**, so every
SYA cell in every published frequency table is 0 (verified in live db:
`kamma 1` has CST 14/71/442… but SYA all zeros). The current
`resources/syāmaraṭṭha_1927/` layout matches the *file map*, so the
freq JSON is stale — it predates a rename of the SYA text files
(the `(copy)` files from March in `shared_data/frequency/` are fossils
of that change). **Fix: re-run the SYA setup step**
(`makeSyaFreq` in `setup/`) to regenerate the three sya JSONs.
No Go code change needed.

Side effect: because SYA guarantees zeros in every `AllFreqList`,
`min` is currently always 0, which masks the gradient min-offset bug
(below). Fixing SYA data may surface it.

## Speed findings, ranked

### 1. freqFinder: per-file maps → per-section maps (79×) — the big one

`freqFinder` walks sections × files × word-forms. SC alone has 7,288
files; ~316k map lookups per headword, ~25 billion per run. Sections
are only 49+39+30+19=137, so merging each section's file maps into one
map at load time (~0.6s) collapses this to ~5.5k lookups per headword.

- old: 12.5 ms/headword → new: 0.159 ms/headword (measured on an
  even-stride sample of all headwords)
- proven equivalent two ways: aggregation identity checked for **every
  word-section pair in all 4 corpora** (exact int sums, same section
  order → holds for all possible word lists), plus 2000 headwords
  end-to-end through both paths.

### 2. updateDb: DELETE + reinsert → prepared UPDATE (13.7×)

Current code deletes the entire 2.2 GB `dpd_headwords` table and
re-inserts every row via GORM `CreateInBatches` — 57.4s, and a crash
mid-write leaves the table empty. A single transaction with a prepared
`UPDATE dpd_headwords SET freq_html=?, freq_data=? WHERE id=?` takes
**4.2s**, touches only the two owned columns, and removes the
empty-table crash window. Same pattern as the Python-side lesson
(`tools/lookup_sync.py:_raw_sql_sync`).

This also unlocks:

### 3. Load only needed columns (3.3s → 0.6s, −1.6 GB heap)

`GetDpdHeadword()` loads all ~60 columns (including every row's
`inflections_html`, `freq_html`…) only because delete+reinsert needs
full rows. `makeFreqTable` needs 6 columns: id, lemma_1, pos, stem,
inflections, inflections_api_ca_eva_iti. Select-6: 0.6s / ~40 MB vs
full: 3.3s / ~1.6 GB heap.

### 4. Template: drop Clone-per-row, pre-minify once (1.4×)

`text/template` `Execute` is documented safe for parallel execution, so
`templ.Clone()` per headword is pure waste; `CleanWhiteSpace` compiles
its regex on **every call** and regex-scans every rendered row, when
minifying the template once at load gives the same bytes (proven
byte-identical on 2000 samples; prototype ran the shared template under
44 workers with identical final md5). 381µs → 277µs per row.

### 5. tools.ReadJson*: json.Valid double-parse (~18% of load)

Every `ReadJson*` helper runs `json.Valid` (full parse) then
`json.Unmarshal` (second parse). On the 71 MB cst file: 1.64s vs 1.35s.
`Unmarshal` already returns an error for invalid JSON — the pre-check
buys nothing. Also benefits `deconstructor/importer` which uses the
same helpers.

## Memory findings

- Section maps replace per-file maps: heap 511 MB → 241 MB for the
  corpus data (fewer, merged entries).
- Column-select load avoids ~1.6 GB of unneeded row data.
- Together with not building the `updatedResults` full-row copy, peak
  RSS drops 6.65 GB → 2.4 GB. Remaining bulk is the html/data stashes
  (~700 MB of output) — could stream rows to a single writer goroutine
  instead of stashing, but 2.4 GB seems fine; not recommended unless
  CI memory pressure demands it.

## Readability & maintainability suggestions (not benchmarked)

1. **Kill the 4× copy-paste corpus pattern.** Eight package globals +
   40-line `init()` + four identical `freqFinder` calls → one
   `corpus` struct (name, fileMap path, freqMap path, sectionMaps) and
   a loop. Adding a fifth edition becomes one slice entry.
2. **Inconsistent path joining** in `init()`: freq maps are joined to
   `DpdBaseDir`, file maps and the template are not. Works only while
   `DpdBaseDir == ""`; unify.
3. **gradient.go**: the 10-branch if/else chain + 11-field
   `stepsStruct` can be a small arithmetic loop. Latent bug: steps are
   `stepWidth*k`, not `min + stepWidth*k` — harmless today only
   because the SYA bug forces `min==0`; decide intended behavior
   before the SYA fix un-masks it (a word present in every section
   would get skewed buckets). `s0`/`s1` are dead fields.
4. **updateDb** delete+reinsert is also a correctness smell (crash =
   empty table); the UPDATE rewrite fixes speed and safety together.
5. **setup/**: `1CST/2SC/3BJT/4SYA.go` are copy-paste siblings sharing
   the save-trio; `writeFileList` is dead code. Low priority — run-once
   scripts — but the SYA fix requires touching them anyway.
6. `shared_data/frequency/*(copy).json` — 69 MB of stale fossils to
   delete.
7. Optional: replace stash maps + mutex with a results channel and one
   collector goroutine — removes shared mutable state.

## Recommended implementation order (follow-up thread)

1. SYA data fix (re-run setup) — data correctness, zero code risk.
2. Section aggregation + column select + prepared UPDATE + shared
   minified template — the 14× / −4.2 GB win, one focused rewrite of
   `main.go` (~same line count, mostly deletions), verifiable
   byte-identically via the existing harness.
3. Drop `json.Valid` from `tools/json.go` helpers.
4. Readability items 1–3, 5–7 as taste dictates.
