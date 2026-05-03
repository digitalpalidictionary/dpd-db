# Plan: Fix multi-match overwrite in find_sentence_example

**GitHub Issue:** #232

## Architecture Decisions

- Change `g.example` from `str` to `list[str]`. This is the minimal structural change: it
  threads naturally through `find_sentence_example`, `find_gatha_example`, and the append site
  without touching anything else.
- The append site iterates `g.example` and appends one `CstSourceSuttaExample` per element.
- `g.example` is reset to `[]` (not `""`) at the start of each `<p>` iteration.

## Phase 1 — Fix the overwrite bug

- [x] Update `GlobalData.__init__`: change `self.example: str = ""` → `self.example: list[str] = []`
  → verify: attribute exists, type is list

- [x] Change `g.example = ""` reset in the main loop to `g.example = []`
  → verify: reset is `[]` not `""`

- [x] Rewrite `find_sentence_example` to append each match to a list instead of overwriting
  → verify: given a paragraph with 2 matches, function sets `g.example` to a list of 2 strings

- [x] Update `find_gatha_example` to append the single result to `g.example` as a list element
  → verify: gāthā example is `g.example[0]`, not a bare string

- [x] Update append site: iterate `for example in g.example:` and append one `CstSourceSuttaExample`
  per element, keeping `(source, sutta, example) not in source_sutta_examples` dedup
  → verify: `an1` / `āvilattā` returns 2 results; single-match word still returns 1; no dupes

## Phase 2 — Verification

- [ ] Confirm `an1` / `āvilattā` now returns both sentences
  → verify: output list contains one entry with `udakassa` and one with `cittassāti`

- [ ] Confirm `vin5` / `adhipātimokkh` (existing __main__ test case) produces results
  → verify: at least one result returned, no errors
