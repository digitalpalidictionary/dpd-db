# Plan: dnt/mnt/snt/ant parsers

## Architecture decisions
- **Mirror existing commentary parsers verbatim.** The ṭīkās use the same rend-tag scheme as the aṭṭhakathās, so each new parser is a near-copy of `dna/mna/sna/ana` with `book = "DNt|MNt|SNt|ANt"`.
- **Single `dnt` parser handles both DN ṭīkās via a `book` heading sniff.** When the parser sees a `book` rend whose text contains `abhinava`, it sets `g.is_abhinava=True` and uses prefix `DNt2`; otherwise `DNt`.
- **No new GlobalData fields.** Use `setattr(g, "is_abhinava", False)` lazily, matching the existing free-attribute pattern (`g.is_bhikkhuni`).
- **Source prefixes**: `DNt`, `DNt2`, `MNt`, `SNt`, `ANt`. Lower-case sutta strings.
- **Dispatcher cases inserted right after the corresponding aṭṭhakathā cases.**

## Phase 1 — DN ṭīkā (dnt) including abhinavaṭīkā
- [ ] 1.1 Add `dnt_digha_nikaya_tika(g)` after `dna_digha_nikaya_commentary`. Mirror dna with conditional prefix.
  → verify: `uv run ruff check tools/cst_source_sutta_example.py` passes.
- [ ] 1.2 Detect `abhinava` in book heading; reset counters on switch.
  → verify: walk-through logic visible in code.
- [ ] 1.3 Add dispatcher case `case "dnt": dnt_digha_nikaya_tika(g)` after `case "dna":`.
  → verify: `grep -n 'case "dnt"' tools/cst_source_sutta_example.py` returns 1 hit.
- [ ] 1.4 Smoke-test `dnt` with text_to_find `brahmajāla`.
  → verify: output contains both `DNt…` and `DNt2…` sources, no errors.

## Phase 2 — MN ṭīkā (mnt)
- [ ] 2.1 Add `mnt_majjhima_nikaya_tika(g)` mirroring `mna` with `book = "MNt"`.
  → verify: ruff clean.
- [ ] 2.2 Add dispatcher case after `case "mna":`.
  → verify: grep hit.
- [ ] 2.3 Smoke-test `mnt` with `mūlapariyāya`.
  → verify: ≥1 tuple, no errors.

## Phase 3 — SN ṭīkā (snt)
- [ ] 3.1 Add `snt_samyutta_nikaya_tika(g)` mirroring `sna` with `book = "SNt"`.
  → verify: ruff clean.
- [ ] 3.2 Dispatcher case after `case "sna":`.
  → verify: grep hit.
- [ ] 3.3 Smoke-test `snt` with `paṭiccasamuppād`.
  → verify: ≥1 tuple, no errors.

## Phase 4 — AN ṭīkā (ant)
- [ ] 4.1 Inspect AN ṭīkā XML for `div id="anN_M"` scheme; document deviations.
  → verify: findings written below.
- [ ] 4.2 Add `ant_anguttara_nikaya_tika(g)` mirroring `ana` with `book = "ANt"`.
  → verify: ruff clean.
- [ ] 4.3 Dispatcher case after `case "ana":`.
  → verify: grep hit.
- [ ] 4.4 Smoke-test `ant` with `rūpādivagg`.
  → verify: ≥1 tuple, no errors.

## Phase 5 — Abbreviation row
- [ ] 5.1 Add row `DNnt` to `shared_data/help/abbreviations.tsv` between `DNa` and `DNt`. Columns: abbrev, meaning, pāli (empty), example (empty), explanation, ru_abbrev (empty), ru_meaning.
  → verify: `rg -n '^"DNnt"' shared_data/help/abbreviations.tsv` returns 1 hit; column count matches header (7 tab-separated fields).
- [ ] 5.2 Switch parser prefix from `DNAt` to `DNnt` so it matches the abbreviation.
  → verify: smoke-test `dnt` returns sources with `DNnt…` prefix.

## Phase 6 — Final verification
- [ ] 6.1 `uv run ruff check tools/cst_source_sutta_example.py`.
  → verify: exit 0.
- [ ] 6.2 `uv run pytest tests/ -k cst_source --no-header -q`.
  → verify: passes or "no tests collected".
- [ ] 6.3 `__main__` block restored to pre-thread default.
  → verify: tail of file matches original.
