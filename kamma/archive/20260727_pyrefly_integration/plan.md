# Plan: pyrefly as a repo-wide type check

Spec: `spec.md`

## Phase 1 — Wire the tool up

- [x] 1.1 Add `pyrefly` to the `dev` dependency group in `pyproject.toml` via `uv add --group dev pyrefly`
  → verify: `uv run pyrefly --version` prints a 1.x version — PASSED (pyrefly 1.1.1)

- [x] 1.2 Add `[tool.pyrefly]` to `pyproject.toml`: `project-includes`, `project-excludes`
  (mirror `[tool.pyright].exclude` plus `**/archive/**`, `scripts/bash/`, `kamma/`,
  `conductor/`, `resources/`, `temp/`), `python-version = "3.13"`, and a `search-path` entry
  for `scripts/suttas/bjt`
  → verify: `uv run pyrefly check` runs project-wide with no `--config` flag and the 14
  `missing-import` findings are gone — PASSED (all 14 resolved by `search-path`)

- [x] 1.3 Add a `typecheck` recipe to `justfile` next to `lint`
  → verify: `just typecheck` runs and reports the expected remaining finding count — PASSED
  (runs in 16s, exits 1 on findings)

- [x] 1.4 (added mid-thread) Regression tests for the gate — `tests/test_typecheck_gate.py`:
  config present, python-version aligned with pyright, pyrefly excludes cover every pyright
  exclude, `just typecheck` recipe invokes pyrefly, gate rejects a real type error, gate accepts
  clean code, project config is stricter than pyrefly's default preset
  → verify: `uv run pytest tests/test_typecheck_gate.py` — PASSED (7 passed in 0.55s);
  ruff check + ruff format + pyright all clean

**Checkpoint:** DONE — see "Phase 1 outcome" below.

## Phase 1 outcome — DRIFT from spec

The spec's baseline of **65 findings** was measured in pyrefly's *single-file* mode against a
hand-built file list. In *project* mode the module graph resolves imports that single-file mode
left `Unknown`, so pyrefly checks far more deeply. The real baseline is **163 findings**, and
their distribution is completely different from the spec's table:

| area | findings | in the build pipeline? |
|---|---|---|
| `scripts/suttas/` | **117 (72%)** | **no** — self-contained, nothing outside imports it, no justfile recipe runs it |
| `scripts/build/` | 7 | yes |
| `exporter/*` | 13 | yes |
| `db/*` | 8 | yes |
| `tools/*` | 10 | yes |
| `db_tests/gui/` | 5 | yes |
| `audio/` | 2 | yes |
| `scripts/info/` | 1 | yes |
| **production total** | **46** | |

The 117 `scripts/suttas/` findings reduce to three copy-pasted patterns: `Cannot set item in
dict[str, str]` (96×, BeautifulSoup `.get()` returning `str | None` into a dict inferred as
`dict[str, str]`), `pb` may be uninitialized (17×), `nipata` may be uninitialized (3×).

Confirmed not in the pipeline: `rg 'from scripts.suttas|import scripts.suttas'` matches only
files inside `scripts/suttas/` itself; no `justfile` recipe references it; the one hit in
`scripts/build/transliterate_bjt.py` is a comment, not an import.

**This is a scoping fork that changes Phase 2's size by ~3.5x. Awaiting user decision —
see "Phase 2 scope decision" below.**

## Phase 2 scope decision — RESOLVED: option A

User chose **A** — gate production code only. `scripts/suttas/**` added to `project-excludes`
in `pyproject.toml` with a comment recording why (one-off corpus extraction, no importers, no
build recipe runs it). Verified baseline after the exclude: **exactly 46 findings**.

## Phase 2 — Drive the 46 production findings to zero

Each task: fix, then run `just typecheck` plus `ruff check --fix` / `ruff format` / `pyright` on
every file touched, plus the named regression test. Per `spec.md`, every task states the test
that would fail if the fix were reverted, or says why the code is not meaningfully testable.

Fixes must be behaviour-preserving. Where a finding is a genuine pyrefly false positive, use a
narrow `# pyrefly: ignore` with a reason — never a config-level rule disable.

- [x] 2.1 `tools/` (10 findings) — DONE: `utils.py:82` (×2, TypedDict dynamic key → summed
  through a plain dict with narrow casts, runtime-identical); `sinhala_tools.py:51,60` (×2,
  aksharamukha's unannotated `process()` falls through to `None` → `cast(str, ...)`, replacing
  the blanket `# type:ignore`); `ipa.py:149` → **module deleted**, see below.
  REMAINING: `bjt_source_sutta_example.py:112,116` (×2), `ai_gemini_manager.py:106` (join over
  `Generator[str | None]`), `ai_manager.py:205` (tuple arity 2 vs 4),
  `phonetic_change_manager.py:105`

  **`tools/ipa.py` deleted (user decision).** Investigating the `ipa.py:149` unbound-`dict`
  finding showed the module is dead: its own docstring says `2025/12/20 REPLACED BY AKSHARAMUKHA
  IPA`, its only production reference (`db/models.py:1290-1291`) is commented out with
  `lemma_ipa` now calling `_lemma_ipa_transliterate`, and `update_tsv()` is reachable only from
  its own `__main__` block. Removed `tools/ipa.py`, `tools/ipa.tsv` (single reader, now gone),
  and `tests/tools/test_ipa.py`.

  Worth recording: the pre-existing `test_convert_uni_to_ipa_invalid_mode_raises` asserted
  `UnboundLocalError` and its docstring claimed "anything other than ipa or tts leaves the
  lookup dict unbound". Probing the real function showed that is false as a generalisation — an
  invalid mode raises for most inputs but silently returns `''` when the cleaned text is empty
  (`''`, `'.'`, any punctuation-only string), because the `while` loop never reaches the dict.
  The test had frozen one arbitrary branch of inconsistent behaviour. Deleting the module made
  the question moot.

  **Left alone deliberately:** `db/models.py:1290-1291` still carries the two commented-out
  `convert_uni_to_ipa` lines, now referencing a deleted module. `db/models.py` is being edited
  by a concurrent thread in this shared working tree — not this thread's file to touch. Flagged
  to the user.
  → verify: no `tools/` findings in `just typecheck` — PASSED (`tools/` clean, repo 46 → 38)
  → gate: `ruff check` + `ruff format` + `pyright` clean on all 6 touched files;
  `uv run pytest tests/tools/` = 567 passed, 1 pre-existing failure (see note)

  Regression tests, per fix:
  - `utils.py` — **added 4 tests** to `tests/tools/test_utils.py`. `sum_rendered_sizes` had
    **zero** coverage before. Cover: empty input, per-key addition, full key set preserved,
    inputs not mutated.
  - `sinhala_tools.py` — no test needed. `cast` is a no-op at runtime; the change is purely
    type-level and the existing 12 tests already pin the transliteration output.
  - `ai_manager.py` — no test needed. Annotation-only change, no runtime effect.
  - `phonetic_change_manager.py` — no test needed. Type widening only; existing 19 tests pass.
  - `ai_gemini_manager.py` — **COVERED (user asked for it; gap closed).** New
    `tests/tools/test_ai_gemini_manager.py`, 15 tests. `GeminiManager.request` is driven with a
    fake client injected after building the instance via `__new__`, bypassing an `__init__` that
    would read `config.ini` and construct a real `genai.Client` — so no API key and no network.
    Covers: uninitialised client, plain `.text` response, blocked response with reason, parts
    joined, **None parts skipped**, all-parts-None fallback, empty-string parts, missing
    candidates, `GoogleAPICallError`, unexpected exception, `models/` prefixing (both ways),
    system-prompt prepending, and grounding on/off tool attachment.

    **Verified the regression guards actually bite:** temporarily restoring the old
    `if hasattr(part, "text")` filter fails exactly
    `test_none_parts_are_skipped_rather_than_crashing_the_join` and
    `test_all_parts_none_falls_through_to_the_empty_response_path` (2 failed, 13 passed);
    restoring the fix returns 15 passed. The old bug was worse than it looked — the `TypeError`
    was swallowed by the bare `except Exception` at the end of `request`, converting a
    recoverable response into an opaque failure message.
  - `bjt_source_sutta_example.py` — **EXEMPT by user decision (2026-07-27): the module is
    unused, so a test is not worth the BJT JSON fixtures it would need.** The fix stands; a
    match before the first heading no longer raises `UnboundLocalError`.

- [x] 2.2 `db/` (8 findings) — DONE. Repo 38 → 30.
  - `families/root_info.py:13` — the `str.join`-over-`list[Sized]` complaint came from the
    unannotated `bases_dict` param. Annotated it `dict[str, set[str]]`, matching what
    `make_roots_family_dict_and_bases_dict` in `db/families/family_root.py:75` actually builds.
  - `bold_definitions/update_bold_definitions_db.py:42` — `i.bold` comes off a TSV dot-dict as
    `Unknown | None` while `pr.counter` wants `str`. Now `i.bold or ""`.
  - `inflections/transliterate_inflections.py:88,94` and
    `lookup/transliterate_lookup_table.py:84,90` — same aksharamukha pattern as
    `tools/sinhala_tools.py`: `cast(str, ...)` replacing the blanket `# type:ignore`.
  - `models.py:1123` (×2) — **suppressed, not fixed.** The line is a deliberate, commented
    performance monkey-patch (`transliterate.getmembers = lru_cache(...)(inspect.getmembers)`)
    that stops aksharamukha rescanning members on every `process()` call. `lru_cache` collapses
    `inspect.getmembers`' overloads, which the type system cannot express. Correct at runtime →
    narrow `# pyrefly: ignore` with a reason. This is the intended use of a suppression.

  → verify: no `db/` findings — PASSED
  → gate: `ruff check` + `ruff format` + `pyright` clean on all 5 touched files;
  `uv run pytest tests/db/ tests/tools/` = 754 passed, 1 pre-existing failure

  Regression tests: **none required for this task.** Four of the five changes are provably
  no-ops at runtime — two `cast` calls, one parameter annotation, one suppression comment. The
  only behavioural change is `i.bold or ""`, which alters a progress-counter string when a TSV
  row has an empty `bold` field; it sits inside a db-writing `main()` and is not worth a
  harness. Stated explicitly rather than skipped silently.

  Note: `db/models.py` was dirty from a concurrent thread earlier in the session. Re-checked
  immediately before editing — clean at that point, so the one-line suppression was safe.

- [x] 2.3 `exporter/` (13 findings) — `analysis/analyzer.py:656,854` (×2, declared return type
  vs actual), `goldendict/export_dpd.py:165,166` (×2, jinja globals dict + worker global),
  `pdf/pdf_exporter.py:112,328,331` (×3, `None` attribute access),
  `tpr/tpr_exporter.py:113,387` (×2), `webapp/main.py:69`, `webapp/toolkit.py:286,470,470` (×3).
  **`toolkit.py:286` is the retry-path bug from `spec.md` — a behaviour decision. Stop and ask
  the user; do not guess.**
  → verify: 10 of 13 fixed, repo 30 → 20. **BLOCKED on `webapp/toolkit.py` (3 findings)** —
  see "toolkit.py decision" below.
  → gate: `ruff` + `pyright` clean on all 5 touched files; `tests/exporter/analysis/` 270
  passed, `tests/exporter/tpr/` 7 passed

  Fixes applied:
  - `goldendict/export_dpd.py:165` + `webapp/main.py:69` — **suppressed.** jinja2 declares
    `self.globals = DEFAULT_NAMESPACE.copy()` with no annotation, so its value type infers as
    the union of jinja's own default globals and no other value can be added. Extending
    `Environment.globals` is the documented API. Upstream typing gap → narrow
    `# pyrefly: ignore` at both sites.
  - `goldendict/export_dpd.py:166` — the worker global was built as a bare dict literal from
    `{**render_data, ...}`. Now constructed as `DpdHeadwordRenderData(**render_data, pth=...,
    jinja_env=...)`, which is what it always was in fact.
  - `pdf/pdf_exporter.py:112,328,331` — TSV dot-dict fields typed `Unknown | None`. `i.abbrev
    or ""` at 112; at 328 the two-stage rewrite now runs through a local `what: str`, because
    assigning to `i.what` does not narrow the attribute for the second read.
  - `tpr/tpr_exporter.py:113` — `tpr_data_list` was declared `list[dict[str, str]]` but the
    rows carry `"id": 0` and `"book_id": 11`. Widened to `dict[str, str | int]`.
  - `tpr/tpr_exporter.py:387` — **real bug.** `version` is bound only inside the `else:` branch
    at 325. When `tpr_download_list_path` is missing the function printed its help text and then
    hit `pr.yes(version)` → `UnboundLocalError`. Added `pr.no("no repo")` + `return`, which also
    closes the `pr.green_tmr` line the printer contract requires.
  - `analysis/analyzer.py:854` — annotated `results: list[AnalysisResult]`.
  - `analysis/analyzer.py:656` — **suppressed after an annotation attempt failed.** Annotating
    `word_details: list[AnalysisOption]` silenced pyrefly but made **pyright** report 6 new
    errors (4 × `reportArgumentType` on the appends, 2 × `reportTypedDictNotRequiredAccess` on
    the `total=False` key reads at 654). Reverted; narrow `# pyrefly: ignore` on the return.

  **Lesson worth keeping:** satisfying pyrefly by adding an annotation can break pyright, and
  the pre-commit gate runs pyright. Every pyrefly fix must be re-checked with `uv run pyright`
  on the same file before moving on — one checker passing is not evidence.

  Regression tests: no behavioural change in the goldendict/webapp/analyzer fixes (suppressions
  and a TypedDict constructor that builds the identical dict). `pdf_exporter.py` and
  `tpr_exporter.py:387` both fix latent crashes on paths that need a missing input file or a
  None TSV cell to reach; existing suites (270 + 7 tests) pass unchanged. The `tpr` early-return
  is worth a test if that error path ever matters — recorded as a gap.

- [x] 2.4 `db_tests/` (7 findings, not 5 — see note) — `gui/add_antonyms.py` (annotated
  `make_all_words_set() -> set[str]`, and `antonym_field.value or ""`),
  `gui/add_family_compound_su_dur.py` + `gui/add_family_compound_taddhita.py`
  (`json.loads(line.exceptions or "[]")`), `gui/add_hyphenations.py` (early return when no
  spelling choice is selected, skip empty entries — previously it would have queried for `None`
  and raised on `.replace`), `single/add_phonetic_changes.py` ×2 (isinstance narrowing).
  **Note:** the 2 findings in `single/add_phonetic_changes.py` were *caused by* task 2.1's
  widening of the rule dict to include `int`. Fixing one file surfaced latent type confusion in
  its consumer — worth knowing that finding counts can rise mid-thread for good reasons.
  → verify: no `db_tests/` findings — PASSED

- [x] 2.5 `scripts/` (8 findings) — `build/families_to_json.py` ×5 (`json_dumper` param widened
  from `dict[str, object]` to `Mapping[str, object]`; `dict` is invariant in its value type, so
  no nested dict could ever be passed), `build/newsletter_scraper.py` (kept the `creds and`
  guard for pyright's None-narrowing *and* added `isinstance(creds, Credentials)` for pyrefly —
  the isinstance alone cost pyright 3 errors), `build/sanskrit_root_families_updater.py`
  (`str(i.rt.root_group)`), `info/plus_case.py` (build `list[list[str]]` at the call site).
  **The `root_group` stop-and-ask did not need the user.** `DpdRoot.root_group` is
  `Mapped[int]` while the error branch sets `""`. The value is written via
  `csv.DictWriter.writerow`, which stringifies everything, so `str(...)` makes the TSV
  byte-identical. No behaviour question to answer.
  → verify: no `scripts/` findings — PASSED

- [x] 2.6 `audio/` (2 findings) — `index_release_download.py` (`fail()` was annotated
  `-> "None"` but ends in `sys.exit(1)`; corrected to `NoReturn`, which is the honest signature
  and resolves the "`response` may be uninitialized" finding at its source),
  `error_check/trim_audio.py` (verified false positive — the `"temp_path" in locals()` guard is
  what makes it safe and no checker models it → narrow `# pyrefly: ignore` with reason).
  → verify: `just typecheck` exits 0 — **PASSED, 0 errors**

### Bibliography test rewrite (user-requested, outside original scope)

`tests/tools/test_docs_update_bibliography.py` was a golden master pinning the entire rendered
bibliography, so it broke on every data edit and had been failing on `main` since `1abb9718`
changed the TSV without the fixture being regenerated. Replaced with 8 tests that drive
`make_bibliography_md` from synthetic rows in `tmp_path` (formatting rules only, immune to data
edits) plus 1 structural smoke test against the live TSV. Deleted the fixtures JSON.

The smoke test failed on its first run and found a real defect: two entries had embedded
newlines in their `title` cell, stranding the closing `*` on its own line and breaking the
published page; three more had trailing spaces rendering as `Thomas , 2019`. Fixed in code with
a `_clean()` helper rather than by patching the TSV, so a stray newline in a spreadsheet cell
can never break the docs again.

**Left for the user:** `docs/bibliography.md` is stale — it is missing the Malalasekera and
Levman rows and a category rename that were committed to the TSV but never regenerated.
`just docs-update` regenerates it.

### toolkit.py decision — RESOLVED: option A, block B deleted

`make_dpd_html()` had a botched retry wrapper. Structure before the fix:

```
 44  def make_dpd_html(...):
 55      for attempt in range(retries):
 56          try:
 57              with get_db_session(...) as db_session:
 58                  with db_session.no_autoflush:
                         ... lookup block A, 180 code lines ...
275                      return dpd_html, summary_html
277          except OperationalError as e:
278              if attempt == retries - 1: raise e
280              time.sleep(...)
281          dpd_html = ""            <-- still inside the for loop
285          lookup_results = db_session.query(Lookup)...   <-- session already closed
                 ... lookup block B, 152 code lines ...
470      return dpd_html, summary_html                      <-- function level
```

Blocks A (60–275) and B (281–469) were **72.3% identical** by `difflib.SequenceMatcher` on
stripped, comment-free lines — a retry wrapper added around a copy of the original body, with
the original body left in place after the `except`. Consequences: the success path returned at
275 so normal traffic never touched block B (which is why it went unnoticed); a caught
`OperationalError` fell into block B and queried a closed session; and if `get_db_session()`
itself raised, `db_session` was never bound, giving a `NameError` at 286 that masked the real
database error.

User chose A. Removed lines 281–469 (189 lines) of `exporter/webapp/toolkit.py`. The trailing
`return dpd_html, summary_html` at old line 470 became
`raise RuntimeError(f"make_dpd_html exhausted {retries} retries for {q!r}")`, because that point
is genuinely unreachable — the body returns on success at 275 and the handler re-raises on the
final attempt, so the `for` loop can never exit normally. Returning names bound inside the
closed `with` block was the original defect.

Verification: `make_dpd_html` was run against the live `dpd.db` before and after the deletion
for 12 queries covering every branch of block A (headword, inflected form, deconstructor,
numeric id, `word N` homonym, closest-matches fallback, root, EPD, nonsense, empty, and two
extras). **Output byte-identical in all 12 cases.** `ruff check`/`format`, `pyright`, and
pyrefly all clean; `ruff --select F401` confirms the deletion orphaned no imports.

All 3 toolkit findings resolved. Repo 20 → 17.

### Rollback incident (2026-07-27)

A concurrent session swept the shared working tree three times during this thread. The third
sweep was total: `[tool.pyrefly]`, the `pyrefly` dependency, the `just typecheck` recipe, all 12
Phase 2 fixes, and the `tools/ipa.py` deletion were all reverted; only untracked files survived.
Everything was replayed from context and re-verified back to the identical 20-finding state.

Durable outcome: a rule was added to `AGENTS.md` under "Kamma Concurrent Threads" banning
whole-tree git commands (`stash`, `checkout -- `, `restore`, `reset --hard`) in this repo, with
the incident cited, plus guidance to audit every touched file after any suspected rollback
because sweeps revert *unevenly* and leave a plausible-looking tree.

Also corrected during cleanup: the failing
`tests/tools/test_docs_update_bibliography.py::test_make_bibliography_md_matches_golden_master`
is **not** caused by a dirty working file, as previously reported twice. `bibliography.tsv` is
clean at HEAD. It was last changed in `1abb9718` while the golden master was last written in
`fd4e0d30` — the source moved and the golden master was never regenerated. The test is failing
on main, independent of this thread. Not this thread's to fix; flagged to the user.

**Checkpoint:** `just typecheck` exits 0; full `uv run pytest tests/`; `ruff check` +
`ruff format` + `pyright` on every touched file.

## Phase 3 — CI and docs

- [x] 3.1 Added `.github/workflows/typecheck.yml` — push to `main` + all PRs, ubuntu-latest,
  checkout with `submodules: false` (resources/ is excluded from checking and cloning it would
  dominate an otherwise ~1 min job), setup-python 3.13, uv, `uv sync --all-groups`,
  `extractions/setup-just`, `just typecheck`
  → verify: appended a deliberate `def f(x: int) -> str: return x` to `tools/utils.py`;
  `just typecheck` reported `bad-return` and **exited 1**; restored the file and it **exited 0**
  with `git diff` back to the intended change — PASSED

- [x] 3.2 Updated `AGENTS.md` with a new "Repo-wide type check: `just typecheck`" subsection
  under the pre-commit gate: what pyrefly is for and why it is deliberately *not* a pre-commit
  hook; that pyright wins on disagreement (97.8% vs 87.8% conformance); the hard rule that a
  pyrefly fix is not done until `uv run pyright <file>` is also clean, citing both times that
  bit in this thread; suppression policy; and why `scripts/suttas/**` is excluded.
  → verify: section matches the actual `.pre-commit-config.yaml`, `[tool.pyrefly]`, and
  workflow — PASSED

**Phase 3 checkpoint:** `just typecheck` 0 errors / exit 0; `uv run pytest tests/` 1722 passed,
0 failed; `ruff check` + `ruff format` + `pyright` clean on all 32 touched Python files.

**Checkpoint:** hand off for `/kamma:3-review`.

## Notes

- Fixes must be behaviour-preserving. No `# noqa`. `# pyrefly: ignore` only for verified false
  positives, with a reason comment.
- Do not touch `[tool.pyright]`, `.pre-commit-config.yaml`, or the existing `lint` recipe.
- Two tasks (2.5 `toolkit.py`, 2.6 `root_group`) are expected to need a user decision. Complete
  everything else in the task first and surface the question rather than blocking the phase.
