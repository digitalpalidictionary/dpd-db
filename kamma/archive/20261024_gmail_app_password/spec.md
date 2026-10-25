# Spec: drop Google Cloud for Gmail, use the app password already in Himalaya

**Thread:** 20261024_gmail_app_password
**Written:** 2026-10-24, handoff from a research session. Nothing was changed in the repo.

## Progress log (updated in place, newest first)

- 2026-10-24 late: Phase 5 — himalaya UPGRADED to v2.2.1 (maintainer override of the
  v1.2.0 plan). v1→v2 config migration done; the DPD account's password is
  read live from `config.ini` via a secret command; a second, personal account
  keeps its own. Both accounts verified with
  `envelope list`; draft add/list/delete round trip ok. `himalaya-mail` skill
  written (drafts only) and symlinked to .agents/.pi/.claude skills dirs.
- 2026-10-24 late: Phase 4 — Google deps removed from the `tools` group;
  `google-api-core` re-added bare with owner comment (google.api_core used
  directly by tools/ai_gemini_manager.py, not pulled by google-genai — the
  AGENTS transitive trap). 2433 tests pass; `just typecheck` 0 errors.
  `credentials.json` / `token.json` still on disk for the maintainer to delete.
- 2026-10-24 late: Phase 3 — scraper fully on IMAP (UID commands only). State
  file migrated from Gmail-ID keys to `Message-ID` keys. Scratch diff vs the
  old output: the old file had the 31 May mail twice (one mis-dated 2026-06-01,
  the forwarded-copy trap) and had lost the "Fwd: (1 May 2026)" mail; the new
  output has each labelled mail exactly once with its true date. 13 new tests
  (pure parse functions + faked IMAP), all pass.

- 2026-10-24: implementation session. Decisions below; phases ticked in `plan.md`.
- 2026-10-24: password source decided — `config.ini` `[gmail]` section, keys
  `mail` and `password` (maintainer pasted them; agent never sees the value).
  Himalaya will read the same value via `backend.auth.cmd` running a `sed` on
  `config.ini`.
- 2026-10-24: IMAP probe passed — login ok, folder is `"DPD Mailers"`, 47 messages;
  `[Gmail]/Drafts` confirmed with `\Drafts` flag.
- 2026-10-24: builder Phase 2 done — `get_gmail_service`/`create_draft` replaced by
  `append_draft` (`imaplib.IMAP4_SSL` + `APPEND` to `[Gmail]/Drafts`). Verified:
  draft appears in Gmail with correct subject, no sign-in.
- 2026-10-24: lesson — IMAP sequence numbers renumber after EXPUNGE; a draft was
  accidentally deleted and recovered from Bin. All new code MUST use UID
  (`UID SEARCH`, `UID COPY`, `UID STORE`) and never act on stale sequence
  numbers.
- 2026-10-24: unrelated pre-existing drafts in the account (`earlybuddhisttexts.org`,
  `DPD newsletter draft`) are NOT ours to delete.

## Phase 6 scope: a three-stage newsletter process (added 2026-10-25)

The maintainer now writes the newsletter locally in markdown, so the docs page can
be built from that markdown. The Gmail scraper is no longer needed. Maintainer
decisions on 2026-10-25: widen this thread (one commit for everything), use real
sub-headings on the docs page, and update the docs page only on uposatha days.

### The three stages
1. **New** — `just newsletter-new <YYYY-MM>` copies `newsletter/newsletter_template.md`
   into `newsletter/<YYYY-MM>/newsletter.md` with an empty `pics/`. Exists already.
2. **Edit, review, live preview** — `just newsletter-preview [month]` builds
   `preview.html`, serves the repo root on `127.0.0.1` (OS-picked port), and opens the
   browser. It polls `newsletter.md` and `pics/` every half second and rebuilds on
   change. A small script, injected into the preview only (never into the email),
   fetches `preview.html` every second and reloads when the text differs, keeping the
   scroll position via `sessionStorage`. Stdlib only. Ctrl-C stops it. Review is an
   agent reading `newsletter.md`; no code.
3. **Publish** — `just newsletter-publish [month]`:
   - always appends the Gmail draft (existing `append_draft`, unchanged);
   - only when `UposathaManger.uposatha_today()` is true, writes the docs entry.
     Otherwise it prints that the docs page was not updated. No override flag.

Month argument: omitted → the newest existing `newsletter/<YYYY-MM>/` folder (today
the current-month default would pick `2026-10`, which does not exist).

### Docs entry format (must keep `tools/rss_feed.py` working)
`rss_feed.py` splits `docs/newsletters.md` on `## YYYY-MM-DD` lines and takes the
first `**bold**` text as the item title. Each new entry is:

```markdown
## <today, YYYY-MM-DD>
**<subject from the H1>**

<body: HTML comments removed, "## X" → "### X", "pics/foo.jpg" → "pics/newsletters/<YYYY-MM>/foo.jpg">

With much *mettā*,

Bodhirasa
```

- Inserted directly above the first `## ` entry (newest first), below `# DPD Newsletters`.
- Re-publishing replaces the existing entry whose first line is `**<subject>**`; it never
  adds a second copy.
- The signoff matches the old entries and the email template.
- Pictures referenced by the body are copied as they are into
  `docs/pics/newsletters/<YYYY-MM>/` (the scraper never compressed images either).
- The 47 existing entries stay as they are.

### Removed
- `scripts/build/newsletter_scraper.py`, `scripts/build/newsletter_processed.json`,
  `tests/scripts/build/test_newsletter_scraper.py`, the `newsletter`/`newsletter-fresh`
  recipes, `newsletter_processed_json` in `tools/paths.py`, the "DPD Mailers" label step.
- The clipboard copy (needs xclip; pasting lost the pictures) and the `--open`/`--draft`
  flags. Recipes go from five to three: new, preview, publish.
- Memory note `project_newsletter_scrape_order` is rewritten for the new process.

### Also fixed
- `newsletter/*/preview.html` was not gitignored.
- The builder docstring pointed at `scripts/build/`.
- The `dpd-newsletter` skill (`.codex/skills/`, gitignored, local) wrote HTML into the
  repo root and forbade touching the docs page. It now fills `newsletter/<YYYY-MM>/newsletter.md`.

## Problem
The maintainer is tired of signing in to Google again and again. The sign-in comes
from the newsletter scripts, which use a Google Cloud OAuth app. Nothing else in the
repo uses Google Cloud.

## What exists today (verified by reading, 2026-10-24)

### The Google Cloud setup
- `credentials.json` (March 2026): desktop-app type, for a dedicated Google Cloud project.
- `token.json`: written today; its scope is `gmail.compose` only. Both files are gitignored.
- Paths come from `tools/paths.py` (`gmail_credentials_path`, `gmail_token_path`).
- Only three files touch Google auth (verified with `rg --hidden`, excluding `uv.lock`
  and `graphify-out`): `scripts/build/newsletter_scraper.py`,
  `newsletter/newsletter_build.py`, `tools/paths.py`.
- Dependencies used only for this: `google-api-python-client`, `google-auth-oauthlib`
  (in `pyproject.toml`, lines ~64-65). `google-genai` is a different thing — keep it.
  `beautifulsoup4` and `markdownify` are also used by the scraper; check other users
  before touching them.

### Scraper (`scripts/build/newsletter_scraper.py`, run by `just newsletter`)
- Scope `gmail.readonly`. Reads messages with the Gmail label `DPD Mailers`.
- Fetches the HTML part, saves inline (`cid:`) images and remote images to
  `docs/pics/newsletters/`, converts to markdown, cuts the text after the sign-off
  word "bodhirasa", writes `docs/newsletters.md` (newest first).
- State file: `scripts/build/newsletter_processed.json` (48 entries on 2026-10-24).
- Incremental runs only look at the newest 5 labelled messages.
- Known traps: an empty or missing label ends the run quietly; forwarded copies make
  duplicate entries. See memory note `project_newsletter_scrape_order`.

### Draft builder (`newsletter/newsletter_build.py`, `just newsletter-draft`)
- Scope `gmail.compose`. Builds a `MIMEMultipart` message with inline images
  (logo and pics via `Content-ID`), then `create_draft()` uploads it with the Gmail API.
- No recipient is set. The maintainer addresses and sends it by hand in Gmail.

### Why the login hurts (not proven)
- Probably the consent screen is in "Testing" status, so Google ends the refresh token
  after 7 days. Not checked in the console.
- The two scripts want different scopes but share one `token.json`. Each can force a
  new sign-in for the other. Not tested.

### Himalaya is already set up
- Installed locally, version 1.2.0 (config keys are the **v1** style,
  such as `backend.auth.cmd`; the online README describes v2 and uses other keys).
- Config: two accounts, both IMAP + SMTP with a Google **app password**: the DPD
  account (default) and a second, personal account.
- The passwords sat in the config in plain text, as `backend.auth.cmd = "echo <password>"`.
- Folder aliases: inbox `INBOX`, sent `[Gmail]/Sent Mail`, drafts `[Gmail]/Drafts`,
  trash `[Gmail]/Bin`.
- Not tested: whether the app passwords still work.

### Password handling
Never print, copy or write the app passwords into any file in this thread.

## Facts checked online (2026-10-24)
- Google's own page (support.google.com/accounts/answer/185833): create app passwords at
  myaccount.google.com/apppasswords. Needs 2-Step Verification. No option for accounts
  with only security keys, work or school accounts, or Advanced Protection. Google says
  app passwords are "not recommended" where a normal sign-in works. Each one is shown
  once. Changing the Google password revokes all of them.
- Himalaya README (v2 line): Gmail IMAP `imap.gmail.com:993`, SMTP `smtp.gmail.com:465`
  (v1 config uses 993 TLS and 587 STARTTLS). Draft upload there:
  `himalaya message add -m drafts --flag draft < message.eml`. Not verified for v1.2.0.
- Pi coding agent has no MCP support (Armin Ronacher, 2026-01). It uses skills and
  command-line tools. One source hints that Pi 1.0 may add MCP. Unconfirmed.
- Claude's own Gmail connector can read and draft. Sending is disputed between sources.
  It does not work in Pi.

## Goal
Remove Google Cloud from the repo. The newsletter scripts talk to Gmail over IMAP/SMTP
with the app password. Pi and Claude Code do ad-hoc mail work through Himalaya.

## Decisions
- **Use Python's stdlib** (`imaplib`, `email`) for the two scripts, not Himalaya.
  Reason: no dependency on Himalaya's version, and `email` already builds the MIME.
  The builder already makes a `MIMEMultipart`; the draft upload becomes
  `imaplib.IMAP4_SSL("imap.gmail.com").append("[Gmail]/Drafts", "\\Draft", ..., msg_bytes)`.
- Agents save **drafts only**. The maintainer presses send.
- The password comes from one source. Open question below.

## Open questions for the maintainer
1. Which password manager does the maintainer use? Himalaya v1 can call a command for
   the password (`backend.auth.cmd`). Fallback: a file readable only by the maintainer,
   outside the repo. (The repo has no `.env`; do not create or edit `.env`/`.ini` files.)
2. Keep the label `DPD Mailers` for the scraper, or search by sender and subject
   instead? Default: keep the label, but fail loudly when it is empty or missing.
3. Check that Gmail shows the label as an IMAP folder named `DPD Mailers`. Probe once
   with a read-only `LIST` before writing code.

## Out of scope
- Rewriting how the scraper converts HTML, strips the footer, or dedupes. Behaviour
  stays the same unless the IMAP change forces it.
- Deleting the Google Cloud project: the maintainer does it by hand.

## Risks
- Gmail label-as-folder naming (question 3).
- Inline image handling differs between the Gmail API and raw mail; prove it on a real
  newsletter and diff `docs/newsletters.md` against the current one.
- `INTERNALDATE` vs the `Date` header: keep using the `Date` header as today.
