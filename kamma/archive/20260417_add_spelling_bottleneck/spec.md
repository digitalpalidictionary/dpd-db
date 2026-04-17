## Overview
Fix the slow response when using "Add spelling" in the meaning field's spell checker.

## What it should do
- After adding a word via "Add spelling", the UI should respond near-instantly
- The added word should disappear from the red error text without re-running the full spell check
- Remaining misspelled words should stay displayed as-is

## Root cause
When "Add spelling" submits, `meaning_field.focus()` fires `_handle_on_focus`, which re-runs `_handle_spell_check`. This calls `spell.candidates(word)` for every remaining misspelled word — an expensive edit-distance-2 computation. The candidates were already computed and displayed; re-running is redundant.

## Constraints
- Must not break existing spell check display on focus/blur
- Must keep user dictionary file append behavior
- Must remain thread-safe

## How we'll know it's done
- Adding a word via "Add spelling" responds in under 0.5 seconds
- Remaining misspelled words stay highlighted after adding
- No regressions in meaning_1, meaning_lit, or notes spell checking

## What's not included
- General optimization of `candidates()` for initial spell checks
- Changes to the spell check UI appearance
