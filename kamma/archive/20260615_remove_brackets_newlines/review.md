# Review: remove_brackets() newline regression

## Outcome: PASS

## What was checked
- **Root cause confirmed empirically** before fixing: ran the live function on multiline
  input and reproduced the newline collapse; bisected to commit `ebdaf1f6` (#162).
- **Fix is minimal and targeted:** only the consuming `\s` became `[^\S\n]`; the lookahead
  `(?=[^\s\d])` deliberately kept as `\s` so punctuation immediately before a newline does
  not gain a trailing space.
- **No #162 behaviour lost:** all nine original regression tests still pass (no-space-before
  punctuation, single-space-after, decimal/reference guard, messy-spacing normalisation,
  leading/whole-string bracket handling).
- **New behaviour covered:** three new tests — newlines preserved, trailing space before a
  newline trimmed, leading space after a newline trimmed.
- **Gate:** 12/12 tests pass, `ruff check` + `ruff format` clean. `gui2/` is pyright-excluded.
- **User manual GUI verification:** confirmed working.

## Confidence: 9/10
