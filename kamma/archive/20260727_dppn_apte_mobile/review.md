# Review — 20260727_dppn_apte_mobile

Date: 2026-07-27

Two review passes were run in parallel, as the project's lessons recommend:
CodeRabbit, and an independent from-scratch audit with no prior context.

## Outcome

**Passed, after one critical fix.** All findings are resolved or consciously
accepted. Full test suites green in both repos.

## Coverage

| Scope | Tool | Result |
| --- | --- | --- |
| App — 6 files | CodeRabbit | 0 findings |
| `exporter/mobile/mobile_exporter.py` | CodeRabbit | 0 findings |
| `dictionaries/apte/apte_from_cologne.py` | CodeRabbit | 0 findings |
| `scripts/prepare_sources.py` | CodeRabbit | **not run** — free CLI rate limit |
| All of the above | independent audit | 5 findings |

The unreviewed file was covered by the independent audit (finding 5 below), so
the gap was not material.

**The parallel-review rule paid for itself.** CodeRabbit returned zero findings
on precisely the files containing a 78,000-row regression. A single reviewer
would have passed this thread with the bug in it.

## Findings

### 1. CRITICAL — fuzzy-key parity regression. Fixed.

`searchDictExact` built its key with Dart's `stripDiacritics` and matched it
against `word_fuzzy`, which the Python exporter generates. The two were not
equivalent: Python drops every Unicode combining mark, Dart used a closed
25-character map covering Pāḷi only. All Sanskrit letters were absent.

78,000 rows, 12% of the table — ~34% of Monier-Williams, ~24% of Apte, ~26% of
BHS. Apte, one of the two dictionaries this thread ships, is a Sanskrit
dictionary. DPPN had zero affected rows, which is exactly why manual testing
passed.

Fixed by deriving the missing characters from the real data (22 of them, led by
`ś` 37,806, `ṣ` 34,454, `ṛ` 19,604), adding them to the map, adding a
combining-mark range guard for decomposed input, and documenting the parity
requirement in the function's doc comment. Verified by porting the patched
algorithm and running it over every row: 606,004 rows 0 mismatches, plus Cone
checked separately from source at 37,395 keys 0 mismatches. Regression test
added at `test/utils/diacritics_test.dart`.

### 2. MEDIUM — bibliography rows disagreed across repos. Fixed.

`dpd-db/shared_data/reference/bibliography.tsv` had Malalasekera filed after
Rhys Davids instead of before, with `1937` rather than `1937-1938` and no
Ānandajoti revision credit — the attribution `dict_meta.author` carries. Row
moved and corrected; a trailing tab knocked off the Rhys Davids row during the
edit was restored (13 fields, verified).

The app's copy was already correct and is **excluded from this thread's commits**
by user decision, because a parallel session added a Nyanatiloka row to the same
file.

### 3. LOW — CSS read without an `exists()` guard. Fixed.

The DPPN and Apte blocks read their CSS unconditionally while the sibling
Monier-Williams block guards with `exists()`. Both files are git-tracked so it
could not fire, but the divergence would have raised a bare `FileNotFoundError`
mid-export instead of the project's `_missing_source_error`. Aligned with the
sibling pattern.

### 4. LOW — stray leading punctuation in DPPN bodies. Fixed, scope changed.

437 entries began `, `, 94 began `. `, one began `.. `. Rather than strip it,
the user chose to move the head-line material into the displayed title. See
plan Phase 4c. Done app-side with no schema change, so it needs no database
rebuild.

### 5. LOW — docstring overstated the offline fallback. Fixed.

`prepare_sources.py` claimed both Cologne dictionaries fall back to local zips.
Only Monier-Williams does; Apte's `ap90web1.zip` is gitignored, so a fresh CI
clone has no fallback and the build fails if Cologne is down. Docstring now says
so explicitly. The underlying inconsistency is deliberate and out of scope —
see "Deferred" below.

## Verified clean by the audit

- The DPPN transform, checked exhaustively against all 13,642 source items: the
  bold-removal never targets the wrong occurrence, the first `<b>` is always the
  headword, the empty-head regex has no false positives, `ṁ`→`ṃ` cannot corrupt
  markup, and `<p>` balance is unchanged (23 pre-existing unbalanced items are
  upstream data, identical before and after).
- `build_apte_json` extraction is behaviour-preserving against its MW sibling.
- Apte through `_cleanMwHtml`: 0 residual document wrappers or section markers
  across all 34,277 rows; its class set is a strict subset of MW's.
- Tier logic: no double-counting, no row dropped from every tier.
- Query plan confirms the index seek; worst-case candidate superset is 119 rows.

## Deferred, deliberately

- **Variant/alternative-spelling search rows** for either dictionary. The mobile
  schema has one word per row and no dictionary carries synonyms.
- **The tracked-zip inconsistency.** Monier-Williams' 46 MB `mwweb1.zip` is
  tracked and re-downloaded on every source-prep run, dirtying the repo each
  time; Apte's equivalent is gitignored. Making them consistent is a deliberate
  call about build resilience and deserves its own thread.
- **Partial-tier backfill.** `searchDictPartial` caps at 50 and rows promoted to
  exact are not replaced, so that tier can now render fewer than 50 where it
  previously showed 50. Cosmetic, not raised by the user.
