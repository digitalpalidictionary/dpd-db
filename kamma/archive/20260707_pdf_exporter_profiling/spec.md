# Spec: Profile the PDF exporter (time, memory, CI feasibility)

Part of the #157 refactoring thread.

## Problem

`exporter/pdf/pdf_exporter.py` renders the whole dictionary into one
~106 MB Typst file and compiles it in-process with the `typst` Python
binding. The step cannot run in the GitHub Actions draft-release
workflow — it always exceeds the runner's memory. It is unclear where
the time and memory actually go (Python/ORM render side vs the Typst
compiler), and whether the memory blow-up is fixable or inherent to
how Typst compiles very large single documents.

## Goal

An evidence-based answer to:

1. Where does the wall-clock time go? (DB load + Jinja render + cleanup
   vs `typst.compile`)
2. Where does the peak memory go? (Python ORM objects + `typst_data`
   strings vs the Typst compiler process)
3. Why does it OOM on the 16 GB `ubuntu-latest` runner?
4. Is the memory cost linear in document size (measure Typst peak RSS
   on 1/2/5/10/20 % slices of the real `typst_data_lite.typ` and
   extrapolate), or super-linear?
5. Is this just how Typst works on huge single documents, and if so,
   does the existing sectioned approach (`pdf_exporter_test.py`:
   per-section compile + pypdf merge) bound the peak?

## Method

- Slice the freshly generated `exporter/pdf/typst_data_lite.typ`
  (preamble + first N% of `#par[` entries) into throwaway files in the
  scratchpad.
- Measure each compile with `/usr/bin/time -v` in a fresh process
  (peak RSS + wall time), never sequentially in one process.
- Measure the Python render phase separately (stage timings already
  printed by `printer`; peak RSS via `/usr/bin/time -v` with the
  compile step skipped).
- No changes to production code in this thread — deliverable is a
  findings report with a recommended optimization path.

## Out of scope

- Implementing the fix (follow-up thread once the numbers pick the
  approach).
- The heavy/full PDF templates (`heavy_*.typ`) — only the lite export
  is in the release pipeline discussion.
