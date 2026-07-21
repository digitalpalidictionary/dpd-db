# Plan — Replace Thai texts with corrected BUDSIR corpus

Issue #231. Five phases, each independently testable and committable. Git submodule ops,
script/regeneration runs, and commits are **user-run** (flagged `⛔ user`).

Status markers: `[ ]` todo · `[~]` in progress · `[x]` done.

---

## Phase 1 — Submodule + path repointing

- [x] `⛔ user` `git submodule add https://github.com/jorgecaa/tipitaka.rte resources/tipitaka.rte` — done
- [x] `.gitmodules` has the `resources/tipitaka.rte` entry (url verified).
- [x] `tools/paths.py`: `self.sya_dir = base_dir / "resources/tipitaka.rte"`
- [x] `go_modules/tools/pth.go`: `SyaTextDir: "resources/tipitaka.rte"`
- [x] → verify: submodule populated; `Canonical/` = 45, `Non-Canonical/` = 70; path resolves.
- [ ] `⛔ user` commit: `#231 thai: add tipitaka.rte submodule, repoint sya paths`

## Phase 2 — Frequency pipeline

- [x] `go_modules/frequency/setup/4SYA.go`: folders → `{"Canonical","Non-Canonical"}`;
      BOM trimmed via `strings.TrimPrefix(text, "﻿")`.
- [x] `go_modules/tools/cleanMachine.go` (`case "sya"`): strip `(pts…)` refs and the
      `page number` / `footnote` marker words.
- [x] Replaced `sya_file_map.json` with branch version — 30 books / 115 files, all resolve.
- [x] `justfile`: added `freq-setup` (`freq` already existed on main).
- [x] `go vet ./go_modules/...` clean (exit 0).
- [ ] `⛔ user` `just freq-setup` → verify: 115 files read, no unexpected `characterTest`
      errors; `sya_freq.json` free of junk keys `page`/`number`/`footnote`/`pts`
      (old baseline: page=49358, footnote=26937, pts=1, i=7771).
- [ ] `⛔ user` commit: `#231 thai: adapt frequency pipeline to corrected budsir format`

## Phase 3 — Variants pipeline

- [x] Replaced `sya_files_to_books` with branch version — 115/115 resolve; book codes
      preserve old semantics; bjt/cst/mst dicts untouched.
- [x] `db/variants/extract_variants_from_sya.py`: `utf-8-sig`; file list scoped to
      `Canonical`+`Non-Canonical` (txt/ excluded); page/footnote/pts regexes retargeted;
      removed unused loop var; **fixed footnote-label leak** on multi-block pages.
- [x] Updated the existing `tests/db/variants/test_extract_variants_from_sya.py` samples to
      the new format + added a label-leak test → 23 passed.
- [x] → verify: ruff clean, pyright 0 errors; real-data check on `09-Digha-1.txt`
      = 190 successes / 2 errors, correct readings, no `txt/` leakage.
- [ ] `⛔ user` full variant extraction (`db/variants/main.py`) → confirm sane rate over all 115.
- [ ] `⛔ user` commit: `#231 thai: adapt variant extraction to corrected budsir format`

**Full-run result (all 115 files):** 71,769 variants paired; 80.8% of pages have body-calls
== footnote-entries; ~89.6% of all body footnote-calls match a footnote. Zero junk keys,
zero marker leaks.

**Why not 100% (diagnosed, working as designed):** the residual ~10.4% of unmatched body
calls are source-apparatus realities, NOT parser defects — verified on real pages:
- orphan calls that have no footnote on the page (jorgecaa documents 566 in the source);
- duplicate/misnumbered footnotes in the source edition (e.g. `01-Mahavibhanga-1` p.129 has
  footnotes numbered `1,2,2,4` — two "2"s, no "3" — for body calls `1,2,3,4`);
- damaged wontfix annotation lines producing spurious call numbers (e.g. `* neßēä…`);
- footnote ranges where one entry serves several calls (543 pages have notes<calls).
The extractor correctly skips unmatched calls rather than fabricating pairings; reaching
100% would require inventing data. This matches the old extractor's behaviour (its own
`# TODO: missing footnotes in text`).

**Known limitation (pre-existing):** body text after a footnote on the same page (jorgecaa
FORMAT.md §3: 416 cases) can merge into the footnote section since `get_sya_text` joins
newlines. Rare, non-fatal, inherent to the single-line-page design.

## Phase 4 — Provenance docs

- [x] `docs/technical/tipitaka_source_files.md`: SYA URL → `jorgecaa/tipitaka.rte`,
      removed "bad shape" note, added provenance sentence, kept "Syāmaraṭṭha" heading.
- [x] `db/variants/README.md`, `docs/features/variants.md`, `shared_data/frequency/README.md`:
      no change needed — they already say "Syāmaraṭṭha", which stays correct.
- [x] `abbreviations.tsv` / `frequency_template.*` labels left untouched (fixtures safe).
- [x] → verify: no source ref to `syāmaraṭṭha_1927` dir; fixture files provably unchanged;
      `tools/paths.py` ruff+pyright clean.
- [ ] `⛔ user` commit: `#231 thai: update thai text provenance docs`

## Phase 5 — Drop old source + final smoke

- [ ] `⛔ user` full regen once more (freq + variants); spot-check a known word's SYA
      frequency and a known variant against the old output for sanity.
- [ ] `⛔ user` `git rm -r "resources/syāmaraṭṭha_1927"`
- [ ] → verify: `go vet ./go_modules/...`; `uv run pytest` over affected areas green;
      no dangling refs to the old dir anywhere in source.
- [ ] `⛔ user` commit: `#231 thai: drop old syāmaraṭṭha_1927 source`

---

## Old vs new variant output comparison (requested)

Ran the OLD extractor on the OLD corpus vs the NEW extractor on the NEW corpus:

| Metric | OLD (syāmaraṭṭha_1927) | NEW (jorgecaa corrected) |
|---|---|---|
| distinct variant headwords | 44,512 | 44,337 |
| total variant entries | 71,675 | 71,689 (**+14**) |
| shared headwords | — | 44,333 (**99.6%**) |
| only-old / only-new | 179 / 4 | |

**Verdict: equivalent coverage, better text, cleaner structure — not worse.**
- All 179 differing keys are valid Pāli attested in DPD (0 corruptions in either output).
- 175/179 old-only words still exist in the new corpus — the footnote just anchors to a
  neighbour. Net entry count is essentially unchanged (+14), so no real data loss.
- Where keys differ, NEW shows genuine diacritic corrections: `koṇāgamano`→`konāgamano`,
  `sappāṭihīrakataṃ`→`sappāṭihirakataṃ`, `adhippayāso`→`adhippāyaso`.
- NEW frequency build produced **zero** characterTest errors; OLD relied on a
  "crazy characters" filter for CJK/PUA decoder garbage.
- Root cause of the ~0.4% key churn: pages with several footnote calls sharing one number
  collide in a dict (last wins); the corrected corpus's true-page pagination changes which
  call is last. Pre-existing extractor limitation, unrelated to the source swap. Candidate
  follow-up, out of scope here.

## Notes / risks

- **`txt/` shadowing** is the sharpest trap: jorgecaa's raw corrupted `txt/Canonical` +
  `txt/Non-Canonical` carry the *same filenames* as the corrected root dirs. Frequency
  (4SYA.go) reads the two named folders explicitly → safe. The Python extractor's
  `rglob("*")` is NOT safe and must be scoped (Phase 3).
- The abandoned branch `budsir-thai-texts` targeted the `txt/` raw rip — reuse its file
  maps / justfile / doc scaffolding, but its path pointed at corrupted text and its
  extractor was never format-adapted.
