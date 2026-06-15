# Spec — Add all Path() to ProjectPaths (issue #157)

## Goal
Every file that is genuinely part of the dpd-db project should be opened through a
`ProjectPaths` attribute (`tools/paths.py`), not via a hardcoded literal path. Throwaway
scratch files may use a tempfile / `temp_dir` instead.

## Source
GitHub issue #157 ("Refactoring"), unchecked task: *"Add all Path() to `ProjectPaths`"*.

## Classification rule (agreed)
The deciding question is **not** "persistent vs throwaway" but:

> Does more than one place have to agree on this path, is it a project input,
> **or does it get committed to git?**

- **Tier 1 — dedicated named `ProjectPaths` attr.** Any of:
  - the file is **committed / git-tracked** (decisive: committed ⇒ encode), OR
  - referenced in 2+ modules (write-here/read-there contract → will drift), OR
  - a genuine project input the build/tests/exporters depend on, OR
  - a named build artifact (consistent with existing `exporter/share/*` convention).
- **Tier 2 — anchor to an existing dir attr** (e.g. `pth.temp_dir / "x.tsv"`).
  Uncommitted single-file scratch nothing else reads. Kills the hardcoded string
  and respects `base_dir` + auto-created dirs, without minting a one-use attr.
- **Tier 3 — leave alone.** Passed-in args/variables, f-strings already on a pp dir,
  **external out-of-repo paths** (e.g. DPR `../../2_Resources/...` — pp is repo-relative),
  and separate tooling (`conductor/`).

Special case: `scripts/suttas/dpd/*.tsv` — 12 untracked, write-only outputs under a
real (non-temp) dir. Not minting 12 attrs; one dir attr (`suttas_dpd_dir`) + derive, or
leave. → ambiguous, decide one-by-one.

## Approach
1. **Audit** (done) — `audit_table.md`.
2. **Reclassify** per the committed-rule above; mark tracked/untracked (done).
3. **Low-hanging fruit first** — the unambiguous Tier-1/Tier-2/reuse changes.
4. **Ambiguous cases one-by-one** — discuss each with the user before acting
   (config.ini, cst_book_translator reader/writer, suttas dpd outputs, external paths,
   conductor template, the theragatha_filler read≠write path bug, etc.).
5. **Alphabetical reorder of `tools/paths.py`** — done LAST, once all new attrs exist,
   so the file is sorted in a single verified pass (alphabetical within the existing
   dir-grouped sections; integrity-checked: same attr set + values, order only).
6. **Verify & finish** — lint + tests, review, finalize.

## Constraints
- Modern type hints, `pathlib.Path`, no `sys.path` hacks (per project rules).
- Behaviour-preserving: same file, same location — only the path *source* changes.
- Touch a file = own its lint (`ruff check`/`format`, `pyright`) + run related tests.
- `tools/configger.py` is low-level: verify no import cycle before pulling in ProjectPaths.
- Prefer **lazy** `ProjectPaths()` instantiation (inside a function/ctor), not module
  import-time, to avoid `create_dirs()` side-effects on import.

## Out of scope
- `tools/writemdict/` (vendored third-party), `archive/`, `resources/` submodules, `tests/`.
- The other #157 checklist items (deps trim, etc.).

## Success
All committed/multi-ref/input opens go through a `ProjectPaths` attr; scratch opens are
dir-anchored; ambiguous cases resolved per user; `paths.py` alphabetised; lint + tests green.
