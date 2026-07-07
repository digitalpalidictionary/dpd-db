# Plan: Chunked Typst compile for the PDF exporter

## Phase 1 — Experiments (scratchpad only, no production code)

- [x] 0. (added mid-thread) Update typst first: typst-py 0.14.9 →
      0.15.0 via `uv lock --upgrade-package typst` + `uv sync
      --all-groups`; CLI 0.15.0 benchmarked from downloaded binary
      (system install pending user sudo)
- [x] 1. E1: chunk splitter prototype (16 chunks, ~200k lines each)
      → verified: concatenated bodies == original body byte-exact
- [x] 2. E1: serial compile, fresh process each → verified: typical
      chunk 1.5–1.8 GB / ~6.5 s; two dense family chunks hit 4.6 GB
      (adaptive sizing needed in Phase 2); 142 s total on 0.15
- [x] 3. E1b: mechanism comparison → verified: in-process binding
      retains ~1.2 GB per call (unusable); binding-subprocess fastest
      (~4.8 s); CLI `--no-pdf-tags` least memory (1.60 GB) + 4.5×
      smaller chunks; CLI chosen
- [x] 4. E2: page numbering baked `#counter(page).update(N)` chain
      → verified: printed footers continuous across all boundaries;
      `"1 / 1"` → `"1"` (grand total would need a second pass)
- [x] 5. E3: pypdf merge 33 s / 2.0 GB; merged 79.7 MB untagged
      (vs 442 MB baseline); pypdf drops tags/metadata/lang — metadata
      restorable, tags accepted loss → verified: 14,974 pages, links
      work, page render pixel-identical except footer
- [x] 6. E4: TOC + bookmark data proven recoverable from chunk
      outlines (89 entries, absolute pages); Contents regeneration +
      outline rebuild feasible; merged PDF ready for user eyeball at
      `scratchpad/chunks/merged_v15.pdf`
- [x] 7. E5: json()+eval spike KILLED (~10 % time / ~14 % memory,
      below 20 % criterion); Jinja pipeline stays
- [x] 6b. E4b (user-flagged showstoppers): Contents regenerated with
      all 13 sections + real page numbers (chunk 0 pagination
      unchanged); bookmark tree rebuilt (13 top-level, letters
      nested); metadata + /Lang restored → verified in
      `chunks/merged_final.pdf`
- [~] 8. CHECKPOINT (report-only): design decisions locked (plain
      numbering, Contents required, tags loss accepted, serial);
      awaiting user eyeball of `merged_final.pdf` — HARD GATE
      before Phase 2

## Phase 2 — Implementation (branch `157-pdf-chunked-compile`)

- [x] 9. Refactored `pdf_exporter.py`: render (unchanged) → split at
      entry boundaries (`split_body_into_chunks`, headers carried to
      next chunk, redundant pagebreak stripped) → serial
      `typst compile --no-pdf-tags` subprocess per chunk with
      `#counter(page).update()` chaining → Contents regenerated from
      chunk outlines + chunk 0 recompiled (pagination asserted
      unchanged) → pypdf merge with rebuilt bookmark tree,
      metadata + /Lang restored → zip. `front_matter.typ` numbering
      `"1 / 1"` → `"1"`; `.gitignore` +`exporter/pdf/typst_chunk_*`
- [x] 10. Deleted `pdf_exporter_test.py` prototype; reworked its
      caller `.github/workflows/pdf_test.yml`
- [x] 11. Tests: 14 new in `tests/exporter/pdf/test_pdf_exporter.py`
      (split/state/source/contents units + real end-to-end via typst
      CLI, skipif no CLI; fast, no `slow` marker needed); existing
      3 tests still pass
- [x] 12. Column-limited ORM query: SKIPPED — render peak is 2.9 GB,
      well within CI budget; not worth the churn (spec: optional)
- [x] 13. Full local run: 31 chunks, 14,982 pages, 80 MB (vs 442 MB),
      5:22 wall, 3.5 GB peak process tree (vs ~29 GB); bookmarks
      13 top-level + nested letters, Contents correct, boundary
      footers continuous (997/998/999)
- [x] 14. Lint gate: ruff check + format clean, pyright 0 errors on
      both touched Python files; full suite 1245 passed
- [x] 15. CI proof: existing `pdf_test.yml` reworked — checks out the
      triggering branch (was hardcoded `main`), builds DB from TSV
      (established pattern, deviation from spec's release-asset idea),
      drops non-PDF exporters, installs typst musl CLI, runs the new
      exporter, uploads `dpd-pdf.zip` (user triggers)
- [~] 16. Report for review (`/kamma:3-review`); commits only when
      user asks
