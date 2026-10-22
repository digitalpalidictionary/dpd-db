# Plan: new system for contributions

**GitHub issue:** [#271 — new system for contributions](https://github.com/digitalpalidictionary/dpd-db/issues/271)
Read `spec.md` first. The form template is `artifacts/form_template.md`.

## Architecture Decisions

- **One stable address.** Every surface links to the contributing overview page
  (`https://digitalpalidictionary.github.io/contributing/`). If the form changes
  later, only that page changes.
- **Google Form, embedded.** No server, no JS, no new dependency. The user
  already runs every DPD form this way.
- **Links change, wording does not.** The feedback section sync thread owns
  wording. Here only the `href` values change, so the two threads do not clash.
- **Pāḷi and code pages stay.** They keep their guidance and point to the form.
- **The form goes on the overview page, at the top (decided by the user,
  2026-10-22).** Below it, three ways to contribute: Pāḷi, Code, Resources.
  "Resources" replaces the old "Other Ways to Help". The sharing-DPD sentence
  is kept at the end of it.
- **Two names, two things (2026-10-22).** "Contribution form" means offer help.
  "Contribution website" means add Pāḷi entries. See "Vocabulary" in `spec.md`.
  No text written in this thread may use one name for the other.
- **Not abstracted:** no shared link constant across Jinja, JS and Dart. Three
  one-line edits do not need one.

## Phase 1 — Build the form (user) — *Fast*

- [x] 1.1 (user tested a real offer on 2026-10-22: it works) The user builds the form from `artifacts/form_template.md` and sends
      the live link, plus the embed link (Send → `<>` tab).
      → verify: the user submits one test offer. The maintainer gets the
      notification email. The test address gets its copy. The row appears in the
      sheet.
- [x] 1.1a (2026-10-22: first page and Resources section read live and pass. The
      Pāḷi and Code sections were read in the earlier session and hold no money
      wording; they were not re-read today) Vinaya check of the live form (see "Vinaya check" in `spec.md`). Read every
      page, help text and the confirmation message.
      → verify: no word or example about money sent to the project (no "payment", "gift card",
      and no invitation to donate; an amount appears only in the Resources section,
      as the donor's own budget, next to the line "No money is sent to DPD"; the description's own line "Donations are not accepted" is
      the one allowed use); the description says the maintainers do not deal with money;
      naming a service need (a server, a subscription) is allowed (user
      decision, 2026-10-22).
- [x] 1.1b (user kept the title "Contribute to the DPD Project", 2026-10-22; the
      Pāḷi section is unchanged) Apply the vocabulary to the live form. The user retitles the form
      (now "Contribute to the DPD Project") so it reads as an offer to help, and
      makes sure the Pāḷi section reads as an offer, not as entry editing.
      The page question is decided: the form sits on the overview page.
      → verify: the live form title and Pāḷi section text say "offer" and never
      imply editing entries.
- [x] 1.2 Record the form link and embed link in `spec.md` under a new
      "Live form" heading.
      → verify: both URLs are in `spec.md`.

Phases 2 and 3 wait for task 1.2.

## Phase 2 — Website — *Fast*

- [x] 2.1 (form shows, user confirmed 2026-10-22; frame height 1120; page cut to the form plus three short lines) Rewrite `docs/contributing/index.md`: add an "Offer your help" section
      holding the embedded form (iframe with the embed link, a plain link
      fallback under it). Keep the existing Pāḷi, code and "other ways to help"
      text. Replace "get in touch" wording that points people to email.
      → verify: `uv run mkdocs build` finishes with no new warnings. Serve the
      site and confirm the form shows on the page.
- [x] 2.1a (added 2026-10-22, user request) Resources gets its own page,
      `docs/contributing/resources.md`, with a nav entry in `mkdocs.yaml`, like
      the Pāḷi and Code pages. The overview page links to it.
- [x] 2.2 In `docs/contributing/pali.md` and `docs/contributing/code.md`, replace
      the mailto line with a link to the overview page's form section. All three
      pages (Pāḷi, Code, Resources) link to the form.
      → verify: `rg "mailto" docs/contributing` returns nothing.
- [x] 2.3 In `docs/contact.md`, change the contribute bullet to link to the
      overview page. Keep the mailto for the other two bullets.
      (Changed 2026-10-22: the developer bullet is also "get involved", so it
      moved to the form too. Only "bright ideas" keeps the mailto. The spec says
      no get-involved mailto may remain on this page.)
      → verify: the contribute bullet links to `contributing/index.md`;
      `uv run mkdocs build` has no broken-link warning.
- [x] 2.4 (built page holds the form frame and the plain link; user saw the form) Phase check.
      → verify: `uv run mkdocs build`, then read the built overview page and
      confirm the form frame and fallback link are both present.

## Phase 3 — Other surfaces — *Fast*

- [x] 3.1 (README gained a Resources link. CONTRIBUTING line 80 now points to the
      form. Other CONTRIBUTING mailtos are help requests, not get-involved
      offers, so they stay.) `README.md` line 9 and `CONTRIBUTING.md` ("Ways to Contribute", the
      "get in touch by email" lines): point to the overview page.
      → verify: `rg -n "mailto" README.md CONTRIBUTING.md` shows no
      "get involved" mailto; the overview link is present.
- [x] 3.2 (href now the overview page; 212 tests pass, none held the old link) Web app: in `exporter/webapp/templates/dpd_headword.html`, change the
      "Get involved" `href` from the mailto to the overview page URL. Keep the
      label and text. Check `tests/exporter/webapp/` for a test or fixture that
      contains the old mailto.
      → verify: `uv run pytest tests/exporter/webapp` passes; `rg "I%20want%20to%20help"
      exporter/webapp` returns nothing.
- [x] 3.3 (both hrefs changed; the fixture holds none of this text) GoldenDict and MDict: in
      `exporter/goldendict/javascript/feedback_template.js`, change the
      "Help with coding" and "Help with Pāḷi" `href` values to the overview page
      URL. Read `tests/exporter/goldendict/test_export_help_fixtures.json` first
      to see whether it holds this text.
      → verify: `uv run pytest tests/exporter/goldendict` passes; no mailto
      "help" links remain in the file.
- [x] 3.4 (the constant was a mailto. Now `https://digitalpalidictionary.github.io/contributing/`.
      Edited in the Flutter repo, not staged) Flutter app (repo `~/MyFiles/3_Active/dpd-flutter-app`): read
      `_getInvolvedUrl` in `lib/widgets/feedback_section.dart`. If it already
      points at the contributing overview page, change nothing and note it
      here. If not, change the constant. This repo is separate: do not stage
      or commit it from here.
      → verify: the constant's value is recorded here, and it equals the
      overview page URL.
- [x] 3.5 (no Python file edited, so no gate applies) Lint each edited Python or JS file per the pre-commit gate
      (`ruff check`, `ruff format`, `pyright`) where it applies. The template
      and JS files have no Python gate; confirm none applies.
      → verify: no Python file was edited, or each edited one passes the gate.
- [x] 3.6 (remaining hits, all deliberate: CONTRIBUTING.md lines 11, 64, 241 are
      "let us know" and help requests; `docs/integrations/add_your_app.md` line 31
      is the app-listing email; `docs/users_say.md` line 55 asks for opinions;
      `docs/contact.md` line 3 is "bright ideas".) Final sweep for missed surfaces: `rg --hidden -n -i "mailto:digitalpalidictionary"
      --glob '!archive/**' --glob '!kamma/archive/**' --glob '!conductor/archive/**'
      --glob '!graphify-out/**' --glob '!resources/**'`
      → verify: every remaining hit is a deliberate one (contact page's other
      bullets, the bug report line). List each in this plan.

## Phase 4 — Wrap up — *Fast*

- [x] 4.1 Add one line to `kamma/tech.md` Resources: offers come in through the
      Google Form on the contributing overview page, and the response sheet is
      the record.
      → verify: the line is present.
- [x] 4.2 (212 passed after the last edit) Run the related test paths from 3.2 and 3.3 once more.
      → verify: all pass.
- [x] 4.3 (follow-ups listed in the review hand-off: expiry reminder emails;
      money as a resource type; feeding accepted offers to the thanks page;
      merging the three "Get involved" blocks (feedback sync thread); the
      GoldenDict text still says "get in touch" and "make email contact";
      the SN42.10 quotation has no place yet; lay-helper steering is undecided;
      the pre-existing docs README warning) Follow-ups noted for the user, not built: expiry reminder emails,
      money as a resource type, feeding accepted offers to the thanks page,
      merging the three "Get involved" blocks (feedback sync thread).
      → verify: the list is in the review hand-off.
