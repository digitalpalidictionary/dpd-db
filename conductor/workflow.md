# Project Workflow

## Guiding Principles

1. **The Plan is the Source of Truth:** All work must be tracked in `plan.md`
2. **NO AGENT COMMITS:** The AI agent must NEVER execute `git commit`, `git add`, or `git notes`. The user will perform all git operations manually.
3. **The Tech Stack is Deliberate:** Changes to the tech stack must be documented in `tech-stack.md` *before* implementation
4. **Data Output Verification:** Write tests to verify accurate data output. Automated tests are NOT required for UI elements, CSS, or HTML, as these are best verified and tweaked by a human. Do not test UI components - user interaction will reveal UI issues. Do not test internal function implementation details.
5. **User Experience First:** Every decision should prioritize user experience
6. **README Maintenance:** Each project folder contains a `README.md`, which MUST be updated if anything within the folder changes to ensure documentation stays in sync with code.
7. **Non-Interactive & CI-Aware:** Prefer non-interactive commands. Use `CI=true` for watch-mode tools (tests, linters) to ensure single execution.
8. **Proactive Research:** Always perform a Google Search during the planning and task execution phases for any framework-specific (e.g., Flet), OS-specific (e.g., Linux window management), or non-trivial technical requirements to identify known quirks, limitations, or best practices.

## Task Workflow

All tasks follow a strict lifecycle:

### Standard Task Workflow

1. **Select Task:** Choose the next available task from `plan.md` in sequential order

2. **Research & Planning:** 
   - Before marking a task in progress, perform a Google Search to identify any known issues or platform-specific nuances related to the task.
   - Update the implementation approach if research reveals a more robust solution.

3. **Mark In Progress:** Before beginning work, edit `plan.md` and change the task from `[ ]` to `[~]`

3. **Write Failing Tests (Red Phase):**
   - Create a new test file for the feature or bug fix.
   - Write one or more unit tests that clearly define the expected behavior and acceptance criteria for the task.
   - **CRITICAL:** Run the tests and confirm that they fail as expected. This is the "Red" phase of TDD. Do not proceed until you have failing tests.

4. **Implement to Pass Tests (Green Phase):**
   - Write the minimum amount of application code necessary to make the failing tests pass.
   - Run the test suite again and confirm that all tests now pass. This is the "Green" phase.

5. **Refactor (Optional but Recommended):**
    - With the safety of passing tests, refactor the implementation code and the test code to improve clarity, remove duplication, and enhance performance without changing the external behavior.
    - Rerun tests to ensure they still pass after refactoring.

6. **Verify Output Accuracy:** Ensure tests verify data output accuracy. Do not enforce coverage metrics or test internal implementation details. Focus on validating that the system produces correct data outputs.

7. **Document Deviations:** If implementation differs from tech stack:
   - **STOP** implementation
   - Update `tech-stack.md` with new design
   - Add dated note explaining the change
   - Resume implementation

8. **Notify User for Commit:**
   - Inform the user that the task is complete and ready for manual review and commit.
   - List all created/modified files.
   - Propose a clear, concise commit message.

9. **Update Plan:**
    - Read `plan.md`, find the line for the completed task, and update its status from `[~]` to `[x]`.
    - Write the updated content back to `plan.md`.

### Phase Completion Verification and Checkpointing Protocol

**Trigger:** This protocol is executed immediately after a task is completed that also concludes a phase in `plan.md`.

1.  **Announce Protocol Start:** Inform the user that the phase is complete and the verification protocol has begun.

2.  **Ensure Test Coverage for Phase Changes:**
    -   **Step 2.1: Determine Phase Scope:** Identify files changed since the last marked phase.
    -   **Step 2.2: Verify and Create Tests:** For each modified code file, verify a corresponding test file exists. Create missing tests as needed.

3.  **Execute Automated Tests with Proactive Debugging:**
    -   Announce the test command (e.g., `CI=true pytest`).
    -   Execute and debug if necessary (max 2 fix attempts).

4.  **Propose a Detailed, Actionable Manual Verification Plan:**
    -   Generate a step-by-step plan for the user to verify the phase's goals.

5.  **Await Explicit User Feedback:**
    -   Ask the user: "**Does this meet your expectations? Please confirm with yes or provide feedback on what needs to be changed.**"
    -   **PAUSE** and await the user's response.

6.  **Mark Phase as Complete in Plan:**
    -   Update `plan.md` to show the phase is finished.

7.  **Announce Completion:** Inform the user that the phase is complete and ready for their manual checkpoint commit.

### Quality Gates

Before marking any task complete, verify:

- [ ] All tests pass
- [ ] Data output accuracy verified through tests
- [ ] Code follows project's code style guidelines
- [ ] All public functions/methods are documented
- [ ] Type safety is enforced
- [ ] No linting or static analysis errors
- [ ] Works correctly on mobile (if applicable)
- [ ] Documentation updated if needed

## Development Commands

### Daily Development
```bash
# Linting and Formatting
uv run ruff check .
uv run ruff format .

# Testing
uv run pytest
```

## Testing Requirements

### Unit Testing
- Every module must have corresponding tests.
- Test both success and failure cases.

## Commit Guidelines (For User)

### Message Format
```
<type>(<scope>): <description>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests
- `chore`: Maintenance tasks

## Definition of Done

A task is complete when:

1. All code implemented to specification
2. Tests verify data output accuracy and are passing
3. Documentation complete (if applicable)
4. Code passes all configured linting and static analysis checks
5. Implementation notes added to `plan.md`
6. User notified to perform manual commit

## Continuous Improvement

- Review workflow weekly
- Update based on pain points