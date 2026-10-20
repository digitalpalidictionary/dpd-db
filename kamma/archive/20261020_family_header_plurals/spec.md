# Spec: Singular/plural agreement in family headings

## Overview

Family headings show the wrong grammatical number. Example from GoldenDict:
"16 compound which contains nibbidā" should read "16 compounds which contain nibbidā".
The reverse also happens: "1 compounds which contain X".

Correct forms:
- 1 compound which contains X / N compounds which contain X
- 1 idiomatic expression which contains X / N idiomatic expressions which contain X
- 1 word belongs to the root family X / N words belong to the root family X

## When it broke (git history)

- GoldenDict was correct until 2024-05-10. The old server-side template
  (`dpd_family_compound_old.html`) picked the form from `f.count`.
  Commit `e559b9e9` (2024-05-10) moved family headings into JavaScript.
  Commit `ec423d05` (2024-05-12) wrote `family_compound_template.js` with the
  number-of-families test. That logic has not changed since. The idiom and
  root JS templates come from the same commit.
- The website single-family "compounds which contains" goes back to the
  first FastAPI template, `86ce4b79` (2024-05-01).

## Verified facts (read from code and the live dpd.db, 2026-10-20)

Live data — families with count = 1:

| table | total | count = 1 |
|---|---|---|
| family_compound | 5524 | 1756 |
| family_idiom | 1172 | 656 |
| family_root | 3325 | 626 |
| family_word | 851 | 0 (min count is 2) |
| family_set | 270 | n/a — heading has no count |

`nibbidā` compound family: count 16.

Bugs found:

1. `exporter/goldendict/javascript/family_compound_template.js` — picks
   singular/plural from the NUMBER OF FAMILIES on the headword
   (`familyCompoundList.length`), not from `fc.count`. One family → always
   "compound which contains"; several families → always "compounds which
   contain". The single-family branch also never closes its `<p>`.
2. `exporter/goldendict/javascript/family_idiom_template.js` — same bug,
   same shape.
3. `exporter/goldendict/javascript/family_root_template.js` — always
   "words belong to the root family", even when `fr.count` is 1.
4. `exporter/webapp/templates/dpd_headword.html`, single compound family
   block (`needs_compound_family_button`) — always "compounds which
   contains" (wrong for every count). The several-families block
   (`needs_compound_families_button`) is correct on number, but puts the
   "⤴" back-to-top link only on the plural branch, so a count-1 family in a
   multi list has no jump link.
5. `exporter/pdf/templates/lite_family_root.typ` — always "words belong".
6. `../dpd-flutter-app/lib/widgets/family_section_builders.dart`,
   `buildRootFamilyHeader` — switches word/words but keeps "belong", giving
   "1 word belong to the root family".

Checked and correct (no change):
- Website root family: the heading comes from `family_root.html` built by
  `db/families/family_root.py:make_root_header`, which handles count 1.
- Website idiom block, PDF lite compound / idiom / word templates.
- Root matrix headings ("word is / words are derived from the root") in the
  website and GoldenDict.
- Flutter compound and idiom headings.
- Word family headings: always plural, and no word family has count 1.
- Set headings: no count.
- Anki, mobile exporter: no headings (data only).

Added after review (user, 2026-10-20: "fix all related singular compound
bugs in all versions of the app"):
7. `exporter/goldendict/javascript/family_set_template.js` — single-set
   heading never closes its `<p>` (same fault as compound/idiom).
8. `exporter/pdf/templates/heavy_family_compound.typ` and
   `heavy_family_root.typ` — always plural. No code loads them today (grep of
   `heavy_` outside the templates finds only kamma notes), but they are fixed
   so a future full PDF export is right.

Not touched:
- `exporter/share/dpd/res/*.js` — gitignored build copies of the GoldenDict
  JS; the next export refreshes them.
- `archive/` copies.

## What it should do

- Every compound, idiom and root family heading in GoldenDict (and MDict,
  which uses the same JS), the website, the PDF and the Flutter app picks
  singular or plural from that family's own count.
- In the website multi-family compound list, every family heading gets the
  "⤴" link, whatever its count (matches GoldenDict).
- In GoldenDict, the single-family compound and idiom heading closes its
  `<p>`.

## Assumptions & uncertainties

- The Flutter app fix belongs in this thread (one line, same bug class;
  confirmed by the user). It is a separate repo with its own test run.
- Assumes no other renderer builds these headings. The sweep covered
  `exporter/`, `db/families/`, `gui2/`, `tools/`, `go_modules/` and the
  Flutter `lib/`.
- The GoldenDict JS has no existing tests. The new tests run the real
  template file in node with a stubbed `superScripter` and data object. node
  is installed locally. CI does not run pytest, so CI is not affected.

## Constraints

- Keep the existing wording, only fix number agreement.
- No new helpers. Inline ternaries in JS, `{% if %}` in Jinja, the same
  `n == 1` pattern Flutter already uses.
- Concurrent threads share the tree: edit only the files named here.

## How we'll know it's done

- New tests fail before the fix and pass after, for: GoldenDict compound,
  idiom and root JS; the website compound blocks; the PDF lite root
  template; the Flutter root header.
- Rendering the real `family_compound_json.js` through the fixed template
  gives "16 compounds which contain nibbidā".

## What's not included

- Website multi-family compound block: `{% if loop.index == 0 %}` is never
  true and emits a stray `</p>`. Not a number bug; changing it would drop the
  first family's `id`. Left as is.
- Website word family says "words which belong to the", GoldenDict says
  "words belong to the". Different wording, both correct, left as is.
- The website single-compound block nests the table inside `<p>`. Browsers
  close the `<p>` on their own, so it renders the same. Left as is.
