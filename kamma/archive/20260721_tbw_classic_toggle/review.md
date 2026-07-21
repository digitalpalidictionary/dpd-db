# Review: TBW Legacy links opt-in via config toggle

**Verdict: PASSED**

## Files Changed
- `tools/configger.py`
- `exporter/goldendict/export_dpd.py`
- `exporter/goldendict/templates/dpd_headword.jinja`
- `exporter/webapp/main.py`
- `exporter/webapp/templates/dpd_headword.html`
- `tests/exporter/goldendict/test_dpd_headword.py`
- `tests/exporter/webapp/test_dpd_headword.py`
- `docs/features/sutta_info.md`

## Review Method
Two independent parallel passes, run against the uncommitted working-tree diff:
1. `coderabbit review --agent --base main --type uncommitted --dir .`
2. An independent fork subagent, prompted to verify the Jinja-global wiring under
   `ProcessPoolExecutor`, `Undefined`-mode safety, other render paths, test
   coverage of the config-to-global wiring, and naming consistency.

## Findings

### CodeRabbit — 2 findings, both rejected
1. **"show_tbw fallback should be `\"no\"` not `\"yes\"`"** (export_dpd.py:292) —
   **false positive**. `config_test(section, option, value)` tests *equality*
   against `value`; it is not a missing-key default (that's `config_read`'s
   role). `config_test("dictionary", "show_tbw", "yes")` returns `True` only
   when `config.ini` literally has `show_tbw = yes`; when absent,
   `config_update_default_value` writes in `DEFAULT_CONFIG`'s `"no"` and the
   equality check correctly returns `False`. This exactly mirrors the existing
   `config_test("dictionary", "show_id", "yes")` one line above it. Applying
   the suggested change would invert the logic and show TBW Legacy by default
   everywhere.
2. **"Add `-> None` return type to the 3 new test methods"**
   (test_dpd_headword.py) — **rejected**. The goldendict test file's own
   established convention has no return-type annotations on any of its 18
   existing test methods; adding it only to the 3 new ones would make the
   file less internally consistent, not more. (The webapp test file already
   uses `-> None` throughout, and the 2 new tests there already follow suit.)

### Independent subagent review — no blocking issues
- Confirmed no race/staleness in `_worker_init`: each `ProcessPoolExecutor`
  worker builds its own fresh `jinja2.Environment` and sets `.globals["show_tbw"]`
  on that instance before storage — no shared mutable state.
- Confirmed both Jinja environments (`get_jinja2_env` and FastAPI's
  `Jinja2Templates`) use the default non-strict `Undefined`, so
  `{% if x and show_tbw %}` evaluates falsy safely when the global is unset.
- Checked all other `dpd_headword`-named template consumers; `exporter/kobo`
  has its own separate `dpd_headword.html` with no `tbw` references — out of
  scope, not a gap.
- Confirmed naming consistency: `show_tbw` under `[dictionary]` matches
  everywhere (config default, both templates, both `config_test` calls, both
  test files).
- Non-blocking suggestion: add an integration-style test proving
  `config_test`'s value actually reaches `render_data["show_tbw"]` /
  `templates.env.globals["show_tbw"]` end-to-end, not just the template gate
  in isolation. **Skipped** — keeps the diff minimal per the project's
  minimal-first convention; the wiring is a single config read assigned
  directly into a dict/global with no intervening logic to hide a bug.

## Test Evidence
```
uv run pytest tests/exporter/goldendict/ tests/exporter/webapp/ tests/tools/test_configger.py -q
146 passed in 32.55s
```
- `uv run ruff check --fix` / `uv run ruff format` — clean on all touched files.
- `uv run pyright` — 0 errors on all touched files.
- Confirmed programmatically: `DEFAULT_CONFIG["dictionary"]["show_tbw"] == "no"`
  and `"show_tbw" not in PROFILES["github_release"].get("dictionary", {})` — a
  fresh CI config stays excluded with no workflow changes.

## Fixes Applied
None — both CodeRabbit findings were false positives / would reduce
consistency; no other issues surfaced.
