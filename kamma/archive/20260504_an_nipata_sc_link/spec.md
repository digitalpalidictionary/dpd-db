## Overview
Add `is_nipata` property to `SuttaInfo` and handle Aṅguttara Nikāya nipātas in `sc_vagga_link`, mirroring how `is_samyutta` and `is_vagga` work for SN.

## What it should do
- `is_nipata` returns True for AN1–AN11 nipāta entries (dpd_sutta ending in "nipāta", no dot/hyphen in dpd_code)
- `sc_vagga_link` for AN nipātas returns `https://suttacentral.net/pitaka/sutta/numbered/an/an{N}`
- Templates show "nipāta" button label and "SC Nipāta Card" link for these entries
- Variant names (e.g. `tikanipāta 1`, `catukkaṅguttara`) resolve correctly via existing alias infrastructure

## Constraints
- Field-hide conditionals (`not is_samyutta` etc.) unchanged — AN nipāta rows have those fields empty anyway
- No changes to cache_load.py or alias_map — variant lookup already works

## How we'll know it's done
- AN1–AN11 `is_nipata=True`, correct `sc_vagga_link`
- Variants resolve to canonical SuttaInfo with `is_nipata=True`
- CodeRabbit: zero findings

## What's not included
- Field-hide guards (`not is_nipata`) — not needed, fields are blank
