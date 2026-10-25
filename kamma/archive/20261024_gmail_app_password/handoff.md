# Handoff — 20261024_gmail_app_password

**Updated:** 2026-10-25. All phases done; review PASSED (`review.md`). Next:
`/kamma:4-finalize`, then the maintainer commits.

## What the thread did

- **Gmail auth:** Google Cloud OAuth replaced by an IMAP app password read from
  `config.ini`. Google API libraries, the OAuth paths and the old credential
  files are gone. Mail tooling for agents uses himalaya with the same password
  source.
- **Newsletter written locally, scraper deleted.** Three recipes:

| Recipe | What it does |
|---|---|
| `just newsletter-new <YYYY-MM>` | copies `newsletter/newsletter_template.md` into the month folder |
| `just newsletter-preview [month]` | local server (newsletter + logo only, localhost only), opens the browser, rebuilds on save of `newsletter.md`, `pics/`, the footer or the builder itself; reloads with scroll kept; puts `![](pics/<name>)` on the clipboard when a new picture lands |
| `just newsletter-publish [month]` | Gmail draft; only if that succeeds and it is an uposatha day, the top entry of `docs/newsletters.md` + pics |

- **Docs entry:** `## <today>`, `**<subject>**`, body with comments stripped and
  headings one level down, pics renamed if re-encoded with `{ width="N" }`,
  signoff, `---`. Re-publish replaces the entry with the same subject. Read
  correctly by `tools/rss_feed.py` (tested).
- **Email look:** logo + subject in small capitals; footer from
  `newsletter/useful_links.md` (copied from the last sent newsletter, then
  ePitaka and How to cite added, lists alphabetised); all links open in a new
  tab; pictures centred.
- **Pictures:** Gmail never shrinks picture bytes (tested on draft, send and
  "best fit" forward). Display box 520x560, taken from how Gmail showed past
  pictures (tall ones always 562 tall). Publish shrinks to 2x display, PNG-256
  or JPEG q82, smaller wins; small screenshots untouched.
- **Old docs page:** regenerated once by the old scraper before it went
  (48 → 47 entries: one duplicate removed, one lost mail restored).

## Lessons

- IMAP sequence numbers renumber on EXPUNGE — always use UID commands.
- `imaplib` raises only on `BAD`; a refused `APPEND` returns `NO`. Check it.
- A long-running preview holds the code it started with; reload the module
  per rebuild, or users see stale layout and conclude the change failed.
- A local preview server must not serve the repo root: `config.ini` sits there.
- Never print mail-tool configs or grep them for auth lines; count matches only.
- `playwright-cli` writes `.playwright-cli/` into the current directory — run it
  from a scratch folder.
- `pgrep -f`/`pkill -f` match their own shell; use `ps -eo pid,args | grep "[p]attern"`.

## Still open

1. Maintainer: delete the old Google Cloud project in its console.
2. First real uposatha publish (docs entry) is untested live.
3. Commit — stage by explicit list: `newsletter/newsletter_build.py`,
   `newsletter/README.md`, `newsletter/newsletter_template.md`,
   `newsletter/useful_links.md`, `newsletter/2026-10/newsletter.md`,
   `scripts/build/newsletter_scraper.py` (deletion),
   `scripts/build/newsletter_processed.json` (deletion), `docs/newsletters.md`,
   `tools/paths.py`, `pyproject.toml`, `uv.lock`, `justfile`, `.gitignore`,
   `tests/newsletter/test_newsletter_build.py`,
   `kamma/archive/20261024_gmail_app_password/`.
   Message: `#275 newsletter: local new/preview/publish, imap draft, drop scraper`.
   Do NOT stage other sessions' files: `db_tests/db_tests_columns.tsv`,
   `mkdocs.yaml`, `shared_data/**`, `docs/integrations/epitaka.md`.
