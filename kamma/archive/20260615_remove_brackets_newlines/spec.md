# Spec: remove_brackets() deletes newlines (regression)

## Context
Commit `ebdaf1f6` (#162 "gui2: fix bracket removal leaving spaces around punctuation")
rewrote `remove_brackets()` in `gui2/dpd_fields_functions.py` from a single substitution
into three `re.sub` passes. All three use `\s`, which matches newlines, so clicking the
**[]** button on a multi-line example/commentary collapsed every line break into a space.

Demonstrated regression:
```
INPUT : 'first line.\nsecond line [note] here.\nthird line'
OUTPUT: 'first line. second line here. third line'   # newlines gone
```

The worst offender is the third pass `([,.;:!?])\s*(?=[^\s\d])` — a sentence-ending `.`
followed by a newline had the newline swallowed and replaced with a space.

## Requirement
1. `remove_brackets()` must preserve newlines while still normalising horizontal spacing
   around brackets and punctuation (keep all #162 behaviour).
2. Clean stray horizontal whitespace at the end of a line and at the beginning of a line.

## Decision
- Replace every *consuming* `\s` with the horizontal-whitespace class `[^\S\n]`. The
  non-consuming lookahead stays `\s` (it conveniently stops a space being inserted when
  punctuation sits directly before a newline).
- Add two trailing passes to trim horizontal whitespace before/after newlines.

## Out of scope
- Any other field/formatting behaviour.
