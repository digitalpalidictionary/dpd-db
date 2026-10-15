# Spec: suggest longer compound words for constructions

## Overview
Some compound constructions break a word into its smallest parts, even when longer
headwords exist for runs of those parts. Example (live db):

- `cātumāsapaccayapavāraṇā` (id 88674, `fem, comp`): `catu > cātu + māsa + paccaya + pavāraṇā`
- `cātumāsa` (id 26413) and `paccayapavāraṇā` (id 39389) are both comp headwords.
- Better line 2: `cātumāsa + paccayapavāraṇā`.

Existing convention: line 1 of `construction` = full breakdown, line 2 = longer words
(`bahussutaka`: `bahu + suta + ka` / `bahussuta + ka`; `tepiṭaka 2`:
`ti > te + piṭaka + *a` / `tipiṭaka + *a`).

Script: `db_tests/single/test_longest_compound_parts.py`.

## What it should do
1. Candidate set = `DpdHeadword` with `grammar` matching `\bcomp\b`, empty `root_key`,
   non-empty `construction`. Same set is used for targets and for longer parts.
2. Targets: single-line constructions with 3+ parts, not in the exceptions file, and not
   starting with `na ` (negatives left out for now, user decision 2026-10-14).
3. Parse line 1 on ` + `; drop `[...]`; for `a > b` keep left (`a`) and right (`b`).
4. A run of 2+ adjacent parts (not the whole line) matches if:
   - concat: right forms joined equal a candidate's `lemma_clean` or any form in its
     `inflections` column (`taṇhāmūlena`, `kāṇamātu` ← `kāṇamātar`); or
   - sublist: the run's left or right forms equal a candidate's parsed line 1
     (left or right forms), e.g. `kumbha + upama` → `kumbhūpama`, `ti + piṭaka` → `tipiṭaka`.
   Never the target itself.
5. Several sublist matches: prefer one that is a substring of the target's `lemma_clean`,
   else first in Pāḷi sort order.
6. Fewest-segments split by dynamic programming; report only if shorter than line 1.
   Tie-break: fewer raw sound-change parts (`a > b`) left alone, so
   `ati > aty > acc + āraddha + vīriya` gives `accāraddha + vīriya`, not
   `ati > aty > acc + āraddhavīriya`. 5 hits still keep a lone arrow part
   (`iccevamādi`, `bavhannapāna`, `tiṃsati`, `saṭṭhi 1.1`, `sakkareyyāna`); shown as normal.
7. Line 2: concat match writes the joined text; sublist match writes the candidate's
   `lemma_clean`; unmatched parts copied verbatim from line 1.
8. Interactive loop (each word opens in GoldenDict via `tools/goldendict_tools.open_in_goldendict(lemma_clean)`): `a` append line 2 and commit, `e` exception, Enter skip, `q` quit.
9. Exceptions: `db_tests/single/test_longest_compound_parts.json` (list of `lemma_1`,
   Pāḷi-sorted), `ProjectPaths.longest_compound_parts_exceptions_path`.

## Assumptions & uncertainties
Verified on the live db 2026-10-14: 35,774 candidates; a trial found 2,401 targets with
a lemma or construction match, plus 80 runs matching only an inflected form.
Assumptions: verbatim copy of unmatched parts is good enough; sutta-name hits and noise
like `a + mata` → `amata` (form of comp `amatā`) are left to the editor.

## Constraints
Write to the db only on `a`. Pāḷi-sorted exceptions file. ruff + pyright clean.

## How we'll know it's done
Unit tests on real-row fixtures pass; the user runs the script and accepts a suggestion.

## What's not included
Words that already have line 2; root words, sandhi, idioms; negatives starting `na`; gui2.
Added on request: `just test-compounds` recipe.
