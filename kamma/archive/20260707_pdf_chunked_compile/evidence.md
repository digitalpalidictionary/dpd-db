# Phase 1 evidence (2026-07-07)

All measurements on the real `typst_data_lite.typ` (106 MB, 89,145
headwords + 79,020 EPD entries, single-compile baseline = 14,966 pages
/ 442 MB / ~29 GB peak). Typst updated first per user instruction:
typst-py 0.14.9 → 0.15.0 (`uv lock --upgrade-package typst`,
`uv sync --all-groups`; pyproject constraint `>=0.14.9` unchanged),
CLI 0.15.0 benchmarked from a downloaded binary
(`/usr/local/bin/typst` still 0.14.0 — needs user sudo to replace).

## E1 — chunked compile works and bounds memory

16 chunks of ~200k lines cut at `#par[`/`#heading3[` boundaries;
concatenated chunk bodies reproduce the original body **byte-exact**.
Chunks 2+ get: defs preamble + replayed `#set page`/`#set par` state +
`#counter(page).update(N)`.

Full pipeline on typst 0.15 CLI `--no-pdf-tags`, serial, fresh process
per chunk:

- total pages 14,974 (+8 boundary part-pages vs baseline, cosmetic)
- compile 142 s + merge 33 s ≈ 3 min total
- max chunk peak RSS 4.57 GB; typical chunk 1.5–1.8 GB
- the two fat chunks (1,644 / 1,736 pages — family sections are
  ~2× denser pages-per-line) need **adaptive chunk sizing** in Phase 2
  to bound everything at ~2 GB

## E1b — Python module vs subprocess (typst 0.15, chunk_05, 848 pages)

| Mechanism | Wall | Peak RSS | Chunk PDF |
|---|---|---|---|
| binding, in-process repeated | ~4.5 s/chunk | **retains ~1.2 GB per call** (comemo cache): 6.5 GB after 5 chunks, ⇒ ~20 GB over 16 — unusable | — |
| binding, fresh subprocess | 4.4–5.2 s | 1.69–1.72 GB | 21.5 MB (tagged; binding cannot disable tags, incl. typst-py 0.15.0) |
| CLI subprocess (tagged) | 6.7–6.9 s | 1.70 GB | 21.5 MB |
| CLI subprocess `--no-pdf-tags` | 6.4–7.7 s | **1.60 GB** | **4.75 MB** |

Fresh-subprocess-per-chunk is mandatory. Binding is ~25 % faster;
CLI `--no-pdf-tags` uses least memory and writes 4.5× smaller chunks.

## E2 — continuous page numbering proven

`#counter(page).update()` chaining gives printed footers continuous
across every boundary (…997, 998… and …11558, 11559, 11560…), printed
number == physical position. `"1 / 1"` format must become `"1"`
(chunk-local totals are wrong); a correct grand total would need a
second full compile pass.

## E3 — merge proven, with two consequences

pypdf merge of 16 chunks: 33 s, ~2.0 GB peak, page count exact,
external links work, page 5 renders pixel-identical to baseline
(except footer format).

1. pypdf drops `/StructTreeRoot` (accessibility tags), `/Metadata`,
   `/Lang`, `/PageLabels` — tags are unmergeable; metadata/lang are
   trivially restorable in the writer. Since tags die in the merge
   anyway, compiling with `--no-pdf-tags` costs nothing and shrinks
   the final artifact: **merged = 79.7 MB untagged vs 122 MB from
   tagged chunks vs 442 MB baseline (5.5× smaller)**.
2. Bookmark tree flattens (level-2 letter headings become top-level
   in chunks with no level-1 heading). Fix in Phase 2: rebuild the
   outline tree in pypdf — all titles + absolute pages are extractable
   from chunk outlines (proven: 89 entries with correct offsets).

## E4 — TOC

The front-matter `#outline()` only lists chunk-0 headings (6 links vs
13 in baseline). Fix: generate the Contents page from the extracted
section→page table and recompile chunk 0 last (TOC stays 1 page, so
offsets are unaffected). Merged output for user eyeball:
`scratchpad/chunks/merged_v15.pdf`.

## E4b — Contents + bookmark tree FIXED in prototype (user-flagged)

User verdict on first merge: incomplete Contents and flattened
bookmarks are mission-critical. Both fixed and proven
(`fix_toc_outline.py`, output `chunks/merged_final.pdf`):

- All outlined headings extracted from chunk PDFs with absolute pages;
  the 13 level-1 sections identified by title.
- `#outline(depth: 1)` in chunk 0 replaced with a generated Contents
  listing all 13 sections with true page numbers (dot leaders);
  chunk 0 recompiled — pagination unchanged (997 pages), so offsets
  hold. Printed TOC has no hyperlinks (cross-chunk links can't be
  compiled in; bookmarks provide click navigation).
- Merge re-done with `import_outline=False` + outline tree rebuilt via
  `add_outline_item`: exactly 13 top-level bookmarks, letter headings
  correctly nested under their sections (P2E: a ā i ī u ū e o k g …).
- Metadata (`/Title`, `/Author`) and `/Lang` restored on the writer.
- Final: 79.7 MB, 14,974 pages.

User decisions locked: plain `"N"` numbering; Contents page required
(now proven); accessibility-tag loss accepted; serial compiles.

## E5 — json() + eval spike: KILLED

Same 2,000 EPD entries, identical 228-page output:
markup 1.73 s / 0.45 GB vs json+eval 1.55 s / 0.39 GB — ~10 % faster,
~14 % lighter, below the 20 % kill criterion. Layout dominates, parse
savings don't materialize at our entry granularity. **Jinja pipeline
stays.**

## Phase 2 full-scale result (production code, branch
`157-pdf-chunked-compile`)

`/usr/bin/time -v` over the whole rewritten pipeline (100k-line
budget → 31 chunks): 14,982 pages, 80 MB final PDF (36 MB zip),
5:22 wall (render 12 s, compiles ~3.5 min, contents rebuild 5 s,
merge 89 s, zip 3 s), **3.5 GB peak RSS for the entire process
tree**. Fat family chunks now ≤ ~900 pages. Bookmarks: 13 top-level
sections with letters nested; Contents lists all 13 sections with
true page numbers; boundary footers continuous. Full pytest suite:
1245 passed.

## Recommended Phase 2 design (for approval)

1. Keep Jinja render → split at entry boundaries with density-aware
   chunk sizing (~800–1,000 pages/chunk, families sections use
   smaller line budgets) → serial `typst compile --no-pdf-tags`
   subprocess per chunk with baked page offsets → pypdf merge with
   metadata/lang restored + outline tree rebuilt + generated Contents
   page (chunk 0 compiled last).
2. Page numbering: plain `"N"` (recommend) — `"N / total"` costs a
   full second compile pass of all chunks.
3. Compile mechanism: typst CLI `--no-pdf-tags` (lowest memory,
   5.5× smaller artifact); CI installs the musl binary in one step.
   Requires typst ≥ 0.14 for `--no-pdf-tags`.
4. Serial compiles in CI (~3 min total, ≤ ~2.3 GB peak with adaptive
   sizing). Parallel two-pass is possible (~2× compute, ~½ wall) but
   memory-risky on the 16 GB runner — not recommended (cf. the
   deconstructor parallel-export OOM revert).
5. Accessibility tags are lost in any merge-based design — accepted
   trade-off (they also don't survive today's pypdf prototype).
