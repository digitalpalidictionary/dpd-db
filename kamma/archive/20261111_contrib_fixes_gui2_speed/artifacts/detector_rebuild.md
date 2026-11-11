# F3 — after-save detector rebuild: full vs slim row load

Machine: laptop. Load average at measurement: **0.93, 1.00, 1.19** (1-minute
under 1 — clean). Method: fresh process per run, 3 runs per variant, median
with min–max. No run hit the 1,500 MB cap. The first `full` run (13.66 s load)
was the cold-disk run and is reported but excluded from the median as the
warm-up.

| variant | load s (median) | build s (median) | peak MB (median) |
|---|---|---|---|
| full (the worker's query today: 5 heavy HTML columns deferred) | 2.53 (2.51–2.53; cold run 13.66) | 0.92 (0.92–0.92) | 759 (758–759) |
| slim (only the detector's 14 columns, `_load_contributor_corpus`-style) | 1.49 (1.45–1.50) | 1.05 (1.03–1.05) | 538 (537–538) |

Totals: full **3.45 s**, slim **2.54 s** — slim is 0.91 s lower, and its peak
is 221 MB lower.

**Recommendation: slim is worth a follow-up** (total time at least 0.5 s lower
AND peak not higher — both met). Note the earlier `lever_results.md` figure
(slim holds more memory) applied to a detector kept as the live cache; here the
slim rows are freed after the build, so the peak is what matters, and it is
lower.
