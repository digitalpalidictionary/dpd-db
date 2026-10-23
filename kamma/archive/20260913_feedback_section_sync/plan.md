# Plan: sync the feedback sections

## Status
Done 2026-10-23. Reviewed and passed.

## Phase 1: before editing
- [x] Read the contributing page heading in `docs/contributing/index.md` and confirm the
  anchor for "Offer your help" by building or reading the docs output. Do not guess the
  slug.
- [x] Grep both repos (`rg --hidden`) for tests or fixtures that hold the old wording
  ("Have something to add", "Help with coding", "Help with Pāḷi", "Visit the DPD docs
  website", "Get involved"). List every hit.

## Phase 2: GoldenDict (`exporter/goldendict/javascript/feedback_template.js`)
- [x] Rename the docs link to "Read the docs" and use the agreed sentence.
- [x] Replace "Help with coding" and "Help with Pāḷi" with one "Contribute to DPD" link
  at the agreed target.
- [x] Keep "Get updated" as it is.
- [x] Add the cross-reference comment.

## Phase 3: website (`exporter/webapp/templates/dpd_headword.html`)
- [x] Drop "Have something to add?" from "Correct a mistake".
- [x] Replace "Get involved" with "Contribute to DPD" and the agreed sentence and target.
- [x] Add the cross-reference comment, with the "Get updated is GoldenDict-only" note.

## Phase 4: app (`dpd-flutter-app/lib/widgets/feedback_section.dart`)
- [x] Drop "Have something to add?" from "Correct a mistake".
- [x] Replace "Get involved" with "Contribute to DPD" and the agreed sentence and target.
  Rename the URL constant to match.
- [x] Add the cross-reference comment, with the "Get updated is GoldenDict-only" note.
- [x] This is a separate repo. The user commits it there.

## Phase 5: check
- [x] Re-read the three final texts side by side. Confirm each of the four items matches
  the spec word for word.
- [x] Lint each touched file per the project gate. JavaScript, Jinja and Dart files: run
  the repo's own checker for each, found by reading its config, not from memory.
- [x] Update any test from Phase 1 that holds old wording.
- [x] Run `graphify update .` in dpd-db after the code edits.

## Notes
- Do not run git commands. The user commits.
- Chat replies stay free of paths. Paths live in this file.
