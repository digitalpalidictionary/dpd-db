# Spec: add sutamaya to the software integrations

**Thread:** 20261025_sutamaya_integration · **GitHub issue:** none given

## Overview
Add a new page for the sutamaya web app to the DPD integrations docs. List it in the
nav, the README and the newsletter links, in alphabetical order.

Follows `docs/integrations/add_your_app.md`. Style follows `docs/integrations/epitaka.md`:
short, plain, no hype.

## What it should do
- New page `docs/integrations/sutamaya.md`.
- `mkdocs.yaml` nav: new entry between "Simsapa Dhamma Reader" and "Sutta Central Website"
  ("sutam" sorts before "sutta"). Nav label: "Sutamaya".
- `README.md` Integrations list: one line before "Sutta Central", with a Docs link.
- `newsletter/useful_links.md` Websites list: one line before "SuttaCentral Voice".
- Screenshots (light and dark, as the template asks) in `docs/pics/sutamaya/`, taken
  from the live app. Naming: `main-view`, `lookup`, `settings`, each as `_light`/`_dark`.

## Page content (verified facts)
- What it is: an offline-first reader and study app for the Pali suttas. Pāḷi sits
  beside Bhikkhu Sujato's English. Another way to read SuttaCentral texts.
- Where: app.sutamaya.org (app), sutamaya.org (site). Runs in a browser on phone,
  tablet, desktop. Installs from the browser as a web app (PWA, per repo docs).
- Texts: DN, MN, SN, AN and six Khuddaka books (Snp, Dhp, Ud, Iti, Thag, Thig),
  4,041 documents (repo `data/README.md`). Source: SuttaCentral (sc-data), English by
  Bhikkhu Sujato, CC0, with editorial changes listed in the repo's
  `docs/translation-changes.md`.
- DPD use: tap a Pāḷi word, a dock opens at the bottom. It lists each DPD entry for
  the word: headword, part of speech, short meaning, literal meaning, root and
  construction. Arrows step to the previous/next word. The dictionary is cut down
  to the words in this corpus. Seen live: tapping "bhagavā" in MN10 gave 3 entries.
- Pāḷi setting: "On tap" or "Always" (verified live; "Always" shows Pāḷi under each
  English line).
- Style settings (verified live): theme Light/Dark/Sepia, text size, line height,
  six typefaces, highlights, translator's notes, segment numbers.
- Features (from site and repo docs): browse by collection; search by reference, title
  or Pāḷi; highlights in three colours; notes; tags; lists and folders; recent history;
  keyboard shortcuts; optional sign-in (Apple, Google, email code) to sync; offline
  reading, Settings can download the whole canon and dictionary.
- Cost: "freely available". No price is stated anywhere. Do NOT write "free".
- Code: github.com/gbbr/sutamaya.org, MIT licence. Dictionary derives from DPD
  (CC BY-NC-SA 4.0). Bug reports: GitHub issues. Contact: metta@sutamaya.org.
- Maker: not named on the site. Name only the GitHub account "gbbr".
- Walkthrough: link both YouTube videos — `teNMmoVf5Y0` (4-minute web walkthrough,
  no voiceover) and `kV0pCRQRSmk` ("sutamaya mobile app introduction", has audio).
- Updating DPD: the maker rebuilds the dictionary from a DPD release. No automatic
  update. Say only that, with no promise about timing.

## Assumptions & uncertainties
- No iOS/Android store link exists. The repo has native builds (`native-release.json`:
  iOS build 5, Android build 2) and lists store submission as outstanding work. Page
  covers the web app only and leaves an HTML comment for store links, as `epitaka.md`
  does. Re-check the repo and site for a store link just before writing.
- Which DPD version is built in is not stated anywhere. Page will not claim one.
- "On tap" revealing a line's Pāḷi is from the repo docs. It was not seen working in
  the browser (clicking a paragraph in a headless run showed nothing). Verify during
  the work.
- Both videos could not be read: the first has no voiceover, and YouTube blocked the
  subtitle download for the second. Use only the links and titles.
- Sign-in options and the offline download come from the repo docs, not tested live.
- The maker has not been contacted. The template says the page is sent to the maker to
  check before it goes live. That email is the user's decision, not part of this thread.
- The user spelled the name "suttamaya". The site, repo and app all spell it "sutamaya".
  The page uses "sutamaya" (the maker's own spelling).

## Constraints
- Alphabetical order everywhere. Plain language, no hype, no money talk.
- Every sentence on the page must come from the facts above (public page rule).
- Run no git command. No commit. No GitHub writes.
- Screenshots go to the scratchpad first, then `docs/pics/sutamaya/`.
- Downloads use `--limit-rate`.

## How we'll know it's done
- Page renders in the docs build with the nav entry between Simsapa and Sutta Central.
- All links on the page return 200.
- Screenshots show in light and dark mode.
- README and newsletter lines sit in alphabetical position.

## What's not included
- Store links, a claim of a store app, a DPD version number.
- Emailing the maker. Changes to the app or to DPD exports.
