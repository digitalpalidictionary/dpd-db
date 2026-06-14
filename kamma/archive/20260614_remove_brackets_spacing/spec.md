# Spec: Fix stray spaces before punctuation when removing square brackets

## Context
In gui2 pass2add, the example field tools let an editor remove square-bracket
variant annotations with the `[]` button. The square brackets in CST examples
hold variant-reading notes, e.g.:

```
atthi c'ev'ettha uttarikaraṇīyan'ti [imassa anantaraṃ pāṭho dissati].
[ārādhanaṃ] pubbakaraṇa samāpetvā.
```

## Problem
`remove_brackets()` in `gui2/dpd_fields_functions.py` does:

```python
re.sub(r"\s*\[[^]]*\]\s*", " ", text)
```

It always substitutes a single space for the bracket plus its surrounding
whitespace. When the bracket sits next to punctuation or at a string boundary,
the inserted space is wrong:

- `...karaṇīyan'ti [imassa ... dissati].` → `...karaṇīyan'ti .` (space before `.`)
- `foo [note] , bar` → `foo , bar` (space before `,`)
- `[ārādhanaṃ] pubbakaraṇa` → ` pubbakaraṇa` (leading space)
- `[whole thing]` → ` ` (stray space instead of empty)

`clean_example()` already strips ` ,` / ` .`, but `remove_brackets()` runs
*after* `clean_example()` in both call sites (the GUI `[]` button and
`scripts/fix/example_1_2_cleaner.py`), so its artifacts are never re-cleaned.
That is the actual source of the reported " ," and " ." problem.

The `'`/`-` additions (speech marks) are interior to words and do not cause
the spacing; the bracket removal is the sole cause.

## Goal
Make `remove_brackets()` leave well-formed text. Punctuation rule:
**always no space before, exactly one space after.** Also no stray
leading/trailing space, a single space where a bracket genuinely separated two
words, and ellipsis (`…`) spacing untouched.

## Acceptance
- Bracket before `.`/`,`/`;`/`:`/`!`/`?` leaves no space before it.
- Each of those marks gets exactly one space after it.
- Decimals/references (`1.55`, `ma. ni. 3.364`) are NOT split — a `.`
  immediately before a digit keeps no inserted space.
- Leading/trailing brackets leave no surrounding whitespace.
- An interior bracket between two words still leaves one separating space.
- Ellipsis spacing (`… pe …`) is unchanged.
- Existing callers keep working unchanged.

## Note
In real CST data commas/semicolons already always have a space after them; the
only observed defect was the space *before*. The space-after rule is enforced
anyway per the stated convention, guarded so decimals survive.

## Non-goals
- No change to where/how brackets enter the data.
- No change to `clean_example`/`clean_text` behaviour.
