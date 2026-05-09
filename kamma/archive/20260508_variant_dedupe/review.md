## Thread
- **ID:** 20260508_variant_dedupe
- **Objective:** Dedupe `DpdHeadword.variant` (remove tokens already in syn/var_phon/var_text) and stop new var_phon/var_text writes from also writing to variant. Part of #144.

## Files Changed
- `scripts/find/variant_dedupe.py` — new dry-run-default script that removes redundant variant tokens
- `tools/synonym_variant.py` — `assign_relationship` and `assign_relationship_dict` no longer write to variant from var_phonetic / var_text branches
- `tests/db_tests/single/test_add_phonetic_variants.py` — repaired pre-existing import drift; updated two assertions to reflect new var behavior; removed dead tests for helpers that no longer exist
- `kamma/threads/20260508_variant_dedupe/{spec,plan,review}.md` — thread artefacts
- DB data: 10,316 headwords had variant tokens removed (11,692 tokens; 9,814 variants emptied)

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `db_tests/single/add_phonetic_variants.json` | 9 new exception entries from user's review session | Out of this thread's scope (data, not code) | Commit separately or note in commit message |
| 2 | minor | `tools/synonym_variant.py:254` | Added phonetic rule `("cch", "ñch", True)` | Out of this thread's scope; user-added in session | Note ride-along in commit message or split commit |

No blocking or major findings.

## Fixes Applied
None during review (no blocking/major findings to fix).

## Test Evidence
- `uv run ruff check tools/synonym_variant.py scripts/find/variant_dedupe.py tests/db_tests/single/test_add_phonetic_variants.py` → pass
- `uv run pytest tests/db_tests/single/test_add_phonetic_variants.py` → 25 passed
- `uv run scripts/find/variant_dedupe.py` (re-run after `--apply`) → 0 affected (idempotent)

## Residual Risks / Notes
- Same-agent review (implementer = reviewer). Independence reduced.
- Pre-existing pycache filename collision in `tests/exporter/webapp/test_dpd_headword.py` — unrelated; not introduced by this thread.
- End-to-end smoke check on live add_*.py scripts deferred to user (interactive). Behavior covered by the two updated `test_assign_*` unit tests.
- CodeRabbit review run after agent review: 0 findings.

## Verdict
PASSED
- Review date: 2026-05-08
- Reviewer: Claude (same-agent caveat noted)
