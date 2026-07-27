# Spec: pyrefly as a repo-wide type check

## Problem

The repo has three commit gates (`ruff check`, `ruff format`, `pyright`) and **no repo-wide
type check anywhere** — not in pre-commit, not in CI. The pre-commit hook runs `pyright` on
*staged files only*, so nothing ever checks the codebase as a whole.

Measured on an identical 386-file set (repo minus existing pyright excludes, `archive/`,
`kamma/`, `conductor/`):

| | pyright `basic` (current) | pyright `standard` | pyright `strict` | pyrefly (default) |
|---|---|---|---|---|
| wall time | 13.6s | 12.7s | ~13s | **1.5s** |
| total errors | 3 | 97 | 8,900 | 65 |
| genuine type errors | 3 | 3 | drowned | **22** |
| possibly-unbound | 0 | 80 | 80 | 29 |

pyright's 3 findings are a strict subset of pyrefly's 65. The 22 genuine type errors are
invisible to pyright at *every* setting tested — `basic`/`standard` do not report them, and
`strict` reports some but buries them under 8,900 `reportUnknown*`/`reportMissingTypeStubs`
diagnostics. Bumping pyright to `standard` is the cheap alternative and it is strictly worse:
+77 possibly-unbound false alarms, +0 type errors.

Verified samples of the pyrefly-only findings:

- `exporter/webapp/toolkit.py:286` — the `OperationalError` retry path falls through past the
  `except` and queries `db_session` after its `with` block exited. If `get_db_session()` itself
  raises on attempt 0 the name is never bound → `NameError` in the live webapp.
- `scripts/build/sanskrit_root_families_updater.py:66` — `self.root_group` is `""` (str) on the
  `i.rt is None` branch and `i.rt.root_group` (`Mapped[int]`, `db/models.py:77`) on the other.
  That value is written to a TSV.
- `exporter/goldendict/export_dpd.py:166` — a plain `dict` assigned to the multiprocessing
  worker global `_WORKER_RENDER_DATA: DpdHeadwordRenderData | None`.
- `tools/utils.py:82` — dynamic `str` key write into the `RenderedSizes` TypedDict. Works at
  runtime; type-purity only.

## Decision

Add pyrefly as a **repo-wide** check (`just typecheck` + CI on push/PR). Do **not** add it to
`.pre-commit-config.yaml`.

Rationale: the gap pyright leaves is a whole-repo gap, not a per-file one. On a single staged
file pyright already runs; a fourth blocking hook that disagrees with the third buys almost
nothing there and adds friction plus a second suppression dialect to reason about at commit
time. pyrefly's 1.5s repo-wide run is what fills the actual gap.

pyright stays exactly as it is — same config, same pre-commit hook, same `basic` mode. This is
an addition, not a replacement. Where the two disagree, pyright wins on spec conformance
(97.8% vs 87.8%), so it keeps its role as the per-file authority.

## Scope

### In

0. **Scope resolved (option A):** the gate covers production code. `scripts/suttas/**` is
   excluded — one-off corpus extraction, nothing outside it imports it, no build recipe runs it.
   Its 117 findings are three copy-pasted patterns in code the pipeline never executes.
   Baseline after the exclude: **46 findings**.

1. `pyrefly` in the `dev` dependency group.
2. `[tool.pyrefly]` in `pyproject.toml` — excludes aligned with `[tool.pyright]` plus
   `archive/`, `kamma/`, `conductor/`; `search-path` for the `scripts/suttas/bjt/` sibling
   imports.
3. A `just typecheck` recipe running pyrefly repo-wide.
4. A GitHub Actions workflow running `just typecheck` on push and PR, blocking on failure.
5. The existing 65 findings driven to zero, so the gate is green on day one.
6. `AGENTS.md` updated: the repo-wide check named in the pre-commit-gate section as a
   before-you-finish step, with the distinction that pyrefly is repo-wide and pyright is
   per-file.

### Out

- Adding pyrefly to `.pre-commit-config.yaml`.
- Changing `[tool.pyright]` config or the existing pre-commit hooks.
- Removing pyright.
- Type-annotating untyped code beyond what a specific finding requires.
- Bringing currently-excluded trees (`gui2/`, `tests/`, `tools/cst_source/`, `exporter/anki/`,
  `tools/writemdict/`) under type checking.

## CORRECTION (Phase 1) — the inventory below is wrong

The table below was measured in pyrefly's *single-file* mode against a hand-built file list.
Project mode resolves the module graph and checks far more deeply: the real baseline is **163
findings**, not 65. 117 of them (72%) are in `scripts/suttas/`, which is not part of the build
pipeline. The corrected inventory and the resulting scope decision live in `plan.md` under
"Phase 1 outcome". The comparison table and the four verified sample findings at the top of this
spec are unaffected — those were measured against pyright on the same file list, apples to
apples, and the decision to adopt pyrefly stands.

## Finding inventory (65, SUPERSEDED — see correction above)

By kind:

| kind | count | disposition |
|---|---|---|
| `unbound-name` | 29 | fix real ones; narrow ignore for the `in locals()` idiom |
| `missing-import` | 14 | all `scripts/suttas/bjt/*` importing sibling `helpers` — one `search-path` config line |
| `bad-assignment` | 8 | fix |
| `no-matching-overload` | 5 | fix |
| `unsupported-operation` | 3 | fix |
| `bad-argument-type` | 2 | fix |
| `missing-attribute` | 1 | fix |
| `incompatible-overload-residual` | 1 | fix |
| `bad-typed-dict-key` | 1 | fix |
| `bad-return` | 1 | fix |

By location: 39 in `scripts/`, 9 `tools/`, 7 `exporter/`, 7 `db/`, 2 `audio/`, 1 `db_tests/`.
34 of the 39 `scripts/` findings are in `scripts/suttas/` and reduce to three repeated
copy-paste patterns: the sibling `helpers` import (config), `pb` may be uninitialized (×17),
`nipata` may be uninitialized (×3).

## Testing requirement (added by user mid-thread, 2026-07-27)

Every new behaviour this thread introduces must have a regression test. Concretely:

- The gate's configuration and teeth — covered by `tests/test_typecheck_gate.py` (Phase 1).
- Each Phase 2 fix — where the fixed code is reachable and testable, add or extend a test that
  would fail if the fix were reverted. Fixes to unreachable/one-off script code that cannot be
  meaningfully unit-tested are exempt, but must be called out explicitly in `plan.md` rather
  than silently skipped.
- The CI workflow (Phase 3) — the gate must be shown to fail on a deliberately introduced type
  error, not merely to run.

**Discovered while writing these tests:** pyrefly's standalone default preset (`basic`) does
*not* catch the errors this thread is adopting pyrefly for — a `return x` from a `-> str`
function passes cleanly under it. The teeth come entirely from `[tool.pyrefly]` in
`pyproject.toml` being picked up. A config regression would therefore silence the gate without
breaking anything visibly, so `test_project_config_is_stricter_than_the_default_preset` asserts
the two disagree.

## Constraints

- Every fix must be behaviour-preserving. No `# noqa`, no blanket ignores. Where a finding is a
  genuine pyrefly false positive (e.g. `audio/error_check/trim_audio.py:156`, guarded by
  `if "temp_path" in locals()`), use a narrowly-scoped `# pyrefly: ignore` with a reason, not a
  config-level rule disable.
- Any finding whose correct fix is a judgement call about intended behaviour — notably the
  `toolkit.py` retry path and the `root_group` int/str split — gets surfaced to the user rather
  than guessed at.
- Touching a file subjects it to the existing pre-commit gate. Every file edited must pass
  `ruff check`, `ruff format`, and `pyright` before the thread is done, including pre-existing
  errors in it.
- CI job must not need submodules — `resources/` is excluded from checking, so checkout stays
  shallow and the job stays under ~2 minutes.

## Success criteria

- `just typecheck` exits 0 on a clean tree.
- The CI workflow runs on push/PR and fails on a deliberately introduced type error.
- `uv run pytest tests/` still passes.
- `uv run pyright` on every touched file still reports 0 errors.
- `AGENTS.md` states when to run pyrefly and how it differs from pyright.

## Confidence

**8/10.** The measurements are solid and reproducible; the tool choice and the
repo-wide-not-pre-commit placement are well-evidenced. The uncertainty is entirely in task 5 —
the 22 genuine type errors have not each been individually diagnosed, and a handful may turn out
to be pyrefly false positives or to need a behaviour decision from the user.
