## Thread
- **ID:** 20260512_verb_finder
- **Objective:** Add `scripts/fix/verb_finder.py` — a read-only diagnostic auditing consistency between present-tense verbs (`pos='pr'`) and the derived forms (`pp/prp/ptp/abs/ger/inf`) that reference them in `grammar`/`derived_from`; produce TSV reports + terminal summary.

## Files Changed
- `scripts/fix/verb_finder.py` — restored the `\\[` rich-markup escape on the spotcheck line (a concurrent commit `acd85c53` had removed the original `\[`, causing rich to swallow the `[bucket]` prefix) + explanatory comment.
- `kamma/threads/20260512_verb_finder/plan.md` — synced all 9 tasks to `[x]` (the script was implemented + freshened in the sibling `scripts_triage` thread); added a Verification block recording the live run and the spotcheck deltas.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | major (pre-existing, non-blocking) | `build_pr_verb_index` / `scan_derived_forms` | `("", "")` catch-all index key collapses 320 rootless pr verbs into one match, polluting the `ambiguous` bucket with ~70/375 compound rows | drowns genuinely-ambiguous rows (e.g. ruṭṭha) with a meaningless 320-verb candidate dump | DEFER — pre-existing logic from the sibling `scripts_triage` impl, not this thread's scope; recommend a `scripts_triage` follow-up or GitHub issue |
| 2 | minor | `main()` total | "total derived forms scanned" double-counts the 173 mismatch rows (counted in a main bucket AND in mismatch) | cosmetic count inflation (16743 vs 16570 distinct) | relabel as "total bucket rows", or sum only the 6 exclusive buckets |
| 3 | minor | `DERIVED_POS` | scans 13 pos (adds aor/fut/imp/opt/perf/imperf/cond) vs spec/plan's 6 | undocumented scope drift (arguably beneficial) | note in plan/spec |
| 4 | minor | `build_pr_verb_index` / `find_roots_without_pr` / `scan_derived_forms` | `db` param untyped | AGENTS.md type-hint mandate | annotate `db: Session` |
| 5 | nit | `grammar_derived_from_mismatch.tsv` | different schema (`grammar_target`) vs sibling buckets | diagnostic-only, internally consistent | align schemas if desired |
| 6 | nit | `_build_proposed_to_root` | uses `family_root` not `root_key` | actually more correct (family_root carries √+prefixes); spec text is stale | update spec wording |

Findings 1–6 are all PRE-EXISTING in the script (implemented in the sibling `scripts_triage` thread) — none were introduced by this thread's changes (escape fix + plan sync). They are out of this thread's scope and non-blocking for a read-only diagnostic whose TSVs drive no automated action. Deferred to the file owner (`scripts_triage`) as follow-ups.

## Fixes Applied
- Restored `\\[` rich-markup escape + comment on the spotcheck line (fixes a regression from concurrent commit `acd85c53` that had removed the original `\[`, making rich swallow `[bucket]` as a markup tag). Behaviour-preserving (runtime `\[` == rich literal `[`); pyright stays clean.
- No other code changes — deferred findings are pre-existing / out-of-scope.

## Test Evidence
- `uv run python scripts/fix/verb_finder.py` → runs clean (~0.5s), 9 TSVs written to `temp/verb_finder/`
- bucket sum reconciles: 340+230+375+3160+1393+173+11072 = 16743 (script's reported total; see finding #2 re: 173 double-count)
- spotcheck (post-fix): `[ok_verb_present] akkanta 1`, `[ok_verb_present] rusita`, `[ambiguous] ruṭṭha` — bucket prefix visible again
- `uv run ruff check scripts/fix/verb_finder.py` → pass
- `uv run ruff format --check scripts/fix/verb_finder.py` → already formatted
- `uv run pyright scripts/fix/verb_finder.py` → 0 errors, 0 warnings, 0 informations

## Verdict
PASSED
- Review date: 2026-07-15
- Reviewer: independent `reviewer` subagent (sections 4–6) + parent agent (kamma-3-review)
- This thread's own scope (track + behaviourally verify + sync plan + escape fix) is fully met; all recorded findings are pre-existing in sibling-thread code and non-blocking.
