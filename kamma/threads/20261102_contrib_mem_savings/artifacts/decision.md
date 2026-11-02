# Gate decision (task 2.6), 2026-11-02

The owner said "keep going until done", so the plan's default rule was applied without a pause: build a lever when it saves at least 100 MB per instance and its equivalence check is clean. `all_inflections_missing_meaning` is kept (the owner's rule: do not remove behaviour that exists); it is built in the same compact form.

Numbers: `lever_results.md` (laptop, 96 rows, all ok). Equivalence: `equivalence.md` (a to e PASS).

| Lever | Saving (MB) | Equivalence | Decision |
|---|---|---|---|
| L1 + L7b split corpus: slim columns, no inflection columns, `freq_data` only for headwords with an empty meaning | 222.1 (warm build) | (d) PASS, 0 differences in 2,589 | **BUILD**, contributors only |
| L8 compact set (sorted 64-bit hashes) for `all_inflections` and `all_inflections_missing_meaning` | 259.3 | (e) PASS: 0 of 1,627,687 members lost, 0 of 200,001 non-members accepted | **BUILD**, contributors only |
| L1 + L7b + L8 together | 481.7 (1,386.3 → 904.6 MB; start-up peak 1,432 → 967 MB) | all PASS | the target of this thread |
| L2 direct sets | 72.2 | (b) PASS | SKIP: replaced by L8 |
| L3 drop the unused second set | 40.7 | n/a | SKIP: removes behaviour; L8 makes it cheap instead |
| L4 interned word finder | −26.6 | (c) PASS | SKIP: costs memory |
| L5 `lookup` table instead of a set | 272.0 | NOT equivalent (1,181,761 set words absent from the table; 1 of 1,402 words of a real text differs) | SKIP |
| L6 lazy managers | 95.5 | n/a | SKIP: under 100 MB, and contributors use all four |
| L7 ceiling (no `freq_data` at all) | 241.8 | would change results | SKIP |

Risk noted, not fixed: after "refresh DB" on a slim corpus the extra memory is 284.9 MB (full corpus: 172.5 MB), because the detector keeps the old rows. Net memory stays far below today's.
