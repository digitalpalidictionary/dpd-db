# Fix verse finder: verses without a gatha1 line return nothing or the wrong verse

## Overview
The source/sutta example finder (gui2 "book + word" search, and the pass2pre corpus index) cannot
find the Dhammapada uddāna line "Dvādasa lokavaggamhi, buddhavaggamhi ṭhārasa".
Search for `buddhavaggamhi ṭhārasa` in book `kn2` → prints "is stuck in a loop" and returns `[]`.

## Root cause (verified)
`tools/cst_source/examples.py::find_gatha_example` finds a verse's start by walking back
through `previous_sibling` until it meets a `rend="gatha1"` element. It skips
`gatha2`/`gatha3`/`gathalast` on the way.

The Dhammapada uddāna (`resources/dpd_submodules/cst/romn/s0502m.mul.xml`, lines ~5540–5640)
writes its verses as `gatha2` + `gathalast` pairs with no `gatha1`:

    <p rend="bodytext">Gāthānamuddānaṃ –</p>
    <p rend="gatha2">Yamake vīsati gāthā, appamādamhi dvādasa;</p>
    <p rend="gathalast">Ekādasa cittavagge, pupphavaggamhi soḷasa.</p>
    ...
    <p rend="gatha2">Dvādasa <pb .../> lokavaggamhi, buddhavaggamhi ṭhārasa <note>soḷasa (sabbattha)</note>;</p>
    <p rend="gathalast">Sukhe ca piyavagge ca, gāthāyo honti dvādasa.</p>

Three faults follow from the one rule:
1. **Stuck.** The walk crosses earlier verses and reaches the `bodytext` heading. No branch
   moves `x`, so the loop spins until the 1-second guard fires and returns `[]`.
2. **Wrong verse.** If a `gatha1` lies further back, the walk crosses one or more `gathalast`
   lines and returns that earlier verse. Live result: searching `pakiṇṇaṃ nirayo nāgo` in kn2
   returns the "jarā attā ca loko ca …" verse.
3. **Run-on at the end.** The forward walk ignores elements that are not gatha2/3/last and keeps
   going until any `gathalast`. A verse without a `gathalast` that is followed by more elements in
   the same div swallows the tail of the next verse. Live result in kn6: VV10, VV27, VV28 return
   "…manussaloke.āsajja dānaṃ adāsiṃ, …".

`tools/cst_source/corpus_index.py::_resolve_gatha1` copies the same backward walk (to key its
per-verse cache), so pass2pre's fast search has faults 1 and 2 too.

## What it should do
- A verse starts at its `gatha1` line, or at the first gatha line after a `gathalast` or after
  any non-gatha element, whichever comes first walking back.
- A verse ends at its `gathalast` line, or at the last gatha line before any non-gatha
  element, whichever comes first walking forward. A `gatha1` met walking forward does NOT end
  the verse (changed 2026-10-20 during Phase 3, see "Corpus findings" below).
- A verse that ends without a `gathalast` ends with a full stop, not the "," that every later
  line gets (added at review, 2026-10-20: the new end rule made this visible far more often).
- `find_gatha_example` and `CstSourceIndex` use one shared verse-start helper in
  `tools/cst_source/examples.py`. `_resolve_gatha1` is deleted. The cache key becomes the verse
  start element.
- The 1-second stuck-loop guard goes, since the new walk always moves or stops.
- Source/sutta labels do not change. The uddāna lines keep the label of the last verse before
  them (`DHP423`, `brāhmaṇavaggo`). This matches existing entries: headword 66411 (valāha 1)
  carries an SN uddāna example labelled with the last sutta, `SN34.55`.

## Affected files
- `tools/cst_source/examples.py` (fix)
- `tools/cst_source/corpus_index.py` (use the shared helper, update module docstring)
- `tools/cst_source/extractor.py` (call signature only)
- `tests/tools/cst_source/test_examples.py` (new)
- Callers that get the fix with no edit: gui2 book+word search in `gui2/dpd_fields_examples.py`
  (via `extractor.py`), `gui2/pass2_pre_controller.py` (via `CstSourceIndex`),
  `exporter/analysis/book_to_verses.py` (via `extractor.py`).

## Verified facts
- Live reproduction of faults 1, 2 and 3 with `find_cst_source_sutta_example` (kn2, kn6).
- The searched text matches the cleaned line. The failure is in the verse walk, not the regex.
- Corpus scan of all `romn/*.xml` (rend values: gatha1 82172, gathalast 80689, gatha2 12046,
  gatha3 8318): 182,666 gatha lines walk back correctly; 407 get stuck (62 files);
  152 reach the wrong verse (41 files).
- Callers of `find_gatha_example`: `extractor.py` and `corpus_index.py` only (rg --hidden,
  archive excluded).

## Assumptions & uncertainties
- Assumed: lines that walk back correctly today give byte-identical output after the fix.
  To be proven by a whole-corpus old-vs-new diff.
- Not measured: how many of the 2,118 lines whose verse has no `gathalast` actually run on
  (many end safely at the end of their div).
- Some commentary verses mark two lines `gatha1` (e.g. `s0508a1.att.xml`). Searching the
  first line now returns the whole verse (the old code dropped the middle line). Searching the
  second `gatha1` line still returns only the lines from there on, as before.
- `book_to_verses.py` keeps the first example per source label. The kn2 uddāna lines come after
  DHP423's own verse, so its kn2 output should not change. Not run (user runs scripts).

## How we'll know it's done
- Searching `buddhavaggamhi ṭhārasa` in kn2 returns one example: the four-line uddāna verse
  "dvādasa lokavaggamhi, buddhavaggamhi ṭhārasa [soḷasa (sabbattha)], sukhe ca piyavagge ca,
  gāthāyo honti dvādasa." with source DHP423, and no "stuck" message.
- `pakiṇṇaṃ nirayo nāgo` returns its own verse. VV10 returns only its own lines.
- New unit tests built from real XML snippets fail before the fix and pass after.
- The whole-corpus diff shows no change for any line that walked back correctly and ended at
  its own `gathalast`. Every changed verse is printed and read.
- Slow parity test `test_parity_with_live_extractor_on_kn1` still passes.
- ruff, ruff format, pyright clean on touched files; `just typecheck` clean.

## Corpus findings (2026-10-20, from the Phase 3 old-vs-new diff)
- **Mid-verse gatha1.** 215 verses reach a `gatha1` before any `gathalast`. Of 25 random
  samples, about 18 were one verse with an odd `gatha1` on a middle line (e.g. Ud 30
  "Sabbaso taṇhānaṃ khayā" in `s0503m.mul.xml`: gatha1, gatha2, gatha3, gatha2, gatha1,
  gathalast) and about 5 were two separate verses. The first draft of the fix stopped at
  `gatha1` and lost the end of the majority. The old code walked on past `gatha1` too (but
  skipped its text), so continuing through it is never worse than today.
- **Back-to-back gathalast.** 135 places (38 files) have `gathalast` directly after
  `gathalast`. Some are six-line verses (gatha1, gathalast, gathalast, e.g. `s0510m1.mul.xml`
  "Ime guṇe paṭilabhe"); many are separate quotations or verses in commentaries
  (`s0504a.att.xml`, `s0505a.att.xml`, `e0608n.nrf.xml`). Not joined: the evidence is mixed.
  For a search on the second `gathalast` line the old code returned the lines before it,
  without the searched line; the new code returns the searched line alone.
- **Empty verse lines.** 10 `gatha*` paragraphs are empty (6) or hold a single space (4) in the
  source (count corrected at review, re-measured over all 217 files). The old code returned
  the following verse for them; the new code returns nothing. A word search cannot match
  them, so this is unreachable from the GUI.
- **Odd mid-verse markup** such as `gatha3` ending a verse with no `gathalast` before the next
  verse (`e0401n.nrf.xml` "Tiṇadosāni … dosadosā") still joins two verses, as the old code did.

## What's not included
- Changing source/sutta labels for uddāna verses.
- Joining back-to-back `gathalast` lines into one verse.
- Any change to the sentence (non-verse) example path.
