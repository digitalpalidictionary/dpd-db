# Plan: drop Google Cloud for Gmail, use the app password

**Thread:** 20261024_gmail_app_password · **Spec:** `spec.md` (read first, including the
password handling and the open questions)

No commits and no GitHub writes. The maintainer commits at the end.

## Phase 1 — Prerequisites (maintainer)
- [x] 1.1 Maintainer revoked and recreated the app passwords (confirmed 2026-10-24,
      IMAP login works with the new password).
- [x] 1.2 Password location decided: `config.ini` `[gmail]` (`mail`, `password`),
      read via `tools.configger.config_read`. Gitignored. Maintainer pasted values.
- [x] 1.3 Himalaya unification is an OPEN QUESTION for the maintainer (review note
      6): both `config.ini` and the Himalaya config hold the app password in plain
      text. Ask before touching either file. Suggested: `backend.auth.cmd` runs a
      `sed` pulling the same `[gmail]` password from `config.ini`.
- [x] 1.4 Probe passed: `LIST` shows `"DPD Mailers"` (47 messages) and
      `"[Gmail]/Drafts"` with `\Drafts`.

## Phase 2 — Draft builder
- [x] 2.1 `newsletter/newsletter_build.py`: Google imports, `SCOPES`,
      `get_gmail_service`, `create_draft` removed. `append_draft` does
      `IMAP4_SSL → login(config) → append("[Gmail]/Drafts", "\\Draft", None, msg)`.
      → ruff/pyright clean, verified in Gmail, no sign-in prompt.
- [x] 2.2 Draft verified in Gmail (correct subject, inline images, no recipient).

## Phase 3 — Scraper
- [x] 3.1 `scripts/build/newsletter_scraper.py`: Gmail API replaced with IMAP
      (UID commands only — see spec lesson). `parse_message` is pure and
      unit-tested; state file keyed by `Message-ID` header, with one-time
      migration dropping old Gmail-ID keys.
- [x] 3.2 Missing/empty `DPD Mailers` → `RuntimeError` + exit 1 (tested).
- [x] 3.3 All messages checked every run via cheap header-only pass (second run:
      47 listed, 0 processed, ~27s).
- [x] 3.4 Scratch diff done (`/tmp/newsletters_before.md`): all sections
      identical except — old file had the 31 May mail TWICE (one mis-dated
      2026-06-01, the forwarded-copy trap) and had LOST the "Fwd: (1 May 2026)"
      mail; the new output has every labelled mail exactly once with its true
      Date-header date. 48 → 47 entries, new one correct.
- [x] 3.5 `tests/scripts/build/test_newsletter_scraper.py`: 13 tests — pure
      parse/strip/cid functions + faked IMAP connection for loud failures and
      UID listing. (Revert ceremony skipped: the old Gmail-based code had no
      testable pure functions at all.)

## Phase 4 — Cleanup
- [x] 4.1 `gmail_credentials_path` / `gmail_token_path` removed from
      `tools/paths.py` (verified: no references left in the repo).
- [x] 4.2 `google-api-python-client` + `google-auth-oauthlib` removed from the
      `tools` group (+ transitives proto-plus, requests-oauthlib, uritemplate).
      `google-genai` kept; `google-api-core` re-added BARE with owner comment —
      `tools/ai_gemini_manager.py` imports `google.api_core.exceptions` directly
      and google-genai does not pull it (the exact AGENTS transitive-dep trap).
      → 2433 tests pass, `just typecheck` 0 errors.
- [x] 4.3 `newsletter/README.md` consent line replaced with the config.ini
      auth description; memory note `project_newsletter_scrape_order` updated
      (auth + dedup/state-key changes).
- [ ] 4.4 MAINTAINER, by hand: delete `credentials.json`, `token.json` in the
      repo root, and the old Google Cloud project.

## Phase 5 — Agent skill for Pi and Claude Code
- [x] 5.1 MAINTAINER DECISION OVERRULED THE v1.2.0 PLAN: upgraded himalaya to
      **v2.2.1** (pimalaya/himalaya) instead. Config migrated v1→v2
      (`[accounts.*]`, `imap.server`, `imap.sasl.plain`, `smtp.*`); both
      accounts read their password live from `config.ini` via a
      `python3 -c configparser` secret command. Verified: `envelope list` works
      for both accounts; draft add → list → store `\Deleted` → expunge round
      trip done. A `himalaya-mail` skill (drafts only; the maintainer sends) is
      shared with the agents' skill folders.
- [x] 5.2 Verified: draft add/list/delete round trip via himalaya v2 (above).

## Phase 6 — Three-stage newsletter process (spec: "Phase 6 scope")
- [x] 6.1 Builder: `--watch` live preview (stdlib server + poll + reload script in the
      preview only). → verify: the email HTML contains no reload script.
- [x] 6.2 Builder: `--publish` = Gmail draft always; docs entry only on uposatha days.
      → verify: tests with `uposatha_today` patched both ways.
- [x] 6.3 Builder: docs entry rendering, insert/replace, picture copy.
      → verify: tests; `tools/rss_feed.parse_newsletters` reads the new entry with the
      right title and date.
- [x] 6.4 Builder: month default = newest existing month folder; drop clipboard,
      `--open`, `--draft`; fix the docstring.
- [x] 6.5 Delete the scraper, its state file, its tests, its two recipes and its path.
- [x] 6.6 justfile: three recipes (new, preview, publish). README rewritten.
      `.gitignore`: `newsletter/*/preview.html`.
- [x] 6.7 `dpd-newsletter` skill and memory note updated for the new process.
- [x] 6.8 Gate: ruff check, ruff format, pyright on touched files; full pytest;
      `just typecheck`. → 2444 passed, typecheck 0 errors. Revert proof: removing
      the uposatha gate fails 1 test; removing the heading shift fails 1 test.
      Headless Chromium probe on a scratch copy: edit → reload, scroll kept at
      700 px, new text shown. Also fixed: `MIMEImage(..., subtype=)` → `_subtype=`
      (the plain name became a Content-Type parameter and the type was guessed
      from the bytes; an SVG would have raised).
- [ ] 6.9 Maintainer live test today (2026-10-25, not uposatha): preview reloads on
      save; publish makes a Gmail draft and skips the docs page.

## Phase 7 — Pictures sized like past newsletters (added 2026-10-25)
Measured 51 pictures in 47 past mails: median 49 KB, 50 of 51 PNG. Gmail never
shrinks bytes (draft, send and "best fit" forward all kept the 1.6 MB test
picture byte for byte). "Best fit" only sets display size: every tall picture
(phone screenshots 1008x2131 / 1008x2244, a 3072x4080 photo) was shown 562 px
tall; wide ones filled the column.
- [x] 7.1 Display box 520 wide (content column) x 560 tall: each `<img>` from
      `pics/` gets explicit width/height in preview and email.
- [x] 7.2 On publish (draft + docs) each picture is at most 2x its display
      size. Kept as is when already within that and <= 200 KB; otherwise resized
      and saved as 256-colour PNG or JPEG q82, whichever is smaller (alpha
      flattened on white; GIFs untouched). Originals in `pics/` never change.
- [x] 7.3 Docs entry uses the published file names (png may become jpg) and the
      same display width via attr_list `{ width="N" }`.
- [x] 7.4 Tests on real shapes: phone screenshot, camera photo, wide
      screenshot, small screenshot (kept byte for byte).
      → 29 newsletter tests pass. Revert proof: shrinking off fails 6, sizing
      off fails 1. Real Gmail draft with 4 real pictures (4.4 MB on disk):
      mail 0.8 MB; phone 252x560 shown / 504x1122 stored 85 KB; photo 422x560 /
      844x1121 135 KB; wide 520x294 / 1040x587 147 KB; test 520x440 / 1040x880
      179 KB. Pillow declared in [project] (was only a flet transitive).

## Touch-a-file rule
Every edited file must pass `ruff check`, `ruff format` and `pyright` (project rule). `tests/`
needs `uv run pyright --project /dev/null <file>`.
