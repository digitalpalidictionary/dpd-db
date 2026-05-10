# Spec: Wire up four-nikāya ṭīkās (dnt, mnt, snt, ant) into cst_source_sutta_example.py

## Overview
The codes `dnt`, `mnt`, `snt`, `ant` already exist in `tools/pali_text_files.py::cst_texts` and point to valid CST ṭīkā XML files, but `tools/cst_source_sutta_example.py` has no parser cases for them. As a result, calling `find_cst_source_sutta_example("dnt", ...)` (etc.) iterates the soups but never sets `g.source` / `g.sutta`, so no examples are returned. This thread adds four parser functions and four dispatcher cases so source/sutta/example extraction works for the ṭīkā corpora.

## What it should do
- `find_cst_source_sutta_example("dnt", text)` returns CstSourceSuttaExample tuples with sources prefixed `DNt…` for the regular three-volume ṭīkā (`s0101t/s0102t/s0103t`), and a distinct prefix `DNnt…` for the abhinavaṭīkā volumes (`s0104t/s0105t`) so the two ṭīkās don't collide in numbering.
- `find_cst_source_sutta_example("mnt", text)` returns sources prefixed `MNt…`.
- `find_cst_source_sutta_example("snt", text)` returns sources prefixed `SNt…`.
- `find_cst_source_sutta_example("ant", text)` returns sources prefixed `ANt…`.
- `g.sutta` carries the human-readable vagga/sutta-vaṇṇanā label, lower-cased, in the same comma-separated style as the existing `dna/mna/sna/ana` commentary parsers.
- Existing behaviour for every other book code is unchanged.

## Repo context discovered
- Book codes live in `tools/pali_text_files.py::cst_texts` (lines 136–160 contain `dnt/mnt/snt/ant`).
- Dispatcher: `find_cst_source_sutta_example()` in `tools/cst_source_sutta_example.py` (lines 2772–2929) — match/case on `book`. Add four new cases here.
- Templates to mirror: `dna_digha_nikaya_commentary` (1701), `mna_majjhima_nikaya_commentary` (1745), `sna_samyutta_nikaya_commentary` (1781), `ana_anguttara_nikaya_commentary` (1824). The ṭīkā XMLs reuse the same `rend="chapter|title|subhead|subsubhead|book"` scheme the aṭṭhakathā parsers already handle.
- DN ṭīkā actually contains **two** ṭīkās in one code:
  - regular Līnatthappakāsinī: `s0101t`–`s0103t`, `<head rend="book">` = `Sīlakkhandhavaggaṭīkā / Mahāvaggaṭīkā / Pāthikavaggaṭīkā`.
  - abhinavaṭīkā (Sādhuvilāsinī): `s0104t.nrf`, `s0105t.nrf`, `<p rend="book">` = `Sīlakkhandhavaggaabhinavaṭīkā` and chapter restarts at `1. Brahmajālasuttaṃ`. Detect this by matching `abhinava` in the book heading and switch source prefix to `DNnt.…` so numbering doesn't collide with `DNt.…`.

## Assumptions & uncertainties
- Source-prefix convention: `DNt`, `MNt`, `SNt`, `ANt` — confirmed by user.
- DN abhinavaṭīkā folded into `dnt` with prefix `DNnt.…` — user-confirmed.
- AN ṭīkā assumed to use the same `<div id="anN_M">` peyyala scheme as AN aṭṭhakathā; verify during implementation.
- vism / abh / kn ṭīkā handling is **out of scope**.

## Constraints
- Touch `tools/cst_source_sutta_example.py` and `shared_data/help/abbreviations.tsv` only.
- No refactor of existing commentary parsers.
- Type hints on new functions.
- No `print()` debug code committed.

## Abbreviation
- New row in `shared_data/help/abbreviations.tsv`: `DNnt` = "Dīgha Nikāya Nava-ṭīkā, Sādhuvilāsinī" (CPD-style `n` for nava/abhinava). Inserted alphabetically between `DNa` and `DNt`.
- Existing `DNt` row left unchanged (it currently mis-attributes Sādhuvilāsinī to the regular ṭīkā — flagged separately, not fixed in this thread).

## How we'll know it's done
- For each of `dnt`, `mnt`, `snt`, `ant`, `find_cst_source_sutta_example(book, "<common-pali-word>")` returns ≥1 `CstSourceSuttaExample` tuple with sensible `source` / `sutta`.
- For `dnt`, output contains both `DNt…` and `DNnt…` sources.
- `uv run ruff check tools/cst_source_sutta_example.py` passes.

## What's not included
- No automated tests added (file currently has none).
- No downstream consumer changes.
- No vism/abh/kn ṭīkā handling.
- No DB/schema changes.
