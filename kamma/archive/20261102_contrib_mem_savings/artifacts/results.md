# Results: contributor instance memory savings (2026-11-02)

Commit under test: 247a8429 (laptop and server the same, `server/results_savings.md` `## 4.2`).

## What was built

| Lever | Laptop saving (MB) | Equivalence | Status |
|---|---|---|---|
| L1 + L7b split corpus (slim columns, no inflection columns, `freq_data` only for headwords with an empty meaning) | 222.1 (warm build) | (d) PASS, 0 differences in 2,589 | built, contributors only |
| L8 compact set (sorted 64-bit hashes) for both inflection sets | 259.3 | (e) PASS: 0 of 1,627,687 members lost, 0 of 200,001 non-members accepted | built, contributors only |
| L1 + L7b + L8 together | 481.7 (1,386.3 to 904.6 MB) | all PASS | built; real code 909.0 MB (3 runs), 0.5 % from the prototype |
| L2, L3, L4, L5, L6, L7 | see `lever_results.md` | see `equivalence.md` | skipped, reasons in `decision.md` |

## Server: before and after (one instance, `dpd-gui@alice`)

Source: `server/readings_savings.jsonl`, labels ending `_run2`; before values from `kamma/threads/20261102_contrib_mem_measure/artifacts/results.md`.

| Reading | Before (MB) | After (MB) | Change |
|---|---|---|---|
| 15 s after restart | 86.5 | 86.5 | 0 |
| Database loaded | 718.6 | not taken | the warm-up starts 9 s later, too fast to catch |
| All tabs and tools ready | 1,165.9 | 943.3 | -222.6 |
| After one `mn` book | 1,485.0 | 1,045.7 (peak 1,113.4) | -439.3 |
| After opening Pass1Add | n/a | 1,045.7 | the word finder was already built by the warm-up |

Caveats:
- The first server run (labels without `_run2`) is invalid: 2,059.4 MB at warm-up, because two extra browser sessions of this agent were open. Each browser connection builds its own copy of the app in the same process, so a second open page costs memory too. The log showed three "App initialized" lines.
- `mn` has no missing words, so the book run found 0 words (counter 0 / 0, confirmed by the owner). The same was true of the earlier thread's `mn` run, so the before and after values compare the same work. A book with many missing words was not run.
- The "refresh DB" risk is unchanged: on a slim corpus the extra memory is 284.9 MB (full corpus: 172.5 MB) because the detector keeps the old rows.

## Projection (baseline 1,066 MB plus N times per instance, same formula as before)

| Contributors | Before (1,485.0 MB each) | After (1,045.7 MB each) | After, at peak (1,113.4 MB each) |
|---|---|---|---|
| 3 | 5,521 | 4,203 | 4,406 |
| 8 | 12,946 | 9,432 | 9,973 |
| 16 | 24,826 | 17,797 | 18,873 |

Eight contributors fit on a 16 GB server with about 6 GB to spare. Sixteen do not. The one-process rebuild (option E) is still the plan for more than 8.

## Done check (spec.md, "How we'll know it's done")

1. Met. `lever_results.md` holds every lever with median, min, max and start-up peak.
2. Met. `decision.md`: the owner said "keep going", so the default rule applied (at least 100 MB and a clean equivalence).
3. Met. New tests fail when reverted (3 fail with the contributor branches off, 5 fail with the hash lookup broken; `plan.md` DRIFT note). `ruff`, `pyright`, `just typecheck` pass. `pytest tests/gui2 tests/tools`: 1,433 pass, 2 fail, neither from this thread (`plan.md`, after 3.7).
4. Met. `server/results_savings.md` and `server/readings_savings.jsonl`.
5. Met. The desktop path is unchanged and its existing corpus tests pass (`plan.md`, after 3.7).

## What is left

- Option E (one process for all users) when there are more than 8 contributors.
- Decide whether to cut the "refresh DB" extra memory (284.9 MB on a slim corpus).
