# Review

## Thread
- **ID:** 20260715_pass2pre_next_word_speed
- **Objective:** Make Pass2Pre next-word loading instant by replacing the per-word CST re-parse with a per-session in-memory corpus index.

## Files Changed
- `tools/cst_source/corpus_index.py` — new `CstSourceIndex`: one-off soup walk per book, flat rows, precomputed gatha examples; `find_examples()` byte-identical to the live extractor
- `tools/cst_source/__init__.py` — export added (gitignored file, local convenience only)
- `gui2/pass2_pre_controller.py` — lazy index build in `get_cst_examples`, reset per PreProcess run
- `tests/tools/cst_source/test_corpus_index.py` — 6 fast unit tests + slow real-book parity test (non-vacuous guard)
- `tests/gui2/test_pass2_pre_components.py` — regex-capture test migrated from monkeypatched finder to injected `FakeIndex`

## Findings
Independent subagent review (fresh context, zero memory) — no blocking, no major.

| # | Severity | Location | What | Resolution |
|---|----------|----------|------|-----------|
| 1 | minor | `corpus_index.py` `_resolve_gatha1` | Stuck gatha groups cost 1s/element at build (vs at match-time live); rend-less sibling divergence | Comment added; AN benchmark shows negligible (1 element, 1.0s) |
| 2 | minor | `corpus_index.py:50` | NavigableString sibling yields `[]` where live path would crash | Deliberate improvement; documented in docstring |
| 3 | nit | `corpus_index.py` | `x.get("rend")` tolerates missing rend | Verified unreachable divergence (parsers crash both paths first); no action |
| 4 | minor | `.gitignore:20` | ALL `__init__.py` gitignored — export can't be committed | Fixed: tracked files import from `tools.cst_source.corpus_index` directly |
| 5 | nit | spec.md | "eliminates the wait including first word" overstated | Spec wording corrected (first word pays ~1.4s build) |

CodeRabbit (parallel run, free CLI): 0 findings across all 6 thread files. Agent review verified semantics parity branch-by-branch (element order, parser.update timing, per-book dedupe, source/sutta guard, gatha cache soundness, stuck-loop guard placement) and controller wiring staleness.

## Fixes Applied
- Divergence comment in `_resolve_gatha1` docstring
- Spec rationale wording (first-word build cost)
- Imports of `CstSourceIndex` moved off the gitignored `__init__.py`

## Test Evidence
- `uv run pytest tests/` → 1582 passed
- `uv run pytest tests/gui2/ tests/tools/cst_source/` → 271 passed (post-fixes: 26 cst_source tests re-run green)
- `uv run pytest -m slow tests/tools/cst_source/test_corpus_index.py` → parity on kn1 incl. match-all regex, non-empty
- ruff check + format + pyright clean on all touched files (`tools/cst_source` lint-excluded by config; checked anyway)
- Manual: user confirmed AN run "blazing fast"

## Verdict
PASSED
- Review date: 2026-07-15
- Reviewer: independent general-purpose subagent + implementing agent (fix pass)
