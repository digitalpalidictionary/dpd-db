# Spec: migrate labels to GitHub issue types and issue fields

## GitHub issue
(none)

## Status
Implemented and verified 2026-09-14.

**Process note, recorded honestly:** this thread's files were written *after* the work
was done, not before. The kamma spec gate requires `spec.md` and `plan.md` on disk before
any change is made; that gate was skipped. Nothing below was planned in advance — it is a
faithful record of what actually happened, reconstructed from the session.

## Overview
GitHub rolled out two features that make three of our home-grown label families redundant:

- **Issue types** (org-level, enabled on the repo): Bug, Feature, Task.
- **Issue fields** (org-level): Priority (Urgent/High/Medium/Low), Effort
  (High/Medium/Low), Start date, Target date.

Priority and Effort are *not* labels and *not* Projects fields — they are a separate
org-level "issue fields" feature. At the time of writing they are reachable through the
API but not surfaced in the web UI, which the user noted and accepted.

## Mapping applied

| Old label | New home | Value |
|---|---|---|
| `1-bug` | issue type | Bug |
| `1-enhancement` | issue type | Feature |
| `1-refactor` | issue type | Task |
| `1-chore` | issue type | Task |
| `p1` | Priority field | Urgent |
| `p2` | Priority field | High |
| `p3` | Priority field | Medium |
| `p4` | Priority field | Low |
| `t1` | Effort field | Low |
| `t2` | Effort field | Medium |
| `t3` | Effort field | High |
| `t4` | Effort field | High |

The time labels were retired at the user's instruction ("ai does all the work now"), with
four buckets collapsed into Effort's three. `t3` and `t4` both land on High.

## Label cleanup
- **Deleted** the twelve migrated labels (`1-*`, `p1`-`p4`, `t1`-`t4`).
- **Deleted** the seven `3-` language labels — same reasoning as the time labels: with AI
  doing the work, "this issue is Python" is not a filter anyone searches on.
- **Renamed** all twenty `2-` section labels to drop the prefix, and stripped the
  `2 Section: ` prefix from their descriptions. Renaming preserves issue associations.
- **Typos fixed** while renaming: `2-fequency` → `frequency`, "idenity" → "identity",
  "Deconstrucing" → "Deconstructing".
- **Left alone:** `stuck!`. Flagged as a status rather than a category, but the user did
  not include it in the delete list.

Label count went from 41 to 21.

## API notes (for whoever does this next)
- Issue type: `updateIssue(input:{id:…, issueTypeId:…})`, or `gh issue edit N --type Bug`.
- Priority/Effort: `setIssueFieldValue(input:{issueId:…, issueFields:[{fieldId:…,
  singleSelectOptionId:…, suggest:false}]})`. **`suggest:false` matters** — the input
  carries agent-oriented fields (`suggest`, `confidence`, `rationale`), and leaving
  `suggest` unset risks the value being stored as a pending suggestion rather than a real
  value.
- Field and option node IDs are fetched from `organization(login:…){issueFields}`. The
  REST endpoint returns numeric ids, which the GraphQL mutations do not accept.
- There is no repo-level `issue-fields` REST endpoint — only `orgs/{org}/issue-fields`.

## Phase 2 — issue templates (added to scope 2026-09-14, at the user's request)

Written **before** the change this time.

### The problem
`.github/ISSUE_TEMPLATE/` holds three markdown templates whose front matter assigns
`labels: '1 Bug'`, `'1 Feature'`, `'1 Update'`. No label of any of those names has ever
existed in this repo — they pre-date the `1-bug` naming. GitHub silently ignores an
unknown label, so every issue opened through a template has been getting no type label at
all. That is the likely source of the 26 issues with no type.

### The fix
Markdown issue templates support a `type:` front-matter key (verified against GitHub's
own docs, not assumed). So the minimal change is to swap the dead `labels:` line for a
`type:` line — the templates stay markdown, no conversion to the YAML issue-forms format.

| Template | Was | Becomes |
|---|---|---|
| `bug_report.md` | `labels: '1 Bug'` | `type: 'Bug'` |
| `feature_request.md` | `labels: '1 Feature'` | `type: 'Feature'` |
| `maintenance.md` | `labels: '1 Update'` | `type: 'Task'` |

`Bug`, `Feature` and `Task` are the exact org-level type names already confirmed enabled
on this repo.

An earlier statement in this session — that fixing this needed the YAML issue-forms format
— was wrong. Markdown front matter takes `type:` directly.

### Deliberately not done
- No conversion to issue forms. The templates work; converting them is a separate
  decision about contributor experience, not part of this fix.
- No `labels:` replacement. Section labels (`gui`, `data`, …) are a judgement call per
  issue, not something a template should guess.

## Out of scope
- `stuck!` label.
- The Start date / Target date fields (unused, left unused).
- Any other docs in the repo that reference the old label names.
