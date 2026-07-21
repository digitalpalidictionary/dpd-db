# Plan — SYA Khuddaka bucketing (Option B: split file 26)

Goal: move Theragāthā + Therīgāthā out of SYA `kn2` into `kn1` so the SYA Khuddaka columns
align with CST and BJT, by splitting the combined volume `26-Vv-Pv-Th-Thi.txt` at the
verified Theragāthā marker inside the Go frequency-setup stage. No template, no fixture-shape,
no positional-index changes.

Synthetic slice keys (Go marshals map keys sorted, so JSON stays canonical):
- `Canonical/26-Vv-Pv-Th-Thi.txt::vv-pv`  → Vimānavatthu + Petavatthu (kn2)
- `Canonical/26-Vv-Pv-Th-Thi.txt::th-thi` → Theragāthā + Therīgāthā (kn1)

## Tasks

- [x] **1. Add the split in `4SYA.go`.**
  In the file loop, keep current behaviour for every file except
  `26-Vv-Pv-Th-Thi.txt`. For that one file, split the BOM-stripped raw `text` at the first
  occurrence of the marker line `suttantapiṭake khuddakanikāyassa theragāthā` (split on the
  line, marker line goes to the Th/Thi part), clean + count each part separately, and write
  two entries into `fileFreqMap` under the two `::` sub-keys above instead of one entry under
  the real filename. Factor the split into a small helper (e.g.
  `splitSyaFile(fileName, text) map[string]string` returning relKey→text, length 1 normally,
  2 for file 26) so the loop stays readable and the marker/sub-keys live in one place.
  → verify: `go vet ./go_modules/...` compiles clean.

- [x] **2. Remap the buckets in `sya_file_map.json`.**
  In `kn1`, append `Canonical/26-Vv-Pv-Th-Thi.txt::th-thi`.
  In `kn2`, replace `Canonical/26-Vv-Pv-Th-Thi.txt` with `Canonical/26-Vv-Pv-Th-Thi.txt::vv-pv`.
  Leave section order and all other sections untouched.
  → verify: JSON parses; `kn1` has 2 entries, `kn2` first entry is the `::vv-pv` slice.

- [x] **3. Regenerate SYA frequency data.**
  `go run ./go_modules/frequency/setup sya` → rewrites `shared_data/frequency/sya_file_freq.json`
  (116 keys: file 26 replaced by its two slices) and leaves `sya_freq.json` corpus-wide total
  byte-identical.
  → verify (measure): sum of the two slice freq dicts == the pre-split file-26 freq dict
  (word-for-word); `sya_freq.json` unchanged vs git; no key named exactly
  `Canonical/26-Vv-Pv-Th-Thi.txt` remains.

- [x] **4. Rebuild the freq columns + spot-check bucket movement.**
  Run the main freq build (`go run ./go_modules/frequency`) against a *copy* of `dpd.db` first.
  → verify (measure): pick words that occur in Th/Thi but not Vv/Pv (e.g. a distinctive
  Therīgāthā term) and confirm their SYA count moved from the Khuddaka-2 slot to the
  Khuddaka-1 slot, while a Vv/Pv-only word stays in Khuddaka-2, and CST/BJT/SC columns are
  unchanged. Confirm SYA `kn1+kn2+kn3` grand total for a sampled word is identical before and
  after (pure reassignment, no gain/loss).

- [x] **5. Fix `ebt_counter.py::_sya_is_ebt` for the new key naming (same issue).**
  Rewrite it to parse `Canonical/NN-Name.txt` (number before the first `-`; Non-Canonical and
  commentaries excluded), keep ranges `num<=2 or 9<=num<=25`, and additionally treat the
  `Canonical/26-Vv-Pv-Th-Thi.txt::th-thi` slice as EBT (the `::vv-pv` slice falls out as
  num=26). This restores SYA's contribution to `ebt_count` and, via the split, counts Th/Thi
  correctly (matches CST `s0508`/`s0509`).
  → verify: on the regenerated `sya_file_freq.json`, `_sya_is_ebt` matches files 01–02, 09–25
  and the `::th-thi` slice, and nothing else (spot-count).

- [x] **6. Fixtures + full suite.**
  Run `uv run pytest tests/exporter/tpr/`. Regenerate `test_tpr_exporter_fixtures.json` only if
  an affected (Th/Thi) word appears in it — regenerate programmatically, never hand-edit
  (JSON-format rule). Then run the broader affected suites.
  → verify: `uv run pytest tests/` green (or unchanged pre-existing failures only, noted).

## Non-goals / deferred
- Bv/Cp (kn3 vs kn2) and Niddesa/Paṭis disagreements — CST and BJT themselves disagree; no
  single correct bucket. Not touched.
- Live `dpd.db` freq columns / `ebt_count` are not rebuilt here — `shared_data/frequency/*.json`
  are gitignored artifacts; the columns regenerate in the normal `/db` freq build. This thread
  changes only the tracked source (`4SYA.go`, `sya_file_map.json`, `ebt_counter.py`).

## Verification summary (from spec, already confirmed)
- Split point line 6427, marker unique in file. Vv/Pv = lines 2–6426, Th/Thi = 6427–EOF.
- `CleanMachine` (`\n`→space, `addHyphenatedWords=false`) makes a whole-line split
  word-count-exact.
- Only `4SYA.go` + `sya_file_map.json` are edited; regeneration handles the rest; array shape
  (30 SYA sections) and the template are untouched.
