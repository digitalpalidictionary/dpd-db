# Review: contributions form (2026-10-22)

Two independent reviews ran in parallel on the finished work. No edits were made
while they ran.

**Verdict: PASSED**

## Files Changed

- `CONTRIBUTING.md`, `README.md`, `mkdocs.yaml`, `kamma/tech.md`
- `docs/contact.md`, `docs/index.md`
- `docs/contributing/code.md`, `docs/contributing/index.md`, `docs/contributing/pali.md`, `docs/contributing/resources.md` (new)
- `exporter/goldendict/javascript/feedback_template.js`
- `exporter/webapp/templates/dpd_headword.html`
- Flutter repo (not staged): `lib/widgets/feedback_section.dart`

## Reviewers

- **GLM** (`glm-5.3`, maximum reasoning, read-only). Input: the diff of this
  thread's files, the Flutter diff, and the new files.
- **CodeRabbit** (`coderabbit review --agent --uncommitted --include-untracked
  --fresh`). It covered the whole working tree, including other threads' files.

## Findings and outcome

| # | Source | Finding | Outcome |
|---|---|---|---|
| 1 | GLM, minor | GoldenDict "Help with Pāḷi" text said "please make email contact" next to a link to the form. | Real. Fixed. The user then ruled that no text may say to email or get in touch about helping. All such lines became "please use the form". |
| 2 | GLM, minor | Web app "Get involved" link lacked `target="_blank"`, unlike every sibling link. | Real. Fixed. Web app tests pass. |
| 3 | CodeRabbit, major | Pāḷi and Code branches of the form do not ask how much or how long. | Skipped. The user chose to keep the form simple. The spec forbids adding questions without their say-so. |
| 4-6 | CodeRabbit | Three findings in `kamma/threads/20261007_temp_server_test/plan.md` (rsync command, submodule path, server cleanup). | Out of scope. Another thread's file. Not touched. |

GLM verdict: approve. It confirmed the anchor, the nav entry, the embed URL, the
fixture check and the Vinaya wording (money appears only as a refusal on the
Resources page).

## Checks after the fixes

- `uv run pytest tests/exporter/webapp tests/exporter/goldendict`: 212 passed.
- `uv run mkdocs build`: no new warnings. One warning existed before this
  thread: "Excluding 'README.md' from the site because it conflicts with
  'index.md'".
- Live form read on 2026-10-22: first page and Resources section pass the
  money-wording check. The user tested a real offer and it worked.
- The full test suite was not run. The change is links, docs and one template.

## Known and left open

- The Flutter app repo holds two changed lines. They are not staged.
- Old newsletter posts still say "get in touch". They are a record.
- Follow-ups are listed in plan task 4.3.
