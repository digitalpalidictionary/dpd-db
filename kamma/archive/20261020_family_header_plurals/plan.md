# Plan: Singular/plural agreement in family headings

Spec: `kamma/threads/20261020_family_header_plurals/spec.md`

## Architecture Decisions

- Fix each heading in place with the idiom its file already uses: a JS
  ternary in the GoldenDict templates, `{% if %}` in the website Jinja and
  the PDF `////`-delimited Jinja (copy `lite_family_word.typ`), and the
  `n == 1 ? … : …` pattern already in the Flutter builders. No shared helper:
  four languages, one line each.
- GoldenDict tests run the REAL template file in node (`node -e`) with a
  stub `superScripter` and a stub `family_*_json` global. A copy of the
  logic in Python would stay green through a revert.
- Website tests render the real `dpd_headword.html` with the same Jinja
  setup as `tests/exporter/webapp/test_dpd_headword.py::_render_template`.
- Tests skip when `node` is missing (`shutil.which("node")`). CI does not
  run pytest.

## Phase 1 — Failing tests

- [x] 1.1 Create `tests/exporter/goldendict/test_family_templates.py`
  (mirrors `exporter/goldendict/javascript/`). A helper runs node: load the
  template file with `(0, eval)(fs.readFileSync(path, "utf8"))`, set
  `globalThis.superScripter = t => t` and the `family_compound_json` /
  `family_idiom_json` global, call the function, print the HTML. Cases:
  - compound, one family, count 16 → contains `<b>16</b> compounds which contain `
  - compound, one family, count 1 → `<b>1</b> compound which contains `
  - compound, two families with counts 1 and 3 → both forms, each once
  - compound, one family → heading `<p …>` is closed before `<table`
  - idiom: the same three count cases with "idiomatic expression(s)"
  - root (`makeFamilyRootHtml(data, fr, "lemma")`), count 1 →
    `1</b> word belongs to the root family`; count 5 → `5</b> words belong`
  Read each function for the `data` keys it needs (`lemma`, `id`,
  `family_compounds`, `family_idioms`) and build the stub from that.
  → verify: `uv run pytest tests/exporter/goldendict/test_family_templates.py -v`;
  expect the count-mismatch, root-count-1 and unclosed-`<p>` cases to FAIL.
  Paste the failure lines below this task.
  **Result (before fix): 7 failed, 3 passed.** Failing: compound single
  family plural, compound several families, compound heading closed, the
  same three for idioms, root count 1. Sample:
  ```
  E  assert '<b>16</b> compounds which contain ' in '<p class="heading underlined" id=test_word_cf_top><b>16</b> compound which contains <b>nibbidā</b><table ...'
  E  assert '<b>1</b> word belongs to the root family ' in '\n <p class="heading underlined">\n <b>1</b> words belong to the root family \n ...'
  ```
- [x] 1.2 In `tests/exporter/webapp/test_dpd_headword.py`, add a render
  helper that sets `needs_compound_family_button` or
  `needs_compound_families_button` and `d.fc` (list of SimpleNamespace with
  `count`, `compound_family`, `html`). Cases:
  - single block, count 16 → `16</b>` … `compounds which contain` and not
    `contains`; count 1 → `compound which contains`
  - multi block, counts 1 and 3 → right form for each, and the `⤴` link
    (`href="#…cf_top"`) appears in BOTH family headings
  Match on whitespace-normalised HTML (`" ".join(html.split())`).
  → verify: `uv run pytest tests/exporter/webapp/test_dpd_headword.py -v`;
  expect the single-block and jump-link cases to FAIL. Paste below.
  **Result (before fix): 3 failed, 10 passed.** The several-families count
  test passes, as the spec says. The fixture needs `su.dpd_sutta` /
  `su.dpd_code` set: the template reads `d.su` properties outside the sutta
  block, and an empty `SuttaInfo` raises `TypeError` in `db/models.py`.
  ```
  E  assert '<b> 16 </b> compounds which contain <b> nibbidā </b>' in '...'
  E  assert '<b> 1 </b> compound which contains <b> nibbidā </b>' in '...'
  E  assert 'href="#test_headwordcf_top"' in 'id="test_headwordcf_kata" class="heading underlined overlined"> <b>1</b> compound which contains <b>kata</b> '
  ```
- [x] 1.3 Create `tests/exporter/pdf/test_lite_family_templates.py`. Build
  the Jinja env exactly as `exporter/pdf/pdf_exporter.py` does (loader,
  `autoescape=True`, `////` and `\\\\` block delimiters) without the db.
  Render `lite_family_root.typ` with `i` = SimpleNamespace (`root_family`,
  `root_meaning`, `count`, plus what the table loop reads; check the file).
  count 1 → `1 word belongs to the root family`; count 5 → `5 words belong`.
  → verify: `uv run pytest tests/exporter/pdf/test_lite_family_templates.py -v`;
  expect count 1 to FAIL. Paste below.
  **Changed approach:** the test builds `pdf_exporter.GlobalVars()` with
  `get_db_session` and `config_read` monkeypatched (the pattern in
  `test_pdf_exporter.py`) and renders its real `root_fam_templ`, instead of
  rebuilding the Jinja env by hand.
  **Result (before fix): 1 failed, 1 passed.**
  ```
  E  assert '1 word belongs to the root family ' in '\n#heading3[√kar]\n\n1 words belong to the root family #blue-bold[√kar] (do)...'
  ```
- [x] 1.4 In `../dpd-flutter-app`, create
  `test/widgets/family_section_builders_test.dart`. Pump
  `buildRootFamilyHeader` in a MaterialApp (add any provider that
  `context.nigg` in `lib/utils/text_filters.dart` needs). Build
  `FamilyRootData` from its generated constructor. count 1 → rendered text
  contains ` word belongs to the root family `; count 5 → ` words belong `.
  → verify: `cd ../dpd-flutter-app && flutter test test/widgets/family_section_builders_test.dart`;
  expect count 1 to FAIL. Paste below.
  No provider needed: `NiggahitaScope.of` defaults to false.
  **Result (before fix): 1 failed, 1 passed.**
  ```
  Expected: contains '1 word belongs to the root family '
    Actual: '1 word belong to the root family √kar (do)'
  ```

## Phase 2 — Fix dpd-db

- [x] 2.1 `exporter/goldendict/javascript/family_compound_template.js`: in
  both branches, build the phrase from `fc.count`
  (`fc.count == 1 ? "compound which contains" : "compounds which contain"`).
  Close the single-family `<p>` with `</p>`.
- [x] 2.2 `exporter/goldendict/javascript/family_idiom_template.js`: same
  change with `fi.count`, and close the single-family `<p>`.
- [x] 2.3 `exporter/goldendict/javascript/family_root_template.js`:
  `${fr.count == 1 ? "word belongs" : "words belong"} to the root family`.
  → verify (2.1–2.3): `uv run pytest tests/exporter/goldendict/test_family_templates.py -v`, all pass.
- [x] 2.4 `exporter/webapp/templates/dpd_headword.html`:
  - single block: `{% if d.fc[0].count == 1 %}compound which contains{% else %}compounds which contain{% endif %}`
  - multi block: move the `⤴` anchor out of the `{% else %}` so it follows
    both branches.
  → verify: `uv run pytest tests/exporter/webapp/test_dpd_headword.py -v`, all pass.
- [x] 2.5 `exporter/pdf/templates/lite_family_root.typ`: wrap the heading
  line in `//// if i.count == 1 \\\\ … //// else \\\\ … //// endif \\\\`,
  as `lite_family_word.typ` does.
  → verify: `uv run pytest tests/exporter/pdf/test_lite_family_templates.py -v`, all pass.
- [x] 2.6 Real-data check: in node, load the real
  `exporter/goldendict/javascript/family_compound_json.js` and the fixed
  template, render a headword whose only family is `nibbidā`.
  → verify: output contains `<b>16</b> compounds which contain <b>nibbidā</b>`.
  Paste the line below.
  **Result:**
  ```
  <p class="heading underlined" id=nibbidā_cf_top><b>16</b> compounds which contain <b>nibbidā</b></p>
  ```
  With two real families (`kaṇika` count 1, `nibbidā` count 16):
  `<b>1</b> compound which contains <b>kaṇika</b>` and
  `<b>16</b> compounds which contain <b>nibbidā</b>`.

## Phase 3 — Fix the Flutter app

- [x] 3.1 `../dpd-flutter-app/lib/widgets/family_section_builders.dart`,
  `buildRootFamilyHeader`: `final word = n == 1 ? 'word belongs' : 'words belong';`
  and `' $word to the root family '`. Update the doc comment to
  `word(s) belong(s)`.
  **Changed in review:** kept `word` as `'word'`/`'words'` and added
  `final belongs = n == 1 ? 'belongs' : 'belong';` with
  `' $word $belongs to the root family '`, to match the compound and idiom
  builders.
  → verify: `cd ../dpd-flutter-app && flutter test test/widgets/family_section_builders_test.dart`, all pass.

## Phase 4 — Verification

- [x] 4.1 Prove the tests guard the fix: revert each fixed file by name (copy
  aside first, never `git checkout`), run its tests, record how many fail,
  restore in the same command.
  → verify: every fixed file has at least one test that fails on revert.
  Paste counts below.
  **Result (each file reverted to HEAD, tests run, fix restored):**
  - family_compound_template.js → 3 failed, 7 passed
  - family_idiom_template.js → 3 failed, 7 passed
  - family_root_template.js → 1 failed, 9 passed
  - dpd_headword.html → 3 failed, 10 passed
  - lite_family_root.typ → 1 failed, 1 passed
  - family_section_builders.dart → 1 failed (one member is singular)
- [x] 4.2 Lint: on each new or edited Python test file run
  `uv run ruff check --fix`, `uv run ruff format`, `uv run pyright`. Run
  `just typecheck`. In the Flutter repo, run `flutter analyze` on the two
  touched Dart files. Do NOT run `dart format` on the whole file if its diff
  balloons (see global rules).
  → verify: all clean.
  **Result:** ruff, ruff format (reformatted the new GoldenDict test file
  only), pyright: 0 errors. **Correction at finalize:** plain `uv run pyright`
  analyses 0 test files (`tests` is excluded in pyproject). The real check,
  `uv run pyright --project /dev/null`, found one pre-existing error in
  `test_dpd_headword.py:11`, now fixed with `cast(types.ModuleType, ...)`. `just typecheck`: 0 errors. `flutter analyze`:
  no issues. `dart format`: 0 changed.
- [x] 4.3 Run `uv run pytest tests/exporter/goldendict tests/exporter/webapp tests/exporter/pdf`
  and `cd ../dpd-flutter-app && flutter test test/widgets`.
  → verify: all pass, or failures noted that existed before this thread.
  **Result:** full dpd-db suite `uv run pytest tests/`: 2181 passed, 12
  deselected (slow). Full Flutter suite `flutter test`: 391 passed. No
  pre-existing failures.

## Phase 5 — Scope added after review (set heading, heavy PDF templates)

- [x] 5.1 Failing tests first:
  - `tests/exporter/goldendict/test_family_templates.py`: add a set case
    (`makeFamilySets(data)`, global `family_set_json`, `data.family_sets`
    with one set) → `_heading_is_closed` is true.
  - `tests/exporter/pdf/test_lite_family_templates.py`: render
    `heavy_family_root.typ` and `heavy_family_compound.typ` through
    `GlobalVars().env.get_template(...)` at counts 1 and 5. Expect
    `1* word belongs` / `5 words belong` (root uses plain `{{ i.count }}`)
    and `*1* compound which contains` / `*5* compounds which contain`.
  → verify: run both files; the set case and the two count-1 heavy cases
  FAIL. Paste below.
  **Result (before fix): 3 failed, 14 passed.**
  ```
  E  assert False  (_heading_is_closed: '<p class="heading underlined" id=test_word_set_top><b>test word</b> belongs to the set of <b>colours</b><table ...')
  E  assert '1 word belongs to the root family ' in '...\n1 words belong to the root family *√kar* (do)...'
  E  assert '*1* compound which contains ' in '...\n*1* compounds which contain *kata*...'
  ```
- [x] 5.2 Fix: add `</p>` to the single-set heading in
  `family_set_template.js`; wrap the heading line of both heavy templates in
  `//// if i.count == 1 \\ … //// else \\ … //// endif \\`.
  → verify: both test files pass; revert each file to HEAD, confirm its
  tests fail, restore.
- [x] 5.3 `ruff check --fix`, `ruff format`, `pyright` on the two test
  files; `uv run pytest tests/exporter/goldendict tests/exporter/webapp tests/exporter/pdf`.
  → verify: all clean and passing.
