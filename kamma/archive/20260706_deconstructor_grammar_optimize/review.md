## Thread
- **ID:** 20260706_deconstructor_grammar_optimize
- **Objective:** Extend the goldendict header-hoist optimization to the deconstructor and grammar_dict exporters (byte-identical, measured).

## Files Changed
- `exporter/deconstructor/data_classes.py` — header lifted to module fn `generate_deconstructor_header(jinja_env)`; `DeconstructorData` simplified (no per-instance header; unused `pth` dropped).
- `exporter/deconstructor/deconstructor_exporter.py` — constant header computed once before the loop; loop uses `DeconstructorData(i)` + `header + minify(...)`.
- `exporter/grammar_dict/data_classes.py` — header lifted to `generate_grammar_header(jinja_env)`; `GrammarData(lookup_entry, header)` takes it injected.
- `exporter/grammar_dict/grammar_dict.py` — constant header computed once; passed into `GrammarData`.
- `tests/exporter/deconstructor/test_data_classes.py` (new), `tests/exporter/grammar_dict/test_data_classes.py` (new).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `tests/exporter/*/test_data_classes.py` | Tests don't pin header *content* bytes | A future `CSSManager` drift wouldn't be caught by these unit tests | Deliberate per no-frozen-golden-master policy; parity proven via temp harness. Accepted, no change. |
| 2 | nit | both `data_classes.py` header fns | `render(css="", js="")` passes args the templates ignore | Harmless; carried over verbatim for byte-parity | Leave; clean up only in a future output-changing pass. |

## Fixes Applied
- None required. No blocking or major findings from either reviewer.

## Test Evidence
- Independent reviewer (fresh fable subagent, zero context): verified byte-identical header logic vs `git show HEAD:`, header constancy, safe `pth` drop, all call sites updated, webapp's own classes isolated, no dead code. Verdict PASSED.
- CodeRabbit (`coderabbit review --base main --type uncommitted`) → **No findings**.
- `uv run pytest tests/exporter/ tests/tools/` → 863 passed, 16 deselected.
- `uv run pytest tests/exporter/deconstructor/ tests/exporter/grammar_dict/` → 16 passed.
- `ruff check` + `ruff format` + `pyright` → clean on all touched files.
- Parity: deconstructor 0 diffs / 50k vs unmodified; grammar 0 diffs across all 285,344 distinct grammar strings vs git HEAD.
- Live run confirmed by user: grammar compile 6.7s (was ~84s); deconstructor render ~2s/50k (was ~15s). Remaining deconstructor section time is now the out-of-scope pyglossary write/zip stage.

## Verdict
PASSED
- Review date: 2026-07-06
- Reviewer: independent fable subagent + CodeRabbit + Claude (consolidation)
