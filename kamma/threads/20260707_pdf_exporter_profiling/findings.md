# Findings: PDF exporter profiling (2026-07-07)

Measured on the real `typst_data_lite.typ` generated 2026-07-07
(106 MB, 3,005,343 lines, final PDF = 14,966 pages / 442 MB).
Machine: 30 GB RAM + 63 GB swap, typst CLI 0.14.0, binding 0.14.9.
Each compile ran in its own fresh process under `/usr/bin/time -v`.

## Where the time goes

| Stage | Time | Peak RSS |
|---|---|---|
| Python: DB load + Jinja render (all sections) | 10.4 s | 2.9 GB |
| Python: cleanup regexes | 1.5 s | — |
| `typst compile` (extrapolated full doc) | ~90 s (RAM-sufficient) | ~29 GB |

Python side is 12 s / 2.9 GB total; the 2.9 GB is the one-shot ORM load
of all 89,145 `DpdHeadword` rows in `make_pali_to_english`. Typst
dominates both time and memory. Locally the full run took ~3 min
(11:10 .typ written → 11:13 pdf) because the compile swaps.

## Where the memory goes: Typst layout, linear in pages

Slices of the real file (preamble preserved, cut at entry boundaries):

| Slice | Input MB | Pages | Wall | Peak RSS |
|---|---|---|---|---|
| 1 % | 2.1 | 162 | 1.1 s | 0.34 GB |
| 2 % | 4.2 | 316 | 1.8 s | 0.64 GB |
| 5 % | 10.5 | 758 | 3.7 s | 1.48 GB |
| 10 % | 21.0 | 1,511 | 8.3 s | 2.9 GB |
| 20 % | 35.1 | 2,894 | 17.2 s | 5.69 GB |
| EPD-only 10 % | 5.3 | 901 | 6.0 s | 1.94 GB |

Fit: **peak RSS ≈ 2 MB per output page**, cleanly linear (no
super-linear blow-up). 14,966 pages → **~29 GB peak**, matching the
observed local behaviour (fits in 30 GB + swap) and guaranteeing OOM
on the 16 GB `ubuntu-latest` runner — same runner-shutdown signature
as the deconstructor parallel-export OOM.

## Is it just Typst? — Yes

Typst performs whole-document layout and holds every laid-out page
frame (plus its comemo memoization cache) in memory before writing the
PDF; there is no streaming output and no CLI memory knob. ~2 MB/page
is simply its cost; a 15k-page single document needs ~29 GB. The
in-process Python binding makes it worse (compiler's 29 GB lands
inside the Python process already holding ~3 GB).

## Why the existing sectioned prototype is not enough

`pdf_exporter_test.py` (per-section compile + pypdf merge) bounds the
peak per *section*, but sections are wildly unequal: English→Pāḷi is
70 % of the file (~9,000 pages → ~19 GB alone). It still OOMs CI.

## Recommended path

Chunked compile + merge, with **fixed-size chunks, not sections**:

1. Split the body at entry boundaries into chunks of ~500–1,000 pages
   (~2.5–5 MB of markup each; page count per MB is stable at ~43/MB).
2. Compile each chunk as a subprocess (fresh process, ~1–2 GB peak,
   2–8 s each); serial total ≈ the current ~90 s compile.
3. Merge with pypdf (already used in the prototype).
4. Page numbering across chunks: pass the running start page via
   `typst compile --input start=N` and `#counter(page).update()` in
   the layout preamble; chunks must then be compiled serially in order
   (page count of chunk k feeds chunk k+1). Use plain `"1"` numbering
   instead of `"1 / 1"` (chunk-local totals make "/ total" wrong).
5. The front-matter `#outline()` only sees its own chunk — either drop
   the TOC, or generate it in a second pass once chunk page ranges are
   known.

Python side needs no work for CI (2.9 GB is fine), though the ORM load
could be trimmed with column-limited queries if ever desired.

Not worth pursuing: shrinking the markup (per-entry feedback URLs are
~18 MB of input but memory is page-bound, not input-bound);
`typst --pages` (still lays out the whole document); more RAM via
larger runners (paid).
