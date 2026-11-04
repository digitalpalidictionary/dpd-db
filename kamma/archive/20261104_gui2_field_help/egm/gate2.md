# Gate 2 — spec review

Backend: native subagents (Plan type, read-only). Two Goldfish, each given only the spec path, the repo and the brief. Neither read `egm/`.
- Comprehension reviewer (C1-C10)
- Design critic (D1-D10)

## Raw findings (condensed)

Design critic
- D1 Major: item 5 / assumption D do not say how the test gets the 50 names. `field_configs` is built inside `__init__` and the constructor needs db, toolkit, spell checker. `ast` route unspecified; count not asserted.
- D2 Major: done criteria partly untestable: mutation checks need a function that takes data; criterion 3 is manual; criterion 5 scope of `just typecheck`; criterion 6 has no evidence; key order stated but not tested.
- D3 Major: no mechanism for how text reaches the label: tooltip as string or `ft.Tooltip`, wrap width, raw versus wrapped text, long words.
- D4 Major: `clear_all_fields` rebuilds the whole `DpdFields`, so the cache must be module level. A warning per key per rebuild gives up to 50 log lines per clear.
- D5 Major: load failure rules incomplete (malformed JSON, wrong top-level type, non-string value, encoding, path).
- D6 Major: 10 fields have no style-guide source; the agent would invent meaning.
- D7 Major: spike has no decision rule. Container fallback changes layout and may eat selection.
- D8 Nit: where to hover on tall rows; no criterion for rows Pass 1 hides.
- D9 Nit: selectable text shows a text cursor, not a help cue.
- D10 Nit: README line contradicts "not included".

Comprehension reviewer
- C1 Major: verified fact wrong. `ft.Tooltip` has `size_constraints` (`tooltip.py:199`).
- C2 Major: `wait_duration` is `DurationValue`, not int; assumption C answerable from source.
- C3 Major: 300-character test and wrapping at load time disagree; newline in JSON allowed or not.
- C4 Major: 10 fields without doc source; "reviews it" is not a gate.
- C5 Major: requirement 4 clause "rows Pass 1 hides when they gain a value" is undefined.
- C6 Major: assumption-A fallback conflicts with fixed layout; check consumers of the label control.
- C7 Major: criterion 3 has no launch steps or pass test.
- C8 Nit: Alt+? key not verified.
- C9 Nit: README contradiction; spec refers to `egm/` files a fresh reader may not read.
- C10 Nit: loader module name, signature, cache, log level unspecified.

## Dispositions

| # | Finding | Severity | Decision | How checked | Where fixed |
|---|---|---|---|---|---|
| 1 | Names for the test (D1) | Major | Accept | `dpd_fields.py:94` assigned in `__init__`; no test builds `DpdFields` | spec item 5 (ast, count 50) |
| 2 | Testability of done criteria (D2, C7) | Major | Accept | read spec criteria | spec item 2 (`validate_field_help`), done 1-6, run via playwright-cli |
| 3 | Text path, wrap, tooltip type (D3, C1, C3) | Major | Accept | `tooltip.py:199` has `size_constraints` (my fact was wrong) | spec item 1, 3, verified facts |
| 4 | `wait_duration` type (C2) | Major | Accept | `tooltip.py:157` and `duration.py:236`: `Duration \| int` | spec item 3 |
| 5 | Rebuild, cache, log volume (D4) | Major | Accept | `clear_all_fields` calls `_build_middle_section` in both views | spec item 2 |
| 6 | Load failure rules (D5) | Major | Accept | no rule existed | spec item 2 |
| 7 | 10 fields without source (D6, C4) | Major | Accept in part | `dpd_headwords_table.md` has 7 of the 10; `translation_1`, `translation_2`, `comment` have none | spec item 1, done 6 |
| 8 | Spike decision rule, fallback layout (D7, C6) | Major | Accept | grep: no code indexes these rows' `controls[0]` | spec assumption A |
| 9 | Hover target, hidden rows (D8, C5) | Nit/Major | Accept | tooltip attached at construction; visibility irrelevant | spec item 4, done 3 |
| 10 | Selectable cursor (D9) | Nit | Reject | already covered by accepted risk E | none |
| 11 | README contradiction (D10, C9) | Nit | Accept | wording | spec "not included" |
| 12 | Loader API (C10) | Nit | Accept | none specified | spec item 2 |
| 13 | Alt+? key unverified (C8) | Nit | Reject | `main.py:297` `_SHORTCUTS_KEYS = ("?", "/")`; spec wording now names the constant | spec header |
| 14 | `egm/` refs unreadable (C9) | Nit | Reject | the executor works in the thread folder and can read it | none |

Counts: 20 raw findings (design critic 10, comprehension 10) merged into 14 rows. 11 accepted (one in part), 3 rejected, 0 escalated.
