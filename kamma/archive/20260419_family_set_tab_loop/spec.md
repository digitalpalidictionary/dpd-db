# Spec: family_set tab-away loop

## Overview
In gui2, the `family_set` field traps keyboard focus when the entered value is not in the known-sets list. The user cannot tab away.

## What it should do
- When blur fires on `family_set` and one or more entries are unknown, show the validation error (suggestions or "Unknown set(s)") in red under the field.
- Focus must leave the field normally on Tab — no re-focus.

## Assumptions & uncertainties
- Root cause located at `gui2/dpd_fields_family_set.py:110`: `_handle_blur` calls `textfield_control.focus()` inside the unknown-entry branch, which re-triggers blur → focus in a loop.
- Other fields in `gui2/dpd_fields.py` (e.g. `pos_blur`, `family_word_change`) use the same `focus()` on error pattern. User only reported `family_set`, so scope stays there.

## Constraints
- Don't touch validation logic or error messaging.
- Don't refactor the sibling fields.

## How we'll know it's done
- Enter `xxxx` into family_set, press Tab → focus leaves; red error remains.

## What's not included
- Similar focus-trap patterns in other fields.
