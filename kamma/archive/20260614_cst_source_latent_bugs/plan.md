# Plan: cst_source latent bugs

> STATUS: NOT STARTED — backlog thread created 2026-06-14 from the refactor's findings.
> These are OUTPUT-CHANGING fixes (real dictionary data), not a lint pass. Each needs a
> domain decision + downstream check before editing. See spec.md.

## Priority order
A (apt prefix) and B (abh2 xxxxxxx) are real data artifacts in shipped output →
highest value. C (kn17) is dead code → safe but unverifiable without a crafted test.
D (x["n"] typing) is benign → fold into any future typing cleanup.

## Phase 1 — Assess blast radius (read-only, no edits)
- [x] Grep the built db / exports for `xxxxxxx` and for `apt`-derived `AP…` source codes; list every downstream consumer of these `source`/`sutta` strings (lookup, sutta_info, exporters).
  → verify: a short written impact note per finding (A, B) — safe-to-change vs. needs-migration.

### Impact note (2026-06-14)
Flow: `find_cst_source_sutta_example` (extractor) → gui2 example picker → editor saves
`source_1/source_2` + `sutta_1/sutta_2` on a `DpdHeadword`. So these strings only persist
when an editor picked an apt/abh2 example. Source of truth = `db/backup_tsv/`.

- **A (apt prefix):** 3 shipped headwords carry apt-derived source codes — `AP2.5`
  (yaññaṅga), `AP3.3` (attha 3.3), `AP2.3` (gupa), all in `source_1`. Both `AP` **and**
  `APt` are registered book codes in `scripts/build/generate_books_tsv.py:126-127` (both
  → "" no-nikāya), so `APt` is valid downstream. `ap` uses prefix `APP` → no collision.
  → **needs-migration**: changing the prefix must rewrite those 3 `source_1` values too.
- **B (xxxxxxx):** ZERO occurrences anywhere in `db/backup_tsv/`. No shipped data affected.
  → **safe-to-change**: pure forward-only fix, no migration.
- Consumers of source/sutta: gui2 (live regen on edit), `exporter/analysis/{passage_by_code,
  book_to_verses}.py`, persisted `source_1/2` + `sutta_1/2` columns. No lookup/sutta_info keying
  off these prefixes.

## Phase 2 — A: ap/apt prefixes  (`tools/cst_source/parsers/misc.py`)
> DECISION (user, 2026-06-14): registered codes are `AP` (Abhidhānappadīpikāpāṭha,
> book `ap`) and `APt` (Abhidhānappadīpikā Ṭīkā, book `apt`). `APP` is bogus. Both
> parsers were cross-wired. See spec.md "CORRECTION".
- [x] Fix `AptParser`: drop dead `book = "AP"` overwrite so `apt` emits `APt`.
- [x] Fix `ApParser`: `book = "APP"` → `book = "AP"` (APP was never a real code).
- [x] Migrate 5 shipped `source_1` values in `dpd.db`: `APP1`→`AP1`, `APP2.4`→`AP2.4`,
      `AP2.5`→`APt2.5`, `AP3.3`→`APt3.3`, `AP2.3`→`APt2.3`. (TSV backup regenerates from db.)
- [x] Unit tests asserting both `ap`→`AP` and `apt`→`APt` prefixes.
  → verify: `tests/tools/cst_source/test_parsers.py` green (2 passed); db shows no `APP*` left.

## Phase 3 — B: abh2 placeholder  (`tools/cst_source/parsers/abhidhamma.py:112`)
> DECISION (2026-06-14): mirror the sibling `Abh1Parser` no-vagga subhead branch
> (`abhidhamma.py:59-60`), which uses `f"{self.section}, {sutta}"` for the exact same
> `not self.vagga` condition. `xxxxxxx` sat where `{self.section}` belongs. Zero shipped
> rows affected (Phase 1), so pure forward-fix.
- [x] Decide the correct no-vagga sutta string; replace `"xxxxxxx"` with `{self.section}`.
- [x] Unit test for a vagga-less `abh2` subhead asserting the corrected `sutta`.
  → verify: test green; no `xxxxxxx` remains in output.

## Phase 4 — C: kn17 dead branch  (`tools/cst_source/parsers/khuddaka.py:485`)
> DECISION (user, 2026-06-14): DELETE — proven unreachable. Real-life probe over the
> actual XML (`s0517m.mul.xml`, 124 subheads): full parse raised no UnboundLocalError
> and the branch condition (`vagga and section and not sutta_name`) was met 0 times
> (every kn17 subhead has a non-empty name). It's copy-paste residue from a prior book.
- [x] Prove reachability against real XML — confirmed unreachable (0 hits, no raise).
- [x] Delete the unreachable branch (referenced unbound locals `vagga`/`section`).
- [x] Add `@pytest.mark.slow` test parsing real kn17, asserting 0 hits + no raise.
  → verify: fast tests 3 passed; slow test 1 passed.

## Phase 5 — D: x["n"] typing  (optional, lowest priority)
> DECISION (user, 2026-06-14): annotate, don't cast. `int(x["n"])` would risk
> ValueError / parity drift (CST `n` can be ranges/leading zeros). Widened the
> genuinely dual-typed counter fields in `base.py` to `str | int`; no runtime change.
- [x] Widen `sutta_counter`/`section_counter`/`vagga_counter` in `base.py` to `str | int`
      (covers `sutta.py:178`, `commentary.py:417/448`, plus the section/vagga str assigns).
  → verify: behaviour unchanged — full cst_source/analysis slow parity suite green (33 passed);
    full fast suite green (2222 passed).

## Done when
- A/B/C each resolved with a recorded decision; tests added; downstream impact handled.
- `uv run pytest tests/` green; `uv run pytest -m slow` green.
- Does NOT close #157.
