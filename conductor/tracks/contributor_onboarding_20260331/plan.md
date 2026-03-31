# Contributor Onboarding Hardening & Contributor Mode Implementation Plan

### Phase 1: Harden setup and update reliability

- [ ] Task: Add archive-aware database release handling to onboarding setup
    - [ ] Inspect `scripts/onboarding/contributor_setup.py` and identify the current release asset selection and download flow
    - [ ] Inspect `tests/scripts/onboarding/test_contributor_setup.py` and locate the existing release asset tests
    - [ ] Write failing tests for selecting the correct database asset when the latest release contains `dpd.db.tar.bz2`
    - [ ] Write failing tests for producing a usable `dpd.db` after archive download and extraction
    - [ ] Write failing tests for extraction failure behavior and returned error outcome
    - [ ] Implement archive-aware asset selection in `scripts/onboarding/contributor_setup.py`
    - [ ] Implement archive extraction logic in `scripts/onboarding/contributor_setup.py` so compressed assets produce `dpd.db` in the project root
    - [ ] Ensure temporary or partially written files are cleaned up on failure
    - [ ] Run the targeted onboarding setup tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Make setup report real failures for required submodule initialization
    - [ ] Write failing tests for required submodule initialization failure reporting in `tests/scripts/onboarding/test_contributor_setup.py`
    - [ ] Refactor `scripts/onboarding/contributor_setup.py` so required submodule commands return success/failure details
    - [ ] Stop setup and show a contributor-friendly error when a required submodule fails
    - [ ] Run the targeted onboarding setup tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Harden contributor update flow against archive and failure cases
    - [ ] Inspect `scripts/onboarding/contributor_update.py` and `tests/scripts/onboarding/test_contributor_update.py`
    - [ ] Write failing tests for update flow handling of archive-based database releases
    - [ ] Write failing tests for update flow messaging when download, extraction, or backup fails
    - [ ] Reuse or extract shared database release handling logic between setup and update where it keeps the code simpler
    - [ ] Update `scripts/onboarding/contributor_update.py` to use the hardened database handling path
    - [ ] Run the targeted contributor update tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Harden setup and update reliability' (Protocol in workflow.md)

### Phase 2: Defer Gemini key onboarding and simplify contributor documentation

- [ ] Task: Remove Gemini key prompt from initial setup flow
    - [ ] Write failing tests in `tests/scripts/onboarding/test_contributor_setup.py` asserting setup no longer requests a Gemini key during initial onboarding
    - [ ] Update `scripts/onboarding/contributor_setup.py` so setup only asks for the contributor username
    - [ ] Ensure setup success messaging no longer references immediate Gemini key entry
    - [ ] Run the targeted setup tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Add deferred Gemini key prompting when AI functionality is first used
    - [ ] Inspect the current AI-dependent GUI entry points, especially `gui2/pass1_auto_view.py` and any related AI manager hooks
    - [ ] Identify the narrowest contributor-facing entry point where missing Gemini configuration should be detected
    - [ ] Write failing tests for the missing-key behavior at the non-UI logic boundary, focusing on output/result accuracy rather than widget internals
    - [ ] Implement a plain-language deferred prompt flow that explains why the key is needed and allows skipping
    - [ ] Ensure non-AI GUI functionality still works when the key is absent
    - [ ] Run the targeted tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Rewrite contributor onboarding documentation to match the simplified flow
    - [ ] Update `scripts/onboarding/README.md` to remove the upfront Gemini prerequisite and reflect the real setup steps
    - [ ] Add plain-language troubleshooting guidance for setup, update, and submit failure cases
    - [ ] Update any related contributor-facing docs that reference the old onboarding behavior, including `CONTRIBUTING.md` and relevant docs pages if affected
    - [ ] Update folder README files if changed folders require README maintenance under the Conductor workflow
    - [ ] Review the changed docs for consistency with the implemented workflow
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Defer Gemini key onboarding and simplify contributor documentation' (Protocol in workflow.md)

### Phase 3: Add contributor mode and simplify the visible GUI

- [ ] Task: Centralize contributor detection logic
    - [ ] Inspect `gui2/user.py`, `gui2/toolkit.py`, `gui2/main.py`, and any other current username checks
    - [ ] Write failing tests for the rule that a contributor is any user whose username is neither `"1"` nor `"deva"`
    - [ ] Implement a centralized helper or manager method for contributor detection
    - [ ] Replace duplicated or less precise contributor checks with the centralized rule
    - [ ] Run the targeted tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Restrict contributor users to the approved tab set
    - [ ] Write failing tests for the contributor-visible tab list at a non-UI logic boundary, validating the exact allowed tab names
    - [ ] Update `gui2/main.py` so contributor users only see `Transl`, `Pass1Auto`, `Pass1Add`, and `Bold Search`
    - [ ] Ensure non-contributor users still receive the full tab set
    - [ ] Ensure contributor users still receive submission and update actions in the app bar
    - [ ] Run the targeted tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Validate contributor mode integration stays simple and maintainable
    - [ ] Review the final contributor-mode logic for unnecessary branching or hidden role rules
    - [ ] Refactor only if needed to keep the rule explicit and easy to maintain
    - [ ] Run the targeted GUI-adjacent tests again and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Add contributor mode and simplify the visible GUI' (Protocol in workflow.md)

### Phase 4: Improve submission and update guidance for non-technical contributors

- [ ] Task: Expand submit flow error handling and user guidance
    - [ ] Inspect `scripts/onboarding/data_submission.py` and `tests/scripts/onboarding/test_data_submission.py`
    - [ ] Write failing tests for plain-language outcomes covering at least: no username, no changes, auth/permission issues, network issues, and push rejection retry failure
    - [ ] Refactor `scripts/onboarding/data_submission.py` to classify common git failures into contributor-friendly messages
    - [ ] Preserve the existing internal git add/commit/push workflow while improving returned result messages
    - [ ] Run the targeted data submission tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Expand update flow error handling and user guidance
    - [ ] Write failing tests in `tests/scripts/onboarding/test_contributor_update.py` for plain-language guidance on dirty worktree, auth/network issues, and database update problems
    - [ ] Refactor `scripts/onboarding/contributor_update.py` to return clearer next-step guidance for common contributor-facing failures
    - [ ] Ensure update messaging helps the contributor decide what to do next without exposing unnecessary git jargon
    - [ ] Run the targeted update tests and confirm they pass
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Verify contributor-facing messages are consistent across setup, update, and submit flows
    - [ ] Review setup, submit, and update result strings together for tone, clarity, and actionability
    - [ ] Normalize wording where needed so contributor messages feel consistent
    - [ ] Run the full onboarding-related test subset and confirm it passes
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Improve submission and update guidance for non-technical contributors' (Protocol in workflow.md)

### Phase 5: Final onboarding coverage and documentation sync

- [ ] Task: Expand onboarding regression coverage for critical paths
    - [ ] Review onboarding tests under `tests/scripts/onboarding/` to identify any remaining gaps after implementation
    - [ ] Add focused regression tests for the most important real-world failure paths that were previously unprotected
    - [ ] Confirm tests verify externally visible outputs and file outcomes instead of internal implementation details
    - [ ] Run the full onboarding-related test subset and confirm it passes
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Sync README and docs requirements for all touched folders
    - [ ] Update `scripts/README.md` if onboarding behavior or folder responsibilities changed
    - [ ] Update `gui2/README.md` if contributor mode changes the documented GUI behavior
    - [ ] Update relevant `docs/` pages so contributor onboarding documentation matches the final implementation
    - [ ] Review all touched README files for consistency with the changed behavior
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Run final quality checks for this track
    - [ ] Run the relevant onboarding test suite and confirm all targeted tests pass
    - [ ] Run `uv run ruff check --fix` on all changed files
    - [ ] Run `uv run ruff format` on all changed files
    - [ ] Prepare a summary of changed files and a proposed manual commit message for the user
    - [ ] Update implementation notes in `conductor/tracks/contributor_onboarding_20260331/plan.md`
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Final onboarding coverage and documentation sync' (Protocol in workflow.md)
