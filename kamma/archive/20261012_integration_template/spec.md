# Spec: "Add Your App" integration template page

## Goal
Add a new docs page as the last item of the Software Integrations section. It is a
fill-in template for app developers who integrate DPD. Each heading asks one question,
with plain text underneath saying what to write. From the filled-in answers, the DPD
team writes that app's integration page.

App developers are often poor at marketing their own app, so the questions must draw the
selling points out of them (what it does, who it is for, what sets it apart).

## Facts (read from source, 2026-10-12)
- Nav lives in `mkdocs.yaml` lines 46-53, section `Software Integrations`. Last entry is
  `Tipitakapali.org: "integrations/tipitakapali.md"`.
- Existing pages: `dhamma_gift.md`, `simsapa.md`, `sutta_central.md`, `tbw.md`, `tpr.md`,
  `tipitakapali.md`, `index.md` in `docs/integrations/`.
- What those pages contain, and so what the template must ask for:
  - one-paragraph intro: what the app is, who makes it (TPR names its developer and manager)
  - website link, info/install page link, GitHub releases page (TPR)
  - platforms (TPR: Windows, Mac, Linux, iOS, Android; Dhamma.gift: browser extensions,
    Telegram bot, PWA; TBW: offline download)
  - feature list (Simsapa, Dhamma.gift)
  - which version of DPD is used (light / full / built-in / several modes)
  - how a user looks up a word (click, mouse-over, popup buttons)
  - numbered step-by-step to turn DPD on or change mode, one screenshot per step
  - how DPD gets updated (Simsapa automatic; TPR extension download, beta version)
  - other languages (Dhamma.gift Russian)
  - extra features beside DPD (TipitakaPali AI) and warnings about them
  - where to report bugs / contact
- Screenshot convention: `docs/pics/<app>/<name>_light.png` + `<name>_dark.png`, shown with
  `#only-light` / `#only-dark` suffixes.
- Markdown extensions available: `attr_list`, pymdownx highlight/inlinehilite/snippets/
  superfences. No admonitions, so the page uses plain headings and text only.
- Contact email (from `docs/contact.md`): digitalpalidictionary@gmail.com.

## Scope
- New file `docs/integrations/add_your_app.md`.
- One nav line added as the last item under Software Integrations in `mkdocs.yaml`.

## Out of scope
- Any generator that turns a filled template into a page. The user named it as the later
  purpose; it is not built here.
- Changes to existing integration pages.
- Commits (user asked: don't commit).

## Acceptance
- Page appears last in the Software Integrations nav.
- Covers every item the user listed plus the items found in existing pages above.
- `mkdocs build` succeeds with no new warnings for this page.
