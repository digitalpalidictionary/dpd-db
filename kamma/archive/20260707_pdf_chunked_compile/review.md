## Thread
- **ID:** 20260707_pdf_chunked_compile
- **Objective:** Rework the PDF exporter to compile in memory-bounded chunks (split at entry boundaries, serial typst subprocesses, chained page numbering, pypdf merge with rebuilt bookmarks/Contents) so it never OOMs CI.

## Files Changed
- `exporter/pdf/pdf_exporter.py` — rewritten: chunked split/compile/merge pipeline replacing single `typst.compile()`.
- `exporter/pdf/templates/front_matter.typ` — page numbering `"1 / 1"` -> `"1"` (grand total would need a 2nd pass).
- `exporter/pdf/pdf_exporter_test.py` — DELETED obsolete per-section prototype.
- `.github/workflows/pdf_test.yml` — builds a minimal DB from TSV on the dispatched branch, runs the new exporter, uploads `dpd-pdf.zip`.
- `.gitignore` — ignore `exporter/pdf/typst_chunk_*`.
- `tests/exporter/pdf/test_pdf_exporter.py` — 14 new unit + end-to-end tests.
- `uv.lock` — typst 0.14.9 -> 0.15.0.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `pdf_exporter.py:53` `STATE_LINE_RE` | Replay regex only matches single-line `#set par/page`; the multi-line `#set page(paper:"a4", numbering:none)` in front_matter.typ is not captured. | Harmless today (a4 is typst's default paper; `numbering:none` is overridden by the later single-line `#set page(numbering:"1")` which IS captured), but a future body-level multi-line `#set page(margin:...)` would silently not replay into later chunks. | Add a comment noting single-line-only replay, or extend the regex to span multi-line sets. Not required now. |
| 2 | nit | `pdf_exporter.py:509-524` `_walk_outline` | Bare `items: list` type hint (elements are `Destination | list`). | Minor precision loss; pyright still clean. | Optional: `list[Any]`. |

## Fixes Applied
- None. Findings are non-blocking; left for author discretion.

## Test Evidence
- `uv run pytest tests/exporter/pdf/` -> 17 passed (14 new + 3 existing; end-to-end test executed, typst 0.15.0 on PATH — not skipped).
- `uv run ruff check` (both touched py files) -> All checks passed.
- `uv run ruff format --check` -> already formatted.
- `uv run pyright` (both touched py files) -> 0 errors.
- Verified `abbreviation_to_pdf.py` imports (GlobalVars, make_layout, make_abbreviations, clean_up_typst_data, save_typist_file) all still present/compatible; `save_typist_file` retained for that caller though no longer called by pdf main() (not dead code).
- Verified no orphaned references to deleted `pdf_exporter_test.py`; CI path (`exporter/share/dpd-pdf.zip`) matches `typst_lite_zip_path`.
- Traced state-replay (last-wins per rule+first-prop, correct for current templates) and Contents-recompile/bookmark-rebuild ordering (safe: `#outline` widget yields no bookmarks; trailing `#pagebreak()` + page-count assert guard the offsets) — both sound.

## Verdict
PASSED
- Review date: 2026-07-07
- Reviewer: Claude (independent review subagent, fresh context)
