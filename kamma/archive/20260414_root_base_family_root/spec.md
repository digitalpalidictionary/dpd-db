## Overview
Improve the auto-selection of `root_base` and `family_root` fields in the GUI by filtering based on existing field values, with fallback to current cycling behavior.

## What it should do

### root_base filtering by root_sign
- When pressing Enter on `root_base`, only cycle through bases that contain the current `root_sign`
- For each part of the sign (space-separated, e.g., `*e iya` → `*e` and `iya`), ALL parts must appear in the base as `+ part`
- For starred parts like `*e`, also match without star (`+ e`)
- root_sign must be filled first; if empty, do nothing (don't cycle)

### family_root derivation from construction
- When pressing Enter on `family_root`, if construction is filled, parse it to extract prefixes and auto-select the matching family_root
- Parse: split first line of construction on `+`, find the `√` part, take everything before it, exclude negative parts (containing `>`), join remaining as `prefix1 prefix2 √root`
- If the derived family_root is in the available options, use it directly (no cycling needed)
- If construction is empty or no match found, fallback to current cycling behavior

## Assumptions & uncertainties
- root_sign is always filled before root_base (confirmed by user)
- Construction parsing: negative prefixes always contain `>` (e.g., `na > a`)
- The root marker `√` always appears in construction when present

## Constraints
- Keep it simple — minimal code changes, no complex sandhi logic
- Don't break existing cycling behavior as fallback

## How we'll know it's done
- root_base only shows bases matching current root_sign
- family_root auto-selects from construction when available
- Both fallback gracefully when data is missing

## What's not included
- Lemma-based sandhi matching for family_root (explicitly excluded)
- Validation/error messages for mismatches
