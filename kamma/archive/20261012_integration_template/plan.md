# Plan: "Add Your App" integration template page

- [x] Write `docs/integrations/add_your_app.md` with headings grouped as: basics, platforms
      and install, about the app, how DPD is used, screenshots, anything else, how to send.
      → verify: every item from the user's list and from spec "Facts" has a heading.
- [x] Add `Add Your App: "integrations/add_your_app.md"` as the last nav item under
      Software Integrations in `mkdocs.yaml`.
      → verify: `uv run mkdocs build -d <scratchpad>` succeeds, no warnings for the new page.
- [x] Hand to user for review. Reviewed by subagent, four findings fixed (see review.md).

## Notes
- 2026-10-12: page written, nav added. `mkdocs build` exit 0; only warnings are the pre-existing Material team notice and README.md/index.md conflict. In-page anchors #screenshots, #turning-dpd-on, #getting-the-latest-dpd resolve.
- 2026-10-12: user asked for an "easy way" section at the top: tell developers to let an AI agent fill in the form. Added "The Easy Way" with a paste-in prompt pointing at https://digitalpalidictionary.github.io/integrations/add_your_app/ (URL built from `extra.alternate` English link + mkdocs directory URLs; live only once deployed).
