# Plan: abha (Abhidhamma commentaries)

## GitHub issue
#150 — leave open after this thread.

## Architecture decisions
- **Single prefix `ADha`** — matches existing abbreviation.
- **Mirror `mna_majjhima_nikaya_commentary`** — simplest flat commentary parser.
- **Unnumbered chapter fallback** — increment a running counter when `get_text_and_number` yields a non-int chapter number.
- **`book`/`title` rends don't drive numbering** — used only for human-readable sutta context.
- **Dispatcher case after `case "ana":`** — keeps all nikāya commentary cases adjacent.
- **gui2 entry after `ANa` in the commentaries group.**

## Phase 1 — Parser
- [ ] 1.1 Add `abha_abhidhamma_commentary(g: GlobalData) -> None` after `ana_anguttara_nikaya_commentary`. Use `book = "ADha"`, mirror `mna` structure.
  → verify: ruff clean.
- [ ] 1.2 Handle all rend types: `book` (no-op), `subsubhead` → `ADha0`, `chapter` → increment vagga_counter, `title` → update vagga context, `subhead` → increment sutta_counter, set source and sutta.
  → verify: logic visible in code; no stale counter from previous volume.
- [ ] 1.3 Add `case "abha": abha_abhidhamma_commentary(g)` after `case "ana":`.
  → verify: `grep -n 'case "abha"'` returns 1 hit.

## Phase 2 — gui2 dropdown
- [ ] 2.1 Add `"ADha Abhidhamma Commentary": "abha"` to `book_codes` in `gui2/dpd_fields_examples.py` after `"ANa Aṅguttara Commentary": "ana"`.
  → verify: ruff clean.

## Phase 3 — Smoke tests
- [ ] 3.1 `find_cst_source_sutta_example("abha", "cittuppād")` → ≥1 ADha… tuple.
- [ ] 3.2 `find_cst_source_sutta_example("abha", "khandh")` → count > 5, spread across multiple ADha{n} buckets.
- [ ] 3.3 `find_cst_source_sutta_example("abha", "dhātukath")` → ≥1 tuple, sutta string contains "dhātukath".

## Phase 4 — Final verification
- [ ] 4.1 `uv run ruff check tools/cst_source_sutta_example.py gui2/dpd_fields_examples.py` → exit 0.
- [ ] 4.2 `tail -5 tools/cst_source_sutta_example.py` matches original `__main__` block.
