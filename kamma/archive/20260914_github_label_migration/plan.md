# Plan: migrate labels to GitHub issue types and issue fields

## Status
All tasks complete, 2026-09-14. Written retrospectively — see the process note in `spec.md`.

## Tasks

- [x] Establish what GitHub actually offers
  → verify: org `issueTypes` returns Bug/Feature/Task, enabled; `orgs/{org}/issue-fields`
    returns Priority, Effort, Start date, Target date. Confirmed Priority is an issue
    *field*, not a label and not a Projects field — `Issue` has no `priority` in the
    GraphQL schema.
- [x] Count what would migrate
  → verify: 213 issues, 28 open; 187 carry a type label, 115 a priority label, 111 a time
    label.
- [x] Snapshot every issue's labels, type and field values before touching anything
  → verify: `artifacts/snapshot_00_before_migration.json`, 213 issues.
- [x] Write and **prove** a rollback path
  → verify: issue 156 migrated to Feature/High/Low, then restored via `restore.py` to
    type `None` / no field values, confirmed by re-reading the API. Rollback is tested,
    not merely written.
- [x] Migrate all 213 issues
  → verify: script reported 187 touched; see review.md for the independent check.
- [x] Delete the twelve migrated labels (`1-*`, `p1`-`p4`, `t1`-`t4`)
  → verify: `gh label list` shows none remaining from those families.
- [x] Delete the seven `3-` language labels
  → verify: zero issues carry a `3-` label afterwards.
- [x] Rename the twenty `2-` labels to drop the prefix, fixing three typos
  → verify: per-issue before/after comparison, zero mismatches.

## Phase 2 tasks — issue templates

- [x] Confirm markdown templates accept a `type:` front-matter key
  → verify: GitHub docs for both markdown templates and issue forms; `type` is listed as
    a supported front-matter key for markdown templates.
- [x] Swap the dead `labels:` line for `type:` in all three templates
  → verify: front matter of each file reads `type: 'Bug' | 'Feature' | 'Task'`, and no
    `labels:` line referencing a non-existent label remains.
- [x] Confirm the three type names match the org's enabled issue types exactly
  → verify: compare against `organization{issueTypes}` — Bug, Feature, Task.
- [x] Confirm nothing else in `.github/` references the dead label names
  → verify: grep `.github/` for `1 Bug`, `1 Feature`, `1 Update`.

**Not verifiable from here:** whether GitHub actually applies the type on issue creation.
That needs a real issue opened through a template, which would mean creating a throwaway
issue in the live tracker. Flag to the user rather than doing it unasked.

## Deviations from the original request
- The user's first framing was "priority can replace my p1-4 labels" as if Priority were a
  label. It is not — it is an org-level issue field. The mapping was unaffected but the
  implementation route changed entirely (GraphQL mutation, not `gh label`).
- Effort was added to scope mid-thread when the user chose to retire the time labels
  rather than keep them.
- `stuck!` was proposed for deletion and then not included in the user's list. Left alone.
