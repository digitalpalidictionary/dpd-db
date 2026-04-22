## GitHub Issue
Side-effect of #192 — Sutta table: Add DN, MN, SN subsections, saṃyuttas, vaggas, etc.

## Architecture Decisions
- Add to `natsort_exact` (exact match list), not `natsort_prefixes`, because the
  user confirmed this specific set name is the only target.

## Phase 1 — Add sort entry

- [x] Add "saṃyuttas of the Saṃyutta Nikāya" to `SORT_STRATEGIES["natsort_exact"]`
  in `db/families/family_set.py` (line ~28, after "previous Buddhas").
  → verify: `_get_sort_strategy("saṃyuttas of the Saṃyutta Nikāya")` returns "natsort"
    and `_get_sort_strategy("previous Buddhas")` still returns "natsort".

## Phase 1 verification
- [x] Read the modified file and confirm both entries are present in `natsort_exact`.
