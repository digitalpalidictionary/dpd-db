# Plan: TBW Legacy links opt-in via config toggle

Thread: `20260721_tbw_classic_toggle`
Spec: `spec.md`

## Tasks

### 1. Add the config default
- [ ] `tools/configger.py` — add `"show_tbw": "no"` to
  `DEFAULT_CONFIG["dictionary"]` (line ~49, alongside `show_id`).
  - `config_initialize` add-missing adds it locally; `github_release` profile
    leaves it untouched → CI stays `no`.
  - → verify: `uv run python -c "from tools.configger import DEFAULT_CONFIG; print(DEFAULT_CONFIG['dictionary']['show_tbw'])"` prints `no`.

### 2. Goldendict: inject the Jinja global
- [ ] `exporter/goldendict/export_dpd.py`
  - Add `show_tbw: bool` to `DpdHeadwordRenderDataBase` (TypedDict, ~line 56).
  - In `generate_dpd_html` (~line 288, beside `show_id`): read
    `show_tbw = config_test("dictionary", "show_tbw", "yes")`; add
    `"show_tbw": show_tbw` to the `render_data` dict (~line 305).
  - In `_worker_init` (~line 156): after building the env, set
    `_WORKER_RENDER_DATA["jinja_env"].globals["show_tbw"] = render_data["show_tbw"]`.
  - Do **not** touch `render_pali_word_dpd_html` — the global reaches the
    template without a per-render kwarg.
- [ ] `exporter/goldendict/templates/dpd_headword.jinja:423` —
  `{% if d.su.tbw_legacy and show_tbw %}`.
  - → verify: `uv run pytest tests/exporter/goldendict/test_dpd_headword.py`.

### 3. Webapp: inject the Jinja global
- [ ] `exporter/webapp/main.py` — after `templates = Jinja2Templates(...)`
  (line 67): `templates.env.globals["show_tbw"] = config_test("dictionary", "show_tbw", "yes")`.
  Add `from tools.configger import config_test` if not already imported.
  - One global covers all six `template_dpd_headword` render sites in
    `toolkit.py` (109, 239, 260, 324, 434, 453) — no per-call edits.
- [ ] `exporter/webapp/templates/dpd_headword.html:434` —
  `{% if d.su.tbw_legacy and show_tbw %}`.

### 4. Tests
- [ ] `tests/exporter/goldendict/test_dpd_headword.py` — add a test: set
  `su.tbw_legacy = "https://find.dhamma.gift/bw/mn/mn1.html"`, assert the row is
  **absent** with no global / global `False`, and **present** when the test env
  has `env.globals["show_tbw"] = True`. (The existing `_render` helper builds
  its own env; extend it to set the global.)
- [ ] `tests/exporter/webapp/test_dpd_headword.py` — mirror the same two
  assertions.
  - → verify: `uv run pytest tests/exporter/goldendict/test_dpd_headword.py tests/exporter/webapp/test_dpd_headword.py`.

### 5. Docs
- [ ] `docs/features/sutta_info.md:71` — note TBW Legacy is opt-in via
  `[dictionary] show_tbw = yes` (excluded by default).

### 6. Pre-commit gate + smoke
- [ ] For every touched Python file: `uv run ruff check --fix`,
  `uv run ruff format`, `uv run pyright`.
- [ ] `uv run pytest tests/exporter/goldendict/ tests/exporter/webapp/`.

## Manual verification (user)
1. Local `config.ini` has no change / `show_tbw = no` → render a headword
   with a sutta example in `just webapp`; TBW Legacy row absent.
2. Set `[dictionary] show_tbw = yes` → same headword now shows TBW Legacy.
3. Confirm a fresh `github_release` profile run leaves `show_tbw = no`.

## Notes
- No change to `justfile`, CI workflows, or `update-dpd.sh` — the default
  handles all public paths; the persistent local `config.ini` handles private.
- `tbw_legacy` property in `db/models.py` is left as-is (it is only the URL
  source; gating happens at render).
