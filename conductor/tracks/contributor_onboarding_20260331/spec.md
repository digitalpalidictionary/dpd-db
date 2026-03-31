# Spec: Contributor Onboarding Hardening & Contributor Mode

## Overview

Make DPD contributor onboarding significantly easier and safer for non-technical users while preserving the current submission model of pushing data changes through git from the GUI.

This track improves the existing onboarding flow across setup, update, submission, documentation, and contributor-facing GUI behavior. It focuses on reducing avoidable friction, preventing setup-breaking failures, and making the contributor experience much more guided and understandable.

The primary target users are non-technical contributors using `gui2` for dictionary work. Contributors should be able to follow a small number of setup instructions, launch the GUI, work in a simplified interface, and submit their data through a one-click workflow with human-friendly feedback.

## Functional Requirements

### FR-1: Setup Reliability Hardening
The onboarding setup flow must reliably prepare a contributor machine for GUI use.

Requirements:
1. The setup flow must correctly handle the current database release asset format, including compressed archive assets such as `dpd.db.tar.bz2`.
2. The setup flow must download the correct release asset and ensure that a valid `dpd.db` file is placed in the project root.
3. If archive extraction fails, setup must stop and show a plain-language error explaining what happened and what the contributor should do next.
4. Required submodule initialization must report real success/failure rather than always reporting success.
5. If a required setup step fails, the contributor must receive a friendly explanation instead of a silent or misleading success message.

### FR-2: Simpler Contributor Setup Documentation
The contributor guide must be rewritten to reduce unnecessary cognitive load and better match the real setup flow.

Requirements:
1. The onboarding documentation must no longer require contributors to obtain a Gemini API key before first launch.
2. The documented setup path must reflect the actual supported setup behavior and current script behavior.
3. The documentation must clearly explain:
   - what contributors need before starting,
   - how to launch the GUI,
   - how data submission works,
   - what to do if setup, update, or submission fails.
4. Troubleshooting guidance must be written for non-technical contributors in plain language.

### FR-3: Deferred Gemini API Key Prompt
AI key configuration must be deferred until it is actually needed.

Requirements:
1. The setup flow must not prompt for a Gemini API key.
2. When a contributor first uses AI-dependent functionality, the application must detect the missing key and prompt the user at that point.
3. The prompt must explain why the key is needed and that it is only required for AI-assisted functionality.
4. If the user skips providing the key, non-AI parts of the GUI must continue to work.

### FR-4: Contributor Mode in GUI
Contributors must see a reduced GUI tailored to normal contribution work.

Requirements:
1. A user is considered a contributor if their username is neither `"1"` nor `"deva"`.
2. Contributor users must only see the following tabs:
   - `Transl`
   - `Pass1Auto`
   - `Pass1Add`
   - `Bold Search`
3. Non-contributor users must continue to see the full GUI.
4. Existing contributor-only actions such as submission and update must continue to be available to contributor users.
5. The contributor filtering logic must be simple, explicit, and centralized enough to remain maintainable.

### FR-5: Friendlier Submission and Update Error Handling
Submission and update workflows must be easier for non-technical users to recover from.

Requirements:
1. The submit flow must continue to use git add/commit/push internally.
2. Common failure cases must produce clear, human-friendly guidance, including at minimum:
   - missing username or setup not completed,
   - no changes to submit,
   - authentication or permission problems,
   - push rejection due to upstream changes,
   - update failure caused by local changes or git state,
   - network-related failures.
3. Error messages must avoid git jargon where possible, or explain it in simple terms if it cannot be avoided.
4. The update flow must continue to handle code update, dependency sync, and database refresh, while explaining failures clearly.
5. User-facing dialogs/messages should help the contributor decide the next action without needing developer help for common cases.

### FR-6: Onboarding Test Coverage Expansion
The onboarding flow must be protected by automated tests for critical real-world failures.

Requirements:
1. Tests must cover release asset handling for the current archive-based database format.
2. Tests must cover archive extraction success and failure paths.
3. Tests must cover contributor-mode user detection and reduced-tab behavior where practical through non-UI logic boundaries.
4. Tests must cover important submission/update error paths and ensure that meaningful messages are returned.
5. Tests must focus on output accuracy and externally visible behavior rather than internal implementation details.

## Non-Functional Requirements

1. **Cross-platform support:** The onboarding flow must remain compatible with Windows, macOS, and Linux.
2. **User experience first:** Contributor-facing language must be plain, calm, and action-oriented.
3. **Maintainability:** Contributor detection and tab filtering should be implemented with simple logic, not a complicated role system.
4. **Accuracy:** Setup and update flows must not report success when critical steps actually failed.
5. **Documentation alignment:** README and relevant docs must match the implemented contributor workflow.

## Acceptance Criteria

- [ ] A new contributor can go from repository clone to a working GUI using the documented onboarding flow.
- [ ] The setup flow correctly handles the current database release archive format and produces a usable `dpd.db`.
- [ ] Setup stops with a helpful message when download or extraction fails.
- [ ] Required submodule initialization reports real failures accurately.
- [ ] The setup flow does not ask for a Gemini API key.
- [ ] The application prompts for a Gemini API key only when the user first attempts AI-dependent functionality.
- [ ] Contributors are identified by the rule: username is not `"1"` and not `"deva"`.
- [ ] Contributor users only see the tabs `Transl`, `Pass1Auto`, `Pass1Add`, and `Bold Search`.
- [ ] Non-contributor users still see the full GUI.
- [ ] Submission and update failures return clear, non-technical guidance for common error cases.
- [ ] Automated tests cover critical onboarding failure paths, including archive-based database download/extraction behavior.
- [ ] Contributor-facing onboarding documentation is updated to reflect the simplified workflow and deferred AI-key behavior.

## Out of Scope

- Replacing git-based submission with a non-git submission system
- Creating packaged native installers or standalone app binaries
- Redesigning the entire `gui2` information architecture beyond the contributor tab reduction
- Adding a full permissions or role-management system beyond the explicit username rule
- Broad GUI redesign unrelated to contributor onboarding
