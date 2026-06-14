# Review: Fix remove_brackets spacing

## Outcome: PASS

## Findings
- Root cause correctly identified: `remove_brackets()` runs *after*
  `clean_example()` in both call sites, so the single-space substitution it
  inserts next to punctuation / boundaries is never re-cleaned. Verified against
  real CST example data pulled from the live `dpd.db`.
- Fix is minimal and at the source: add a `\s+([,.;:!?])` collapse plus a
  `strip()`. The `'`/`-` speech-mark additions were ruled out as a cause (they
  are word-internal).
- Ellipsis `…` deliberately excluded from the punctuation set, so `… pe …`
  spacing is preserved — confirmed by test.
- The second sub removes whitespace before sentence punctuation generally, not
  only bracket-induced whitespace. For example text this is always a correct
  normalisation; abbreviation lists like `sī. syā. pī.` are unaffected
  (whitespace follows the dot, not precedes it).
- Both callers (GUI `[]` button, `scripts/fix/example_1_2_cleaner.py`) want
  cleaned output; no behavioural regression.

## Update — space-after rule
Per the convention "no space before, exactly one space after", a third sub was
added: `r"([,.;:!?])\s*(?=[^\s\d])" -> r"\1 "`. The `[^\s\d]` lookahead is the
key safeguard — it skips a following digit, so real-data decimals/references
(`1.55`, `ma. ni. 3.364`, including those inside round brackets that
`remove_brackets` leaves intact) are not split, and skips end-of-string so no
trailing space is introduced. Real CST commas/semicolons already carry a
space after, so this rule is belt-and-braces for them.

## Verification
- 9 regression tests in `tests/gui2/test_dpd_fields_functions.py` pass
  (incl. space-after, decimal-not-split, messy-spacing).
- Full `tests/gui2/` suite: passed.
- ruff check + format + pyright clean on both touched files.
