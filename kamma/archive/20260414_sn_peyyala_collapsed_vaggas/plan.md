---
thread: 20260414_sn_peyyala_collapsed_vaggas
---

## Phase 1: Encode the known collapsed-vagga cases

- [x] Add a targeted mapping in `tools/cst_source_sutta_example.py` for collapsed SN vaggas that should advance the sutta counter
  → include only the explicitly identified cases:
  `SN49 appamādavaggo = 10`,
  `SN50 appamādavaggo = 10`,
  `SN50 balakaraṇīyavaggo = 12`,
  `SN50 esanāvaggo = 10`,
  `SN50 appamāda-balakaraṇīyavaggā = 22`,
  `SN53 appamādavaggo = 10`,
  `SN53 balakaraṇīyavaggo = 12`,
  `SN53 esanāvaggo = 10`
  → added as `sn_collapsed_vagga_counts`

## Phase 2: Advance the counter for collapsed `vitthāretabbo` vaggas

- [x] Update the SN handling path in `tools/cst_source_sutta_example.py`
  → when a `rend="centre"` element contains `vitthāretabbo` text and matches one of the mapped collapsed vaggas for the current saṃyutta, increment `g.sutta_counter` by the configured amount
  → implemented in `sn_samyutta_nikaya()` as a narrow `rend == "centre"` branch

- [x] Keep this as a narrow special-case branch
  → do not rewrite the general traversal logic or broaden scope beyond the known broken cases

## Phase 3: Correct the peyyāla ranges

- [x] Fix SN49 `sn_peyyalas` entries in `tools/cst_source_sutta_example.py`
  → set ranges to:
  `1-12 Pācīnādisuttadvādasakaṃ`,
  `23-34 Balakaraṇīyādisuttadvādasakaṃ`,
  `35-44 Esanādisuttadasakaṃ`,
  `45-54 Oghādisuttadasakaṃ`

- [x] Fix SN50 `sn_peyyalas` entries in `tools/cst_source_sutta_example.py`
  → set ranges to:
  `1-12 Balādisuttadvādasakaṃ`,
  `45-54 Oghādisuttadasakaṃ`,
  `55-66 Pācīnādisuttadvādasakaṃ`,
  `89-98 Esanādisuttadvādasakaṃ`,
  `99-108 Oghādisuttadasakaṃ`

- [x] Fix SN53 `sn_peyyalas` entries in `tools/cst_source_sutta_example.py`
  → set ranges to:
  `1-12 Jhānādisuttadvādasakaṃ`,
  `45-54 Oghādisuttaṃ`

## Phase 4: Verification

- [x] Re-check the known failing SN49 case
  → confirm `oghādisuttadasakaṃ` now resolves to `SN49.45-54` instead of `SN49.1-12`
  → verified by direct CST traversal: `SN49: 1-10. Oghādisuttadasakaṃ -> SN49.45-54`

- [x] Spot-check the other identified affected saṃyuttas
  → confirm SN50 and SN53 peyyāla sources now align with the expected corrected ranges from the prior analysis
  → verified:
  `SN50.45-54`, `SN50.55-66`, `SN50.89-98`, `SN50.99-108`, `SN53.45-54`

- [x] Run the smallest relevant verification for the affected path
  → use the project’s normal local validation approach without expanding scope into unrelated suites
  → `python -m compileall tools/cst_source_sutta_example.py` succeeded
