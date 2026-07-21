# Spec — Replace Thai texts with corrected BUDSIR corpus (jorgecaa/tipitaka.rte)

GitHub issue: #231 "Use BUDSIR for Thai texts".

## Problem

DPD's Thai `SYA` source is `resources/syāmaraṭṭha_1927/` — poorly formatted, full of
typos. It feeds two pipelines:

1. **Frequency tables** — `go_modules/frequency/setup/4SYA.go` counts word frequency per
   book, keyed via `go_modules/frequency/file_maps/sya_file_map.json`.
2. **Thai variant readings** — `db/variants/extract_variants_from_sya.py` extracts
   variant readings from the footnote apparatus, keyed via
   `db/variants/files_to_books.py::sya_files_to_books`.

A previous attempt (local branch `budsir-thai-texts`, commit `26c27bc0`) wired in the
`dhamma/tipitaka.rte` mirror (`resources/BUDSIR`) but was **abandoned** because it pointed
at that repo's `txt/` directory — the **raw BUDSIR rip, which is decoder-corrupted**
(word-initial `ī ū ṭh ḍ` garbled, Latin-1 passthrough `ß é`, PUA `U+F8xx`). Replacing
typo-ridden text with differently-corrupted text is no improvement.

## Solution

Use **`jorgecaa/tipitaka.rte`** instead. It keeps `txt/` as the immutable raw rip but adds
root-level `Canonical/` (45) + `Non-Canonical/` (70) = a **mechanically-corrected corpus**
produced by a reproducible pipeline with a proven "no Pāli word added / deleted / altered"
guarantee (its `METHODOLOGY.md` / `FORMAT.md`). Same 115-file inventory, **same filenames
the abandoned branch already remapped to** — verified 115/115 exact match against both
`sya_file_map.json` and `sya_files_to_books`.

The *edition* is still the Syāmaraṭṭha (Royal Siamese, 1925–28); BUDSIR is only the
digitizer. So the `SYA` source code and "Syāmaraṭṭha" label stay; only the digitization
source and URLs change.

### Decisions (confirmed with user)

- **A.** Submodule `https://github.com/jorgecaa/tipitaka.rte` directly under `resources/`
  (no org fork/mirror). Path: `resources/tipitaka.rte`.
- **B.** Fresh thread off `main`; reuse the file-map remap content from `budsir-thai-texts`
  (matches jorgecaa 1:1). The old `BUDSIR` mirror is never added, so "drop old budsir"
  holds by construction.
- **C.** Delete the old `resources/syāmaraṭṭha_1927/` directory once regeneration verifies.

### Point at the corrected root dirs, not `txt/`

`sya_dir` / `SyaTextDir` → `resources/tipitaka.rte` (repo root). Both consumers iterate the
two corrected folders `Canonical/` + `Non-Canonical/`. **`txt/` and `utils/` must be
excluded** — `txt/` holds the raw corrupted files under the *same filenames*, so a naive
recursive glob would silently re-introduce the corruption and double-count.

### Format changes to handle (old → new)

| Element | OLD `syāmaraṭṭha_1927` | NEW jorgecaa corrected |
|---|---|---|
| encoding | UTF-8, no BOM | UTF-8 **with BOM** → open `utf-8-sig` (Py) / trim `﻿` (Go) |
| page marker | `[page 001]` | `page number: 001` |
| footnote | `Footnote:1 Sī. …` (capital, inline) | `footnote: 1 sī. …` (lowercase, own line) |
| footnote call | ` 1-` | ` 1-` (identical) |
| PTS ref | `< PTS. D I , 2 >` (angle brackets) | `(pts. d i, 2)` (parens, lowercase) |
| passage / separator | `[1]` / `-------` | same |
| case | mixed | already lowercase |

## Scope (minimal)

Keep all `sya` / `SYA` code identifiers. Only change: text source, folder names, format
parsing for the two consumers, and source-label docs.

**In scope**
- `.gitmodules` + submodule `resources/tipitaka.rte`.
- `tools/paths.py::sya_dir`, `go_modules/tools/pth.go::SyaTextDir` → new path.
- Frequency: `4SYA.go` folders (`canon`/`commentary` → `Canonical`/`Non-Canonical`) + BOM
  trim; `CleanMachine` "sya" branch strips `page number:`, `footnote:` marker words and
  `(pts. …)` refs. Reuse branch's `sya_file_map.json`.
- Variants: `extract_variants_from_sya.py` — `utf-8-sig`; page/footnote/PTS regexes
  retargeted; file list scoped to the two corrected dirs only. Reuse branch's
  `sya_files_to_books`.
- Provenance docs only: point the source URL at jorgecaa and drop the "bad shape" line.
  Files: `docs/technical/tipitaka_source_files.md`, `db/variants/README.md`,
  `docs/features/variants.md`, `shared_data/frequency/README.md`.
- `justfile`: add `freq-setup` / `freq` recipes (from branch) for regeneration.

**Out of scope / deliberately NOT changed**
- **The `SYA` abbreviation label is left exactly as-is** ("Syāmaraṭṭha 1927 Royal Edition
  (Thailand)"). It is already correct (the edition is unchanged) and it flows from
  `shared_data/reference/abbreviations.tsv` → `docs/abbreviations.md`,
  `shared_data/help/abbreviations.tsv`, and the `title=` strings in the three
  `frequency_template.*` files, which are in turn baked into test fixtures
  (`tests/exporter/tpr/…`, `tests/tools/…`). Changing the label would force a fixture
  regeneration for no benefit. The branch's "BUDSIR Edition" rename was both philologically
  wrong and fixture-breaking — do not adopt it.
- `tools/all_tipitaka_words.py`, `go_modules/tools/freq.go` — consume the *generated*
  `sya_wordlist` / `SyaFreqMap` JSONs, not filenames; they pick up new data on regen. No edit.
- The `user_dictionary.txt` `Āpaṇa` addition from the branch (unexplained; drop it).
- The `SYA` source code, niggahita convention, and all downstream freq/variant consumers.

## Text-name lists (per user request — full inventory)

Swept the whole tree. The **only** hardcoded lists of Thai text filenames are the two file
maps, both already remapped on the branch to match jorgecaa 115/115:
- `go_modules/frequency/file_maps/sya_file_map.json` (frequency)
- `db/variants/files_to_books.py::sya_files_to_books` (variants)
No other file hardcodes Thai filenames.

## Gated steps (user runs — never run unprompted)

- `git submodule add https://github.com/jorgecaa/tipitaka.rte resources/tipitaka.rte`
- `git rm -r "resources/syāmaraṭṭha_1927"` (after verification)
- Regeneration: `just freq-setup && just freq` (Go) and the variant-extraction build step.
- All commits.

## Acceptance

- `just freq-setup` reads 115 files from `Canonical/`+`Non-Canonical/`, no `characterTest`
  errors beyond jorgecaa's inventoried residue; freq map free of `page`/`number`/`footnote`/`pts` junk keys.
- Variant extraction runs on the new format with a sane (non-zero, comparable) success/error
  rate; keys are clean Pāli.
- No path references the old `syāmaraṭṭha_1927` dir; old dir removed.
