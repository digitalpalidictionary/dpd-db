# Spec: Wire up Abhidhamma commentaries (`abha`) into cst_source_sutta_example.py

## GitHub issue
#150 — "GUI2: Add more books to source sutta example" (open). Closes one checkbox: "Abhidhamma commentaries". Issue stays open afterwards.

## Overview
The code `abha` exists in `tools/pali_text_files.py::cst_texts` pointing to three CST Abhidhamma aṭṭhakathā files (`abh01a.att.txt` = Atthasālinī, `abh02a.att.txt` = Sammohavinodanī, `abh03a.att.txt` = Pañcappakaraṇaṭṭhakathā). No parser case exists in `tools/cst_source_sutta_example.py` and there is no gui2 dropdown entry. This thread adds both.

## What it should do
- `find_cst_source_sutta_example("abha", text)` returns CstSourceSuttaExample tuples with sources prefixed `ADha…`.
- Single source prefix `ADha` covers all three files — no internal split for the 5 sub-aṭṭhakathās bundled inside `abh03a`. User-confirmed.
- `g.sutta` is human-readable, comma-joined, lower-cased — same style as existing commentary parsers.
- The book code `abha` becomes selectable in the gui2 dropdown.
- Existing behaviour for every other book code is unchanged.

## Repo context
- `cst_texts["abha"] = ["abh01a.att.txt", "abh02a.att.txt", "abh03a.att.txt"]` — already defined in `tools/pali_text_files.py`.
- Dispatcher in `find_cst_source_sutta_example()` in `tools/cst_source_sutta_example.py` — add `case "abha":` after `case "ana":`.
- Structural template: `mna_majjhima_nikaya_commentary` — flat chapter/subsubhead/subhead handling, comma-joined sutta string.
- Heading shapes in the XML:
  - `rend="book"` — volume marker (`Dhammasaṅgaṇī-aṭṭhakathā` etc.); no source/sutta change.
  - `rend="subsubhead"` — opening prose (`Ganthārambhakathā` etc.); source `ADha0`.
  - `rend="chapter"` — major sections, sometimes numbered (`1. Cittuppādakaṇḍo`), sometimes not (`Tikamātikāpadavaṇṇanā`, `Dhātukathā-aṭṭhakathā`).
  - `rend="title"` — sub-section label; update `g.vagga` context only.
  - `rend="subhead"` — leaf sutta-vaṇṇanā; increment sutta_counter, set source and sutta.
- `ADha` abbreviation row already exists in `shared_data/help/abbreviations.tsv` (line 24). No new row needed.

## Assumptions
- Single `ADha` prefix. User-confirmed.
- `mna` parser shape is the right template.
- Unnumbered chapter headings fall back to a running counter.
- `book` and `title` rends don't drive source numbering.

## Constraints
- Touch `tools/cst_source_sutta_example.py` and `gui2/dpd_fields_examples.py` only.
- No refactor of existing parsers.
- Type hints on new function.
- No `print()` / debug code committed.

## How we'll know it's done
- Smoke tests with *cittuppād*, *khandh*, *dhātukath* each return ≥1 ADha… tuple with sensible sutta strings, no exceptions.
- Manual test in gui2 produces results.

## What's not included
- No internal split of abh03a's bundled aṭṭhakathās.
- No `abht`, `vint`, `knt`, grammar books (separate issue #150 items).
- No change to the `ADha` abbreviation row.
- No automated tests.
