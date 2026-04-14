---
thread: 20260414_sn_peyyala_collapsed_vaggas
type: fix
---

## Overview
Fix incorrect Saṃyutta Nikāya peyyāla source numbering in the CST sutta example pipeline by handling collapsed `vitthāretabbo` vaggas that should advance the running sutta counter.

## Context
- The visible symptom was in `gui2/pass2_pre_view.py` while reviewing examples for the headword `oghādisuttadasaka 3`.
- The database entry `meaning_2` correctly says `Saṃyutta Nikāya 49.45-54 (SN49.45-54) []`.
- The CST example source currently shows `SN49.1-12`, which is wrong for the `oghādisuttadasakaṃ` peyyāla.
- The root cause identified in the previous analysis is in `tools/cst_source_sutta_example.py`, not in the GUI preview itself.
- In SN49, a collapsed `appamādavaggo` is represented as a `rend="centre"` element with `vitthāretabbo` text, so the current counter logic never advances through those omitted suttas.
- Because the counter does not advance, later peyyāla entries never match correctly. One SN49 peyyāla row also has an obvious typo where `end < start`.
- The same structural pattern was identified in SN50 and SN53, so the fix should cover those explicitly at the same time.

## What it should do
1. Keep the existing targeted, data-driven style used in this file for special cases rather than introducing a broad parser rewrite.
2. Add a small explicit mapping for collapsed SN vaggas whose `vitthāretabbo` sections must advance the sutta counter.
3. Update the SN handler so relevant `rend="centre"` elements increment the counter when they match those known collapsed vaggas.
4. Correct the affected `sn_peyyalas` ranges so the displayed source ranges match the real SC numbering for the affected peyyālas.
5. Ensure the example source for SN49 `oghādisuttadasakaṃ` resolves to `SN49.45-54`.

## Agreed implementation direction
- Use a very specific conditional path for the known badly formatted sections.
- Do not spend time on broader refactoring or speculative cleanup.
- Treat SN49 as the discovered bug and include the already-identified analogous fixes for SN50 and SN53 in the same change.

## Expected corrected numbering
- SN49
  - `Pācīnādisuttadvādasakaṃ` → `SN49.1-12`
  - collapsed `appamādavaggo` advances the counter by 10
  - `Balakaraṇīyādisuttadvādasakaṃ` → `SN49.23-34`
  - `Esanādisuttadasakaṃ` → `SN49.35-44`
  - `Oghādisuttadasakaṃ` → `SN49.45-54`
- SN50
  - `Balādisuttadvādasakaṃ` → `SN50.1-12`
  - collapsed `appamādavaggo`, `balakaraṇīyavaggo`, `esanāvaggo` advance the counter before the first `Oghādisuttadasakaṃ`
  - later collapsed `appamāda-balakaraṇīyavaggā` advances the counter before the second half
  - corrected displayed ranges should be `SN50.45-54`, `SN50.55-66`, `SN50.89-98`, `SN50.99-108`
- SN53
  - `Jhānādisuttadvādasakaṃ` → `SN53.1-12`
  - collapsed `appamādavaggo`, `balakaraṇīyavaggo`, `esanāvaggo` advance the counter
  - `Oghādisuttaṃ` → `SN53.45-54`

## Constraints
- Limit changes to the CST sutta example pipeline and the Kamma thread files.
- Do not modify GUI preview logic unless verification proves it is also required.
- Preserve existing project conventions: Python 3.13, modern type hints, `Path` for file paths when relevant.
- Keep the solution explicit and easy to audit.

## How we'll know it's done
- The SN handler advances counters through the known collapsed `vitthāretabbo` vaggas for SN49, SN50, and SN53.
- The affected peyyāla ranges in `sn_peyyalas` are corrected.
- Re-checking the known failing case yields `SN49.45-54` for `oghādisuttadasakaṃ`.

## What's not included
- A generalized parser for all possible CST structural irregularities.
- Broader cleanup of unrelated saṃyutta numbering logic.
- GUI changes unrelated to displaying the corrected source text.
