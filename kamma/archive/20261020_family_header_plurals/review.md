## Thread
- **ID:** 20261020_family_header_plurals
- **Objective:** Compound, idiom and root family headings agree in number with each family's own count, in GoldenDict, the website, the PDF and the Flutter app.

## Files Changed
- `exporter/goldendict/javascript/family_compound_template.js` — phrase from `fc.count`, not from the number of families; single-family heading closes its `<p>`.
- `exporter/goldendict/javascript/family_idiom_template.js` — same, with `fi.count`.
- `exporter/goldendict/javascript/family_root_template.js` — "word belongs" / "words belong" from `fr.count`.
- `exporter/webapp/templates/dpd_headword.html` — single compound block picks the form from the count; ⤴ link on every family in the multi block.
- `exporter/pdf/templates/lite_family_root.typ` — if/else on `i.count`, as in `lite_family_word.typ`.
- `exporter/goldendict/javascript/family_set_template.js` — single-set heading closes its `<p>` (added after review, user request).
- `exporter/pdf/templates/heavy_family_root.typ`, `heavy_family_compound.typ` — if/else on `i.count` (added after review, user request; not loaded by any code today).
- `tests/exporter/goldendict/test_family_templates.py` (new), `tests/exporter/pdf/test_lite_family_templates.py` (new, lite + heavy templates), `tests/exporter/webapp/test_dpd_headword.py` (4 tests added).
- `../dpd-flutter-app/lib/widgets/family_section_builders.dart` — `buildRootFamilyHeader` adds `belongs`/`belong`; `../dpd-flutter-app/test/widgets/family_section_builders_test.dart` (new).

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `exporter/goldendict/javascript/family_set_template.js:30-32` | Single-set heading never closes its `<p>`. | Same defect fixed here for compounds/idioms. Pre-existing, outside the spec (sets have no count). Browsers auto-close, renders the same. | **Fixed** (user: "fix all related singular compound bugs in all versions of the app"). |
| 2 | nit | `exporter/webapp/templates/dpd_headword.html:1387` | `{% if loop.index == 0 %}` never true, emits a stray `</p>` per family. | Pre-existing, unchanged. Changing to `== 1` would drop the first family's `id` and break its jump link. | Leave. |
| 3 | nit | `../dpd-flutter-app/lib/widgets/family_section_builders.dart:61` | `word` held "word belongs"; siblings split noun and verb. | Spec asked for the sibling pattern. | **Fixed:** `word` + `belongs`. |
| 4 | nit | `exporter/pdf/templates/lite_family_root.typ:4-8` | Block tags add blank lines. | Reviewer compiled old vs new with typst: identical images. Siblings do the same. | None. |
| 5 | nit | `tests/exporter/webapp/test_dpd_headword.py:189` | Helper builds its own Jinja env. | Harmless. | Skipped. |
| 6 | minor (CodeRabbit, pass 1) | `tests/exporter/goldendict/test_family_templates.py:10` | `JS_DIR` relative to cwd. | **Rejected:** project rule forbids `Path(__file__).resolve().parents[n]` and says tests run from the repo root; sibling tests use the same relative form. | None. |

| 7 | observation (pass 2) | `family_word_template.js:10`, website word block, Flutter `buildWordFamilyHeader` | Word family headings are always plural. | Correct today: `family_word` has 851 rows, `min(count)` = 2. Would need a fix if a one-member word family ever appears. | None. |

Pass 2 (Sonnet subagent, after the user tested and approved) found no blocking, major or minor issues. It repeated findings 2 and 6 as nits, with the same conclusion.

## Fixes Applied
- Finding 1: `</p>` added to the single-set heading. Test fails on HEAD (1 failed, 10 passed), passes after. `html.parser` check of 1-set and 2-set output: no stray, nested or unclosed tags.
- User-requested scope: heavy PDF root and compound templates pick the form from `i.count`. Each has a count-1 test that fails on HEAD (1 failed, 5 passed) and passes after.
- Finalize: the earlier "pyright clean" on the test files was a no-op (`[tool.pyright].exclude` covers `tests`, `filesAnalyzed: 0`; see `kamma/tech.md`). The real run (`--project /dev/null`) found a pre-existing `reportArgumentType` error at `tests/exporter/webapp/test_dpd_headword.py:11` (`SimpleNamespace` passed to `sys.modules.setdefault`). Fixed with `cast(types.ModuleType, ...)`, no behaviour change. The same pattern sits in four test files this thread did not touch (`tests/tools/test_sutta_codes.py`, `tests/exporter/goldendict/test_dpd_headword.py`, `tests/exporter/goldendict/test_dpd_header.py`, `tests/db/test_sutta_info.py`); not touched.
- Finding 3: Flutter root heading split into `word` and `belongs`. Re-ran its test (2 passed), `flutter analyze` (no issues), `dart format` (0 changed).

## Test Evidence
- `uv run pytest tests/` (scope: whole dpd-db suite, slow tests deselected, after all fixes) → 2186 passed.
- `flutter test` (scope: whole Flutter suite, after all fixes) → 391 passed.
- `just typecheck` after all fixes → 0 errors.
- Revert proof (each fixed file swapped for HEAD, tests run, fix restored): compound JS 3 fail, idiom JS 3 fail, root JS 1 fail, website 3 fail, PDF 1 fail, Flutter 1 fail. Independent reviewer reproduced the dpd-db numbers against HEAD copies in a scratch dir.
- Real data: fixed template + real `family_compound_json.js` → `<b>16</b> compounds which contain <b>nibbidā</b>` and `<b>1</b> compound which contains <b>kaṇika</b>`.
- GoldenDict output parsed with `html.parser` (both reviewers): no unclosed, stray or nested tags in compound/idiom (counts {1}, {16}, {1,3}), root (1, 5) and set (1 and 2 sets) output.
- Pass 2 revert proof against HEAD copies in the scratchpad (working tree untouched): GoldenDict JS 8 failed / 3 passed; website 3 failed / 10 passed; PDF lite + heavy 3 failed / 3 passed. Flutter revert reasoned from the HEAD text ("1 word belong").
- Pass 2: `uv run pytest tests/exporter/goldendict tests/exporter/webapp tests/exporter/pdf` → 176 passed; ruff, ruff format, pyright, `just typecheck`, `flutter analyze`, Flutter test file → clean / 2 passed.
- `ruff check`, `ruff format` (3 test files), `just typecheck` (whole repo) → clean. `uv run pyright --project /dev/null` on the 3 test files → `filesAnalyzed: 3`, 0 errors (after the finalize fix); then `uv run pytest tests/exporter/webapp tests/exporter/goldendict tests/exporter/pdf` → 176 passed.
- CodeRabbit `--dir exporter`, `--dir tests`, Flutter repo (all `--uncommitted --include-untracked`) → 0, 1 (rejected), 0 findings. Re-run on `exporter` and `tests` after the post-review additions → 0 and 0 findings. Pass 2 `--fresh`: `tests` → 0, Flutter repo → 0 (covers the `word`/`belongs` change), `exporter` → connection error ("WebSocket closed") on the retry; not retried further. The exporter files are unchanged since the 0-finding run above.
- Independent `rg --hidden` sweep of exporter/, db/, gui2/, tools/, go_modules/, scripts/, Flutter repo → no other wrong heading.

## Not Verified
- The user tested the website and approved. No real GoldenDict or PDF export was run here, and the phone app was not run on a device.
- The heavy PDF templates were checked by render tests only. No code loads them, so no real typst compile of them was run.

## Verdict
PASSED
- Review date: 2026-10-20
- Reviewer: pass 1 independent general-purpose subagent + CodeRabbit CLI; pass 2 independent Sonnet subagent + CodeRabbit CLI; consolidated by Claude Opus 5.5
