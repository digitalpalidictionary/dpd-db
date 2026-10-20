# Plan: verse finder fails on verses without a gatha1 line

Spec: `kamma/threads/20261020_dhp_uddana_verse/spec.md`

## Architecture Decisions
- One shared helper, `find_verse_start`, lives in `tools/cst_source/examples.py`.
  `corpus_index.py` imports it and deletes its copy `_resolve_gatha1`. Two copies of one rule
  are how the index and the live search would drift apart.
- The verse boundary rule is local: walk sibling tags only, stop at any non-verse element.
  No new state, no look-ahead across divs.
- The unused `text_to_find` argument of `find_gatha_example` goes. It only fed the
  "stuck in a loop" message, which goes with the 1-second guard. The two callers update.
- The first line of a verse keeps today's cleaning (`clean_gatha` only), whatever its rend.
  Lines that already work must stay byte-identical.
- Labels are not touched. Parsers are not touched.

## Phase 1 — Failing tests
- [x] 1.1 Write `tests/tools/cst_source/test_examples.py`. Build each fixture by copying real
  XML from the corpus (iconv the UTF-16 file to read it), parse with
  `BeautifulSoup(snippet, "xml")`, and run the same preprocessing as
  `tools/cst_source/loader.py::make_cst_soup` (decompose `pb`, replace `note` with
  ` [text] `). Tests:
  - uddāna, stuck case: `s0502m.mul.xml` from `<p rend="bodytext">Gāthānamuddānaṃ –</p>`
    through the "Dvādasa … ṭhārasa" / "Sukhe ca piyavagge ca" pair. Call `find_gatha_example`
    on the "Dvādasa" element. Expect exactly
    `["dvādasa lokavaggamhi,\nbuddhavaggamhi ṭhārasa [soḷasa (sabbattha)],\nsukhe ca piyavagge ca,\ngāthāyo honti dvādasa."]`
    (confirm the exact string from the post-fix output, then freeze it; spacing around
    the note must match what `clean_gatha` produces).
  - uddāna, wrong-verse case: `s0502m.mul.xml` from `<p rend="bodytext">Dhammapade vaggānamuddānaṃ –</p>`
    through "Ete chabbīsati vaggā". Call on "Pakiṇṇaṃ nirayo nāgo". Expect its own two lines
    only; assert "jarā" is not in the result.
  - run-on case: `s0506m.mul.xml`, the VV10 verse "Ahaṃ manussesu manussabhūtā, purimāya
    jātiyā manussaloke." plus the following `hangnum` and the next verse. Expect one line only;
    assert "āsajja" is not in the result.
  - control: a normal `gatha1` … `gathalast` verse from `s0502m.mul.xml` (Dhp 1). Call on its
    second line. Expect today's output.
  → verify: `uv run pytest tests/tools/cst_source/test_examples.py`. Expect the first three to
    fail and the control to pass. Paste the real failure output into this plan before Phase 2.
  - Done. All four tests assert the full expected string (stronger than the "not in" checks
    above). The tests call the walk through one helper, `verse()`, which still passes the old
    second argument `"test"`; task 2.1 drops it there. Failure output (2026-10-20, before fix):
    ```
    test_verse_without_gatha1_after_heading
    E       AssertionError: assert [] == ['dvādasa lok...nti dvādasa.']
    ----------------------------- Captured stdout call -----------------------------
    test is stuck in a loop

    test_verse_without_gatha1_does_not_reach_earlier_verse
    E       At index 0 diff: 'jarā attā ca loko ca,\nbuddho sukhaṃ piyena ca,\nkodho malañca dhammaṭṭho,\nmaggavaggena vīsati.' != 'pakiṇṇaṃ nirayo nāgo,\ntaṇhā bhikkhu ca brāhmaṇo,\nete chabbīsati vaggā,\ndesitādiccabandhunā.'

    test_verse_without_gathalast_does_not_run_into_next_verse
    E       At index 0 diff: 'ahaṃ manussesu manussabhūtā,\npurimāya jātiyā manussaloke.āsajja dānaṃ adāsiṃ,\nakāmā tiladakkhiṇaṃ,\ndakkhiṇeyyassa buddhassa,\npasannā sehi pāṇibhi.' != 'ahaṃ manussesu manussabhūtā,\npurimāya jātiyā manussaloke.'

    3 failed, 1 passed in 1.11s
    ```

- [x] 1.2 Phase check
  → verify: ruff check, ruff format, pyright on the new test file are clean.
  - Done: ruff clean, format unchanged, `pyright --project /dev/null` 0 errors.

## Phase 2 — Fix
- [x] 2.1 Rewrite the verse walk in `tools/cst_source/examples.py`. Shape:
  ```python
  def _sibling_tag(x: element.Tag, forward: bool) -> element.Tag | None:
      """Nearest sibling tag; None at the edge or at loose text (a verse boundary)."""
      sib = x.next_sibling if forward else x.previous_sibling
      while sib is not None and not isinstance(sib, element.Tag):
          if sib.strip():
              return None
          sib = sib.next_sibling if forward else sib.previous_sibling
      return sib

  def _rend(x: element.Tag | None) -> str:
      return "" if x is None else str(x.get("rend", ""))

  def find_verse_start(x: element.Tag) -> element.Tag:
      # Some verses have no gatha1 (e.g. the Dhammapada uddāna), so a verse also
      # starts right after a gathalast or any non-verse element.
      start = x
      while _rend(start) != "gatha1":
          prev = _sibling_tag(start, forward=False)
          if prev is None or _rend(prev) not in ("gatha1", "gatha2", "gatha3"):
              break
          start = prev
      return start

  def find_gatha_example(x: element.Tag) -> list[str]:
      line = find_verse_start(x)
      example = clean_gatha(line.text)
      while _rend(line) != "gathalast":
          nxt = _sibling_tag(line, forward=True)
          rend = _rend(nxt)
          if nxt is None or rend not in ("gatha2", "gatha3", "gathalast"):
              break
          line = nxt
          text = clean_gatha(line.text)
          example += re.sub(",$", ".", text) if rend == "gathalast" else text.replace(".", ",")
      return [example] if example else []
  ```
  Drop the `time` import, the guard, and the `rich` print if unused. Update the call in
  `tools/cst_source/extractor.py` to `find_gatha_example(x)`.
  → verify: `uv run pytest tests/tools/cst_source/test_examples.py`, all four pass.
  - Done: 4 passed. The uddāna string derived by hand matched the real output exactly.

- [x] 2.2 In `tools/cst_source/corpus_index.py`: delete `_resolve_gatha1`. Key the gatha cache
  on `id(find_verse_start(x))`. Call `find_gatha_example(x)`. Drop the `time` import. Rewrite
  the module docstring sentence about the stuck-loop guard to describe the verse-start key.
  → verify: `uv run pytest tests/tools/cst_source/` passes; `rg -n "_resolve_gatha1|stuck" tools/cst_source` returns nothing.
  - Done: 47 passed. The rg finds only the new docstring word "first line"; no "stuck" or
    `_resolve_gatha1` left. `from bs4 import element` was also removed (now unused).

- [x] 2.3 Lint and type gate on every touched file (`examples.py`, `extractor.py`,
  `corpus_index.py`, the test file): `uv run ruff check --fix`, `uv run ruff format`,
  `uv run pyright`.
  → verify: all three clean on all four files.
  - Done. Note: `[tool.ruff] exclude` in `pyproject.toml` lists `tools/cst_source` with
    `force-exclude = true`, so plain `ruff check <file>` there prints "No Python files found"
    and checks nothing (the commit hook skips it too). Ran with `--no-force-exclude` instead:
    ruff clean, format clean; `pyright tools/cst_source/` 0 errors; test file clean with
    `pyright --project /dev/null`.
  - Correction: `[tool.pyright].exclude` also lists `tools/cst_source`, so plain `pyright` there
    analyses nothing. Re-ran as `uv run pyright --project /dev/null tools/cst_source/{examples,extractor,corpus_index}.py`:
    0 errors (the old `examples.py` gives 14 errors under the same command, so the check is real).

- [x] 2.4 (added 2026-10-20 after the first 3.1 run) Let the forward walk continue through
  `gatha1`: the stop set becomes "not gatha1/gatha2/gatha3/gathalast". New test
  `test_gatha1_inside_a_verse_does_not_end_it` (Ud 30, real snippet from `s0503m.mul.xml`).
  See spec "Corpus findings" for the evidence.
  → verify: the new test fails before the change and passes after; all cst_source tests pass.
  - Done. Before the change: `At index 0 diff: '...anupādā [anupādānā] punabbhavo na hoti,\n' !=
    '...anupādā [anupādānā] punabbhavo na hoti,\nabhibhūto māro vijitasaṅgāmo,\nupaccagā sabbabhavāni tādīti. dasamaṃ.\n'`
    (1 failed, 4 passed). After: 48 passed. ruff/format/pyright clean on both files.

## Phase 3 — Whole-corpus proof
- [x] 3.1 Write `kamma/threads/20261020_dhp_uddana_verse/artifacts/verse_walk_diff.py`. It loads
  the old `find_gatha_example` from `git show HEAD:tools/cst_source/examples.py` (saved to the
  scratchpad and imported from there), builds soups with `make_cst_soup` for every unique file
  in `tools/pali_text_files.py::cst_texts`, and runs old and new on every gatha element.
  It prints: lines unchanged, lines changed, and every changed verse (deduped by new text)
  with file, old output, new output. Write the output to `artifacts/verse_walk_diff.txt`.
  The old code stalls 1 s per stuck line (~407 s), so run it in the background under
  `timeout 1800`.
  → verify: zero changes among lines the spec's scan class calls "ok" whose verse ends at its
    own `gathalast`. Read every changed verse in the report. Note any that look wrong in this plan.
  - Run 1 (first rule, stop at gatha1): 2,577 lines changed, 0 in the clean class. Reading it
    showed the gatha1 stop lost the end of most verses with a mid-verse gatha1 → task 2.4.
  - Run 2 (final rule), report in `artifacts/verse_walk_diff.txt`: 217 files; 180,646 gatha
    lines unchanged; 2,579 changed; **0 changed in the clean-verse class**; 1,114 changed verses
    after dedupe. Every changed line was checked for whether the result holds the searched
    line: old-has/new-lacks **0**; new-only 438; both 567; neither 98 (all `…pe…` lines the
    check strips — read all 98: the new result is the line itself, the old one a run-on or a
    different verse); 11 empty/short heads.
  - By kind: 444 run-ons cut at a non-verse element (rule-guaranteed; ~130 read); 333 formerly
    empty, now a verse (all read; includes all 8 Dhammapada uddāna verses); 140 with dropped
    middle lines restored (all read); 191 other (all read: the old result was a different verse
    or a mix, the new one coherent); empty source lines now return nothing (correct; the
    true count is 10 lines, 6 empty and 4 a single space, corrected at review).
  - Nothing looked wrong beyond the source-markup limits listed in spec "Corpus findings"
    (back-to-back gathalast; unterminated verses next to each other still join, as before).

- [x] 3.2 Live recheck of the spec cases through both real entry points:
  `find_cst_source_sutta_example("kn2", "buddhavaggamhi ṭhārasa")`,
  `… ("kn2", "pakiṇṇaṃ nirayo nāgo")`, `… ("kn6", "purimāya jātiyā manussaloke")`, and the
  same three through `CstSourceIndex(["kn2"])` / `CstSourceIndex(["kn6"])`.
  → verify: the first returns one example with source `DHP423`; the second returns its own verse;
    the VV10 result holds no "āsajja"; index and live results are equal; no "stuck" message.
  - Done (2026-10-20). kn2 `buddhavaggamhi ṭhārasa` → 1 result, `DHP423 | brāhmaṇavaggo |
    'dvādasa lokavaggamhi,\nbuddhavaggamhi ṭhārasa [soḷasa (sabbattha)],\nsukhe ca piyavagge ca,\ngāthāyo honti dvādasa.'`.
    kn2 `pakiṇṇaṃ nirayo nāgo` → its own verse ("… ete chabbīsati vaggā, desitādiccabandhunā.").
    kn6 → 11 results; VV10, VV27, VV28 now `'ahaṃ manussesu manussabhūtā,\npurimāya jātiyā manussaloke.'`.
    Index equal to live in all three. No "stuck" message.
  - Re-run after task 2.4: same results; also kn3 `abhibhūto māro` → `UD30 | lokasuttaṃ` lines
    5–6 of Ud 30 (the walk back still stops at a gatha1, as before — see spec).

- [x] 3.3 Final gate.
  → verify: `uv run pytest tests/tools/cst_source/` and `uv run pytest -m slow tests/tools/cst_source/test_corpus_index.py`
    pass; `just typecheck` clean; `graphify update .` run.
  - Done (2026-10-20, after task 2.4): cst_source 48 passed; slow 2 passed (includes the
    index-vs-live parity test on kn1); `just typecheck` 0 errors; `graphify update .` run.
    Smoke gate: `uv run pytest tests/` → 2191 passed, 12 deselected, 0 failed.

## Review fixes (2026-10-20)
- [x] R1 Add tests the independent review found missing: `test_line_after_mid_verse_gatha1_starts_there`
  (Ud 30 line 5 → lines 5–6), `test_verse_start_is_shared_by_its_lines_only` (`find_verse_start`
  identity on the Dhp uddāna), and `test_verse_without_gathalast_ends_with_full_stop` (Dhp 99).
  → verify: revert check — replacing the walk-back stop with `while True:` fails the Ud 30 test.
  - Done: revert run "1 failed, 7 passed"; file restored in the same command; 8 passed after.
- [x] R2 Restore the final full stop when a verse ends without a `gathalast` (`examples.py`, first
  in the `break` branch only; moved after the loop in R5).
  → verify: Dhp 99 test fails before ("…na te kāmagavesino,") and passes after; cst_source tests pass.
  - Done: 51 passed. ruff (`--no-force-exclude`), format, `pyright --project /dev/null` clean.
- [x] R3 Docstring in `corpus_index.py`: "cached per verse" → "cached per verse start".
- [x] R4 Re-run the whole-corpus diff; confirm 0 changes in the clean-verse class.
  - Done: 217 files; 180,635 unchanged; 2,590 changed; **0 in the clean class**; 1,119 verses.
    79 changed verses still ended in "," — lone `gathalast` lines (commentary quotations) that
    never reach the `break`.
- [x] R5 Move the full-stop rule from the `break` branch to after the loop (idempotent for verses
  that end at a `gathalast`). New test `test_single_line_verse_ends_with_full_stop`
  (real snippet, `s0505a.att.xml`).
  → verify: new-vs-previous over the whole corpus changes nothing but a final "," → ".".
  - Done: 183,144 lines identical, 81 differ only by the final comma becoming a full stop, 0 other.
    Revert check: the new test fails on the previous version (1 failed, 8 passed); restored.
    cst_source 52 passed; slow 2 passed; full suite 2195 passed; `just typecheck` 0 errors;
    ruff/format/pyright (forced) clean.
