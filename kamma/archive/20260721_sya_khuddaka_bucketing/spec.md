# Spec — SYA Khuddaka frequency-bucket misallocation

Status: **RESEARCHED — decided Option B.** Spun off from #231 (BUDSIR Thai migration).
No GitHub issue yet.

## Decision (2026-07-21): Option B — split file 26 in the Go setup stage

Research confirmed the freq system is **purely positional**: each edition's file map is an
ordered list of sections, the bucket key names (`kn1`…) are discarded in `loadCorpus`, and
`frequency_template.html` hard-references fixed positional slots per corpus (SYA slot 8 =
Khuddaka 1, 9 = Khuddaka 2, 10 = Khuddaka 3), with ~30 SYA slots and CST/BJT/SC slots
interleaved.

- **Option A (merge kn1+kn2)** collapses a section → shifts every later positional index →
  breaks every `{{index .SyaFreq N}}` (and the aligned CST/BJT/SC indices), and changes the
  freq-array *length* (30→29), breaking every snapshot fixture structurally. Rejected.
- **Option B (split file 26)** keeps 3 Khuddaka sections → array length stays 30 → template
  and fixture *shape* unchanged. Only word-count values for Th/Thi words change. Chosen.

### Verified split boundary (measured thrice)

Source: `resources/tipitaka.rte/Canonical/26-Vv-Pv-Th-Thi.txt` (12,736 lines). Each contained
text opens with a `suttantapiṭake khuddakanikāyassa …` marker after the prior text's
`niṭṭhitā` colophon + a page-number line. Exactly 4 markers:

| Text | Start line | Marker line | Correct bucket |
|---|---|---|---|
| Vimānavatthu | 2 | `suttantapiṭake khuddakanikāyassa` (l.4) | kn2 ✓ |
| Petavatthu | 3829 | `suttantapiṭake khuddakanikāyassa` (l.3829) | kn2 ✓ |
| **Theragāthā** | **6427** | `suttantapiṭake khuddakanikāyassa theragāthā` | **kn1** |
| **Therīgāthā** | 11067 | `suttantapiṭake khuddakanikāyassa therīgāthā` | kn1 |

Single clean cut at **line 6427** — the string `suttantapiṭake khuddakanikāyassa theragāthā`
is **unique** in the file. Everything from line 6427 to EOF = Th+Thi → **kn1**; everything
before = Vv+Pv → **kn2**. `CleanMachine` maps `\n`→space before any token op and is called
with `addHyphenatedWords=false`, so splitting at this whole-line boundary preserves the exact
word multiset (no word straddles the cut).

### Blast radius (Option B)
- `go_modules/frequency/setup/4SYA.go` — split file 26 at the marker into two freq entries.
- `go_modules/frequency/file_maps/sya_file_map.json` — Th/Thi slice → kn1, Vv/Pv slice → kn2.
- Regenerate `shared_data/frequency/sya_file_freq.json` (file 26 → 2 synthetic keys) and
  rerun the main freq build (updates `freq_html`/`freq_data`). `sya_freq.json` corpus-wide
  total is byte-identical (sum unchanged).
- `tests/exporter/tpr/test_tpr_exporter_fixtures.json` — SYA array length stays 30; only
  regenerate if a fixture word occurs in Th/Thi (current fixture word `akataññujātaka` is a
  Jātaka word → unaffected).

### In scope — `ebt_counter` SYA fix (same issue number)
`scripts/build/ebt_counter.py::_sya_is_ebt` expects old key format `canon/NN_…`, but the live
`sya_file_freq.json` keys are `Canonical/NN-Name.txt` (since #231's source swap). It matches
**0** current SYA keys → SYA currently contributes **0** to every headword's `ebt_count`.
Pre-existing regression from the same #231 migration → folded into this thread.

Fix: rewrite `_sya_is_ebt` for the new naming. EBT ranges are unchanged (files `01–02` monks'
Vibhaṅga; `09–25` DN/MN/SN/AN + kn1 small texts), **plus** the new Th/Thi slice. Verified
against CST's `ebts` list: it includes `s0508`/`s0509` (Theragāthā/Therīgāthā = kn8/kn9) but
not `s0506`/`s0507` (Vimānavatthu/Petavatthu) — so the split's `::th-thi` slice is EBT and
`::vv-pv` is not. The same file-26 cut therefore fixes bucketing **and** EBT membership.

## The problem

The frequency table groups the Khuddaka Nikāya into three buckets — kn1 / kn2 / kn3
(displayed as Khuddaka 1/2/3). For SYA (Thai), some texts land in a different bucket than
CST and BJT, so the per-bucket frequency columns don't line up across editions.

### Decoded bucket membership (verified 2026-07-21)

| Text | CST | BJT | SYA | SYA file |
|---|---|---|---|---|
| Khp, Dhp, Ud, Iti, Sn | kn1 | kn1 | kn1 ✓ | 25-Khp-Dhp-Ud-Iti-Sn |
| **Theragāthā** | kn1 | kn1 | **kn2** ✗ | 26-Vv-Pv-Th-Thi |
| **Therīgāthā** | kn1 | kn1 | **kn2** ✗ | 26-Vv-Pv-Th-Thi |
| Vimānavatthu, Petavatthu | kn2 | kn2 | kn2 ✓ | 26-Vv-Pv-Th-Thi |
| Jātaka | kn2 | kn2 | kn2 ✓ | 27,28 |
| Apadāna | kn2 | kn2 | kn2 ✓ | 32,33 |
| Buddhavaṃsa, Cariyāpiṭaka | kn3 | kn2 | kn2 (≈BJT) | 33 |
| Mahāniddesa, Cūḷaniddesa, Paṭisambhidā | kn2 | kn3 | kn3 (≈BJT) | 29,30,31 |
| Milindapañha | kn3 | — | kn3 | 56-Milindapanha |

### Root cause

The Thai Syāmaraṭṭha edition **packages several texts into single physical volumes**
(e.g. file `26-Vv-Pv-Th-Thi.txt` = 4 texts; Th begins ~line 6439). The freq file map
assigns a *whole file* to one bucket, so Th/Thi (which belong in kn1) get dragged into kn2
alongside Vv/Pv (which belong in kn2).

- The one **unambiguous** mismatch vs BOTH CST and BJT: **Theragāthā + Therīgāthā in kn2**.
- Niddesa/Paṭis (kn3) and Bv/Cp (kn2) match BJT; CST and BJT already disagree there, so no
  single correct answer — lower priority.
- This bucketing is **identical in the old and new `sya_file_map.json`** — pre-existing,
  NOT introduced by the #231 source swap.

## Two candidate approaches (research both before choosing)

### Option A — merge the KN1 and KN2 buckets (for all editions, or SYA-only)
Collapse kn1+kn2 into one Khuddaka bucket so the Th/Thi placement no longer matters.
- **Cost:** changes the frequency HTML template + JS (`exporter/goldendict/javascript/
  frequency_template.{html,js}`, `go_modules/frequency/templates/frequency_template.html`),
  the Go bucket rollup logic, ALL four file maps (cst/bjt/sya/sc), and — critically — the
  TPR/exporter test fixtures that snapshot the freq HTML (`tests/exporter/tpr/…`,
  `tests/tools/…`). Wide blast radius.
- **Risk:** coarsens the data for CST/BJT too, losing the kn1 vs kn2 distinction they get
  right. Full research needed: enumerate every consumer of the kn1/kn2/kn3 split.

### Option B — split the SYA combined volumes by text (PREFERRED — matches CST & BJT)
Slice file 26 at the Theragāthā heading (and any other multi-text volume) into per-text
sub-files, then map each slice to its correct bucket.
- **Cost:** a preprocessing/derivation step (the freq map maps whole files; it can't slice).
  Either derive split files under a build step or extend the freq setup to accept
  intra-file offsets.
- **Upside:** SYA buckets then align with CST and BJT exactly; no template/fixture churn.
- **Finicky:** must find reliable, stable split boundaries (text headings) in every combined
  volume; verify no text is dropped or double-counted at the seams.

**User's steer:** both are finicky; **B matches CST/BJT**, so lean B. Do a full research pass
on both before implementing.

## Research checklist (COMPLETE — 2026-07-21)
- [x] Enumerated every consumer of the bucket keys: `loadCorpus`/`freqFinder` in
      `go_modules/frequency/main.go` (positional) + `frequency_template.html` (fixed slots) +
      `ebt_counter.py` (per-file freq). Keys are discarded; only section order matters.
- [x] Combined-volume confirmed: only file 26 mixes buckets (Th/Thi in kn1 vs Vv/Pv in kn2).
      File 25 is all kn1; 27–33 all non-EBT/kn2–3. Stable split heading = the unique line
      `suttantapiṭake khuddakanikāyassa theragāthā` (line 6427).
- [x] Prototyped Option B: split slices, remapped, regenerated freq; verified slice sum ==
      pre-split word-for-word, `sya_freq.json` byte-identical, and `theragāthāya` moved
      kn2→kn1 while `pabhāsatīti` (Vv/Pv) stayed kn2.
- [x] Scoped Option A: rejected — collapsing a section shifts every positional index and
      changes array length 30→29, breaking the template and every snapshot fixture.
- [x] Recommended + implemented Option B in this thread (no separate GitHub issue opened;
      folded the `ebt_counter` fix in under the same change).

## Out of scope
Anything in #231 (already committed). This thread does not block the BUDSIR migration.
