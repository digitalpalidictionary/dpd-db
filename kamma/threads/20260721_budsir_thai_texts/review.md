# Review — Replace Thai texts with corrected BUDSIR corpus

Issue #231. Self-review of the thread as it stands (pre manual review + GitHub build).

## Outcome vs spec

All in-scope items done and verified. `SYA` code + "Syāmaraṭṭha" label kept intact; only the
text source, two file maps, format parsing, and one provenance URL changed.

## Changed files (this thread only)

| File | Change |
|---|---|
| `.gitmodules`, `resources/tipitaka.rte` | add jorgecaa/tipitaka.rte submodule |
| `tools/paths.py` | `sya_dir` → `resources/tipitaka.rte` |
| `go_modules/tools/pth.go` | `SyaTextDir` → `resources/tipitaka.rte` |
| `go_modules/frequency/setup/4SYA.go` | folders → `Canonical`/`Non-Canonical`; BOM trim |
| `go_modules/tools/cleanMachine.go` | sya branch strips `(pts…)`, `page number`, `footnote` |
| `go_modules/frequency/file_maps/sya_file_map.json` | remapped to 115 corrected filenames |
| `db/variants/files_to_books.py` | `sya_files_to_books` remapped (115/115); other dicts untouched |
| `db/variants/extract_variants_from_sya.py` | `utf-8-sig`; scope to Canonical/Non-Canonical; page/footnote/pts regexes; label-leak fix |
| `tests/db/variants/test_extract_variants_from_sya.py` | samples → new format; +label-leak test |
| `docs/technical/tipitaka_source_files.md` | SYA URL → jorgecaa; drop "bad shape" |
| `justfile` | add `freq-setup` |

**NOT part of this thread (exclude from commit):** `shared_data/deconstructor/spelling_mistakes.tsv`
— unrelated spelling edits from a concurrent thread/process, not Thai-related.

## Verification performed

- **Phase 1:** submodule 45+70 files; `sya_dir` resolves.
- **Phase 2 (freq):** `just freq-setup` ran clean — **0 characterTest errors** (old corpus
  needed a CJK/PUA "crazy characters" filter). `sya_freq.json`: `footnote`/`number` keys
  gone, `page` 49358→1. Before/after corpus counts: 589,236 vs 589,177 unique words,
  100% of union shared, tokens 6.64M→6.61M. Equivalent coverage, cleaner data.
- **Phase 3 (variants):** old-vs-new full-corpus diff — 71,675 vs 71,689 entries, 99.6%
  shared headwords, 0 corruptions in either, genuine diacritic corrections in new
  (`koṇāgamano`→`konāgamano`). Isolation run: 71,769 pairs; ~89.6% call-match (rest are
  source-apparatus orphans/misnumbering, not parser defects — verified on p.129 of
  Mahāvibhaṅga). `txt/` raw-rip correctly excluded.
- **Gate:** `go vet` clean; ruff check+format clean; pyright 0 errors; 83 tests pass
  (variants + tpr freq fixtures with the SYA label unchanged).

## Deferred / follow-up (out of scope)

- Duplicate-footnote-number collision in `get_variants_in_page` (dict last-wins) causes the
  ~0.4% headword churn. Pre-existing; candidate follow-up.
- Phase 5 (drop `resources/syāmaraṭṭha_1927/`) intentionally held until after the user's
  manual review + a green GitHub build confirm the new source end-to-end.

## Build / CI switches for a full Thai regeneration

- Local full build already regenerates Thai: `generate_components.py` runs `db/variants/main.py`
  (gated `[exporter] make_variants = yes` — already on) and `frequency/main.go`. To rebuild the
  freq *maps* from the new corpus, run `just freq-setup` (or `initial_setup_run_once.py`) first —
  `frequency/main.go` alone consumes existing maps.
- CI `draft_release.yml`: `submodules: 'recursive'` checks out the new submodule and
  `initial_setup_run_once.py` runs `frequency/setup/*.go` → maps regenerate from new Thai
  automatically. No workflow edit needed.

## Verdict

Ready for manual review + GitHub build. Not committed. Phase 5 pending post-build sign-off.
