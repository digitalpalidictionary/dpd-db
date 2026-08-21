# Plan: fix TPR download-list updater for jsdelivr mirror + new download_list_2.json

## Architecture Decisions
- Extract the per-file update into a small helper so the same logic runs against
  both `download_list.json` and `download_list_2.json` without duplicating the
  zip/URL-building code — avoids copy-pasting the ~30-line block.
- Match entries by URL suffix (`str.endswith(".../release_zips/<name>.zip")`)
  rather than by the JSON `filename` field, because the existing data has a
  copy-paste bug (`dpd_beta`'s `filename` field is literally `"dpd.zip"`, same as
  the release entry) — the URL suffix is the one field guaranteed to be correct
  and unique per entry today.
- Missing file or missing matching entry in a given file → warn via `pr` and skip
  that file; never append a new entry (confirmed with user — no beta entry needed
  in `download_list_2.json`).
- Keep zip-building (`_zip_it_up`) and filesize logic untouched; only the
  "find + rewrite the download-list entry" part changes.

## Phase 1 — path + core logic
- [x] Add `tpr_download_list_2_path` to `tools/paths.py`, next to
      `tpr_download_list_path` (same `resources/tpr_downloads/download_source_files/`
      dir, filename `download_list_2.json`).
  → verify: `uv run pyright tools/paths.py` clean.
- [x] In `exporter/tpr/tpr_exporter.py`, refactor `copy_zip_to_tpr_downloads`:
      - Build the jsdelivr URL for release/beta:
        `f"https://cdn.jsdelivr.net/gh/bksubhuti/tpr_downloads@master/release_zips/{filename}"`
        (`dpd.zip` / `dpd_beta.zip`) instead of the current GitHub raw URL.
      - Add a helper, e.g.
        `_update_download_list(list_path: Path, entry_info: dict, url_suffix: str) -> None`,
        that: skips with a `pr` warning if `list_path` doesn't exist; loads the
        JSON; finds the index of the entry whose `"url"` ends with `url_suffix`;
        skips with a `pr` warning if not found; otherwise replaces that index with
        `entry_info` and writes the file back (same `json.dumps(..., indent=4,
        ensure_ascii=False)` formatting as today).
      - Call this helper twice per entry (release, beta) — once for
        `g.pth.tpr_download_list_path`, once for `g.pth.tpr_download_list_2_path`.
  → verify: `uv run ruff check --fix exporter/tpr/tpr_exporter.py`,
    `uv run ruff format exporter/tpr/tpr_exporter.py`,
    `uv run pyright exporter/tpr/tpr_exporter.py` all clean.

## Phase 2 — tests
- [x] Add unit tests for the new helper/behavior in
      `tests/exporter/tpr/test_tpr_exporter.py`: build small fixture
      `download_list.json`-shaped lists in a `tmp_path`, covering (a) entry found by
      URL suffix → replaced with jsdelivr URL, (b) file missing → no crash, warning
      only, (c) no matching entry → no crash, list unchanged, warning only.
  → verify: `uv run pytest tests/exporter/tpr/test_tpr_exporter.py`, all pass. PASSED.
- [x] Phase verification: `uv run pytest tests/exporter/tpr/ tests/tools/`, all pass;
      `uv run ruff check --fix` + `uv run ruff format` + `uv run pyright` on every
      touched file, clean. PASSED — 619 passed, 7 deselected; ruff/pyright clean on
      `tools/paths.py`, `exporter/tpr/tpr_exporter.py`,
      `tests/exporter/tpr/test_tpr_exporter.py`.

### Follow-up (mid-thread, user-reported)
- [x] `tests/exporter/tpr/test_tpr_exporter.py` is excluded from the pyright
      pre-commit hook's project config (`[tool.pyright].exclude` includes `tests`),
      so `uv run pyright tests/...` normally reports "0 files analyzed" — not
      actually clean. Forcing a real check
      (`uv run pyright --project /dev/null tests/exporter/tpr/test_tpr_exporter.py`)
      surfaced 4 genuine pre-existing pyright errors in
      `test_root_homonym_grouping_uses_br` and `test_compound_type_renders_compound_row`
      (calling `.startswith`/`.endswith`/`in` on `dict[str, str | int]` values
      without narrowing). Fixed by adding `isinstance(definition, str)` asserts
      before the string operations, per "touch a file = own its lint."
  → verify: `uv run pyright --project /dev/null tests/exporter/tpr/test_tpr_exporter.py`
    → 0 errors (was 4). `uv run ruff check --fix` + `uv run ruff format` clean.
    `uv run pytest tests/exporter/tpr/ tests/tools/` → 619 passed, 7 deselected.
    Remaining IDE-reported diagnostics (`sqlalchemy` import unresolved,
    `_frozen_today is not accessed`) are false positives from a checker run
    outside the project's `uv` venv / without pytest-fixture awareness — confirmed
    against `uv run pyright` (the project's actual gate), which reports these
    imports resolve fine elsewhere in the same file's dependency tree
    (`db/models.py` clean) and `_frozen_today` is a standard `autouse=True` pytest
    fixture, not dead code.
