# Spec — TH/THI chapter.verse sutta codes

## Overview
Make `TH1.45` and `THI2.3` resolve to the same headwords as the sequential
`TH45` / `THI10`, mirroring how `SNP45` and `SNP4.7` both resolve.

## What it should do
For every `SuttaInfo` row where `dpd_code` starts `TH`/`THI` and `sc_code`
starts `THAG`/`THIG`, emit a synthetic alias by rewriting the sc_code prefix:
- `THAG1.45` → `TH1.45`
- `THIG2.3` → `THI2.3`

Additive — `THAG`/`THIG` forms keep working. All three forms resolve.

## Constraints
- Single file change: `tools/sutta_codes.py`.
- No DB schema change.
- No template or display changes.

## How we'll know it's done
- `make_list_of_sutta_codes(TH45/THAG1.45)` returns all three forms.
- After lookup rebuild, `TH1.45` and `THI2.3` resolve in the Lookup table.
