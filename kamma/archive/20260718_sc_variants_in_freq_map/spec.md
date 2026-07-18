# Spec: Include Sutta Central variant readings in the SC frequency maps

## Problem

The frequency maps count words from each corpus's text files. CST texts carry
variant readings inline, so CST variants land in the CST freq map automatically.
Sutta Central keeps variant readings in separate files
(`resources/sc-data/sc_bilara_data/variant/pli/ms/**`), which
`go_modules/frequency/setup/2SC.go` never reads — so words that occur only as SC
variants have zero SC frequency.

## Investigation results (2026-07-18)

- 4,423 variant files, 19,434 entries; every entry uses the format
  `mūla → variant (witness) | mūla → variant (witness); alternate (witness)`.
- 41 irregular entries: continuation clauses after `|` with no repeated `→`
  (the whole clause is the variant text) — handled by a fallback.
- Every variant file has exactly one matching root file:
  `X_root-pli-ms.json` ↔ `X_variant-pli-ms.json`, same relative directory,
  zero orphans. So variant words map cleanly to the existing per-file freq keys.
- Test-parse of the full corpus yields ~42k variant word tokens.
- Review correction (2026-07-18): the initial study undercounted unbalanced
  parens. ~21 clauses (≈30 entries, mostly `thag*`/`ja*`) contain an unclosed
  `(` opening a witness/citation group that never closes; without handling,
  witness codes and citation text leak into the freq map as pseudo-Pāḷi words.
  In every observed case the genuine variant words precede the unclosed `(`,
  so truncating the clause at the first `(` left after witness-stripping keeps
  the real variants and drops the junk.

## Decisions

- Count **only** the variant readings (right of `→`); mūla words on the left are
  already counted from the root text.
- Witness abbreviations in parentheses (`bj`, `si`, `sya-all`, …) are stripped
  before cleaning, so they never enter the freq map.
- Variant words merge into the same per-file freq entry as the root file
  (keyed by the root file's relative path in `sc_file_freq.json`).

## Change

1. `go_modules/tools/pth.go`: add `ScVariantTextDir` =
   `resources/sc-data/sc_bilara_data/variant/pli/ms` beside `ScJsonTextDir`.
2. `go_modules/frequency/setup/2SC.go`:
   - `extractVariantWords(entry string) string` — pure function: split entry on
     `|`; per clause take text right of `→` (whole clause if no arrow); strip
     `(...)` groups; truncate at any unclosed `(`; drop leftover `→`/`)`;
     join with spaces.
   - `scVariantText` treats only `os.IsNotExist` as "no variant twin"; any
     other `os.Stat` error fails loud via `tools.HardCheck`.
   - In the `makeScFreq` loop: derive the variant path from the root file's
     relative path (`_root-pli-ms.json` → `_variant-pli-ms.json` under
     `ScVariantTextDir`); if it exists, read it and append the extracted words
     to `compiledText` before the existing `CleanMachine` + count step.
3. Unit test `2SC_test.go` covering: simple entry, multi-clause `|`, `;`
   alternates, no-arrow continuation clause, unbalanced-paren entry.

Downstream (`sc_freq.json`, `sc_file_freq.json`, `sc_wordlist.json`, gradient
maps, `ebt_counter.py`) needs no changes — counts simply include variants.

## Out of scope

- Regenerating the freq JSONs (user runs the build).
- BJT/SYA/CST variant handling (already inline or not applicable).
- Segment-level frequency granularity.
