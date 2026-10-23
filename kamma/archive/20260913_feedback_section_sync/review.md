## Thread
- **ID:** 20260913_feedback_section_sync
- **Objective:** Align the wording of the feedback section across website, GoldenDict and app, and add cross-reference comments.

## Files Changed
- `exporter/webapp/templates/dpd_headword.html` — dropped "Have something to add?", "Get involved" became "Contribute to DPD", added a Jinja cross-reference comment.
- `exporter/goldendict/javascript/feedback_template.js` — "Read the docs" wording, one "Contribute to DPD" link replaces two, added a cross-reference comment.
- `dpd-flutter-app/lib/widgets/feedback_section.dart` (separate repo) — dropped "Have something to add?", "Contribute to DPD", constant renamed to `_contributeUrl`, added a cross-reference comment.
- `kamma/threads/20260913_feedback_section_sync/spec.md`, `plan.md` — spec and plan.

## Findings
| # | Severity | Location | What | Why | Fix |
|---|----------|----------|------|-----|-----|
| 1 | minor | `spec.md` current state | Said "Add a missing word" is identical on all three. The app omits the spreadsheet sentence. | Spec stated a false fact. Code unaffected. | Spec corrected; gap recorded as open. |
| 2 | minor | `spec.md` current state | Said "How to cite" is identical on all three. The app has no such link. | Same. | Spec corrected; gap recorded as open. |

## Fixes Applied
- Spec "Current state" corrected for findings 1 and 2. Both gaps are listed as not agreed to align.

## Test Evidence
- `node --check feedback_template.js` (scope: that file's syntax only) → pass
- Jinja `get_template('dpd_headword.html')` (scope: template parses; not rendered with data) → pass
- `dart analyze lib/widgets/feedback_section.dart` (scope: that one file) → "No issues found!"
- `curl` of the live contributing page (scope: anchor exists) → `id="offer-your-help"` present
- `rg --hidden` for old wording in both repos (scope: whole repos minus archive/build/graphify-out) → only the changed files and kamma notes; no test or fixture holds old wording
- DeepSeek review, `deepseek-v4-pro`, thinking max, read-only (scope: spec, three diffs, full files, neighbouring files) → Approve, 2 minor findings above

## Not Verified
- The website template was not rendered with real data, and the app was not run.
- No project lint (ruff/pyright, pyrefly) applies to these JS, Jinja and Dart files; none was run beyond the checks above.
- CodeRabbit was not run. The user chose the DeepSeek review instead.
- The Sonnet subagent review was stopped by the user before it reported.

## Verdict
PASSED
- Review date: 2026-10-23
- Reviewer: DeepSeek v4 pro via pi, validated by Claude
