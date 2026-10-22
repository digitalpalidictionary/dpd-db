# Handoff: contributions form (written 2026-10-22)

Thread: `20261022_contributions_form`. GitHub issue #271 (created this session,
title "new system for contributions"; do not write to it again unless asked).
Read `spec.md`, `plan.md` and `artifacts/form_template.md` first. This file adds
what they do not say.

## Where we are

- Spec, plan and form template are written. No code or docs outside this thread
  folder has been changed. Nothing is committed (the user commits).
- Phase 1 of the plan (the Google Form) is nearly done. The user built and styled
  the form. Phases 2 and 3 (website, other surfaces) have NOT started.
- Plan task 1.1 (a real test offer) is open. Task 1.2 (record the links in
  `spec.md` under a "Live form" heading) is open.

## The live form (read from the real form this session)

- Public link: https://forms.gle/Z7ENe8CVFpe2yQqKA
- It redirects to: https://docs.google.com/forms/d/e/1FAIpQLSdMbJJrddEfpWca-ma-9rKql9LCWvzwdgqbW5Rz_8bBZfuxUQ/viewform
- Editor (needs the owner's login): https://docs.google.com/forms/d/1BI-Zul58aU69fr-G9Mcz3QI7wySHeTxmk5sS5WjsJpw/edit
- Preview (cannot submit): .../1BI-Zul58aU69fr-G9Mcz3QI7wySHeTxmk5sS5WjsJpw/previewResponse
- Form title: "Contribute to the DPD Project" (the template says "Offer your help
  to DPD"; the live title wins). Editor document name: "DPD Contributors".
- Not verified: the embed link. The standard Google form is `viewform?embedded=true`
  in an iframe. Confirm on the real page in Phase 2.

### Structure (4 sections, differs from the 5-question template)

1. **Contribute to the DPD Project.** Built-in Email (required), Name, "I can help
   with:" (multiple choice: Pāḷi, Code, Resources; routes to sections 2, 3, 4).
   Description contains the user's no-money line (see Vinaya below).
2. **Pāḷi.** Qualifications/courses; "What would you like to help with?"
   (Proofreading, Creating dictionary entries, One-off projects, Other); a brief
   description. All required. Ends in Submit.
3. **Coding & Project Maintenance.** Coding experience (multiple choice: Professional,
   Academically trained, Self taught, Vibe coder); expertise checkboxes (Python,
   HTML/CSS/JS/TS, Go, Dart/Flutter, Server, Database, Build and release
   automation / GitHub Actions, Testing, Design, Documentation, Other); a brief
   description. All required. Ends in Submit.
4. **Resources.** Description (required), "How much would you like to spend on a
   subscription or service for DPD?" (required), "How long does your offer last?"
   (required). The section text says no money is sent to DPD and the donor buys
   directly from the service with a login the maintainers give.

### Settings (verified in the editor)

Collect email: Responder input. Send responders a copy: Always. Limit to 1
response: OFF (it was on and forced a Google sign-in; the user turned it off).
Allow editing: off. Confirmation message set. Sheet linked ("View in Sheets").
Email notifications for new responses: ON (aria-checked=true).

### Verified by walking the public form in a clean browser

All three branches lead to the right section and each ends in Submit. The two
problems found (Resources description optional; coding experience was checkboxes)
were fixed by the user and rechecked. No known defect remains in the form.

### NOT verified

- The notification email to the maintainer, the copy email to the offerer, and the
  sheet contents (does it have a Status column?). All need one real submission.
- My attempted test submission (name "test", test@testy.com) did NOT go through:
  the page came back as the same form, no confirmation, URL ended `/formResponse`.
  Likely reCAPTCHA blocking an automated browser. I did not retry. The user should
  send one offer by hand, from an address they can read (not test@testy.com, whose
  copy they cannot see), and check the Responses tab first for a stray row.
- Per-option routing of the Pāḷi/Code/Resources choices was verified only by
  clicking through. Section end-routing in the editor: sections 2 and 3 end in
  "Submit form".

## Vinaya decisions (full detail in `spec.md`, "Vinaya check")

Source: `~/MyFiles/Obsidian/Vicaya/2026-10-22 - vinaya-offerings-to-bhikkhus.md`
(read in full). Decided by the user:

- Maintainers are Buddhist monastics. Only time, energy, resources and pre-bought
  services are accepted. Donations are not accepted. Never any money to the project.
- The donor buys a subscription directly from the provider; the form may ask the
  donor's budget, because no money reaches the maintainers.
- A single-purpose prepaid top-up (airtime, AI credit) is not money. Open-loop
  value (store gift cards, general vouchers, crypto, mobile money) is out.
- The form must not name specific project needs (hinting counts as asking).
- STILL OPEN: who does the steering of donors. The essay's allowed route is
  informing a lay steward. Option: a lay helper reads offers and replies. The
  user has not answered.
- I made two mistakes early on that the user caught: the "worth ... in time or
  money" question with "$20 a month / $50 once" examples, and a list of specific
  needs in help text. Both were removed, then the budget wording was restored in
  a safe form (Resources section only, next to the "no money is sent" line).

## Resources the project uses

Table in `spec.md` (servers, domains, AI providers, hardware, internet, CI, email
service). It is a reference for the maintainer only. It is NOT on the form.

## Open decisions for the user

- Where the SN42.10 quotation goes (form description, or the website page above
  the form), and the full passage vs the plainer line (SN42.10, 3.2). Text and
  source are in `artifacts/form_template.md`. Not placed anywhere yet.
- Lay-helper steering (above).

## Stale items in the thread files (fix when you next touch them)

- `spec.md` "What it should do" item 2 and `artifacts/form_template.md` describe a
  single-section, five-question form. The live form has four sections (above).
  Update both to match, or add a "Live form" section and keep the template as the
  design record.
- Plan task 1.2 needs the links above recorded in `spec.md`.
- Plan Phase 2 wording says the page embeds the form; confirm the iframe works
  (the Google embed may need `?embedded=true`).

## How I read the form (reusable)

- `WebFetch` on the `viewform` URL gives only page 1 (no later sections).
- `playwright-cli` works. Working dir: the scratchpad `pw` folder, so `.playwright-cli/`
  files stay out of the repo. `playwright-cli attach --extension=chrome` attaches
  to the user's logged-in Chrome (needed for the editor). The user once rejected a
  re-attach and asked for a clean background browser instead: use
  `playwright-cli -s=pub open <viewform URL>` for anything on the public form.
- Refs are per snapshot and change after each click; re-snapshot every time. A
  stale ref silently does nothing (a Resources test once ran against the wrong
  page for that reason; check the section heading after every Next/Back).
- The public form has a live Submit button in a clean browser. Never click Submit
  unless the user says so. The preview's Submit is disabled.
- Reading text values: the accessibility snapshot hides most textbox values; use
  `playwright-cli eval` over `input, textarea, [contenteditable]` and decode the
  escaped output with Python.

## Where each surface lives (Phase 3 targets, verified 2026-10-22)

- Website: `docs/contributing/index.md`, `pali.md`, `code.md`; nav in `mkdocs.yaml`
  lines 61-64; `docs/contact.md` line 9; `docs/index.md` line 23.
- `README.md` line 9; `CONTRIBUTING.md` "Ways to Contribute" (about lines 68-100).
- Web app: `exporter/webapp/templates/dpd_headword.html` about line 1623 (mailto
  "Get involved").
- GoldenDict/MDict: `exporter/goldendict/javascript/feedback_template.js` about
  lines 50-58 (two mailto links). Check `tests/exporter/goldendict/test_export_help_fixtures.json`.
- Flutter app (separate repo `~/MyFiles/3_Active/dpd-flutter-app`):
  `lib/widgets/feedback_section.dart` line 119; the value of `_getInvolvedUrl`
  was not read.
- Overlap: `kamma/threads/20260913_feedback_section_sync/` owns the wording of the
  three "Get involved" blocks. This thread changes links only.

## User preferences seen this session

- Wants bullets, not walls of text. Wants "what is wrong", not what is right.
- Wants the form kept simple for the person making the offer; do not add questions.
- Builds Google Forms by hand; give templates, not scripts.
- Said "Hopa!" rule applies before every tool use (global rule).

## Next steps

1. Ask the user for the result of the real test offer (inbox + sheet, Status column).
2. Record the form links in `spec.md` (task 1.2) and fix the stale items above.
3. Phase 2 (website), then Phase 3 (other surfaces), then Phase 4, per `plan.md`.
