# Project Rules

These rules are specific to the dpd-db project. Global rules (security, python type hints, debugging, etc.) are in `~/.agents/AGENTS.md`.

## Project Overview

This project converts Mako templates to Jinja2 templates for the Digital Pali Dictionary.

## Flet
- When answering questions about Flet refer to the /resources/flet-docs folder.

## Tree
- On a weekly basis, or anytime the project tree changes, check that the project tree matches the tree specified in @docs/technical/project_folder_structure.md

## Database model
- On a weekly basis, or anytime the database model changes, check that the database model in `db/models.py` matches the docs in `docs/technical/dpd_headwords_table.md`

## GitHub
- Unless otherwise specified the repository in question is https://github.com/digitalpalidictionary/dpd-db.
- DO NOT add or commit to GitHub, unless specifically instructed to do so.

### Solve
- "Solve" means read the specified GitHub issue using get_issue and offer solutions. Don't think about it, don't ask questions, just read it.
- Ask the user to open the necessary files that you need.
- Is this a straightforward solution, or does it need to be solved at a higher level?
- Show code snippets of suggested changes.

### Commit
- Only ever commit when asked. NEVER unasked.
- "Commit" means commit the changed files using execute_command.
- Use this format, all in lowercase. #issue number area: change1, change2 . E.g. #67 webapp: updated css, fixed overflow

## Update Gemini CLI
```bash
npm install -g @google/gemini-cli@latest
```
