# Plan — add_synonym_variant_del v1

## Architecture Decisions
- Reuse helpers from `add_synonym_variant_multi.py` rather than copy.
- `_is_valid_synonym` is a private helper in this file (single caller).
- Homonym handling — final rule:
  - Restrict the validity decision to same-pos-class candidates. A
    cross-pos homonym can't be the intended target.
  - If any same-pos candidate is fully valid → entry satisfied, skip.
  - If none is valid → flag the same-pos candidates only.
  - If no same-pos candidate exists at all → the reference is
    dangling; flag the cross-pos candidates so it surfaces for manual
    cleanup.
  Evolved from "per-candidate" → "any-valid wins"
  (`akatavedī`/`akataññū 2.1`) → "same-pos restricted"
  (`akkhema adj`/`bhaya 2 nt`) → "soft gating: ≥1 shared cleaned
  meaning is enough to suppress siblings" (`ativiya`/`bhusaṃ 1`). The
  gating check no longer uses strict validity; only `flag_candidates`
  selection does. Trade: tolerates wrong syns that share 1 cleaned
  meaning. Reversible.
- Prompt trimmed to d/e/pass/r/q (user-confirmed).
- Separate exceptions file (`add_synonym_variant_del.json`) via
  `syn_var_del_exceptions_path` on `ProjectPaths`. del-exception =
  "keep despite failing validity"; multi/single-exception = "don't
  propose as syn". Opposite verdicts must not share a file.

## Phase 1 — Rewrite the file
- [ ] Replace `db_tests/single/add_synonym_variant_del.py` with v1
      implementation.
      → verify: `uv run ruff check db_tests/single/add_synonym_variant_del.py` exits 0.
- [ ] Compile check.
      → verify: `uv run python -m py_compile db_tests/single/add_synonym_variant_del.py` exits 0.
- [ ] Phase verify: user runs the script and confirms behaviour.
