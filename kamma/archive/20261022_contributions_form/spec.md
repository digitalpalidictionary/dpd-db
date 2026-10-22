# Spec: new system for contributions

**Thread:** 20261022_contributions_form
**Date:** 2026-10-22
**GitHub issue:** [#271 — new system for contributions](https://github.com/digitalpalidictionary/dpd-db/issues/271)
(commits reference `#271`)
**Related, not the same thing:** #215 contributor onboarding (people who already
edit data in gui2). This thread is the front door: people who OFFER to help.
**Overlap:** `kamma/threads/20260913_feedback_section_sync/` (placeholder) covers
the wording of the same three "Get involved" blocks. This thread changes only
where those links point, not their wording.

## Overview

Today a person who wants to help clicks a mailto link or reads "get in touch".
The only record is a Gmail thread. Nothing says what they offered, or how long
the offer lasts. Offers of resources (servers, domains, AI credits) are easy to
lose.

Replace this with one Google Form, embedded on the website's contributing
overview page. Every surface then links to that one page.

## Vocabulary (decided by the user, 2026-10-22)

Two things carry the word "contribution". Keep them apart in every text.

- **Contribution form** = offer help. A person offers time, skill, resources or
  a pre-bought service. This thread builds it.
- **Contribution website** = add Pāḷi entries. The hosted gui2 where approved
  people edit the dictionary (thread `20260719_contributor_web_server`, #215).
  It is private and gets no public link from this thread.
- The quick suggestion forms (add a missing word, correct a mistake) are a
  third thing. They are neither of the two above. Call them "suggestion forms".
- The live form's title stays "Contribute to the DPD Project" (decided by the
  user, 2026-10-22). The earlier title "Offer your help to DPD" in
  `artifacts/form_template.md` is dropped.
- The offer form's Pāḷi section is an offer to help. It does not edit entries.
  Approval and access to the contribution website come after the offer.

## What it should do

1. One place to offer help: the contributing overview page on the docs website.
2. The form stays simple for the person. The user built it with four sections
   (see "Live form" below): a first page (email, name, what they can help with:
   Pāḷi, Code or Resources), then one section for each choice. The Resources
   section asks for a description, the most the donor would spend on a
   subscription or service, and how long the offer lasts. The person states the
   size of the offer. (Reworded after the Vinaya check below. The five-question
   design in `artifacts/form_template.md` is the earlier design record.)
3. The person makes the offer. The maintainer decides where it goes. The form
   has no list of specific project needs and no date box. It branches by the
   first choice, as the user built it.
4. Every offer is a row in a response sheet. The maintainer adds a Status column
   by hand.
5. Every offer sends an email to the maintainer and an email copy to the person.
6. Every "get involved" link in every DPD surface points to the contributing
   overview page.

7. A short Pāḷi quotation on monks not accepting money, with its English
   translation under it, is shown with the offer form. The user asked for it
   on 2026-10-22, with the key word *tiṇatthika*. That word is in SN42.10
   (DPD headword id 30530, meaning "wanting grass; in need of straw"). The
   chosen passage and its source are in `artifacts/form_template.md`. Where it
   sits (form description or the page above the form) is not yet decided.

The user builds the form by hand in Google Forms, in the same style as the
other DPD forms. The full template (header, each question, each setting) is in
`artifacts/form_template.md`. The user gives the live form link later. Code and
docs work that needs the link waits for it.

## Live form (read from the real form, 2026-10-22)

- Public link: https://forms.gle/Z7ENe8CVFpe2yQqKA
- Full link: https://docs.google.com/forms/d/e/1FAIpQLSdMbJJrddEfpWca-ma-9rKql9LCWvzwdgqbW5Rz_8bBZfuxUQ/viewform
- Embed link: the full link with `?embedded=true` added. Checked by the user
  on the served page, 2026-10-22. It works at frame height 1120.
- Editor (owner login only): https://docs.google.com/forms/d/1BI-Zul58aU69fr-G9Mcz3QI7wySHeTxmk5sS5WjsJpw/edit
- The form has four sections: first page (email, name, what they can help
  with), Pāḷi, Coding & Project Maintenance, Resources. The first-page choice
  sends the person to the matching section. Details are in `handoff.md`.
- Not yet verified: the two emails and the Status column in the sheet. These
  need one real test offer (task 1.1).

## Resources the project uses (examined 2026-10-22)

This list is a reference for the maintainer only. It is NOT on the form, and
no example from it appears in the form text (see the Vinaya check). Each item names
its evidence in the repo.

| Resource | Evidence |
|---|---|
| Server or hosting | dpdict.net web app (thanks page credits a person for setting it up); contributor web server VPS planned in `kamma/threads/20260719_contributor_web_server/`; temporary test server in `kamma/threads/20261007_temp_server_test/` |
| Domain name | dpdict.net, docs.dpdict.net (`rg` of `exporter/`, `tools/`), s.4nt.org (sutta deep links), digitalpalidictionary.github.io (GitHub Pages) |
| AI subscription or API credits | `[apis]` section of `config.ini` (key names only read): DeepSeek, Gemini, OpenRouter, NVIDIA, Z.ai, ElevenLabs, Bhashini, Sarvam, CanonRAG. `tools/ai_openai_compat.py` `PROVIDER_SPECS`; CLI wrappers for `claude` and `codex` named in `kamma/tech.md` |
| Text-to-speech credits | ElevenLabs and Bhashini keys; `audio/bhashini/` (folded into the AI choice on the form) |
| Computer or hardware | `docs/thanks.md`: laptops given in 2018 and 2024. Builds need large memory: PDF export peaks near 3.5 GB (`kamma/tech.md`) |
| Internet connection or data | `docs/thanks.md`: two people credited for the internet connection |
| Build or CI time | `.github/workflows/`: five workflows, `ubuntu-latest` and one `macos-latest` runner; secrets `DPD_DEPLOY_KEY`, `GH_PAT` |
| Email or mailing list service | the mailing list form `forms.gle/gJ7ouhJriYREPm1s8` linked from the web app and GoldenDict; the monthly newsletter |
| Other | catch-all |

Not found in the repo, so left out of the form: app store developer accounts
(the Flutter app is a separate repo, not read for this), cloud storage or
backup, money.

## Current behaviour (verified by reading the files, 2026-10-22)

- Docs website is static: mkdocs (`mkdocs.yaml`), built by
  `.github/workflows/static.yml` and copied to the organisation repo. No server.
- Contributing pages: `docs/contributing/index.md`, `pali.md`, `code.md`. Nav in
  `mkdocs.yaml` lines 61-64.
- `docs/contributing/pali.md` ends with "get in touch by email". `code.md` has
  the same mailto. `docs/contact.md` line 9 asks people to email to contribute.
- `docs/index.md` line 23 links "get in touch" to the contact page.
- `README.md` line 9 links the three contributing pages.
- `CONTRIBUTING.md` "Ways to Contribute" (about lines 68-100) says "get in touch
  by email" for substantial Pāḷi help, and has an email line near the top.
- Web app: `exporter/webapp/templates/dpd_headword.html` about line 1623, a
  "Get involved" link that is a mailto. The browser extension shows this HTML
  (stated in the feedback sync spec; not re-verified here).
- GoldenDict and MDict: `exporter/goldendict/javascript/feedback_template.js`
  about lines 50-58, two mailto links: "Help with coding", "Help with Pāḷi".
- Flutter app (separate repo, `~/MyFiles/3_Active/dpd-flutter-app`):
  `lib/widgets/feedback_section.dart` line 119, "Get involved", opens
  `_getInvolvedUrl`. The value of that constant was not read.
- No code in this repo sends email.

## Vinaya check (2026-10-22)

Source: the vault essay `~/MyFiles/Obsidian/Vicaya/2026-10-22 - vinaya-offerings-to-bhikkhus.md`
(read in full). The project is maintained by Buddhist monastics who do not
accept money. What the essay says, and what it means for the form:

1. **Money is never accepted, sought or approved.** NP18 forbids taking it,
   having it taken, or consenting when it is deposited "for the venerable";
   SN42.10 and the Meṇḍaka passage say gold and silver are not to be accepted
   *or sought*. The form must not invite, name or give examples of money **sent to the
   project**. A budget for the donor's own direct purchase is allowed (see the
   2026-10-22 decision below). Done:
   the "worth" question and its "$20 a month" and "$50 once" examples are gone.
   Question 4 now asks "How much can you offer?" with time examples only. The
   form description says the maintainers do not deal with money and accept
   only time, energy, resources and pre-bought services, and do not accept
   donations (the user's wording).
2. **"Money" is defined by function.** The Samantapāsādikā on NP18 counts
   whatever passes as currency in any region, even bone, leather or seeds. Gift
   cards, vouchers, prepaid credit and cryptocurrency may fall under this. The
   essay does not decide it. **Decided by the user, 2026-10-22:** only
   pre-bought services are accepted (the donor pays the provider in advance),
   and donations are not accepted. A transfer of stored value to the
   maintainers is a donation, so it is out. **Clarified by the user,
   2026-10-22:** the donor never gives money. The donor is given a login to the
   service and buys the subscription directly from the provider, and the form
   asks the most they would like to spend. Money goes donor to provider, never
   to the maintainers. The Resources section text must say so. **Decided by the user,
   2026-10-22:** a single-purpose prepaid top-up (airtime, AI credit) is not money,
   because it buys only that one thing and cannot be spent at a shop. This fits
   the Samantapāsādikā's test on NP18: *rajata* is whatever passes in commerce as
   currency (*vohāraṃ gacchati*). The essay does not state this case; it is an
   inference from that test. The line to keep: closed-loop credit (one provider,
   not transferable) is fine; open-loop value (store gift cards, general
   vouchers, cryptocurrency, mobile money) is out.
3. **Hinting is asking.** *Viññatti* is *yācanā*, and roundabout speech
   (*parikathā*) and suggestion (*obhāsa*) count as asking. Asking is allowed
   only in a closed list of cases (proper time, relatives, those who have
   invited, another's sake, one's own wealth). A form text that lists what the
   project needs, such as a server or AI credits, could be hinting. Done: the
   examples are removed from the form.
   **Decided by the user, 2026-10-22, overriding the reading above:** a monk who
   needs a service may ask for it. SN42.10: one who needs grass asks for grass,
   wood for wood, a horse for a horse, a man for a man. These are goods and
   services, not money. So the page and the form may name needs such as a
   server or a subscription. Money is still never named, sought or accepted.
4. **Steering a donor is the same risk.** The user plans to steer offers in the
   right direction. The essay's permitted wording is to inform "the one who
   makes things allowable" (a lay steward, *kappiyakāraka*): "we have this and
   we need this and that" (NP20, non-offence clause). **Open: user decision.**
   Option: a lay helper reads the offers and does the steering, and the
   notification emails go to that person.
5. **The donor sets the scope.** In the essay's invitation cases, asking is
   allowed only within what the donor offered ("give of what belongs to them").
   The "How much can you offer?" answer plays that role. This is an analogy
   from robes and requisites. The essay does not cover software or services.
6. **Uncovered cases.** The essay lists as a gap the four great references
   (*mahāpadesā*, Vinaya 02 §305) for a case no rule covers. Servers, domain
   names and subscriptions are not classified in it. **Decided by the user,
   2026-10-22:** the project accepts only time, energy, resources and
   pre-bought services. Donations are not accepted. So resource offers stay on
   the form.
7. **Labour is likely fine.** SN42.10 "a man by one who needs a man". The essay
   reads this as a person's labour or service, and marks the reading as an
   inference from the surrounding rules, not as stated text.
8. **Replies.** When someone offers money anyway, the Vinaya reply to a
   messenger is "we do not accept money; we accept what is allowable at the
   proper time" (NP10: *na kho mayaṃ, āvuso, cīvaracetāpannaṃ paṭiggaṇhāma …*).
   A reply email template can follow that shape. Not built here.

## Assumptions & uncertainties

- Google Forms can be embedded in an iframe on the mkdocs page. Unverified until
  the form link exists. Fallback: a plain link that opens the form in a new tab.
- "Send responders a copy: Always" needs the email question to be a normal
  short-answer question with an email check. Assumed fine; the user knows the
  settings screen.
- Consent is a sentence in the form description, not a tick box. Decided
  2026-10-22 to keep the form simple.
- The Flutter app's `_getInvolvedUrl` may already point at the docs. If it does,
  no change is needed there.
- A test fixture for the GoldenDict export help text contains Google Form links.
  It may or may not contain the feedback block. Check before editing the
  template.
- Whether `docs/thanks.md` is generated from `shared_data/reference/thanks.tsv`
  (a test file `tests/tools/test_docs_update_thanks_fixtures.json` suggests it).
  Not needed in this thread; recorded for the follow-up.

## Constraints

- Google Form only. No server, no JS, no new dependency.
- Do not write passwords or logins into the form. The form text says so.
- Links only change, with one exception (user decision, 2026-10-22): no text may
  tell people to email or "get in touch" about helping or offering. Those
  phrases became "please use the form" in the web app, GoldenDict, the Flutter
  app and the docs home page. Old newsletter posts are a record and stay as
  they are. The feedback sync thread owns all other wording.
- The form stores other people's names and emails. The form description says
  so. The response sheet stays private.
- Keep the form simple for the person. Do not add questions without the user's
  say-so.

## How we'll know it's done

- The live form is embedded on the contributing overview page and sends both
  emails on a test submission.
- `uv run mkdocs build` finishes with no new warnings.
- Every surface in the list above links to the overview page, and no mailto
  "get involved" link remains in the web app, GoldenDict, `docs/contributing/`
  or `docs/contact.md`.
- Related tests pass.
- The live form passes the Vinaya check: no money wording or examples, the
  no-money line is in the description. Naming a service need (a server, a
  subscription) is allowed.

## What's not included

- Expiry reminder emails (add later with an Apps Script timer, once the sheet
  has real data).
- A resource-type list, a duration date box, a country question, money, and a
  public-thanks question. All dropped on 2026-10-22 to keep the form simple.
- Merging or rewording the "Get involved" blocks (belongs to the feedback
  section sync thread).
- Moving accepted Pāḷi helpers into the contributor setup (#215).
- Feeding accepted offers into the thanks page.
- A custom website form with JS, or any server-side code.
