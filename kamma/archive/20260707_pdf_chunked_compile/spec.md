# Spec: Chunked Typst compile for the PDF exporter

Part of the #157 refactoring thread. Follows the profiling thread
`20260707_pdf_exporter_profiling` (findings.md there is the evidence
base: peak RSS ≈ 2 MB/page, full doc = 14,966 pages ≈ 29 GB, OOM on
the 16 GB CI runner; EPD section alone ≈ 19 GB, so the per-section
prototype `pdf_exporter_test.py` is insufficient).

## Problem

`exporter/pdf/pdf_exporter.py` compiles one 106 MB Typst file
(~15k pages) in a single `typst.compile()` call. Typst holds the whole
laid-out document in memory (~2 MB/page, no streaming, no memory flag,
no fix planned upstream), so the export needs ~29 GB and can never run
in the draft-release workflow. Community consensus for huge documents
is split-into-chunks + merge.

## Goal

Rework the PDF export so peak memory is bounded (~2–3 GB regardless of
dictionary growth) and the export is as fast as we can reasonably make
it, without degrading the visual quality of the printed dictionary.
This code will not be touched again for a long time — prefer the
thorough, well-tested solution over the quick one.

## Approach: prove first, implement second

**Phase 1 — experiments (no production code, scratchpad prototypes
driven by the real `typst_data_lite.typ`).** Every design decision
gets proven or killed by a measurement before implementation starts:

- E1 chunked compile: split at entry boundaries into ~1,000-page
  chunks, compile each in a fresh process, verify peak RSS per chunk
  and total wall time.
- E1b compile mechanism — Python module vs subprocess, decided on
  measured time AND memory: (a) typst CLI subprocess, (b) Python
  binding in a fresh subprocess (CI installs no CLI; the binding
  ships its own compiler), (c) Python binding in-process repeated
  calls — specifically whether memory is retained across compiles
  (comemo cache / allocator) making in-process chunking unsafe.
- E2 continuous page numbering: inject
  `#counter(page).update(int(sys.inputs.at("start-page")))` after the
  preamble; serial chain (chunk k's page count feeds k+1). Decide
  `"1"` vs two-pass `"N / total"` numbering (two-pass doubles compile
  work but enables parallel compiles and a correct grand total).
- E3 merge: pypdf vs qpdf/mutool on ~15k pages / ~440 MB; measure
  memory/time; verify page count, PDF bookmarks survive, external
  links work, file size vs the 442 MB single-compile baseline.
- E4 quality: text-extract boundary pages to verify numbering
  continuity; TOC strategy (`#outline()` sees only its own chunk —
  rebuild front-matter TOC from measured chunk page ranges, or drop);
  user eyeballs the merged PDF against today's `dpd.pdf`.
- E5 json() data-file rendering spike (community lever: data via
  `json()` instead of inline markup cut parse memory ~3× upstream).
  Complication: our fields (`meaning_1_typst` etc.) embed Typst markup
  and would need per-entry `eval(mode: "markup")`. Measure on one
  section slice. Kill criterion: < 20 % memory or time improvement
  over chunked-markup baseline → keep the Jinja pipeline.

**HARD GATE: present Phase 1 evidence; user approves the design
before any production edit.**

**Phase 2 — implementation (new branch).**

- Refactor `pdf_exporter.py` to the proven design: render sections →
  split into chunks → compile each chunk in a fresh subprocess →
  merge → zip. Winning choices from E1–E5 only.
- Delete or fold in the obsolete `pdf_exporter_test.py` prototype.
- pytest coverage in `tests/exporter/pdf/`: chunk splitting preserves
  content exactly and cuts only at entry boundaries; page-offset
  chaining; merge page-count invariant; end-to-end on a small slice
  (marked `slow` if it parses/compiles large inputs).
- Optional (measured, only if trivial): trim the 2.9 GB ORM load with
  column-limited queries — typst dominates, so this is CI headroom,
  not a requirement.

## Constraints

- Visual output quality decisions (numbering format, TOC, chunk
  boundary page breaks) belong to the user — present options with
  evidence, don't decide silently.
- No commits without explicit permission; checkpoints are report-only.
- CI validation is prepared here but only triggered by the user.
  (Implemented by reworking the pre-existing `workflow_dispatch`
  workflow `.github/workflows/pdf_test.yml` — discovered mid-thread;
  it builds the DB from TSV like the release workflow, which replaces
  the originally proposed release-asset download.)

## Out of scope

- The swap-on-runner workaround (superseded: chunking bounds memory
  properly and permanently).
- The heavy/full PDF templates (`heavy_*.typ`).
- Upgrading typst (0.15 changelog shows no layout-memory gains).
