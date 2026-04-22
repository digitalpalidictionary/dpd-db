# Goldendict #192 Sutta Info Parity

GitHub issue reference: `#192`

## Overview
This thread adds Goldendict exporter support for the same `#192` sutta-info behavior already implemented in the webapp, limited to the new aggregate entry types introduced for Dīgha Nikāya vaggas, Majjhima Nikāya paṇṇāsakas, Saṃyutta Nikāya saṃyuttas, and related subdivision rows.

The goal is parity of rendered behavior between the webapp and Goldendict for `#192`-related sutta-info presentation, while keeping the implementation simple and localized to the Goldendict rendering path.

## What it should do
- Update Goldendict headword rendering so `#192` aggregate rows no longer behave like plain single-sutta rows when showing sutta-info.
- Use the same current `SuttaInfo` model behavior already used by the webapp:
  - `is_vagga`
  - `is_samyutta`
  - `sc_vagga_link`
  - the current `dv_exists` / `dv_parallels_exists` gating
- In the Goldendict headword template, mirror the current webapp behavior for `#192` entries:
  - change the sutta-info button label from `sutta` to `vagga` or `saṃyutta` where applicable
  - hide sutta-specific fields for aggregate rows in the same cases the webapp now hides them
  - keep shared metadata visible where the webapp keeps it visible
  - show the correct SC link label branch for aggregate rows:
    - `SC Vagga Card`
    - `SC Saṃyutta Card`
    - existing normal `SC Card` behavior for non-aggregate rows
  - suppress DV catalogue/parallels sections for aggregate rows in the same cases as the webapp
- Preserve current Goldendict exporter wiring and data flow, which already pass `SuttaInfo` through `HeadwordData`.
- Add Goldendict tests that lock in the `#192` rendering behavior, using the existing Goldendict test style and folder structure.

## Assumptions & uncertainties
- Assumption: “all related to #192” means parity only for the aggregate-row sutta-info behavior added in the `#192` webapp changes, not unrelated recent webapp UI changes.
- Assumption: the main implementation surface is `exporter/goldendict/templates/dpd_headword.jinja`, with little or no Python exporter logic change required.
- Assumption: current `db.models.SuttaInfo` behavior is the source of truth, even where its current heuristics are slightly imperfect.
- Assumption: parity means matching current webapp output behavior, not first correcting any underlying `#192` behavior quirks.
- Uncertainty: Goldendict may have minor markup differences from the webapp template that should remain if they are exporter-specific and not behaviorally significant.
- Uncertainty: there may be small wording differences in link text already present in Goldendict that should be normalized only where needed for `#192` parity.

## Constraints
- Keep scope limited to `#192` behavior only.
- Do not introduce a shared webapp/Goldendict template abstraction unless clearly necessary.
- Preserve existing Goldendict export flow in `exporter/goldendict/export_dpd.py` and `exporter/goldendict/data_classes.py` unless a small targeted change is required.
- Follow existing project conventions for tests and minimal targeted changes.
- Do not change the `SuttaInfo` model behavior as part of this thread unless an implementation blocker makes it unavoidable.

## How we'll know it's done
- Goldendict renders `#192` aggregate rows with the same effective sutta-info behavior as the webapp for:
  - button label
  - shown/hidden sutta-info fields
  - SC link branch selection and labeling
  - DV section suppression for aggregate rows
- Normal non-aggregate Goldendict sutta-info rendering remains unchanged.
- New focused tests cover the Goldendict `#192` cases and pass.
- Relevant lint/test checks for the changed Goldendict files pass.

## What's not included
- Refactoring webapp and Goldendict to share a common template or rendering abstraction.
- Fixing or redesigning current `SuttaInfo` heuristics beyond what is needed for parity.
- Non-`#192` recent webapp changes.
- Broad Goldendict visual or structural cleanup unrelated to `#192`.
- Changes to database generation or `sutta_info.tsv` content.
