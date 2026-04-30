---
thread: 20260430_kva
objective: Add dvemātikāpāḷi + kaṅkhāvitaraṇī-aṭṭhakathā (KVA) as a selectable book in cst_source_sutta_example.py and gui2
---

## Overview
Add `vin04t.nrf.xml` (dvemātikāpāḷi / kaṅkhāvitaraṇī-aṭṭhakathā) as a first-class book (`kva`) to the CST source/sutta/example lookup system and expose it as a selectable book in gui2.

## What it should do
- `find_cst_source_sutta_example("kva", text)` returns correct `(source, sutta, example)` tuples for any text in the file.
- The source/sutta scheme:
  - **Pātimokkha (mātikā):** `KVA1.1.<uddesa#>` (bhikkhu) / `KVA1.2.<uddesa#>` (bhikkhunī); sutta = `<section>, <uddesa>[, <rule-name>]`
  - **Commentary:** `KVA2.1.<kaṇḍa#>[.<vagga#>]` (bhikkhu) / `KVA2.2.<kaṇḍa#>[.<vagga#>]` (bhikkhunī); sutta = `<section>, <kaṇḍo>[, <vaggo>][, <sikkhāpadavaṇṇanā>]`
- "KVA dvemātikāpāḷi + kaṅkhāvitaraṇī" appears in the gui2 book dropdown.

## XML structure (vin04t.nrf.xml)
Two logical sections, each with bhikkhu/bhikkhunī halves:

**Pātimokkha:** `book` → `chapter` (Bhikkhupātimokkha/Bhikkhunīpātimokkha) → `subhead` (uddesa) → `centre`/`bodytext` ending `sikkhāpadaṃ` (rule name) → `bodytext n="N"` (rule text)

**Commentary:** `chapter "Kaṅkhāvitaraṇī-aṭṭhakathā"` (transition) → `subsubhead "Ganthārambhakathā"` → `chapter` (kaṇḍas) → optional `title` (vaggas) → `subhead` (individual entries); then `chapter "Bhikkhunīpātimokkhavaṇṇanā"` flips to bhikkhunī.

## Assumptions & uncertainties
- No SC bilara data exists for this text; `SuttaCentralSource` entries use `None` paths.
- Rule names in sekhiyā section appear in both `centre` and `bodytext` rend — handled by checking text ending.

## Constraints
- Do not modify existing handlers.
- `vin04t.nrf.txt` remains in `vint` (tika collection) — `kva` is an independent entry.

## How we'll know it's done
- 8 test cases all PASS (bhikkhu pārājika/nissaggiya/sekhiyā, bhikkhunī pārājika, bhikkhu commentary pārājika/nissaggiya-vagga, bhikkhunī commentary pācittiya-vagga, ganthārambhakathā).
- KVA selectable in gui2 and returns correct source/sutta/example.

## What's not included
- No SC bilara integration (no data exists).
- No handling of `vint` tika files.
