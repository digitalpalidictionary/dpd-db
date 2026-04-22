## Overview
Add "saṃyuttas of the Saṃyutta Nikāya" as a natsort-by-meaning_1 sort strategy
in `db/families/family_set.py`. Side-effect of GitHub issue #192.

## What it should do
When the FamilySet name is exactly "saṃyuttas of the Saṃyutta Nikāya", its
headwords should be sorted by meaning_1 using natural sort (natsorted), consistent
with the existing strategy for "vaggas of …" and "parts of …" sets.

## Assumptions & uncertainties
- "vaggas of" and "parts of" prefix matching already works correctly — no change needed.
- The exact set name is "saṃyuttas of the Saṃyutta Nikāya" (singular target confirmed by user).
- No other "saṃyuttas of …" set names currently exist that need this treatment.

## Constraints
- Touch only `db/families/family_set.py`.
- No new strategies or abstractions — just add to existing `natsort_exact` list.

## How we'll know it's done
- `SORT_STRATEGIES["natsort_exact"]` contains "saṃyuttas of the Saṃyutta Nikāya".
- `_get_sort_strategy("saṃyuttas of the Saṃyutta Nikāya")` returns "natsort".

## What's not included
- No changes to "vaggas of", "parts of", or any other existing sort strategies.
