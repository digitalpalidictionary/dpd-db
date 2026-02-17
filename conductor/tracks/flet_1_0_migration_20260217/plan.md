# Implementation Plan: Flet 1.0 Migration & Architectural Refactor (gui3)

## Phase 1: Environment Setup & Worktree Initialization
- [ ] Task: Create and switch to the `gui3` branch.
- [ ] Task: Initialize a new git worktree for `gui3` at the project root.
- [ ] Task: Update dependencies in `pyproject.toml` to use Flet 0.80.x (Beta) and run `uv sync`.
- [ ] Task: Verify the environment by attempting to run a minimal Flet 1.0 script.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Environment Setup' (Protocol in workflow.md)

## Phase 2: Architecture & Base Component Refactoring
- [ ] Task: Refactor `gui2/ui_utils.py` (or equivalent) to provide Flet 1.0 compatible reusable components.
    - [ ] Task: Implement `DPDButton` (wrapping `content=ft.Text(...)`).
    - [ ] Task: Implement `DPDIcon` and `DPDIconButton` (mapping `icon` property).
- [ ] Task: Define the Base Composition Pattern for Views.
    - [ ] Task: Create a base class or template that uses composition instead of extending `ft.Column`.
- [ ] Task: Update `gui2/main.py` entry point.
    - [ ] Task: Implement `ft.run(main)`.
    - [ ] Task: Update `Theme` configuration to Flet 1.0 standards.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Architecture & Base Components' (Protocol in workflow.md)

## Phase 3: Migration - Core Database & Field Modules
- [ ] Task: Migrate `dpd_fields.py` and its sub-modules (meaning, examples, commentary, etc.).
    - [ ] Task: Write Tests (Red Phase): Verify logic of field managers still produces correct data models.
    - [ ] Task: Implement (Green Phase): Refactor to composition and Flet 1.0 syntax.
- [ ] Task: Migrate `database_manager.py`.
    - [ ] Task: Write Tests (Red Phase): Verify DB interaction logic.
    - [ ] Task: Implement (Green Phase): Refactor and update Flet calls.
- [ ] Task: Migrate `pass2_add_view.py` and `pass1_add_view.py`.
    - [ ] Task: Implement (Green Phase): Heavy lifting of button and alignment refactoring.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Core Database Migration' (Protocol in workflow.md)

## Phase 4: Migration - Search, Filters & Analysis Modules
- [ ] Task: Migrate `bold_search_view.py` and `bold_search_controller.py`.
    - [ ] Task: Write Tests (Red Phase): Verify search parsing logic.
    - [ ] Task: Implement (Green Phase): Refactor to composition and Flet 1.0.
- [ ] Task: Migrate `filter_tab_view.py` and `filter_component.py`.
    - [ ] Task: Implement (Green Phase): Update complex layouts and button properties.
- [ ] Task: Migrate `ai_search.py` and `wordfinder_widget.py`.
    - [ ] Task: Implement (Green Phase): Update popup logic and service calls.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Search & Analysis Migration' (Protocol in workflow.md)

## Phase 5: Migration - Auxiliary Modules & Final Cleanup
- [ ] Task: Migrate remaining views: `sandhi_view.py`, `translations_view.py`, `tests_tab_view.py`.
- [ ] Task: Migrate all utility scripts in `gui2/utilities/`.
- [ ] Task: Global Linting & Formatting.
    - [ ] Task: Run `uv run ruff check --fix` and `uv run ruff format` on the entire `gui3` worktree.
- [ ] Task: Update Documentation.
    - [ ] Task: Update `gui3/README.md` with the new architecture and Flet 1.0 requirements.
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Final Verification' (Protocol in workflow.md)
