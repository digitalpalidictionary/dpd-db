# Spec — Simplify deconstructor config flags

## Problem

The deconstructor pipeline is governed by **three** config settings that overlap confusingly:

1. `[deconstructor] use_premade` — premade-tarball vs. Go-regenerate source switch
2. `[generate] deconstructor` — whether to load premade data into the lookup table (read in one place only)
3. `[exporter] make_deconstructor` — build GoldenDict/MDict

`use_premade` and `generate.deconstructor` are not orthogonal in practice: in both the local full build (`uposatha`) and CI (`github_release`) the data is wanted (`generate=yes`); only the *source* differs (local regenerates with Go, CI loads the committed premade tarball — it cannot run Go). The source is an **environment fact** (which pipeline runs), not a free choice, so it does not need its own flag.

## Decision

Collapse to **two** flags by deleting `[deconstructor] use_premade` and redefining `[generate] deconstructor` as: *"deconstructor data should be present in the db this build."* The source is decided by which pipeline runs:

- **Local** (`generate_components.py`): `generate=yes` → run Go → `SaveToDb` → re-tarball (refreshing the committed premade for the next CI run). `generate=no` → do nothing (rely on existing db).
- **CI** (workflow steps): always loads the committed premade via its own `tar -xzvf` + `deconstructor_output_add_to_db.py` steps, gated only by `generate != no`.

`[exporter] make_deconstructor` is unchanged (export only).

## Component gates: before → after

| Component | Before | After |
|---|---|---|
| `deconstructor_extract_archive.py` | run iff `use_premade==yes` | **deleted** (dead: only the local pipeline used it; CI uses inline `tar`) |
| `deconstructor_output_add_to_db.py` | run iff `generate!=no AND use_premade==yes` | **removed from local pipeline**; stays a CI step, gated `generate!=no` |
| go `main.go` | run iff `(make_deconstructor‖make_tpr‖make_ebook‖db_rebuild) AND use_premade==no` | run iff `generate==yes` |
| `tarball_deconstructor_output.py` | run iff `use_premade==no` (skip when premade) | run iff `generate==yes` (mind polarity) |
| `deconstructor_exporter.py` | run iff `make_deconstructor==yes` | unchanged |

## Behavior changes (signed off)

- Local builds always regenerate when `generate=yes`; there is no local premade-load path (user confirmed: no local case where the db is empty and regeneration is unwanted).
- Go deconstructor decoupled from `make_tpr` / `make_ebook` / `db_rebuild`: building TPR/ebook no longer auto-forces a regen — it uses existing db data unless `generate=yes`.

## Out of scope / constraints

- `config.ini` is **not** edited (global rule: never modify `.ini`; file is gitignored and CI-regenerated). The now-dead `[deconstructor]` section is harmless and will be removed by the user manually.
- CI safety: `config.ini` is regenerated from `DEFAULT_CONFIG` where `generate.deconstructor` defaults to `yes`; the `github_release` profile does not touch `[generate]`, so CI keeps loading premade.

## Files touched

- `tools/configger.py` — drop `[deconstructor]` from `DEFAULT_CONFIG` and from the `uposatha` / `github_release` / `quick` profiles
- `tests/tools/test_configger_fixtures.json` — drop the three `use_premade` entries
- `go_modules/deconstructor/main.go` — gate
- `scripts/build/deconstructor_output_add_to_db.py` — gate
- `scripts/build/tarball_deconstructor_output.py` — gate
- `scripts/build/deconstructor_extract_archive.py` — delete
- `scripts/bash/generate_components.py` — drop extract + add_to_db steps
- `justfile` — repurpose `decon-on` / `decon-off` to toggle `generate.deconstructor`
