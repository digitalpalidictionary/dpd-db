## Thread
- **ID:** 20261024_gmail_app_password
- **Objective:** Drop Google Cloud OAuth for a Gmail app password, and replace the scrape-from-Gmail newsletter flow with a local new → live preview → publish process.

## Files Changed
- `newsletter/newsletter_build.py` — builder: init, live preview server, IMAP draft, uposatha-gated docs entry, picture sizing/shrinking, clipboard links
- `newsletter/useful_links.md`, `README.md`, `newsletter_template.md` — editable footer, docs, template
- `tests/newsletter/test_newsletter_build.py` — 55 tests
- `scripts/build/newsletter_scraper.py`, `scripts/build/newsletter_processed.json` — deleted
- `tools/paths.py`, `pyproject.toml`, `uv.lock`, `justfile`, `.gitignore`, `docs/newsletters.md` — paths, deps (Google libs and markdownify out, Pillow in), recipes, ignore preview, 48→47 entries

## Findings
Reviewers: Sonnet subagent, CodeRabbit (`--agent --uncommitted --include-untracked --fresh`), pi agent. Each claim was checked against the code before fixing.

| # | Severity | Location | What | Fix |
|---|----------|----------|------|-----|
| 1 | major | `newsletter_build.py` `watch` | Preview server served the repo root: `config.ini` (live passwords) and `dpd.db` downloadable; no Host check | `PreviewHandler` serves only `newsletter/` + `identity/logo/`, rejects non-localhost Host |
| 2 | major | `append_draft` / `publish` | imaplib raises only on BAD; a NO reply printed "draft created" and the docs page was still written | Check status, return bool; publish stops before docs |
| 3 | major (Sonnet: blocking) | `MEDIA_QUERIES` | Literal `{{ }}` — mobile CSS invalid | Single braces |
| 4 | minor | `extract_subject` vs README | Text above the H1 leaked into mail and docs | Drop it, as the README says |
| 5 | minor | `render_html` | Subject and preheader unescaped | `html.escape` |
| 6 | minor | `make_mime_message` | Plain part held CSS, title and hidden preheader | `plain_text()` strips them |
| 7 | minor | `main` / `prettify_month` | Month unvalidated (`2026-13` crash, `../x` path); "init done" printed on failure | `month_arg` type; init returns bool |
| 8 | minor | `size_pictures` | Decoded every picture on every save | `upright_size()` reads header + EXIF only |
| 9 | minor | `docs_entry` | Stray `# ` H1 not shifted | Shift `#{1,5}` |
| 10 | nit | builder | `pr.no` used standalone; stale docstrings/comment; `TEMPLATE_PATH` mid-file; clipboard step ran stale module | Fixed |
| 11 | nit | handoff/plan | Named `2026-11`; folder is `2026-10` | Fixed |

Not changed, with reason: small transparent PNGs keep alpha (card is white); `a.png`/`a.jpg` same-stem collision and animated webp (rare); re-publish keyed by subject (spec'd); `css-inline`/`markdown` group placement (repo always syncs all groups).

Raised to the maintainer, not code, and decided: a local file-permission question (left as is); KOReader link text in `newsletter/2026-10/newsletter.md` (reworded); private details in these thread notes (stripped before commit); an unused test picture in the month folder (deleted).

## Fixes Applied
Findings 1–11 above. Each guarded by a test; breaking the media query, server allow-list, draft status check and text-above-H1 rule each fails ≥1 test (restored after).

## Test Evidence
- `uv run pytest tests/newsletter -q` (scope: builder module) → 55 passed
- `uv run pytest tests/ -q` (scope: whole repo suite, slow tests deselected) → 2488 passed
- `just typecheck` (scope: whole repo, pyrefly) → 0 errors; ruff + pyright clean on both touched Python files
- Live server probe from repo root → `/config.ini`, `/dpd.db`, `../config.ini`, `/`, foreign Host: 404; preview + logo: 200
- Real Gmail draft (earlier): 4 real pictures, 4.4 MB on disk → 0.8 MB mail, read back byte-checked

## Not Verified
- A real Gmail NO reply (fake IMAP only); a real uposatha-day docs publish (first one due 2026-10-26).
- Mail rendering in clients other than Gmail web; the mobile media query on a real phone.

## Verdict
PASSED
- Review date: 2026-10-25
- Reviewer: Claude Opus 5.5 (main session), with Sonnet subagent, CodeRabbit and pi agent
