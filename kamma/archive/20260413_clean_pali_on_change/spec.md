# Spec: Clean Pāḷi fields on change

## Overview
Strip non-Pāḷi characters immediately on typing (on_change) for variant, var_phonetic, and var_text fields in gui2, not just on blur.

## What it should do
When a user types or pastes into antonym, synonym, variant, var_phonetic, or var_text, non-Pāḷi characters are removed. on_change catches typing; on_blur catches paste.

## Constraints
- Only allowed characters: Pāḷi alphabet + comma + space
- Existing `clean_pali_field` method handles the cleaning logic

## How we'll know it's done
Typing non-Pāḷi chars into any of the 5 fields strips them on change. Pasting strips on blur.

## What's not included
- antonym and synonym already had on_change cleaning wired — no changes needed.
