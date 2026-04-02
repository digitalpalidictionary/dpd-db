---
name: dpd-newsletter
description: Generate the monthly DPD newsletter for the current release. Use when the user asks to write, draft, or generate a newsletter, monthly update, or release email for the Digital Pāḷi Dictionary project.
---

Generate the monthly DPD newsletter for the current release.

## Steps

### Step 1 — Gather data (use subagents in parallel)

Launch ALL of the following as **parallel subagents** using the Agent tool in a single message. Each agent runs independently and reports back:

1. **Agent: "get release date and commits"** — run `gh release list --exclude-drafts --exclude-pre-releases --limit 1` to get the latest official release date, then `git log --oneline --since="<that-date>"` (use head and tail) to get all commits since. Return both the release date and the full commit list.

2. **Agent: "run changelog script"** — run `uv run python tools/docs_changelog_and_release_notes.py` and return the full output (GitHub issues closed, dictionary stats, new words count, Pass1/Pass2 progress).

3. **Agent: "check flutter app"** — check `../dpd-flutter-app/` for new releases or notable changes since the last newsletter. Look at recent git log, releases, and any notable files.

Also in the same message, directly:

4. **Read** `docs/newsletters.md` — for tone, structure, sign-off style, and previous stats to compare against.

### Step 2 — Analyse and compare

- **Compare stats** against previous newsletter — diff the dictionary data numbers (headwords, roots, compounds, inflections, etc.) and highlight growth (e.g. "+2 000 headwords since last month")
- **Extract new words count** from the changelog script output (it prints `[N]` at the end of the new words line)
- **Group commits** into sections:
   - Major announcements (new platforms, big features)
   - Other dictionaries (CPD, MW, Apte, etc.)
   - Quality-of-life improvements (small GitHub issues, UI tweaks, bug fixes)
   - Data progress (which nikāya books completed, Pass1/Pass2 status from changelog output)
   - Corrections and additions (always include this section)

### Step 3 — Ask the user

Call AskUserQuestion **multiple times in a single message** so all questions queue up and the user can answer them in rapid succession:

1. Any major DPD announcements to highlight this month?
2. Any nikāya progress updates beyond what the changelog script shows?
3. Any exciting developments in the Pāḷi field in general worth sharing with the community? (e.g. new apps, websites, publications, conferences, other projects)
4. Any specific people to thank?
5. Sign-off location? (check the previous newsletter's sign-off and suggest it as the default, e.g. "from India last time — same again?")
6. Suggest a subject line based on the pattern from previous newsletters (e.g. "Digital Pāḷi Dictionary update (Month Year)") — confirm or let the user adjust.

### Step 4 — Write and preview

- **Write the newsletter as HTML** to `newsletter_<date>.html` in the project root. Gmail doesn't render markdown, so use `<b>`, `<br>`, `<ul>/<li>`, `<a href>`, and `<i>` tags directly.
- **Preview** — run `xdg-open newsletter_<date>.html` so the user can see how it looks before pasting into Gmail.

## Format Reference

- Wrap the entire newsletter in a `<div style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.6;">`
- Use `<p style="margin: 0 0 10px 0;">` for all paragraphs (not `<br><br>`) to match Gmail's default spacing
- Title: `<b>Digital Pāḷi Dictionary update (Month Year)</b>`
- Greeting: `Dear Venerable monastics, professors, and Pāḷi enthusiasts,`
- Each section: `<b>- Section Title</b>` followed by description
- Bullet lists using `<ul>/<li>` for small improvements and download links
- Dictionary data stats from the changelog output, with growth numbers compared to last month
- Pass1/Pass2 progress lines from the changelog output
- Sign-off: `With much <i>mettā</i> from <location>,`

## Important Notes

- ALWAYS use proper Pāḷi diacritics everywhere (Pāḷi, Nikāya, Saṃyutta, Devanāgarī, mettā, etc.).
- Do NOT add the newsletter to `docs/newsletters.md` — that is auto-built from the Gmail send.
- Do NOT create a markdown version — only the HTML file is needed.
- The changelog script must be run first to get accurate stats.
- Group small GitHub issues into "Small Quality-of-Life Improvements" rather than listing each separately.
- Include the standard download links section at the end, pulling the latest URLs from previous newsletters. Check if any new download formats have been added.
