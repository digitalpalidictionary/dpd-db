# Plan: Profile the PDF exporter

## Tasks

- [x] 1. Baseline facts: size/shape of `typst_data_lite.typ`, entry
      counts per section, typst binding version, GH runner specs
      → verified: 106 MB / 3,005,343 lines; EPD section = 70 % of file;
      typst CLI 0.14.0, binding 0.14.9; full PDF = 14,966 pages
- [x] 2. Slice `typst_data_lite.typ` into 1/2/5/10/20 % files in the
      scratchpad (preamble preserved, cut at `#par[`/`#heading3[`
      boundaries) → verified: all slices compile standalone, exit 0
- [x] 3. Compile each slice in a fresh process under `/usr/bin/time -v`
      → verified: monotone series, peak RSS ≈ 2 MB/page, cleanly linear
- [x] 4. Measure Python render phase (compile skipped) under
      `/usr/bin/time -v` → verified: 12 s total, 2.9 GB peak (ORM load)
- [x] 5. Extrapolate to 100 %: ~29 GB peak vs 16 GB runner; EPD-only
      10 % slice compiled to confirm per-section split insufficient
      → verified: findings.md written to thread dir
- [x] 6. Findings + recommended optimization path reported to user
